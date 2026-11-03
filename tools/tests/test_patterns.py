"""Task 7: every pattern carries one complete script that passes the static checker."""
import json
import re
from pathlib import Path

import pytest

from check import check_script
from lint_kit import lint

FENCE_RE = re.compile(r"```([^\n]*)\n(.*?)```", re.S)
EXPECTED = {"gaze-contingent-events", "rating-after-trial", "stim-file-stimuli", "randomized-conditions", "biopac-markers",
            "show-hide-objects-per-trial"}


@pytest.fixture(scope="module")
def api(kit: Path) -> dict:
    return json.loads((kit / "src" / "sightlab-2" / "api" / "sightlab-api.json").read_text())


@pytest.fixture(scope="module")
def patterns(kit: Path) -> dict:
    folder = kit / "src" / "sightlab-2" / "patterns"
    return {p.stem: p.read_text(encoding="utf-8") for p in folder.glob("*.md")}


def complete_blocks(text: str) -> list:
    return [body for info, body in FENCE_RE.findall(text) if info.split()[:1] == ["python"] and "complete" in info.split()]


def test_expected_patterns_exist(patterns):
    assert EXPECTED <= set(patterns)


def test_every_pattern_has_one_complete_script(patterns):
    for name in EXPECTED:
        assert len(complete_blocks(patterns[name])) == 1, name


def test_complete_scripts_pass_check(tmp_path, patterns, api, kit: Path):
    """Patterns are what the agent copies: clean under the shipped checker with the real resources."""
    from check import load_resources
    resources = load_resources(str(kit / "src" / "sightlab-2" / "api" / "resources.json"))
    for name in EXPECTED:
        p = tmp_path / f"{name}.py"
        p.write_text(complete_blocks(patterns[name])[0])
        report = check_script(p, api, resources)
        assert report["errors"] == [], (name, report["errors"])
        assert not [w for w in report["warnings"] if w["code"] == "W_UNKNOWN_ENVIRONMENT"], (name, report["warnings"])
        assert report["frame"]["schedules_run_experiment"] and report["frame"]["start_end_pairs"] >= 1, name


def test_pattern_sections(patterns):
    for name in EXPECTED:
        text = patterns[name]
        for heading in ("## Intent", "## Script", "## Gotchas", "## Data produced", "## Shows up in", "## Needs"):
            assert heading in text, (name, heading)


def test_fragment_is_reported(tmp_path, api, kit):
    """Review Focus 4: a pattern whose block is a fragment names the pattern and the code."""
    src = tmp_path / "src"
    (src / "patterns").mkdir(parents=True)
    (src / "SKILL.md").write_text("---\nname: x\ndescription: y\n---\n\n<!-- host-section -->\n")
    (src / "patterns" / "broken.md").write_text("# broken\n\n## Script\n\n```python complete\nimport sightlab_utils.sightlab as sl\nsightlab = sl.SightLab(gui=False)\n```\n")
    index = json.loads((kit / "src" / "sightlab-2" / "examples" / "index.json").read_text())
    problems = lint(src, api, index)
    assert any("patterns/broken.md" in p and "E_NO_RUN_EXPERIMENT" in p for p in problems)
