"""Task 4: the static checker finds frame and API mistakes without running Vizard."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from check import check_script

FIXTURES = Path(__file__).resolve().parents[2] / "src" / "harness" / "fixtures"
CHECK = Path(__file__).resolve().parents[2] / "src" / "harness" / "check.py"


@pytest.fixture(scope="module")
def api(kit: Path) -> dict:
    return json.loads((kit / "src" / "api" / "sightlab-api.json").read_text())


@pytest.fixture(scope="module")
def resources(SOURCES: Path) -> set:
    return set((SOURCES / "resources-list.txt").read_text().splitlines())


def codes(report: dict) -> set:
    return {f["code"] for f in report["errors"]} | {f["code"] for f in report["warnings"]}


@pytest.mark.parametrize(
    "fixture, expected",
    [
        ("ok_nongui.py", set()),
        ("alias_import.py", set()),
        ("positional_start.py", set()),
        ("missing_trialcount.py", {"W_NO_TRIAL_COUNT"}),
        ("viz_go.py", {"W_VIZ_GO"}),
        ("unknown_method.py", {"E_UNKNOWN_METHOD"}),
        ("unknown_kwarg.py", {"E_UNKNOWN_KWARG"}),
        ("no_schedule.py", {"E_NO_RUN_EXPERIMENT"}),
        ("bad_env.py", {"W_UNKNOWN_ENVIRONMENT"}),
        # Shipped examples mostly wait on the space key, not EXPERIMENT_START: that is fine.
        ("keydown_wait.py", set()),
        # A generator that calls startTrial with no wait at all runs before setup is complete.
        ("immediate_start.py", {"W_START_TRIAL_IMMEDIATE"}),
        # A single-trial script with no getTrialCount loop needs no setTrialCount.
        ("single_trial.py", set()),
        # gui defaults to True: objects and trial count come from the GUI, so no warnings.
        ("gui_default.py", set()),
        # viztask.schedule accepts the generator object too; shipped STIM example does this.
        ("schedule_call_form.py", set()),
        # Review fix 4: instances held on self, and the bare-import alias, are still checked.
        ("class_based.py", {"E_UNKNOWN_METHOD"}),
        ("bare_import.py", {"E_UNKNOWN_METHOD"}),
        # Review fix 4: a file that imports SightLab but never constructs it is not a pass.
        ("no_instance.py", {"W_NO_INSTANCE"}),
        # E2E follow-ups: Windows backslashes still match; a case-only mismatch is flagged.
        ("backslash_env.py", set()),
        ("case_env.py", {"W_UNKNOWN_ENVIRONMENT"}),
        # textContinueKey replaces the trigger: text that says "trigger" strands a headset participant.
        ("key_and_trigger_text.py", {"W_KEY_REPLACES_TRIGGER"}),
        ("key_and_trigger_end.py", {"W_KEY_REPLACES_TRIGGER"}),
        ("key_desktop_only.py", set()),
        # A folder-only string (concatenated name, media directory) is not a missing file.
        ("folder_concat_env.py", set()),
    ],
)
def test_fixture_codes(fixture, expected, api, resources):
    report = check_script(FIXTURES / fixture, api, resources)
    assert codes(report) == expected, report


def test_case_mismatch_suggests_spelling(api, resources):
    report = check_script(FIXTURES / "case_env.py", api, resources)
    assert any("Plant.osgb" in w["message"] for w in report["warnings"])


def test_cli_default_resources(tmp_path, kit: Path):
    """With resources.json beside it, check.py flags unknown resources with no flags at all."""
    harness = tmp_path / "harness"
    harness.mkdir()
    shutil.copyfile(kit / "src" / "harness" / "check.py", harness / "check.py")
    shutil.copyfile(kit / "src" / "api" / "sightlab-api.json", harness / "sightlab-api.json")
    shutil.copyfile(kit / "src" / "api" / "resources.json", harness / "resources.json")
    r = subprocess.run([sys.executable, str(harness / "check.py"), str(FIXTURES / "bad_env.py")], capture_output=True, text=True, cwd=tmp_path)
    assert r.returncode == 0 and "W_UNKNOWN_ENVIRONMENT" in r.stdout, r.stdout + r.stderr


def test_text_output_names_instances(kit: Path, SOURCES: Path):
    r = subprocess.run([sys.executable, str(CHECK), str(FIXTURES / "ok_nongui.py"), "--api", str(kit / "src" / "api" / "sightlab-api.json")], capture_output=True, text=True)
    assert "instances: sightlab (SightLab)" in r.stdout


def test_default_api_found_beside_or_above(tmp_path, kit: Path):
    """Review fix 1: a copied check.py finds sightlab-api.json beside itself with no flags."""
    harness = tmp_path / "harness"
    harness.mkdir()
    shutil.copyfile(kit / "src" / "harness" / "check.py", harness / "check.py")
    shutil.copyfile(kit / "src" / "api" / "sightlab-api.json", harness / "sightlab-api.json")
    r = subprocess.run([sys.executable, str(harness / "check.py"), str(FIXTURES / "ok_nongui.py")], capture_output=True, text=True, cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert "0 error(s)" in r.stdout


def test_frame_summary(api, resources):
    report = check_script(FIXTURES / "ok_nongui.py", api, resources)
    assert report["frame"] == {
        "gui": False, "sets_trial_count": True, "schedules_run_experiment": True,
        "waits_experiment_start": True, "waits_before_start": True, "start_end_pairs": 1,
    }


def test_no_gaze_object_warns(tmp_path, api, resources):
    src = (FIXTURES / "ok_nongui.py").read_text().replace("gaze=True", "gaze=False")
    p = tmp_path / "nogaze.py"
    p.write_text(src)
    assert codes(check_script(p, api, resources)) == {"W_NO_GAZE_OBJECT"}


def test_ctor_kwarg_checked(tmp_path, api, resources):
    src = (FIXTURES / "ok_nongui.py").read_text().replace("SightLab(gui=False)", "SightLab(gui=False, headlamp=True)")
    p = tmp_path / "ctor.py"
    p.write_text(src)
    assert codes(check_script(p, api, resources)) == {"E_UNKNOWN_KWARG"}


def test_cli_exit_codes(kit: Path, SOURCES: Path):
    api = kit / "src" / "api" / "sightlab-api.json"
    res = SOURCES / "resources-list.txt"
    ok = subprocess.run([sys.executable, str(CHECK), str(FIXTURES / "ok_nongui.py"), "--api", str(api), "--resources", str(res), "--json"], capture_output=True, text=True)
    assert ok.returncode == 0, ok.stderr
    assert json.loads(ok.stdout)["errors"] == []
    bad = subprocess.run([sys.executable, str(CHECK), str(FIXTURES / "unknown_method.py"), "--api", str(api)], capture_output=True, text=True)
    assert bad.returncode == 1
    assert "E_UNKNOWN_METHOD" in bad.stdout


def test_runtime_map_from_package(SOURCES: Path, resources):
    """--sightlab-utils builds the map from an install instead of the bundled JSON."""
    r = subprocess.run([sys.executable, str(CHECK), str(FIXTURES / "ok_nongui.py"), "--sightlab-utils", str(SOURCES / "sightlab_utils"), "--json"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["api_source"].endswith("sightlab_utils") and out["errors"] == []
