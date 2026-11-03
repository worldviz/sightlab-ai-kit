"""Task 3: the examples index describes every shipped example folder for the agent."""
import json
from pathlib import Path

import pytest

from gen_api_map import build_api_map
from gen_examples_index import build_examples_index, write_examples_index


@pytest.fixture(scope="module")
def api(SOURCES: Path) -> dict:
    return build_api_map(SOURCES / "sightlab_utils")


@pytest.fixture(scope="module")
def index(SOURCES: Path, api: dict) -> list:
    return build_examples_index(SOURCES / "ExampleScripts", api)


def _entry(index: list, folder: str) -> dict:
    found = [e for e in index if e["folder"] == folder]
    assert found, f"{folder} not indexed"
    return found[0]


def test_folder_count(index):
    assert 90 <= len(index) <= 98
    assert not any(e["folder"] in ("_dashboard", "_downloaded", "regenerate_test") for e in index)


def test_gaze_example(index):
    e = _entry(index, "Gaze_Based_Interactions")
    assert "addSceneObject" in e["methods"]
    assert e["flags"]["gaze"] is True
    assert "Gaze_Based_Interaction_Simple.py" in e["scripts"]


def test_biopac_flag(index):
    assert _entry(index, "Biopac Saving to Data Files")["flags"]["biopac"] is True


def test_nested_scripts(tmp_path, api):
    (tmp_path / "Deep" / "sub").mkdir(parents=True)
    (tmp_path / "Deep" / "sub" / "run.py").write_text("import sightlab_utils.sightlab as sl\nsightlab = sl.SightLab(gui=False)\n")
    index = build_examples_index(tmp_path, api)
    assert [e["folder"] for e in index] == ["Deep"]
    assert index[0]["scripts"] == ["sub/run.py"]


def test_hints_use_word_boundaries(tmp_path, api):
    """Review fix 6: 'question' is not a Quest; a comment is not a BIOPAC dependency."""
    d = tmp_path / "Survey"
    d.mkdir()
    d.write_text if False else None
    (d / "survey.py").write_text(
        "import sightlab_utils.sightlab as sl\nsightlab = sl.SightLab(gui=False)\n"
        "# ask the question; BIOPAC is not used here\nBIOPAC_ON = False\n"
    )
    e = build_examples_index(tmp_path, api)[0]
    assert e["hardware_hints"] == [] and e["flags"]["biopac"] is False


def test_biopac_flag_requires_real_use(tmp_path, api):
    d = tmp_path / "Markers"
    d.mkdir()
    (d / "markers.py").write_text("import sightlab_utils.sightlab as sl\nsightlab = sl.SightLab(gui=False, biopac=True)\n")
    assert build_examples_index(tmp_path, api)[0]["flags"]["biopac"] is True
    d2 = tmp_path / "Quest"
    d2.mkdir()
    (d2 / "q.py").write_text("import sightlab_utils.sightlab as sl\nsightlab = sl.SightLab(hardwareconfig='Meta Quest Pro')\n")
    assert build_examples_index(tmp_path, api)[1]["hardware_hints"] == ["Quest Pro"]


def test_summary_is_never_code(index):
    bad = [e["folder"] for e in index if e["summary"].startswith(("import ", "from ", "def ", "class "))]
    assert bad == []


def test_markdown(tmp_path, index):
    write_examples_index(index, tmp_path)
    md = (tmp_path / "index.md").read_text()
    assert "| Folder | What it shows | SightLab calls | Needs |" in md
    assert md.count("\n| ") == len(index) + 2  # header + separator + one row per entry
    data = json.loads((tmp_path / "index.json").read_text())
    assert len(data) == len(index)
