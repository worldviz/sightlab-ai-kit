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
    assert "claude plugin install sightlab --marketplace worldviz/sightlab-ai-kit" in claude
    assert "codex plugin marketplace add worldviz/sightlab-ai-kit" in agents
    assert "worldviz/sightlab-ai-kit" in readme


def test_host_sections_give_kit_relative_paths(kit: Path):
    import host_sections
    assert "${CLAUDE_PLUGIN_ROOT}/skills/sightlab-2x/harness/autopilot.py" in host_sections.HOST["sightlab-2x"]["claude-plugin"]
    assert "harness/autopilot.py" in host_sections.HOST["sightlab-2x"]["openai-plugin"]  # Codex runs it from the plugin's skill folder
    assert "worldviz/sightlab-ai-kit" in host_sections.HOST["sightlab-2x"]["chat-bundle"]


# --- 2026.11.3: the plugin is product-neutral; the skill keeps the generation in its name ------

OLD_INSTALL = "claude plugin install sightlab-2x"


def test_plugin_is_named_sightlab_everywhere(kit: Path):
    import json
    manifest = json.loads((kit / "templates" / "claude-plugin" / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "sightlab"
    cmds = sorted(p.name for p in (kit / "templates" / "claude-plugin" / "commands").glob("*.md"))
    assert cmds == ["check.md", "new.md", "review.md"]
    files = list((kit / "templates").rglob("*.md")) + list((kit / "docs").rglob("*.md")) + [kit / "README.md", kit / "tools" / "host_sections.py"]
    files += [p for p in (kit / "src").rglob("*.md") if "reference" not in p.parts]  # shipped content too (review #1)
    for path in files:
        if path.name == "CHANGELOG.md":
            continue
        text = path.read_text(encoding="utf-8")
        assert OLD_INSTALL not in text and "/sightlab-2x:" not in text and "update sightlab-2x@worldviz" not in text, path


def test_readme_tells_2026_11_2_installs_to_reinstall(kit: Path):
    text = (kit / "README.md").read_text(encoding="utf-8")
    assert "claude plugin uninstall sightlab-2x@worldviz" in text
    assert "claude.ai" in text[text.index("Installed 2026.11.2"):][:600]  # review #7: claude.ai users remove the old plugin too


def test_skill_routes_between_generations_first(kit: Path):
    """Both generations will be installed side by side for a year; the import line is the signal."""
    text = (kit / "src" / "sightlab-2x" / "SKILL.md").read_text(encoding="utf-8")
    i = text.index("## Which SightLab")
    assert i < text.index("<!-- host-section -->") < text.index("## 0. Size the request")
    section = text[i:text.index("<!-- host-section -->")]
    for signal in ("sightlab_utils", ".oep.json", ".oep-project.json", "from sightlab import", "_sightlab_version.py", "Ask once", "`sightlab-3`", "not covered"):
        assert signal in section, signal
    assert "class named `SightLab`" in section


def test_routing_decides_in_chat_and_defers_sizing(kit: Path):
    """Review #2: a chat host has no files, so an explicit statement or a pasted script decides; ask once otherwise."""
    import host_sections
    text = (kit / "src" / "sightlab-2x" / "SKILL.md").read_text(encoding="utf-8")
    section = text[text.index("## Which SightLab"):text.index("<!-- host-section -->")]
    assert "3. **What the researcher says" in section and "pasted" in section
    assert "`import sightlab`" in section and "vocabulary" in section
    assert "Do not guess from the wording" not in section
    for wrapper, host in host_sections.HOST["sightlab-2x"].items():
        assert "then size the request" in host and "Size the request first" not in host, wrapper
