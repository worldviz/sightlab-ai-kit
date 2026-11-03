# Autopilot: run a SightLab 2.x experiment unattended in desktop mode and report on it.
#
#   "C:\Program Files\WorldViz\Vizard8\bin\winviz.exe" autopilot.py <experiment.py>
#         [--trials N] [--seconds-per-trial S] [--timeout T] [--record]
#         [--config PATH] [--assertions PATH] [--run-root DIR]
#
# Runs inside Vizard's Python (3.8 syntax, stdlib + Vizard modules only). The pure half is
# autopilot_core.py. See harness/README.md for the report, the verdicts and the assertions.
#
# What it never does: edit the researcher's script, run in the researcher's folder, or send
# SightLab's own events (SightLab raises those itself when setup completes).
import argparse
import os
import runpy
import shutil
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from autopilot_core import (MarkerSink, RunDirTooLarge, autopilot_blocked, cap_trialcount, decide, demo_mode, finish, load_assertions,  # noqa: E402
                            new_report, pop_prompt, prepare_run_dir, push_prompt, record,
                            should_count_trial_end, write_report,
                            gaze_euler, perform_key_continue, perform_rating_select, pick_look_target, rating_options,
                            register_wait, within_reach)


def parse_args(argv):
    p = argparse.ArgumentParser(description="Run a SightLab 2.x experiment unattended in desktop mode.")
    p.add_argument("script")
    p.add_argument("--trials", type=int, default=None, help="cap setTrialCount at N")
    p.add_argument("--seconds-per-trial", type=float, default=15.0, help="stall limit before the harness steps in")
    p.add_argument("--timeout", type=float, default=120.0, help="whole-run limit in seconds")
    p.add_argument("--record", action="store_true", help="turn on SightLab's screen recording")
    p.add_argument("--config", default=None, help="a saved SightLab config (.stlb) for gui=True scripts")
    p.add_argument("--assertions", default=None, help="autopilot-assertions.json (default: beside the script)")
    p.add_argument("--run-root", default=None, help="where .autopilot/runs/ goes (default: the experiment folder)")
    return p.parse_args(argv)


args = parse_args(sys.argv[1:])
script = os.path.abspath(args.script)
blocked = autopilot_blocked(os.path.dirname(script), args.run_root)
if blocked:
    print("autopilot: refused, %s is present; delete it to allow unattended runs" % blocked, file=sys.stderr)
    sys.stderr.flush()
    os._exit(3)
try:
    run_dir = prepare_run_dir(script, args.run_root)
except RunDirTooLarge as e:
    print("autopilot: %s" % e, file=sys.stderr)
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(1)
copied = os.path.join(run_dir, os.path.basename(script))
report = new_report(script, run_dir)
write_report(report, run_dir)  # provisional: if Vizard dies, the folder still says "failed, not launched"
assertions_path = args.assertions or os.path.join(os.path.dirname(script), "autopilot-assertions.json")
try:
    assertions = load_assertions(assertions_path)
except ValueError as e:
    report["notes"].append(str(e))
    assertions = []
if assertions_path and os.path.isfile(assertions_path):
    shutil.copyfile(assertions_path, os.path.join(run_dir, "autopilot-assertions.json"))

# 1. The experiment must believe it was launched directly from the run copy.
sys.argv = [copied]
os.chdir(run_dir)
sys.path.insert(0, run_dir)

# 2. Demo mode caps.
demo = demo_mode()
report["demo_mode"] = demo
trial_cap = args.trials
timeout = args.timeout
if demo:
    trial_cap = min(trial_cap or 4, 4)
    timeout = min(timeout, 280.0)
spt = args.seconds_per_trial
t0 = time.time()


def now():
    return time.time() - t0


import viz        # noqa: E402
import vizact     # noqa: E402
import vizconnect # noqa: E402
import vizinput   # noqa: E402
import viztask    # noqa: E402

report["vizard"] = viz.version()
written = {"done": False}


def finish_and_quit():
    if written["done"]:
        return
    written["done"] = True
    lab = state.get("lab") if "state" in globals() else None
    if lab is not None:
        try:
            n = lab.getTrialCount()
            report["trials_expected"] = None if n is None or n < 0 else int(n)
            report["gaze_objects"] = list(lab.sceneObjects[sl.GAZE_OBJECTS].keys())
        except Exception as ex:  # noqa: BLE001
            report["notes"].append("finish: %r" % ex)
    finish(report, run_dir, assertions, t0)
    if report["verdict"] == "failed":
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)  # the report is on disk; nothing else is worth keeping
    viz.quit()


def note_exception(kind, exc_type, exc, tb):
    report["exceptions"].append({"kind": kind, "error": "".join(traceback.format_exception(exc_type, exc, tb))[-2000:]})


# 3. Native dialogs block the whole process; nothing inside Vizard can click them.
def _suppress(name, default):
    def fake(*a, **k):
        text = " ".join(str(x) for x in a)[:200]
        record(report, "popup-suppressed", now(), dialog=name, text=text)
        return default
    return fake


vizinput.message = _suppress("message", None)
vizinput.input = _suppress("input", "")
vizinput.choose = _suppress("choose", 0)
if hasattr(vizinput, "ask"):
    vizinput.ask = _suppress("ask", 1)
if hasattr(vizinput, "directory"):
    vizinput.directory = _suppress("directory", "")

try:
    import sightlab_utils
    import sightlab_utils.sightlab as sl
    report["sightlab_version"] = getattr(sightlab_utils, "__version__", None)
except Exception:  # noqa: BLE001
    note_exception("import", *sys.exc_info())
    finish_and_quit()
    raise

state = {
    "lab": None, "started": False, "prompt_up": None, "prompt_stack": [], "last_continue": 0.0, "last_look": 0.0,
    "look_index": 0, "last_progress": 0.0, "trial_open": False, "trial_index": 0, "blind_sent": False,
    "forced_this_trial": False, "forcing": False, "wait_key": None, "key_sent": False, "last_capture": 0.0,
    "trial_budget": 0.0, "blind_entry": None, "blind_at": 0.0,
}


def progress():
    t = now()
    state["last_progress"] = t
    state["blind_sent"] = False
    entry = state.get("blind_entry")
    if entry is not None and entry.get("effect") == "pending":
        entry["effect"] = "unblocked" if t - state["blind_at"] <= 2.0 else "none"
        state["blind_entry"] = None


def capture(name):
    path = os.path.join(run_dir, name)
    try:
        viz.window.screenCapture(path)
        report["screenshots"].append(name)
    except Exception as e:  # noqa: BLE001
        report["notes"].append("screenshot %s failed: %r" % (name, e))


# 4. Force the arguments that make an unattended desktop run possible.
_orig_init = sl.SightLab.__init__


def _init(self, *a, **kw):
    forced = {"hardwareconfig": "Desktop", "vizconnectconfig": None, "pid": False}
    if args.record:
        forced["screenrecord"] = True
    if args.config:
        forced["configpath"] = args.config
    for k, v in forced.items():
        if kw.get(k) != v:
            record(report, "forced-kwarg", now(), arg=k, was=repr(kw.get(k)), now=repr(v))
        kw[k] = v
    requested = cap_trialcount(kw, trial_cap)
    if requested is not None:
        record(report, "trial-cap", now(), requested=requested, capped_to=trial_cap, via="trialcount=")
    state["lab"] = self
    return _orig_init(self, *a, **kw)


sl.SightLab.__init__ = _init

# 4b. BIOPAC: SightLab connects to AcqKnowledge with biopacndt.AcqNdtQuickConnect() and turns
# BIOPAC off when that raises. Without a server the harness stands in, so the markers the script
# and SightLab would send are counted (`marker_calls`); delivery is still a needs_human item.
_orig_quick_connect = sl.biopacndt.AcqNdtQuickConnect


def _quick_connect(*a, **kw):
    try:
        server = _orig_quick_connect(*a, **kw)
        report["biopac"] = "connected"
        return server
    except Exception as ex:  # noqa: BLE001
        report["biopac"] = "stub"
        report["notes"].append("no AcqKnowledge server (%r); counting markers with a stand-in" % (ex,))
        return MarkerSink(on_marker=lambda label: report.__setitem__("marker_calls", report["marker_calls"] + 1))


sl.biopacndt.AcqNdtQuickConnect = _quick_connect

# 5. Trial cap (Review Focus 2: holds wherever the script sets it).
_orig_set_count = sl.SightLab.setTrialCount


def _set_count(self, *a, **kw):
    n = a[0] if a else kw.get("trialCount")
    if trial_cap is not None and isinstance(n, int) and n > trial_cap:
        record(report, "trial-cap", now(), requested=n, capped_to=trial_cap)
        n = trial_cap
        a, kw = (n,), {}
    return _orig_set_count(self, *a, **kw)


sl.SightLab.setTrialCount = _set_count


# 6. Prompts: the harness answers them the way a person would, and knows when one is up.
def _prompt_kind(method, kw):
    if method == "startTrial" and (kw.get("startTrialText") or kw.get("startExperimentText")):
        return "start-text"
    if method == "endTrial" and (kw.get("endTrialText") or kw.get("endExperimentText")):
        return "end-text"
    if method == "showInstructions":
        return "instructions"
    if method == "showRatings":
        return "ratings"
    return None


def _wrap_generator(method, before=None, after=None):
    orig = getattr(sl.SightLab, method)

    def wrapped(self, *a, **kw):
        kind = _prompt_kind(method, kw)
        if before:
            before(self, a, kw)
        if kind:
            # Prompts nest: startTrial shows its text through showInstructions. A stack keeps the
            # outer prompt up while the inner one comes down (harness review fix 1).
            push_prompt(state, kind, n_options=rating_options(a, kw) if kind == "ratings" else None)
            state["last_continue"] = now()
        try:
            gen = orig(self, *a, **kw)
            if hasattr(gen, "__next__"):
                result = yield from gen
            else:
                result = gen
        finally:
            if kind:
                pop_prompt(state)
        if after:
            after(self, result, kw)
        return result

    setattr(sl.SightLab, method, wrapped)


def _before_end(self, a, kw):
    if state["trial_open"]:
        capture("trial_%d_end.png" % state["trial_index"])


def _after_start(self, result, kw):
    state["trial_index"] += 1
    state["trial_open"] = True
    state["forced_this_trial"] = False
    length = kw.get("trialLength")
    # A trial the script said lasts N seconds is not a stall for N + 5 s (harness review fix 4).
    state["trial_budget"] = float(length) + 5.0 if isinstance(length, (int, float)) and length > 0 else 0.0
    progress()
    idx = state["trial_index"]
    vizact.ontimer2(2.0, 0, lambda: capture("trial_%d_start.png" % idx))


def _after_end(self, result, kw):
    if should_count_trial_end(state):
        report["trials_completed"] += 1
    state["trial_open"] = False
    state["trial_budget"] = 0.0
    progress()


_wrap_generator("startTrial", after=_after_start)
_wrap_generator("endTrial", before=_before_end, after=_after_end)
_wrap_generator("showInstructions")
_wrap_generator("showRatings")

# A script's own `yield viztask.waitKeyDown(key)` is a declared wait: press that key for it.
_orig_wait_key = viztask.waitKeyDown


def _wait_key(key, *a, **kw):
    register_wait(state, key)
    return _orig_wait_key(key, *a, **kw)


viztask.waitKeyDown = _wait_key

# Exceptions inside a scheduled task may never reach sys.excepthook; catch them at the source
# so the report says what broke instead of stalling to the timeout (harness review fix 9).
_orig_schedule = viztask.schedule


def _guarded(gen):
    try:
        result = yield from gen
    except Exception:  # noqa: BLE001
        note_exception("task", *sys.exc_info())
        finish_and_quit()
        raise
    return result


def _schedule(task, *a, **kw):
    if hasattr(task, "__next__"):
        return _orig_schedule(_guarded(task), *a, **kw)
    if callable(task):
        def runner(*x, **y):
            gen = task(*x, **y)
            if hasattr(gen, "__next__"):
                return (yield from _guarded(gen))
            return gen
        return _orig_schedule(runner, *a, **kw)
    return _orig_schedule(task, *a, **kw)


viztask.schedule = _schedule


# 7. The driver: autopilot_core.decide() chooses, this performs.
def _forced_end(lab):
    state["forcing"] = True
    try:
        yield from lab.endTrial()
    finally:
        state["forcing"] = False


def tick():
    t = now()
    lab = state["lab"]
    # A script's own showInstructions(); waitEvent('triggerPress') shows on the HUD without going
    # through a wrapped prompt call; treat a visible instructions screen as a prompt.
    effective = state
    if not state["prompt_up"] and lab is not None:
        screen = getattr(lab, "instructionsScreen", None)
        try:
            if screen is not None and screen.getVisible():
                effective = dict(state)
                effective["prompt_up"] = "instructions"
        except Exception:  # noqa: BLE001
            pass
    if lab is not None and state["started"]:
        try:
            report["gaze_objects"] = list(lab.sceneObjects[sl.GAZE_OBJECTS].keys())
        except Exception:  # noqa: BLE001
            pass
    entry = state.get("blind_entry")
    if entry is not None and entry.get("effect") == "pending" and t - state["blind_at"] > 2.0:
        entry["effect"] = "none"
        state["blind_entry"] = None
    for kind, detail in decide(effective, t, spt, timeout):
        if kind == "timeout":
            record(report, "timeout", t, after_s=timeout)
            finish_and_quit()
            return
        if kind == "rating-select":
            # Move the highlighted option before confirming, as a person would with the controller.
            presses = perform_rating_select(state, t, detail,
                                            lambda: viz.sendEvent(viz.getEventID("pressRight"), viz.Event(name="pressRight")))
            record(report, "rating-selected", t, presses=presses, prompt=state.get("rating_prompt"),
                   landed=getattr(lab, "currChoice", None))
        elif kind in ("prompt-continue", "rating-confirmed"):
            state["last_continue"] = t
            viz.sendEvent(viz.getEventID("triggerPress"), viz.Event(name="triggerPress"))
            record(report, kind, t, prompt=detail)
            progress()
        elif kind == "key-continue":
            perform_key_continue(state, t, detail, lambda k: viz.sendEvent(viz.KEYDOWN_EVENT, k))
            record(report, "key-continue", t, key=repr(detail))
            progress()
        elif kind == "blind-continue":
            state["blind_sent"] = True
            state["last_continue"] = t
            viz.sendEvent(viz.KEYDOWN_EVENT, getattr(sl, "CONTINUE_EVENT_KEY", " "))
            viz.sendEvent(viz.getEventID("triggerPress"), viz.Event(name="triggerPress"))
            record(report, "blind-continue", t, stalled_s=detail, trial=state["trial_index"], effect="pending")
            state["blind_entry"] = report["interventions"][-1]
            state["blind_at"] = t
        elif kind == "forced-advance" and lab is not None:
            state["forced_this_trial"] = True
            record(report, "forced-advance", t, trial=state["trial_index"], stalled_s=detail)
            _orig_schedule(_forced_end(lab))
            progress()
    if lab is not None and report["gaze_objects"] and t - state["last_look"] >= 1.5:
        state["last_look"] = t
        objs = lab.sceneObjects[sl.GAZE_OBJECTS]
        eye_pos = viz.MainView.getPosition(viz.ABS_GLOBAL)  # the view, not the raw tracker: SightLab offsets it
        name, state["look_index"] = pick_look_target(report["gaze_objects"], state["look_index"],
                                                     lambda n: objs[n].getVisible(),
                                                     lambda n: within_reach(objs[n].getBoundingBox(viz.ABS_GLOBAL).center, eye_pos))
        if name is None:
            return
        try:
            # On the desktop a person "looks at" something by moving the mouse, which the Mouse-and-
            # Keyboard head tracker accumulates as an absolute euler (it only changes on mouse events,
            # so a set sticks); SightLab's desktop gaze ray then runs straight ahead from the view.
            # The bounding box, not the node position: a gaze object cut from the environment mesh
            # sits at the world origin as a node.
            target = objs[name].getBoundingBox(viz.ABS_GLOBAL).center
            head = vizconnect.getTracker("head_tracker").getRaw()
            direction = [target[i] - eye_pos[i] for i in range(3)]
            head.setEuler(gaze_euler(direction), viz.ABS_GLOBAL)
            gaze_point = lab.sceneObjects.get(sl.GAZE_POINT_OBJECT)
            record(report, "look-at", t, object=name,
                   visible_names=[n for n in report["gaze_objects"] if objs[n].getVisible()],
                   target=[round(v, 3) for v in target],
                   head_euler=[round(v, 1) for v in head.getEuler(viz.ABS_GLOBAL)],
                   gaze_point=[round(v, 3) for v in gaze_point.getPosition(viz.ABS_GLOBAL)] if gaze_point else None)
        except Exception as e:  # noqa: BLE001
            report["notes"].append("look-at %s: %r" % (name, e))


vizact.ontimer(0.5, tick)


# 8. SightLab's own events tell the harness where the run is.
def on_start(e=None):
    state["started"] = True
    progress()
    lab = state["lab"]
    if lab is None:
        return
    try:
        report["trials_expected"] = lab.getTrialCount()
        report["gaze_objects"] = list(lab.sceneObjects[sl.GAZE_OBJECTS].keys())
        vizact.addCallback(lab.GAZE_TIME_EVENT, lambda ev: report.__setitem__("gaze_events_seen", report["gaze_events_seen"] + 1))
        acq = getattr(lab, "acqServer", None)
        if acq is not None and hasattr(acq, "insertGlobalEvent") and not getattr(acq, "_autopilot_stub", False):
            orig_insert = acq.insertGlobalEvent

            def counted_insert(*a, **k):
                report["marker_calls"] += 1
                return orig_insert(*a, **k)

            acq.insertGlobalEvent = counted_insert
    except Exception as ex:  # noqa: BLE001
        report["notes"].append("start hook: %r" % ex)


def on_end(e=None):
    # Give SightLab a moment to close the last trial's files and any recording before reading them.
    vizact.ontimer2(1.5, 0, finish_and_quit)


# vizact.addCallback adds alongside the script's own callbacks; viz.callback would replace them
# (and could be replaced by them), since both files run as __main__ (harness review fix 5).
vizact.addCallback(sl.EXPERIMENT_START, on_start)
vizact.addCallback(sl.EXPERIMENT_END, on_end)
vizact.addCallback(viz.EXIT_EVENT, lambda *a: finish_and_quit() if report["launched"] else None)

_orig_hook = sys.excepthook


def _hook(exc_type, exc, tb):
    note_exception("runtime", exc_type, exc, tb)
    _orig_hook(exc_type, exc, tb)
    finish_and_quit()


sys.excepthook = _hook

# 9. Run the experiment in this process.
try:
    runpy.run_path(copied, run_name="__main__")
    report["launched"] = True
    write_report(report, run_dir)
except Exception:  # noqa: BLE001
    note_exception("run_path", *sys.exc_info())
    finish_and_quit()
