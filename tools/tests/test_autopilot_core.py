"""Autopilot plan, Task 1: the pure core of the harness, testable without Vizard."""
import ast
import json
import os
import sys
import time
from pathlib import Path

import pytest

from autopilot_core import (COUNTED_KINDS, HARNESS_VERSION, NEEDS_HUMAN, compute_verdict, demo_mode,
                            evaluate_assertions, finish, load_assertions, new_report, prepare_run_dir, record)

REPORT_KEYS = {
    "verdict", "launched", "demo_mode", "sightlab_version", "vizard", "trials_expected", "trials_completed",
    "interventions", "data_folder", "files", "columns", "assertions", "gaze_objects", "gaze_events_seen",
    "marker_calls", "biopac", "exceptions", "screenshots", "needs_human", "duration_s", "harness_version", "script",
    "run_dir", "notes",
}


def _launched(**over):
    r = new_report("x.py", "/tmp/run")
    r.update({"launched": True, "trials_expected": 2, "trials_completed": 2})
    r.update(over)
    return r


def _summary(run_dir: Path, text: str, name: str = "01-01-2026_p_experiment_summary.csv") -> Path:
    d = run_dir / "data" / "exp"
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_bytes(text.encode("utf-8"))
    return p


def test_prepare_run_dir_copies_only_experiment_folder(tmp_path):
    exp = tmp_path / "Proj" / "Study"
    (exp / "data" / "old").mkdir(parents=True)
    (exp / "study.py").write_text("x")
    (exp / "sightlab_configs").mkdir()
    (exp / "sightlab_configs" / "a.stlb").write_text("cfg")
    other = tmp_path / "Proj" / "Other"
    other.mkdir()
    (other / "big.bin").write_bytes(b"0" * 10)
    run = Path(prepare_run_dir(str(exp / "study.py")))
    assert run.parent.name == "runs" and run.parent.parent.name == ".autopilot" and run.parent.parent.parent == exp
    assert (run / "study.py").is_file() and (run / "sightlab_configs" / "a.stlb").is_file()
    assert not (run / "data").exists() and not list(run.rglob("big.bin"))


def test_prepare_run_dir_skips_git_env_and_skill_folders(tmp_path):
    """Sado 2026-11-05: the run copy must not carry .git, .env files, virtualenvs or project-local skill folders."""
    exp = tmp_path / "Study"
    for d in (".git/objects", ".venv/lib", ".claude/skills/old", ".codex", "node_modules/x", "sightlab_configs"):
        (exp / d).mkdir(parents=True)
    (exp / ".git" / "objects" / "ab").write_text("blob")
    (exp / ".env").write_text("SECRET=1")
    (exp / ".env.local").write_text("SECRET=2")
    (exp / "sightlab_configs" / "a.stlb").write_text("cfg")
    (exp / "study.py").write_text("x")
    run = Path(prepare_run_dir(str(exp / "study.py")))
    assert (run / "study.py").is_file() and (run / "sightlab_configs" / "a.stlb").is_file()
    for gone in (".git", ".env", ".env.local", ".venv", ".claude", ".codex", "node_modules"):
        assert not (run / gone).exists(), gone


def test_trials_exact_assertion_fails_on_extra_trials(tmp_path):
    """Sado 2026-11-05: trials_completed means at least n, so a script that runs extra trials still passes; trials_exact pins it."""
    spec = [{"name": "exact", "type": "trials_exact", "n": 6}]
    (tmp_path / "autopilot-assertions.json").write_text(json.dumps(spec))
    items = load_assertions(str(tmp_path / "autopilot-assertions.json"))
    assert items[0]["type"] == "trials_exact"
    exact = evaluate_assertions(_launched(trials_expected=6, trials_completed=6), str(tmp_path), items)
    assert exact[0]["pass"] is True
    extra = evaluate_assertions(_launched(trials_expected=6, trials_completed=7), str(tmp_path), items)
    assert extra[0]["pass"] is False and "7" in extra[0]["detail"]
    with pytest.raises(ValueError):
        (tmp_path / "bad.json").write_text(json.dumps([{"type": "trials_exact", "n": "6"}]))
        load_assertions(str(tmp_path / "bad.json"))


def test_prepare_run_dir_keeps_last_five(tmp_path):
    exp = tmp_path / "Study"
    exp.mkdir()
    (exp / "s.py").write_text("x")
    runs = exp / ".autopilot" / "runs"
    runs.mkdir(parents=True)
    for i in range(7):
        (runs / f"2026-01-0{i + 1}T00-00-00").mkdir()
    prepare_run_dir(str(exp / "s.py"), keep=5)
    assert len(list(runs.iterdir())) == 5
    assert not (runs / "2026-01-01T00-00-00").exists() and not (runs / "2026-01-02T00-00-00").exists()


def test_new_report_shape():
    r = new_report("x.py", "/tmp/run")
    assert set(r) == REPORT_KEYS
    assert r["verdict"] == "failed" and r["launched"] is False and r["harness_version"] == HARNESS_VERSION
    assert r["interventions"] == [] and r["trials_completed"] == 0


def test_record_appends_intervention():
    r = new_report("x.py", "/tmp/run")
    record(r, "forced-advance", 12.345, trial=2, why="stalled")
    assert r["interventions"] == [{"t": 12.3, "kind": "forced-advance", "trial": 2, "why": "stalled"}]


def test_verdict_failed_on_exception():
    assert compute_verdict(_launched(exceptions=[{"kind": "runtime", "error": "boom"}])) == "failed"


def test_verdict_failed_on_zero_trials():
    assert compute_verdict(_launched(trials_completed=0)) == "failed"


def test_verdict_smoke_when_forced_advance():
    r = _launched()
    record(r, "forced-advance", 10.0)
    assert compute_verdict(r) == "smoke-passed"


def test_verdict_behaviour_when_clean():
    r = _launched()
    record(r, "forced-kwarg", 0.1, arg="pid")
    record(r, "prompt-continue", 3.0)
    record(r, "look-at", 4.0, object="cube")
    assert compute_verdict(r) == "behaviour-verified"


def test_verdict_smoke_when_gaze_objects_but_no_events():
    r = _launched(gaze_objects=["cube"], gaze_events_seen=0)
    assert compute_verdict(r) == "smoke-passed"
    r["gaze_events_seen"] = 1
    assert compute_verdict(r) == "behaviour-verified"


def test_verdict_smoke_when_trials_short():
    assert compute_verdict(_launched(trials_expected=3, trials_completed=2)) == "smoke-passed"


def test_verdict_smoke_when_assertion_failed():
    r = _launched(assertions=[{"name": "a", "type": "trials_completed", "pass": False, "detail": ""}])
    assert compute_verdict(r) == "smoke-passed"


def test_counted_kinds():
    assert {"forced-advance", "popup-suppressed", "blind-continue", "timeout"} <= COUNTED_KINDS
    assert not {"forced-kwarg", "prompt-continue", "look-at", "trial-cap", "rating-confirmed"} & COUNTED_KINDS


def test_column_assertions_read_bom_and_crlf(tmp_path):
    _summary(tmp_path, "﻿Trial Number,Rating\r\n1,5\r\n2,3\r\n")
    r = _launched()
    res = evaluate_assertions(r, str(tmp_path), [
        {"name": "present", "type": "column_present", "file": "summary", "column": "Rating"},
        {"name": "nonempty", "type": "column_nonempty", "file": "summary", "column": "Rating"},
    ])
    assert [a["pass"] for a in res] == [True, True] and r["assertions"] == res


def test_column_nonempty_names_missing_file(tmp_path):
    d = tmp_path / "data" / "exp" / "trial_data"
    d.mkdir(parents=True)
    (d / "x_trial_data_1.csv").write_text("a,Response\n1,k\n")
    (d / "x_trial_data_2.csv").write_text("a\n1\n")
    res = evaluate_assertions(_launched(), str(tmp_path), [{"name": "resp", "type": "column_nonempty", "file": "trial_data", "column": "Response"}])
    assert res[0]["pass"] is False and "x_trial_data_2.csv" in res[0]["detail"]


def test_column_nonempty_fails_on_blank_value(tmp_path):
    _summary(tmp_path, "Trial Number,Rating\n1,5\n2,\n")
    res = evaluate_assertions(_launched(), str(tmp_path), [{"name": "r", "type": "column_nonempty", "file": "summary", "column": "Rating"}])
    assert res[0]["pass"] is False and "row 2" in res[0]["detail"]


def test_value_in_and_min_rows(tmp_path):
    _summary(tmp_path, "Trial Number,Condition\n1,near\n2,far\n3,near\n")
    res = evaluate_assertions(_launched(), str(tmp_path), [
        {"name": "cond", "type": "value_in", "file": "summary", "column": "Condition", "allowed": ["near", "far"]},
        {"name": "rows", "type": "min_rows", "file": "summary", "n": 3},
        {"name": "rows4", "type": "min_rows", "file": "summary", "n": 4},
        {"name": "bad", "type": "value_in", "file": "summary", "column": "Condition", "allowed": ["near"]},
    ])
    assert [a["pass"] for a in res] == [True, True, False, False]


def test_report_assertions(tmp_path):
    r = _launched(gaze_events_seen=2, marker_calls=4)
    res = evaluate_assertions(r, str(tmp_path), [
        {"name": "t", "type": "trials_completed", "n": 2},
        {"name": "g", "type": "gaze_events_min", "n": 3},
        {"name": "m", "type": "marker_calls_min", "n": 4},
    ])
    assert [a["pass"] for a in res] == [True, False, True]


def test_missing_file_kind_fails_not_raises(tmp_path):
    res = evaluate_assertions(_launched(), str(tmp_path), [{"name": "d", "type": "column_present", "file": "dwell", "column": "x"}])
    assert res[0]["pass"] is False and "no" in res[0]["detail"].lower()


def test_load_assertions_rejects_unknown_type(tmp_path):
    p = tmp_path / "a.json"
    p.write_text(json.dumps([{"name": "x", "type": "nope"}]))
    with pytest.raises(ValueError):
        load_assertions(str(p))
    assert load_assertions(str(tmp_path / "absent.json")) == []
    p.write_text(json.dumps([{"name": "x", "type": "min_rows", "file": "summary", "n": 1}]))
    assert len(load_assertions(str(p))) == 1


@pytest.mark.skipif(sys.platform == "win32", reason="registry rule is exercised on the VM")
def test_demo_mode_is_none_off_windows():
    assert demo_mode() is None


def test_finish_writes_report(tmp_path):
    _summary(tmp_path, "Trial Number,Rating\n1,5\n")
    r = _launched(trials_expected=1, trials_completed=1)
    out = finish(r, str(tmp_path), [{"name": "t", "type": "trials_completed", "n": 1}], time.time() - 5)
    saved = json.loads((tmp_path / "autopilot-report.json").read_text())
    assert saved["verdict"] == "behaviour-verified" and saved["duration_s"] >= 5
    assert saved["needs_human"] == NEEDS_HUMAN and saved["files"] and saved["columns"]
    assert out is r


def _state(**over):
    s = {"prompt_up": None, "wait_key": None, "key_sent": False, "last_continue": 0.0, "last_progress": 0.0,
         "started": True, "trial_open": True, "blind_sent": False, "forced_this_trial": False, "trial_index": 1}
    s.update(over)
    return s


def test_decide_prompt_with_pending_key_presses_the_key():
    """Review fix 2: a prompt waiting on textContinueKey must get the key, not only the trigger."""
    from autopilot_core import decide
    actions = decide(_state(prompt_up="start-text", wait_key=" "), t=5.0, spt=15.0, timeout=120.0)
    kinds = [a[0] for a in actions]
    assert "key-continue" in kinds and "prompt-continue" in kinds


def test_decide_prompt_sends_trigger_every_1_5_s():
    from autopilot_core import decide
    assert [a[0] for a in decide(_state(prompt_up="ratings", last_continue=4.0), t=5.0, spt=15.0, timeout=120.0)] == []
    assert [a[0] for a in decide(_state(prompt_up="ratings", last_continue=3.0), t=5.0, spt=15.0, timeout=120.0)] == ["rating-confirmed"]


def test_decide_key_wait_pressed_once():
    from autopilot_core import decide
    s = _state(wait_key=" ", last_continue=0.0)
    assert [a[0] for a in decide(s, t=2.0, spt=15.0, timeout=120.0)] == ["key-continue"]
    assert decide(_state(wait_key=" ", key_sent=True), t=3.0, spt=15.0, timeout=120.0) == []


def test_decide_stall_escalates():
    from autopilot_core import decide
    assert [a[0] for a in decide(_state(last_progress=0.0), t=16.0, spt=15.0, timeout=120.0)] == ["blind-continue"]
    assert [a[0] for a in decide(_state(last_progress=0.0, blind_sent=True), t=31.0, spt=15.0, timeout=120.0)] == ["forced-advance"]
    assert decide(_state(last_progress=0.0, blind_sent=True, forced_this_trial=True), t=40.0, spt=15.0, timeout=120.0) == []


def test_decide_timeout_wins():
    from autopilot_core import decide
    assert [a[0] for a in decide(_state(prompt_up="start-text"), t=121.0, spt=15.0, timeout=120.0)] == ["timeout"]


def test_prompt_stack_restores_outer_prompt():
    """Harness review fix 1: startTrial calls showInstructions internally; leaving the inner wrapper
    must restore the outer prompt, not clear it."""
    from autopilot_core import pop_prompt, push_prompt
    s = _state()
    push_prompt(s, "start-text")
    push_prompt(s, "instructions")
    assert s["prompt_up"] == "instructions"
    pop_prompt(s)
    assert s["prompt_up"] == "start-text"
    pop_prompt(s)
    assert s["prompt_up"] is None


def test_cap_trialcount_kwarg():
    """Harness review fix 3: SightLab(trialcount=20) bypasses setTrialCount; cap it too."""
    from autopilot_core import cap_trialcount
    kw = {"gui": False, "trialcount": 20}
    assert cap_trialcount(kw, 4) == 20 and kw["trialcount"] == 4
    kw2 = {"gui": False, "trialcount": 2}
    assert cap_trialcount(kw2, 4) is None and kw2["trialcount"] == 2
    assert cap_trialcount({"gui": False}, 4) is None


def test_forced_end_is_not_a_completed_trial():
    """Harness review fix 2: the harness's own endTrial never counts."""
    from autopilot_core import should_count_trial_end
    assert should_count_trial_end(_state(forcing=False)) is True
    assert should_count_trial_end(_state(forcing=True)) is False


def test_decide_respects_trial_budget():
    """Harness review fix 4: a 20 s trial with trialLength known is not a stall at 15 s."""
    from autopilot_core import decide
    s = _state(last_progress=0.0, trial_budget=25.0)
    assert decide(s, t=16.0, spt=15.0, timeout=120.0) == []
    assert [a[0] for a in decide(s, t=26.0, spt=15.0, timeout=120.0)] == ["blind-continue"]


def test_blind_continue_without_effect_is_not_counted():
    """Harness review fix 4: a blind continue that unblocked nothing does not cost the behaviour tier."""
    r = _launched()
    record(r, "blind-continue", 16.0, effect="none")
    assert compute_verdict(r) == "behaviour-verified"
    record(r, "blind-continue", 40.0, effect="unblocked")
    assert compute_verdict(r) == "smoke-passed"


def test_prepare_run_dir_refuses_huge_folders(tmp_path):
    """Harness review fix 10 (Review Focus 1): a script in a giant folder must not be copied five times."""
    from autopilot_core import RunDirTooLarge
    exp = tmp_path / "Huge"
    exp.mkdir()
    (exp / "s.py").write_text("x")
    for i in range(5):
        (exp / f"f{i}.bin").write_bytes(b"0")
    with pytest.raises(RunDirTooLarge):
        prepare_run_dir(str(exp / "s.py"), max_files=3)
    assert not (exp / ".autopilot" / "runs").exists() or not list((exp / ".autopilot" / "runs").iterdir())


def test_core_parses_as_python38(kit: Path):
    src = (kit / "src" / "sightlab-2" / "harness" / "autopilot_core.py").read_text()
    ast.parse(src, feature_version=(3, 8))
    assert "f\"" not in src.replace("f\"{", "") or True  # f-strings are fine in 3.8; walrus/match are not
    assert " match " not in src and ":=" not in src


# VM run C (2026-10-31): a key sent to the script resumed it synchronously, the script re-armed its
# next waitKeyDown inside that send, and the glue then cleared the fresh wait; the trial stalled.
def test_register_wait_sets_pending_key():
    from autopilot_core import register_wait
    state = {"wait_key": None, "key_sent": True}
    register_wait(state, [" ", "a"])
    assert state["wait_key"] == " " and state["key_sent"] is False


def test_wait_rearmed_during_key_send_survives():
    from autopilot_core import perform_key_continue, register_wait
    state = {"wait_key": " ", "key_sent": False, "last_continue": 0.0}
    sent = []

    def send(key):
        sent.append(key)
        register_wait(state, " ")  # the script's next waitKeyDown, re-armed inside the dispatch

    perform_key_continue(state, 7.0, " ", send)
    assert sent == [" "]
    assert state["wait_key"] == " " and state["key_sent"] is False and state["last_continue"] == 7.0


def test_key_send_without_rearm_clears_wait():
    from autopilot_core import perform_key_continue
    state = {"wait_key": " ", "key_sent": False, "last_continue": 0.0}
    perform_key_continue(state, 7.0, " ", lambda k: None)
    assert state["wait_key"] is None and state["key_sent"] is True


# e2e gaze_dwell.py hides six of its eight gaze objects per trial; looking at hidden ones wastes the trial.
def test_pick_look_target_prefers_visible():
    from autopilot_core import pick_look_target
    names = ["a", "b", "c", "d"]
    visible = {"a": False, "b": True, "c": False, "d": True}
    assert pick_look_target(names, 0, lambda n: visible[n]) == ("b", 2)
    assert pick_look_target(names, 2, lambda n: visible[n]) == ("d", 4)
    assert pick_look_target(names, 4, lambda n: visible[n]) == ("b", 6)


def test_pick_look_target_keeps_its_place_while_nothing_is_visible():
    from autopilot_core import pick_look_target
    assert pick_look_target(["a", "b", "c"], 1, lambda n: False) == (None, 1)
    # and resumes from the same place once something shows
    assert pick_look_target(["a", "b", "c"], 1, lambda n: n == "c") == ("c", 3)


# VM runs A/B/C (2026-10-31): viz.MainView.lookAt is overridden every frame by the Desktop head tracker;
# gaze events only fired for objects already in view. SightLab's own desktop gaze is the eye node in view
# space (its j/l/i/k keys), so the harness steers that: yaw/pitch toward a target given in view coordinates.
def test_gaze_euler_forward_is_zero():
    from autopilot_core import gaze_euler
    assert gaze_euler([0.0, 0.0, 2.0]) == [0.0, 0.0, 0.0]


def test_gaze_euler_right_and_up():
    from autopilot_core import gaze_euler
    yaw, pitch, roll = gaze_euler([1.0, 0.0, 1.0])
    assert round(yaw, 3) == 45.0 and pitch == 0.0 and roll == 0.0
    yaw, pitch, roll = gaze_euler([0.0, 1.0, 1.0])
    assert yaw == 0.0 and round(pitch, 3) == -45.0  # Vizard pitch is positive downwards


def test_gaze_euler_behind_turns_round():
    from autopilot_core import gaze_euler
    yaw, pitch, _ = gaze_euler([0.0, 0.0, -1.0])
    assert round(abs(yaw), 3) == 180.0 and pitch == 0.0


# VM runs E1/E2E (2026-10-31): SightLab writes setExperimentSummaryData values only on each trial's
# ENTIRE_SCENE row; the per-object rows above it are shorter. Short rows are not empty cells.
SUMMARY_WITH_OBJECT_ROWS = (
    "Participant ID,Trial Number,Label,ROI/Object,Dwell Visits,rating choice\n"
    "p1,1,,Plant,2\n"
    "p1,1,,ENTIRE_SCENE,2,Low\n"
)


def test_column_nonempty_reads_the_entire_scene_row(tmp_path):
    _summary(tmp_path, SUMMARY_WITH_OBJECT_ROWS)
    r = _launched()
    evaluate_assertions(r, str(tmp_path), [{"name": "rating", "type": "column_nonempty", "file": "summary", "column": "rating choice"},
                                          {"name": "allowed", "type": "value_in", "file": "summary", "column": "rating choice", "allowed": ["Low", "Med", "High"]}])
    assert [a["pass"] for a in r["assertions"]] == [True, True], r["assertions"]


def test_column_nonempty_fails_when_no_row_carries_the_column(tmp_path):
    _summary(tmp_path, "Participant ID,Trial Number,Label,ROI/Object,Dwell Visits,rating choice\np1,1,,Plant,2\n")
    r = _launched()
    evaluate_assertions(r, str(tmp_path), [{"name": "rating", "type": "column_nonempty", "file": "summary", "column": "rating choice"}])
    assert r["assertions"][0]["pass"] is False and "no row" in r["assertions"][0]["detail"]


def test_column_nonempty_still_fails_on_a_blank_entire_scene_cell(tmp_path):
    _summary(tmp_path, "Participant ID,Trial Number,Label,ROI/Object,Dwell Visits,rating choice\np1,1,,Plant,2\np1,1,,ENTIRE_SCENE,2,\n")
    r = _launched()
    evaluate_assertions(r, str(tmp_path), [{"name": "rating", "type": "column_nonempty", "file": "summary", "column": "rating choice"}])
    assert r["assertions"][0]["pass"] is False and "empty" in r["assertions"][0]["detail"]


# --- BIOPAC stand-in -------------------------------------------------------------------------
# Eval nback-biopac-markers on the VM: without AcqKnowledge, SightLab's AcqNdtQuickConnect raises,
# SightLab sets acqServer None and biopacFlag False, and neither its automatic trial markers nor
# the script's own reach anything, so marker_calls was 0 for a correct script. The harness stands
# in for the server and counts what would have been sent.

def test_marker_sink_counts_calls_and_keeps_labels():
    from autopilot_core import MarkerSink
    sink = MarkerSink()
    sink.insertGlobalEvent("Trial Start", "stim", "")
    sink.insertGlobalEvent("item basketball repeat", "stim", "")
    assert sink.count == 2
    assert sink.labels == ["Trial Start", "item basketball repeat"]


def test_marker_sink_answers_sightlabs_acquisition_calls():
    from autopilot_core import MarkerSink
    sink = MarkerSink()
    assert sink.getAcquisitionInProgress() is True   # so startTrial never toggles acquisition
    assert sink.toggleAcquisition() is None
    assert sink.count == 0                            # those are not markers


def test_marker_sink_tolerates_methods_it_has_not_heard_of():
    from autopilot_core import MarkerSink
    sink = MarkerSink()
    assert sink.someFutureCall(1, two=2) is None
    assert sink.count == 0


def test_pick_look_target_returns_none_when_nothing_is_visible():
    # Rebuilt memory eval: between phases every object is hidden at the origin; the fallback made
    # the harness stare at the floor under the camera. Nothing visible means look at nothing.
    from autopilot_core import pick_look_target
    name, nxt = pick_look_target(["a", "b"], 0, lambda n: False)
    assert name is None and nxt == 0


# --- 2026-11-03: the harness itself honours NO_AUTOPILOT (Astra/Sado review) ------------------

def test_autopilot_blocked_by_marker_file(tmp_path):
    from autopilot_core import autopilot_blocked
    exp = tmp_path / "exp"
    exp.mkdir()
    assert autopilot_blocked(str(exp)) is None
    (exp / "NO_AUTOPILOT").write_text("")
    assert autopilot_blocked(str(exp)) == str(exp / "NO_AUTOPILOT")
    (exp / "NO_AUTOPILOT").unlink()
    root = tmp_path / "root"
    root.mkdir()
    (root / "NO_AUTOPILOT").write_text("")
    assert autopilot_blocked(str(exp), str(root)) == str(root / "NO_AUTOPILOT")


# --- 2026-11-03: a parked gaze object is not a look-at target (Sado finding: 50 m below the scene) --

def test_within_reach_rejects_parked_and_far():
    from autopilot_core import within_reach
    eye = [0.0, 1.5, 0.0]
    assert within_reach([0.0, 1.2, 2.0], eye)
    assert not within_reach([0.0, -50.0, 0.0], eye)
    assert not within_reach([0.0, 1.5, 40.0], eye)
    assert within_reach([0.0, 1.5, 40.0], eye, max_dist=50.0)


def test_pick_look_target_skips_unreachable():
    from autopilot_core import pick_look_target
    names = ["parked", "near", "far"]
    reach = {"parked": False, "near": True, "far": False}
    name, nxt = pick_look_target(names, 0, lambda n: True, lambda n: reach[n])
    assert name == "near" and nxt == 2
    name, nxt = pick_look_target(names, 2, lambda n: True, lambda n: reach[n])
    assert name == "near"
    assert pick_look_target(names, 0, lambda n: True, lambda n: False) == ("parked", 1)  # nothing nearer: fall back


# --- 2026-11-03: ratings vary across prompts (Sado finding: the harness always chose 1) ----------

def test_rating_steps_cycles_first_middle_last():
    from autopilot_core import rating_steps
    assert [rating_steps(i, 7) for i in range(4)] == [0, 3, 6, 0]
    assert [rating_steps(i, 1) for i in range(3)] == [0, 0, 0]
    assert rating_steps(2, 11) == 10


def test_decide_selects_before_confirming_rating():
    from autopilot_core import decide, pop_prompt, push_prompt
    st = _state(last_continue=3.0)
    push_prompt(st, "ratings", n_options=7)  # first rating prompt: option 0, nothing to press
    assert [a[0] for a in decide(st, t=5.0, spt=15.0, timeout=120.0)] == ["rating-confirmed"]
    pop_prompt(st)
    push_prompt(st, "ratings", n_options=7)  # second: the middle option, three presses first
    assert decide(st, t=7.0, spt=15.0, timeout=120.0) == [("rating-select", 3)]
    st["rating_selected"] = True
    st["last_continue"] = 7.0
    assert [a[0] for a in decide(st, t=9.0, spt=15.0, timeout=120.0)] == ["rating-confirmed"]


# --- 2026-11-03 review fixes ---------------------------------------------------------------------

def test_pick_look_target_falls_back_to_visible_when_nothing_is_in_reach():
    """Review I-6: a scene whose real targets are far must still get looks; reach only orders, never starves."""
    from autopilot_core import pick_look_target
    names = ["far-a", "far-b"]
    name, nxt = pick_look_target(names, 0, lambda n: True, lambda n: False)
    assert name == "far-a" and nxt == 1
    assert pick_look_target(names, 0, lambda n: False, lambda n: False) == (None, 0)


def test_rating_steps_never_exceed_options():
    """Review focus 3 as a property: presses are at most n_options - 1 for every prompt number."""
    from autopilot_core import rating_steps
    for n in range(1, 21):
        for prompt in range(6):
            assert 0 <= rating_steps(prompt, n) <= n - 1


def test_rating_options_from_call_shapes():
    """SightLab calls showRatings(message, ratingScale=...) and showRatings(message, scale) and showRatings(**kw)."""
    from autopilot_core import rating_options
    assert rating_options(("Q?", ["1", "2", "3"]), {}) == 3
    assert rating_options(("Q?",), {"ratingScale": ["a", "b"]}) == 2
    assert rating_options(("Q?",), {}) is None
    assert rating_options((), {"message": "Q?"}) is None


def test_perform_rating_select_then_confirm_over_three_prompts():
    """Review I-7: the full sequence through the core: select (N presses), then confirm, prompt after prompt."""
    from autopilot_core import decide, perform_rating_select, pop_prompt, push_prompt
    sent = []
    st = _state(last_continue=0.0)
    seen = []
    t = 0.0
    for prompt in range(3):
        push_prompt(st, "ratings", n_options=5)
        st["last_continue"] = t
        t += 2.0
        actions = decide(st, t=t, spt=15.0, timeout=120.0)
        if actions and actions[0][0] == "rating-select":
            perform_rating_select(st, t, actions[0][1], lambda: sent.append("pressRight"))
            seen.append(("select", actions[0][1]))
            assert st["rating_selected"] is True and st["last_continue"] == t
            t += 2.0
            actions = decide(st, t=t, spt=15.0, timeout=120.0)
        assert [a[0] for a in actions] == ["rating-confirmed"], (prompt, actions)
        seen.append(("confirm", prompt))
        pop_prompt(st)
    assert seen == [("confirm", 0), ("select", 2), ("confirm", 1), ("select", 4), ("confirm", 2)]
    assert sent.count("pressRight") == 6
