"""Autopilot plan, Task 2: static checks on the Vizard glue (it only runs inside Vizard)."""
import ast
import re
from pathlib import Path

from allowlists import HARNESS


def _src(kit: Path) -> str:
    return (kit / "src" / "harness" / "autopilot.py").read_text(encoding="utf-8")


def test_parses_as_python38(kit: Path):
    ast.parse(_src(kit), feature_version=(3, 8))
    assert ":=" not in _src(kit)


def test_never_sends_sightlab_events(kit: Path):
    src = _src(kit)
    for ev in ("EXPERIMENT_START", "TRIAL_START", "TRIAL_END", "EXPERIMENT_END"):
        assert not re.search(r"sendEvent\(\s*(sl\.)?%s" % ev, src), ev


def test_imports_core_only_from_sibling(kit: Path):
    src = _src(kit)
    assert "from autopilot_core import" in src
    assert "tools" not in [n.names[0].name.split(".")[0] for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Import)]


def test_spike_deleted(kit: Path):
    assert not (kit / "src" / "harness" / "autopilot_spike.py").exists()


def test_allowlist_ships_both():
    assert "harness/autopilot.py" in HARNESS and "harness/autopilot_core.py" in HARNESS


def test_cli_flags_present(kit: Path):
    src = _src(kit)
    for flag in ("--trials", "--seconds-per-trial", "--timeout", "--record", "--config", "--assertions", "--run-root"):
        assert flag in src, flag


def test_event_subscriptions_do_not_use_single_slot_callback(kit: Path):
    """Harness review fix 5: viz.callback holds one callback per event per module; a script's own
    callback would replace ours. Subscribe with vizact.addCallback."""
    src = _src(kit)
    assert not re.search(r"viz\.callback\(\s*sl\.", src)
    for ev in ("EXPERIMENT_START", "EXPERIMENT_END"):
        assert re.search(r"vizact\.addCallback\(\s*sl\.%s" % ev, src), ev


def test_glue_uses_core_helpers(kit: Path):
    src = _src(kit)
    for name in ("push_prompt", "pop_prompt", "cap_trialcount", "should_count_trial_end", "RunDirTooLarge", "instructionsScreen", "trial_budget", "viztask.schedule ="):
        assert name in src, name


def test_patches_vizinput_and_prompts(kit: Path):
    src = _src(kit)
    for name in ("vizinput.message", "vizinput.input", "vizinput.choose", "showInstructions", "showRatings", "setTrialCount"):
        assert name in src, name


def test_trigger_event_carries_an_argument(kit: Path):
    # VM run B (2026-10-31): SightLab's pressConfirm(e) and every example's trigger handler take one
    # event argument; a bare sendEvent(getEventID("triggerPress")) raised TypeError inside showRatings.
    src = _src(kit)
    assert not re.search(r'sendEvent\(\s*viz\.getEventID\(\s*"triggerPress"\s*\)\s*\)', src)
    assert re.search(r'sendEvent\(\s*viz\.getEventID\(\s*"triggerPress"\s*\)\s*,\s*viz\.Event\(', src)


def test_glue_uses_wait_and_look_helpers(kit: Path):
    src = _src(kit)
    for name in ("register_wait", "perform_key_continue", "pick_look_target"):
        assert re.search(r"\b%s\(" % name, src), name


def test_look_at_turns_the_desktop_head_tracker_at_the_bounding_box(kit: Path):
    # VM pass 3 diagnostics: a gaze object's node position can be the world origin (its transform is
    # baked into the environment mesh), and SightLab's desktop gaze ray does not follow the raw eye
    # node's rotation. What a person does on the desktop is move the mouse, which the Mouse-and-
    # Keyboard tracker accumulates as an absolute euler; so the harness turns that tracker toward
    # the object's world bounding-box centre.
    src = _src(kit)
    block = src[src.index('t - state["last_look"]'):src.index("vizact.ontimer(0.5, tick)")]
    assert "MainView.lookAt" not in src
    assert "eye_tracker" not in block
    assert re.search(r"vizconnect\.getTracker\(\s*['\"]head_tracker['\"]\s*\)\.getRaw\(\)", block)
    assert re.search(r"getBoundingBox\(\s*viz\.ABS_GLOBAL\s*\)\.center", block)
    assert re.search(r"\.setEuler\(\s*gaze_euler\([^)]*\)\s*,\s*viz\.ABS_GLOBAL\s*\)", block)
    # Final pass, run A: the raw tracker says 1.82 m but the view sits at 1.53 m (SightLab offsets
    # it), so a ray measured from the tracker lands 0.3 m low and misses a small cube 2 m away.
    assert "head.getPosition" not in block
    assert re.search(r"viz\.MainView\.getPosition\(\s*viz\.ABS_GLOBAL\s*\)", block)


def test_look_at_records_where_the_head_and_gaze_point_went(kit: Path):
    # VM pass 3: look-ats ran without error and gaze events stayed at 0; the report records the
    # target point, the head's euler after the set, and SightLab's gaze point so the next such
    # run explains itself.
    src = _src(kit)
    block = src[src.index('record(report, "look-at"'):]
    block = block[:block.index(")\n")]
    for field in ("head_euler=", "target=", "gaze_point=", "visible_names="):
        assert field in block, field


def test_biopac_connect_is_wrapped_with_a_counting_stand_in(kit: Path):
    # Eval nback-biopac-markers: without AcqKnowledge SightLab turns BIOPAC off and marker_calls
    # stayed 0 for a correct script. The harness stands in for the server and counts the markers.
    src = _src(kit)
    assert re.search(r"sl\.biopacndt\.AcqNdtQuickConnect\s*=\s*_quick_connect", src)
    assert "MarkerSink(" in src
    # the real-connection counter in on_start must not also count the stand-in's calls
    assert '_autopilot_stub' in src[src.index("def on_start"):]


def test_glue_refuses_when_no_autopilot_marker_present(kit: Path):
    """The marker is enforced by the harness, not only by the agent's instructions: checked before any copy."""
    text = (kit / "src" / "harness" / "autopilot.py").read_text(encoding="utf-8")
    assert "autopilot_blocked(" in text and text.index("autopilot_blocked(") < text.index("prepare_run_dir(")
    assert "os._exit(3)" in text


def test_look_at_filters_by_reach(kit: Path):
    text = (kit / "src" / "harness" / "autopilot.py").read_text(encoding="utf-8")
    assert "within_reach(" in text
    i = text.index("pick_look_target(report[\"gaze_objects\"]")
    assert "within_reach" in text[i:i + 600]


def test_glue_performs_rating_select_with_press_right(kit: Path):
    text = (kit / "src" / "harness" / "autopilot.py").read_text(encoding="utf-8")
    assert '"rating-select"' in text and 'getEventID("pressRight")' in text
    assert "n_options=" in text  # the options count reaches push_prompt from showRatings' ratingScale


def test_autopilot_refuses_before_touching_anything(kit: Path, tmp_path: Path):
    """Review focus 1, as behaviour: with the marker present the harness exits 3 and creates no run folder,
    before it ever imports viz (so this runs on any Python)."""
    import subprocess
    import sys
    exp = tmp_path / "exp"
    exp.mkdir()
    (exp / "study.py").write_text("print('never runs')\n", encoding="utf-8")
    (exp / "NO_AUTOPILOT").write_text("", encoding="utf-8")
    r = subprocess.run([sys.executable, str(kit / "src" / "harness" / "autopilot.py"), str(exp / "study.py")],
                       capture_output=True, text=True, cwd=tmp_path)
    assert r.returncode == 3, (r.returncode, r.stderr)
    assert "NO_AUTOPILOT" in r.stderr and not (exp / ".autopilot").exists()


def test_glue_uses_core_rating_helpers(kit: Path):
    text = (kit / "src" / "harness" / "autopilot.py").read_text(encoding="utf-8")
    assert "perform_rating_select(" in text and "rating_options(" in text
