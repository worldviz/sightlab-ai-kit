"""The pure half of the autopilot harness (design 6.1): no Vizard import, Python 3.8, stdlib only.

autopilot.py (the Vizard glue) calls into this module. Everything here is unit-tested on any
machine: run folders, the report, the verdict rules, assertions over the CSVs, demo-mode detection.
"""
from __future__ import annotations

import csv
import glob
import json
import math
import os
import shutil
import sys
import time

HARNESS_VERSION = "2026.11.1"
NO_AUTOPILOT = "NO_AUTOPILOT"  # a file of this name in the experiment folder (or --run-root) stops the harness

# Interventions of these kinds mean the harness had to force its way through: the run can be
# smoke-passed at best (a blind-continue whose effect was "none" is exempt). Everything else
# (forced-kwarg, trial-cap, prompt-continue, rating-confirmed, key-continue, look-at) is the
# harness doing what a person would do at a prompt.
COUNTED_KINDS = {"forced-advance", "popup-suppressed", "blind-continue", "timeout"}

# Always a human's or the hardware's to check, whatever the verdict says.
NEEDS_HUMAN = ["real eye tracking on the headset", "BIOPAC marker delivery", "timing and interaction feel"]

ASSERTION_TYPES = {"column_present", "column_nonempty", "value_in", "min_rows", "trials_completed", "gaze_events_min", "marker_calls_min"}
FILE_KINDS = {
    "summary": "*_experiment_summary.csv",
    "trial_data": os.path.join("trial_data", "*_trial_data_*.csv"),
    "dwell": "*_trial_timeline_dwell_*.csv",
    "fixation": "*_trial_timeline_fixation_saccade_*.csv",
}
RUN_IGNORE = ("data", ".autopilot", "recordings", "__pycache__")
REPORT_NAME = "autopilot-report.json"
MAX_RUN_FILES = 5000
MAX_RUN_BYTES = 500 * 1024 * 1024


class RunDirTooLarge(Exception):
    """The experiment's folder is far bigger than an experiment; refuse to copy it five times over."""


def _measure(exp_dir, max_files, max_bytes):
    files = 0
    size = 0
    for root, dirs, names in os.walk(exp_dir):
        dirs[:] = [d for d in dirs if d not in RUN_IGNORE]
        for n in names:
            files += 1
            try:
                size += os.path.getsize(os.path.join(root, n))
            except OSError:
                pass
            if files > max_files or size > max_bytes:
                raise RunDirTooLarge("%s holds more than %d files or %d MB; move the experiment to its own folder" % (exp_dir, max_files, max_bytes // (1024 * 1024)))
    return files, size


# ----------------------------------------------------------------------------- run folders

def autopilot_blocked(exp_dir, run_root=None):
    """The NO_AUTOPILOT marker's path when one sits in the experiment folder or the run root, else None.

    The agent's instructions honour the marker too; this makes the harness refuse on its own, so a
    researcher who put the file there is protected even from an agent that forgot."""
    for folder in (exp_dir, run_root):
        if folder:
            marker = os.path.join(folder, NO_AUTOPILOT)
            if os.path.isfile(marker):
                return marker
    return None


def prepare_run_dir(script_path, run_root=None, keep=5, max_files=MAX_RUN_FILES, max_bytes=MAX_RUN_BYTES):
    """Copy the experiment's own folder (never its parent, never data/) to a fresh run folder."""
    script_path = os.path.abspath(script_path)
    exp_dir = os.path.dirname(script_path)
    _measure(exp_dir, max_files, max_bytes)
    root = os.path.join(run_root or exp_dir, ".autopilot", "runs")
    os.makedirs(root, exist_ok=True)
    stamp = time.strftime("%Y-%m-%dT%H-%M-%S")
    run_dir = os.path.join(root, stamp)
    n = 1
    while os.path.exists(run_dir):
        n += 1
        run_dir = os.path.join(root, "%s-%d" % (stamp, n))
    shutil.copytree(exp_dir, run_dir, ignore=shutil.ignore_patterns(*RUN_IGNORE))
    runs = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
    for old in runs[:-keep] if keep > 0 else []:
        shutil.rmtree(os.path.join(root, old), ignore_errors=True)
    return run_dir


# ----------------------------------------------------------------------------- report

def new_report(script, run_dir):
    return {
        "verdict": "failed", "launched": False, "demo_mode": None,
        "sightlab_version": None, "vizard": None, "harness_version": HARNESS_VERSION,
        "script": script, "run_dir": run_dir,
        "trials_expected": None, "trials_completed": 0,
        "interventions": [], "data_folder": None, "files": [], "columns": {}, "assertions": [],
        "gaze_objects": [], "gaze_events_seen": 0, "marker_calls": 0, "biopac": "off",
        "exceptions": [], "screenshots": [], "needs_human": list(NEEDS_HUMAN),
        "duration_s": None, "notes": [],
    }


def record(report, kind, t, **fields):
    entry = {"t": round(float(t), 1), "kind": kind}
    entry.update(fields)
    report["interventions"].append(entry)


def write_report(report, run_dir):
    with open(os.path.join(run_dir, REPORT_NAME), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)


def collect_data(report, run_dir):
    data_dir = os.path.join(run_dir, "data")
    report["files"] = []
    report["columns"] = {}
    if not os.path.isdir(data_dir):
        report["data_folder"] = None
        return
    report["data_folder"] = data_dir
    for root, _dirs, files in os.walk(data_dir):
        for f in sorted(files):
            full = os.path.join(root, f)
            rel = os.path.relpath(full, run_dir).replace("\\", "/")
            report["files"].append(rel)
            if f.lower().endswith(".csv"):
                try:
                    with open(full, "r", encoding="utf-8-sig", errors="replace", newline="") as fh:
                        report["columns"][rel] = next(csv.reader(fh), [])
                except OSError as e:
                    report["notes"].append("could not read %s: %r" % (rel, e))


# ----------------------------------------------------------------------------- assertions

def load_assertions(path):
    if not path or not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8-sig") as fh:
        items = json.load(fh)
    if not isinstance(items, list):
        raise ValueError("%s: expected a JSON list of assertions" % path)
    for i, a in enumerate(items):
        if not isinstance(a, dict) or a.get("type") not in ASSERTION_TYPES:
            raise ValueError("%s: assertion %d has an unknown type %r" % (path, i, (a or {}).get("type") if isinstance(a, dict) else a))
        if a["type"] in ("column_present", "column_nonempty", "value_in") and not (a.get("file") in FILE_KINDS and a.get("column")):
            raise ValueError("%s: assertion %d needs file (one of %s) and column" % (path, i, sorted(FILE_KINDS)))
        if a["type"] == "min_rows" and not (a.get("file") in FILE_KINDS and isinstance(a.get("n"), int)):
            raise ValueError("%s: assertion %d needs file and integer n" % (path, i))
        if a["type"] in ("trials_completed", "gaze_events_min", "marker_calls_min") and not isinstance(a.get("n"), int):
            raise ValueError("%s: assertion %d needs integer n" % (path, i))
        if a["type"] == "value_in" and not isinstance(a.get("allowed"), list):
            raise ValueError("%s: assertion %d needs an allowed list" % (path, i))
        a.setdefault("name", "%s #%d" % (a["type"], i))
    return items


def _matching_files(run_dir, kind):
    pattern = os.path.join(run_dir, "data", "**", FILE_KINDS[kind])
    return sorted(glob.glob(pattern, recursive=True))


def _rows(path):
    with open(path, "r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader, [])
        rows = [r for r in reader if any(c.strip() for c in r)]
    return header, rows


def _check_one(report, run_dir, a):
    t = a["type"]
    if t == "trials_completed":
        ok = report["trials_completed"] >= a["n"]
        return ok, "trials_completed=%d, need %d" % (report["trials_completed"], a["n"])
    if t == "gaze_events_min":
        ok = report["gaze_events_seen"] >= a["n"]
        return ok, "gaze_events_seen=%d, need %d" % (report["gaze_events_seen"], a["n"])
    if t == "marker_calls_min":
        ok = report["marker_calls"] >= a["n"]
        return ok, "marker_calls=%d, need %d" % (report["marker_calls"], a["n"])
    files = _matching_files(run_dir, a["file"])
    if not files:
        return False, "no %s file found under data/" % a["file"]
    for path in files:
        name = os.path.basename(path)
        header, rows = _rows(path)
        if t == "min_rows":
            if len(rows) < a["n"]:
                return False, "%s has %d data rows, need %d" % (name, len(rows), a["n"])
            continue
        if a["column"] not in header:
            return False, "%s lacks column %r" % (name, a["column"])
        if t == "column_present":
            continue
        idx = header.index(a["column"])
        # SightLab's summary has one row per gaze object and then an ENTIRE_SCENE row per trial;
        # only that last row carries setExperimentSummaryData columns, so shorter rows are skipped.
        carrying = [(i, row) for i, row in enumerate(rows, 1) if idx < len(row)]
        if not carrying:
            return False, "%s: no row carries column %r" % (name, a["column"])
        for i, row in carrying:
            value = row[idx].strip()
            if t == "column_nonempty" and value == "":
                return False, "%s row %d has an empty %r" % (name, i, a["column"])
            if t == "value_in" and value not in [str(v) for v in a["allowed"]]:
                return False, "%s row %d has %r, not in %r" % (name, i, value, a["allowed"])
    return True, "%d file(s) checked" % len(files)


def evaluate_assertions(report, run_dir, assertions):
    results = []
    for a in assertions:
        try:
            ok, detail = _check_one(report, run_dir, a)
        except Exception as e:  # noqa: BLE001 - a bad CSV is a failed assertion, not a crash
            ok, detail = False, "error while checking: %r" % e
        results.append({"name": a.get("name", a["type"]), "type": a["type"], "pass": bool(ok), "detail": detail})
    report["assertions"] = results
    return results


# ----------------------------------------------------------------------------- verdict

def compute_verdict(report):
    if not report["launched"] or report["exceptions"] or report["trials_completed"] == 0:
        return "failed"
    # A blind continue that unblocked nothing (the script was mid-timer) did no harm and does not count.
    counted = [i for i in report["interventions"] if i["kind"] in COUNTED_KINDS
               and not (i["kind"] == "blind-continue" and i.get("effect") == "none")]
    expected = report["trials_expected"]
    short = expected is not None and report["trials_completed"] < expected
    failed_assertions = [a for a in report["assertions"] if not a["pass"]]
    no_gaze = bool(report["gaze_objects"]) and report["gaze_events_seen"] == 0
    if counted or short or failed_assertions or no_gaze:
        return "smoke-passed"
    return "behaviour-verified"


# ----------------------------------------------------------------------------- driver state helpers

RATING_DEFAULT_OPTIONS = 11  # SightLab's default ratingScale is '0'..'10'


def rating_steps(prompt_number, n_options):
    """How many `pressRight` events to send before confirming the `prompt_number`-th rating prompt
    (0-based): the first prompt keeps option 0, the second takes the middle, the third the last,
    then the cycle repeats. A harness that always confirmed option 0 never exercised the choice."""
    n = max(int(n_options or RATING_DEFAULT_OPTIONS), 1)
    choice = [0, (n - 1) // 2, n - 1][int(prompt_number) % 3]
    return max(0, min(choice, n - 1))


def push_prompt(state, kind, n_options=None):
    """A prompt went up. Prompts nest (startTrial shows its text through showInstructions), so keep a stack.
    A ratings prompt also decides which option this run will choose (see rating_steps)."""
    state.setdefault("prompt_stack", []).append(kind)
    state["prompt_up"] = kind
    if kind == "ratings":
        number = state.get("rating_prompt", 0)
        state["rating_prompt"] = number + 1
        state["rating_steps_pending"] = rating_steps(number, n_options)
        state["rating_selected"] = False


def pop_prompt(state):
    """The innermost prompt came down; the outer one, if any, is still up."""
    stack = state.setdefault("prompt_stack", [])
    if stack:
        stack.pop()
    state["prompt_up"] = stack[-1] if stack else None


def cap_trialcount(kwargs, cap):
    """Cap a SightLab(trialcount=N) constructor argument; returns the original N when it was capped."""
    n = kwargs.get("trialcount")
    if cap is not None and isinstance(n, int) and n > cap:
        kwargs["trialcount"] = cap
        return n
    return None


def should_count_trial_end(state):
    """The harness's own forced endTrial is never a completed trial."""
    return not state.get("forcing", False)


# ----------------------------------------------------------------------------- driver decisions

def register_wait(state, key):
    """The script called viztask.waitKeyDown(key): remember the key the driver should press."""
    state["wait_key"] = key[0] if isinstance(key, (list, tuple)) and key else key
    state["key_sent"] = False


def perform_key_continue(state, t, key, send):
    """Press `key` for the script. The state is settled BEFORE the send: the event resumes the script
    synchronously, and a waitKeyDown it re-arms inside that dispatch must survive (VM run C)."""
    state["last_continue"] = t
    state["key_sent"] = True
    state["wait_key"] = None
    send(key)


LOOK_REACH_M = 30.0  # farther than this from the eye, an object is parked or scenery, not a target


def within_reach(center, eye, max_dist=LOOK_REACH_M):
    """True when `center` is within `max_dist` metres of `eye`: a parked object (say at y = -50)
    is still visible() to Vizard, and turning the head toward it wastes the look."""
    try:
        d = math.sqrt(sum((float(center[i]) - float(eye[i])) ** 2 for i in range(3)))
    except Exception:  # noqa: BLE001
        return True
    return d <= max_dist


def pick_look_target(names, index, is_visible, is_reachable=None):
    """The next visible, reachable gaze object from `index`, or None: (name, next_index)."""
    if not names:
        return None, index
    n = len(names)
    for k in range(n):
        name = names[(index + k) % n]
        try:
            ok = bool(is_visible(name)) and (is_reachable is None or bool(is_reachable(name)))
        except Exception:  # noqa: BLE001
            ok = True
        if ok:
            return name, index + k + 1
    return None, index  # nothing to look at: hidden objects sit wherever they were parked


class MarkerSink(object):
    """Stand-in for SightLab's AcqKnowledge server when none is running.

    Without AcqKnowledge, SightLab's AcqNdtQuickConnect raises, SightLab sets acqServer to None
    and turns BIOPAC off, and no marker is sent anywhere, so a correct script would report zero
    marker calls. The sink answers the calls SightLab makes and counts the markers that would
    have gone out; `on_marker` is called for each one. Delivery stays a needs_human item."""

    _autopilot_stub = True

    def __init__(self, on_marker=None):
        self.count = 0
        self.labels = []
        self._on_marker = on_marker

    def insertGlobalEvent(self, label, *a, **k):
        self.count += 1
        self.labels.append(label)
        if self._on_marker is not None:
            self._on_marker(label)

    def getAcquisitionInProgress(self):
        return True

    def toggleAcquisition(self):
        return None

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return lambda *a, **k: None


def gaze_euler(local):
    """Vizard euler [yaw, pitch, 0] that points a node along `local`, a direction given in that
    node's parent frame (x right, y up, z forward; Vizard's positive pitch looks down). The
    harness gives it head-position-to-target in world space for the desktop head tracker."""
    x, y, z = float(local[0]), float(local[1]), float(local[2])
    yaw = math.degrees(math.atan2(x, z)) or 0.0
    pitch = -math.degrees(math.atan2(y, math.hypot(x, z))) or 0.0
    return [yaw, pitch, 0.0]


def decide(state, t, spt, timeout):
    """What the driver should do now, as a list of (kind, detail) actions; pure, so it is testable.

    state keys: prompt_up (None or the prompt kind), wait_key (a key the script waits on, or None),
    key_sent, last_continue, last_progress, started, trial_open, blind_sent, forced_this_trial,
    trial_budget (seconds the current trial may legitimately take, when the script said so).
    The glue (autopilot.py) performs the actions and updates the state.
    """
    if t > timeout:
        return [("timeout", timeout)]
    actions = []
    budget = max(float(spt), float(state.get("trial_budget") or 0.0))
    if state.get("prompt_up"):
        if t - state.get("last_continue", 0.0) >= 1.5:
            if (state["prompt_up"] == "ratings" and state.get("rating_steps_pending", 0) > 0
                    and not state.get("rating_selected")):
                return [("rating-select", int(state["rating_steps_pending"]))]
            kind = "rating-confirmed" if state["prompt_up"] == "ratings" else "prompt-continue"
            actions.append((kind, state["prompt_up"]))
            # A prompt may be waiting on textContinueKey rather than the trigger: press the key too.
            if state.get("wait_key") is not None and not state.get("key_sent"):
                actions.append(("key-continue", state["wait_key"]))
        return actions
    if state.get("wait_key") is not None and not state.get("key_sent"):
        if t - state.get("last_continue", 0.0) >= 1.0:
            return [("key-continue", state["wait_key"])]
        return []
    if state.get("started"):
        stalled = t - state.get("last_progress", 0.0)
        if stalled > budget and not state.get("blind_sent"):
            return [("blind-continue", round(stalled, 1))]
        if stalled > 2 * budget and state.get("trial_open") and not state.get("forced_this_trial"):
            return [("forced-advance", round(stalled, 1))]
    return []


# ----------------------------------------------------------------------------- demo mode

def demo_mode():
    """True on a trial (no-key) install, False when licensed, None where there is no registry.

    Mirrors sightlab.py's check_registry_key_exists (7909-7922) for a single-machine run: a
    value containing MULTI or SINGLE means licensed; a missing key or any other value means demo.
    """
    if sys.platform != "win32":
        return None
    try:
        import winreg  # noqa: WPS433 - Windows only
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WorldViz\Sightlab2", 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        try:
            value, _ = winreg.QueryValueEx(key, "EXT_PATH")
        finally:
            winreg.CloseKey(key)
    except FileNotFoundError:
        return True
    except Exception:  # noqa: BLE001
        return True
    value = str(value)
    if "MULTI" in value or "SINGLE" in value:
        return False
    return True


# ----------------------------------------------------------------------------- finish

def finish(report, run_dir, assertions, t0):
    collect_data(report, run_dir)
    evaluate_assertions(report, run_dir, assertions)
    report["verdict"] = compute_verdict(report)
    report["duration_s"] = round(time.time() - t0, 1)
    report["needs_human"] = list(NEEDS_HUMAN)
    write_report(report, run_dir)
    return report
