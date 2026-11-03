"""Task 2: the API map generator reads sightlab_utils with ast and reports its surface."""
from pathlib import Path

import pytest

from gen_api_map import build_api_map, write_api_map


@pytest.fixture(scope="module")
def api(SOURCES: Path) -> dict:
    return build_api_map(SOURCES / "sightlab_utils")


def _classes(api: dict) -> dict:
    return api["modules"]["sightlab"]["classes"]


def test_counts(api):
    sl = _classes(api)
    assert len(sl["SightLab"]["methods"]) == 93
    assert sum(len(c["methods"]) for c in sl.values()) == 178
    assert sum(1 for c in sl.values() for m in c["methods"].values() if m["doc"]) == 109


def test_start_trial_kwargs(api):
    names = [p["name"] for p in _classes(api)["SightLab"]["methods"]["startTrial"]["params"]]
    assert "startRatings" in names and "textContinueEvent" in names


def test_init_params(api):
    names = [p["name"] for p in _classes(api)["SightLab"]["init_params"]]
    assert "gui" in names and "hardwareconfig" in names and "self" not in names


def test_private_excluded(api):
    assert not any(n.startswith("_") for c in _classes(api).values() for n in c["methods"])


def test_version_and_settings(api):
    assert api["sightlab_utils_version"].startswith("2.")
    assert "CONTINUE_EVENT_KEY" in api["settings_constants"]


def test_markdown_and_undocumented(tmp_path, api):
    write_api_map(api, tmp_path)
    md = (tmp_path / "sightlab-api.md").read_text()
    assert "## class SightLab" in md and "class GUI" not in md
    und = (tmp_path / "undocumented.md").read_text()
    assert und.count("\n- ") == 69
    assert (tmp_path / "sightlab-api.json").is_file()
