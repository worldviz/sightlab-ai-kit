"""Evals plan, Task 2: the scorer turns a check report and an autopilot report into one honest row."""
import json
from pathlib import Path

from autopilot_core import new_report, record
from score_eval import append_scoreboard, score


def _eval_dir(kit: Path) -> Path:
    return kit / "src" / "sightlab-2x" / "evals" / "gaze-dwell-rating"


def _check(errors=0, warnings=1) -> dict:
    return {"errors": [{"code": "E_X", "line": 1, "message": "x"}] * errors,
            "warnings": [{"code": "W_X", "line": 0, "message": "x"}] * warnings, "frame": {}, "instances": {"sightlab": "SightLab"}}


def _autopilot(verdict="behaviour-verified", assertions=None) -> dict:
    r = new_report("gaze_dwell.py", "/tmp/run")
    r.update({"launched": True, "trials_expected": 4, "trials_completed": 4, "gaze_objects": ["a"], "gaze_events_seen": 2,
              "sightlab_version": "2.9.3", "verdict": verdict})
    r["assertions"] = assertions if assertions is not None else [
        {"name": n, "type": "column_nonempty", "pass": True, "detail": ""} for n in ("four trials completed", "left rating stored every trial")]
    if verdict == "smoke-passed":
        record(r, "forced-advance", 10.0)
    return r


META = {"agent": "claude-code 2.1.195", "kit_version": "2026.11.0-dev", "date": "2026-10-31", "tokens": 12345, "wall_s": 240.0}


def test_pass_row(kit):
    row = score(_eval_dir(kit), _check(), _autopilot(), META)
    assert row["pass"] is True and row["verdict"] == "behaviour-verified"
    assert row["eval"] == "gaze-dwell-rating" and row["check_errors"] == 0 and row["check_warnings"] == 1
    assert row["trials"] == "4/4" and row["assertions_passed"] == "2/2" and row["counted_interventions"] == 0
    assert row["sightlab_utils_version"] == "2.9.3" and row["cost_tokens"] == 12345


def test_fail_on_check_error(kit):
    row = score(_eval_dir(kit), _check(errors=1), _autopilot(), META)
    assert row["pass"] is False and row["check_errors"] == 1


def test_smoke_is_not_a_pass(kit):
    row = score(_eval_dir(kit), _check(), _autopilot("smoke-passed"), META)
    assert row["pass"] is False and row["counted_interventions"] == 1


def test_assertion_mismatch_flagged(kit):
    """Review Focus 2: an assertion column the brief never mentions fails the eval, not the harness."""
    extra = [{"name": "bogus", "type": "column_nonempty", "file": "summary", "column": "Rating_middle", "pass": True, "detail": ""}]
    row = score(_eval_dir(kit), _check(), _autopilot(assertions=extra), META)
    assert row["assertion_mismatch"] == ["bogus"] and row["pass"] is False


def test_brief_trials_mismatch_flagged(kit):
    """Review fix 3 (plan Review Focus 5): the brief's §10 count is read and compared with the script's."""
    row = score(_eval_dir(kit), _check(), _autopilot(), META)
    assert row["brief_trials"] == 4 and row["brief_trials_mismatch"] is False
    short = _autopilot()
    short["trials_expected"] = 3
    short["trials_completed"] = 3
    row = score(_eval_dir(kit), _check(), short, META)
    assert row["brief_trials_mismatch"] is True and row["pass"] is False


def test_missing_autopilot_report_is_not_a_pass(kit):
    row = score(_eval_dir(kit), _check(), None, META)
    assert row["pass"] is False and row["verdict"] is None and row["trials"] == "-"


def test_scoreboard_appends_once_header(tmp_path, kit):
    out = tmp_path / "2026-11.md"
    append_scoreboard(score(_eval_dir(kit), _check(), _autopilot(), META), out)
    append_scoreboard(score(_eval_dir(kit), _check(errors=2), None, META), out)
    text = out.read_text()
    assert text.count("| Eval |") == 1 and text.count("\n| gaze-dwell-rating |") == 2
    assert "behaviour-verified" in text and "✔" in text and "✘" in text
