"""E2E follow-ups, Task 1: the shipped resource names, generated from the fetched list."""
import json
import shutil
import zipfile
from pathlib import Path

import pytest

from build_kit import build
from gen_resources import build_resources, write_resources


@pytest.fixture(scope="module")
def res(SOURCES: Path) -> dict:
    return build_resources(SOURCES / "resources-list.txt")


def test_folders_and_counts(res):
    env = res["folders"]["environments"]
    assert len(env) == 29 and "complete_scene.osgb" in env
    assert "Plant.osgb" in res["folders"]["objects"] and "basketball.osgb" in res["folders"]["objects"]
    assert "generated" in res


def test_all_paths_relative(res):
    assert res["all"] and not any(p.startswith("/") or ".." in p for p in res["all"])
    assert all(p == p.replace("\\", "/") for p in res["all"])


def test_markdown_lists_every_environment(tmp_path, res):
    write_resources(res, tmp_path)
    md = (tmp_path / "resources.md").read_text(encoding="utf-8")
    for name in res["folders"]["environments"]:
        assert f"`{name}`" in md
    assert "## environments" in md and "## objects" in md
    assert json.loads((tmp_path / "resources.json").read_text())["folders"]["objects"] == res["folders"]["objects"]


def test_shipped_in_wrappers(tmp_path, kit):
    shutil.copytree(kit / "src", tmp_path / "src")
    build(tmp_path / "src", kit / "templates", tmp_path / "dist", "0.0.0-test", kit / "SightLab-VR-Assistant-0.80.6")
    d = tmp_path / "dist"
    for rel in ("claude-plugin/skills/sightlab-2x/api/resources.json",
                "openai-plugin/skills/sightlab-2x/api/resources.md"):
        assert (d / rel).is_file(), rel
    assert any(n.endswith("api/resources.json") for n in zipfile.ZipFile(d / "chat-bundle.zip").namelist())


# --- sizes (2026-10-31: the memory eval put a life-size chair on a table because the kit listed
# names only; the agent marked the scale assumed) ---------------------------------------------

MEAS = {
    "generated": "2026-10-31T21:00Z", "vizard": "8.0", "root": "x",
    "folders": {
        "objects": {
            "Table.osgb": {"size": [1.2, 0.75, 0.6], "center": [0.0, 0.375, 0.0]},
            "Baseball.osgb": {"size": [0.074, 0.074, 0.074], "center": [0.0, 0.037, 0.0]},
            "chair.osgb": {"size": [0.6, 0.95, 0.6], "center": [0.0, 0.475, 0.0]},
        },
        "environments": {"whiteroom.osgb": {"size": [8.0, 3.0, 8.0], "center": [0.0, 1.5, 0.0]}},
    },
    "failed": [],
}


def test_size_class_bands():
    from gen_resources import size_class
    assert size_class([0.074, 0.074, 0.074]) == "hand-held"
    assert size_class([0.3, 0.5, 0.3]) == "table-top"
    assert size_class([0.6, 0.95, 0.6]) == "large"


def test_sizes_folded_in_by_path(SOURCES: Path):
    res = build_resources(SOURCES / "resources-list.txt", measurements=MEAS)
    assert res["sizes"]["objects/Table.osgb"] == {"size": [1.2, 0.75, 0.6], "center": [0.0, 0.375, 0.0], "bottom": 0.0, "class": "large"}
    assert res["sizes"]["objects/Baseball.osgb"]["class"] == "hand-held"
    assert res["folders"]["objects"] == build_resources(SOURCES / "resources-list.txt")["folders"]["objects"]  # names unchanged


def test_markdown_shows_size_class_and_bottom(tmp_path, SOURCES: Path):
    res = build_resources(SOURCES / "resources-list.txt", measurements=MEAS)
    write_resources(res, tmp_path)
    md = (tmp_path / "resources.md").read_text(encoding="utf-8")
    assert "| `Table.osgb` | 1.20 × 0.75 × 0.60 | large | 0.00 |" in md
    assert "| `Baseball.osgb` | 0.07 × 0.07 × 0.07 | hand-held | 0.00 |" in md
    assert "| `whiteroom.osgb` | 8.00 × 3.00 × 8.00 |" in md
    assert "`Plant.osgb` | unmeasured" in md  # listed, no measurement


def test_without_measurements_markdown_is_names_only(tmp_path, SOURCES: Path):
    res = build_resources(SOURCES / "resources-list.txt")
    assert "sizes" not in res
    write_resources(res, tmp_path)
    md = (tmp_path / "resources.md").read_text(encoding="utf-8")
    assert "unmeasured" not in md and "| `Table.osgb` |" not in md
