"""2026-11-03: proportional workflow, kit-relative paths, endFade wording (Sado's review)."""
from pathlib import Path


def test_skill_has_request_sizing_section(kit: Path):
    text = (kit / "src" / "sightlab-2x" / "SKILL.md").read_text(encoding="utf-8")
    assert "## 0. Size the request" in text
    assert "small edit" in text and "No brief" in text
    assert text.index("## 0. Size the request") < text.index("## 1. Scope guard")


def test_skill_defines_kit_folder_and_absolute_script_path(kit: Path):
    text = (kit / "src" / "sightlab-2x" / "SKILL.md").read_text(encoding="utf-8")
    assert "`<kit>`" in text and "<kit>/harness/check.py" in text and "<kit>/harness/autopilot.py" in text
    assert "absolute path" in text
    assert "`harness/check.py" not in text and "`python harness/" not in text  # no project-relative harness path remains


def test_rating_pattern_states_endfade_truth(kit: Path):
    text = (kit / "src" / "sightlab-2x" / "patterns" / "rating-after-trial.md").read_text(encoding="utf-8")
    assert "hidden behind the scale regardless" in text
    assert "keeps the scene visible behind the scale" not in text


def test_starter_templates_point_at_the_installed_plugin(kit: Path):
    t = kit / "templates" / "starter-project"
    claude = (t / "CLAUDE.md").read_text(encoding="utf-8")
    agents = (t / "AGENTS.md").read_text(encoding="utf-8")
    readme = (t / "README.md").read_text(encoding="utf-8")
    for text in (claude, agents, readme):
        assert ".claude/skills" not in text and "harness/check.py" not in text
    assert "claude plugin install sightlab-2x --marketplace worldviz/sightlab-ai-kit" in claude
    assert "codex plugin marketplace add worldviz/sightlab-ai-kit" in agents
    assert "worldviz/sightlab-ai-kit" in readme


def test_host_sections_give_kit_relative_paths(kit: Path):
    import host_sections
    assert "${CLAUDE_PLUGIN_ROOT}/skills/sightlab-2x/harness/autopilot.py" in host_sections.HOST["sightlab-2x"]["claude-plugin"]
    assert "harness/autopilot.py" in host_sections.HOST["sightlab-2x"]["openai-plugin"]  # Codex runs it from the plugin's skill folder
    assert "worldviz/sightlab-ai-kit" in host_sections.HOST["sightlab-2x"]["chat-bundle"]
