"""Evals plan, Task 1: four evaluation tasks, each a complete brief with harness-readable assertions."""
import re
import shutil
from pathlib import Path

import pytest

from autopilot_core import load_assertions
from build_kit import build

SLUGS = ["gaze-dwell-rating", "nback-biopac-markers", "stim-visual-search", "memory-two-conditions"]
SECTION_IDS = ["purpose", "design", "stimuli", "procedure", "instructions", "responses", "ivs", "dvs", "data-logging", "trials", "notes", "hardware"]


@pytest.fixture(scope="module")
def evals(kit: Path) -> Path:
    return kit / "src" / "sightlab-2x" / "evals"


def test_four_evals_present(evals: Path):
    for slug in SLUGS:
        for name in ("brief.md", "autopilot-assertions.json", "acceptance.md"):
            assert (evals / slug / name).is_file(), f"{slug}/{name}"
    assert (evals / "README.md").is_file()


def test_brief_has_twelve_sections(evals: Path):
    for slug in SLUGS:
        text = (evals / slug / "brief.md").read_text(encoding="utf-8")
        ids = re.findall(r"<!--\s*id:\s*([a-z-]+)", text)
        assert ids == SECTION_IDS, (slug, ids)


def test_assertions_load(evals: Path):
    for slug in SLUGS:
        items = load_assertions(str(evals / slug / "autopilot-assertions.json"))
        assert len(items) >= 3, slug
        assert any(a["type"] == "trials_completed" for a in items), slug


def _trials_in_brief(text: str) -> int:
    section = text.split("<!-- id: trials")[1].split("## ")[0]
    m = re.search(r"setTrialCount\((\d+)\)", section) or re.search(r"\b(\d+)\b", section)
    assert m, "no trial count in §10"
    return int(m.group(1))


def test_trials_assertion_matches_brief(evals: Path):
    """Review Focus 1: the brief's trial count and the harness assertion agree."""
    for slug in SLUGS:
        text = (evals / slug / "brief.md").read_text(encoding="utf-8")
        n = next(a["n"] for a in load_assertions(str(evals / slug / "autopilot-assertions.json")) if a["type"] == "trials_completed")
        assert _trials_in_brief(text) == n, slug
        assert n <= 4, slug  # demo mode


def test_named_resources_ship(evals: Path, SOURCES: Path):
    """Review fix 8: every *.osgb a brief names must exist in sightlab_resources."""
    shipped = {Path(line).name for line in (SOURCES / "resources-list.txt").read_text().splitlines()}
    for slug in SLUGS:
        text = (evals / slug / "brief.md").read_text(encoding="utf-8")
        for name in re.findall(r"`([^`/\s]+\.osgb)`", text, re.I):
            assert name in shipped, (slug, name)
        assert "vase" not in text, slug


def test_acceptance_sections(evals: Path):
    for slug in SLUGS:
        text = (evals / slug / "acceptance.md").read_text(encoding="utf-8")
        for h in ("## Pass means", "## Feel pass (human)", "## Known hard parts"):
            assert h in text, (slug, h)
        assert text.count("\n") <= 40, slug


def test_evals_ship_in_all_wrappers(tmp_path: Path, kit: Path):
    shutil.copytree(kit / "src", tmp_path / "src")
    build(tmp_path / "src", kit / "templates", tmp_path / "dist", "0.0.0-test", kit / "SightLab-VR-Assistant-0.80.6")
    d = tmp_path / "dist"
    assert (d / "claude-plugin" / "skills" / "sightlab-2x" / "evals" / "gaze-dwell-rating" / "brief.md").is_file()
    assert (d / "openai-plugin" / "skills" / "instructions" / "evals" / "gaze-dwell-rating" / "autopilot-assertions.json").is_file()
    assert not (d / "starter-project" / ".claude").exists()  # the starter is a template; the plugin carries the evals
    import zipfile
    assert any(n.endswith("evals/gaze-dwell-rating/acceptance.md") for n in zipfile.ZipFile(d / "chat-bundle.zip").namelist())
