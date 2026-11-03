"""Task 5: the kit lint keeps every Markdown claim consistent with the generated API map."""
import json
from pathlib import Path

import pytest

from lint_kit import lint

MARKER = "<!-- host-section -->"


@pytest.fixture(scope="module")
def api(kit: Path) -> dict:
    return json.loads((kit / "src" / "sightlab-2" / "api" / "sightlab-api.json").read_text())


@pytest.fixture(scope="module")
def index(kit: Path) -> list:
    return json.loads((kit / "src" / "sightlab-2" / "examples" / "index.json").read_text())


def _mini_kit(tmp_path: Path, rule_text: str, skill_text: str | None = None) -> Path:
    src = tmp_path / "src"
    (src / "rules").mkdir(parents=True)
    (src / "SKILL.md").write_text(skill_text if skill_text is not None else f"---\nname: sightlab-2\ndescription: test\n---\n\n# Skill\n\n{MARKER}\n")
    (src / "rules" / "one.md").write_text(rule_text)
    return src


def test_unknown_method_mention_is_reported(tmp_path, api, index):
    src = _mini_kit(tmp_path, "Call `sightlab.notAMethod()` to begin.\n")
    problems = lint(src, api, index)
    assert len(problems) == 1 and "rules/one.md" in problems[0] and "notAMethod" in problems[0]


def test_known_method_mention_passes(tmp_path, api, index):
    src = _mini_kit(tmp_path, "Call `sightlab.startTrial()` and `SightLab(gui=False)`.\n")
    assert lint(src, api, index) == []


def test_biopac_spelling(tmp_path, api, index):
    src = _mini_kit(tmp_path, "Send markers to Biopac after each trial.\n")
    problems = lint(src, api, index)
    assert len(problems) == 1 and "BIOPAC" in problems[0]
    src2 = _mini_kit(tmp_path / "b", "Send markers to BIOPAC; the module is `biopacndt` in code: `sightlab = sl.SightLab(biopac=True)`.\n")
    assert lint(src2, api, index) == []


def test_unknown_example_link(tmp_path, api, index):
    src = _mini_kit(tmp_path, "See `examples/No_Such_Folder` for the full script.\n")
    problems = lint(src, api, index)
    assert len(problems) == 1 and "No_Such_Folder" in problems[0]


def test_host_marker_required_once(tmp_path, api, index):
    src = _mini_kit(tmp_path, "fine\n", skill_text="---\nname: x\ndescription: y\n---\n\nno marker here\n")
    assert any(MARKER in p for p in lint(src, api, index))


def test_front_matter_required(tmp_path, api, index):
    src = _mini_kit(tmp_path, "fine\n", skill_text=f"# Skill without front matter\n\n{MARKER}\n")
    assert any("front matter" in p for p in lint(src, api, index))


def test_complete_block_must_pass_check(tmp_path, api, index):
    bad = "```python complete\nimport sightlab_utils.sightlab as sl\nsightlab = sl.SightLab(gui=False)\ndef run():\n    yield sightlab.startTrial()\n```\n"
    src = _mini_kit(tmp_path, bad)
    problems = lint(src, api, index)
    assert any("E_NO_RUN_EXPERIMENT" in p and "rules/one.md" in p for p in problems)


def test_guide_install_steps_rejected(tmp_path, api, index):
    """Evals plan Review Focus 3: a guide may describe a feature, never tell the agent to install."""
    src = _mini_kit(tmp_path, "fine\n")
    (src / "guides").mkdir()
    (src / "guides" / "x.md").write_text("# X\n\nSource: test\n\nRun `pip install openai` first, then download and run setup.exe.\n")
    problems = [p for p in lint(src, api, index) if "guides/x.md" in p]
    assert len(problems) == 1 and "install" in problems[0]


def test_guide_length_capped(tmp_path, api, index):
    src = _mini_kit(tmp_path, "fine\n")
    (src / "guides").mkdir()
    (src / "guides" / "long.md").write_text("# Long\n\nSource: test\n" + "line\n" * 260)
    problems = [p for p in lint(src, api, index) if "guides/long.md" in p]
    assert len(problems) == 1 and "250" in problems[0]


def test_unshipped_resource_name_reported(tmp_path, api, index, kit: Path):
    """E2E follow-ups Review Focus 4: a backticked resource file name must exist in api/resources.json."""
    import shutil
    src = _mini_kit(tmp_path, "Load `nope.osgb` from the objects folder, next to `Plant.osgb`.\n")
    (src / "api").mkdir()
    shutil.copyfile(kit / "src" / "sightlab-2" / "api" / "resources.json", src / "api" / "resources.json")
    problems = lint(src, api, index)
    assert len(problems) == 1 and "nope.osgb" in problems[0]


def test_resource_rule_sees_fences_with_star_import(tmp_path, api, index, kit: Path):
    """Review fix: every pattern fence contains `import *`; the rule must still inspect it."""
    import shutil
    src = _mini_kit(tmp_path, "# p\n\n```python complete\nfrom sightlab_utils.settings import *\nenv = vizfx.addChild('sightlab_resources/objects/nope_object.osgb')\n```\n")
    (src / "api").mkdir()
    shutil.copyfile(kit / "src" / "sightlab-2" / "api" / "resources.json", src / "api" / "resources.json")
    problems = [p for p in lint(src, api, index) if "nope_object.osgb" in p]
    assert len(problems) == 1


def test_resource_case_must_match_exactly(tmp_path, api, index, kit: Path):
    import shutil
    src = _mini_kit(tmp_path, "Use `plant.osgb` here.\n")
    (src / "api").mkdir()
    shutil.copyfile(kit / "src" / "sightlab-2" / "api" / "resources.json", src / "api" / "resources.json")
    problems = lint(src, api, index)
    assert len(problems) == 1 and "Plant.osgb" in problems[0]


def test_rules_environment_list_matches_resources(kit: Path):
    """The hand-typed environment list in the rules may not drift from the generated resources."""
    import json
    import re
    shipped = set(json.loads((kit / "src" / "sightlab-2" / "api" / "resources.json").read_text())["folders"]["environments"])
    text = (kit / "src" / "sightlab-2" / "rules" / "environments-and-resources.md").read_text(encoding="utf-8")
    para = text.split("is a real spelling for one of them):")[1].split("\n\n")[1]
    listed = set(re.findall(r"`([^`]+\.osgb)`", para, re.I))
    assert listed == shipped, (listed ^ shipped)


def test_real_kit_is_clean(kit: Path, api, index):
    assert lint(kit / "src" / "sightlab-2", api, index) == []
