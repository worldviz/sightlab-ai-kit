"""2026-11-03: proportional workflow, kit-relative paths, endFade wording (Sado's review)."""
from pathlib import Path


def test_skill_has_request_sizing_section(kit: Path):
    text = (kit / "src" / "sightlab-2" / "SKILL.md").read_text(encoding="utf-8")
    assert "## 0. Size the request" in text
    assert "small edit" in text and "No brief" in text
    assert text.index("## 0. Size the request") < text.index("## 1. Capabilities and custom development")


def test_skill_defines_kit_folder_and_absolute_script_path(kit: Path):
    text = (kit / "src" / "sightlab-2" / "SKILL.md").read_text(encoding="utf-8")
    assert "`<kit>`" in text and "<kit>/harness/check.py" in text and "<kit>/harness/autopilot.py" in text
    assert "absolute path" in text
    assert "`harness/check.py" not in text and "`python harness/" not in text  # no project-relative harness path remains


def test_rating_pattern_states_endfade_truth(kit: Path):
    text = (kit / "src" / "sightlab-2" / "patterns" / "rating-after-trial.md").read_text(encoding="utf-8")
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
    assert "${CLAUDE_PLUGIN_ROOT}/skills/sightlab-2/harness/autopilot.py" in host_sections.HOST["sightlab-2"]["claude-plugin"]
    assert "harness/autopilot.py" in host_sections.HOST["sightlab-2"]["openai-plugin"]  # Codex runs it from the plugin's skill folder
    assert "worldviz/sightlab-ai-kit" in host_sections.HOST["sightlab-2"]["chat-bundle"]


# --- 2026.11.3: the plugin is product-neutral; the skill keeps the generation in its name ------

OLD_INSTALL = "claude plugin install sightlab-2" + "x"


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
        assert OLD_INSTALL not in text and "/sightlab-2" + "x:" not in text and "update sightlab-2" + "x@worldviz" not in text, path


def test_readme_tells_2026_11_2_installs_to_reinstall(kit: Path):
    text = (kit / "README.md").read_text(encoding="utf-8")
    assert "claude plugin uninstall sightlab-2" + "x@worldviz" in text  # the 2026.11.2 plugin name, kept for the migration note
    assert "claude.ai" in text[text.index("Installed 2026.11.2"):][:600]  # review #7: claude.ai users remove the old plugin too


def test_skill_routes_between_generations_first(kit: Path):
    """Both generations will be installed side by side for a year. Default to SightLab 2;
    `sightlab_utils` is the SightLab 2 signal, and a bare `import sightlab` or class name does not prove 3."""
    text = (kit / "src" / "sightlab-2" / "SKILL.md").read_text(encoding="utf-8")
    i = text.index("## Which SightLab")
    assert i < text.index("<!-- host-section -->") < text.index("## 0. Size the request")
    section = text[i:text.index("<!-- host-section -->")]
    for signal in ("sightlab_utils", "Default to SightLab 2", "`import sightlab`", "class name", "SightLab 3 skill", "coverage gap",
                   "register/capabilities-and-custom-development.md"):
        assert signal in section, signal


def test_routing_decides_in_chat_and_defers_sizing(kit: Path):
    """Review #2: a chat host has no files, so an explicit statement decides; ask only when it materially matters."""
    import host_sections
    text = (kit / "src" / "sightlab-2" / "SKILL.md").read_text(encoding="utf-8")
    section = text[text.index("## Which SightLab"):text.index("<!-- host-section -->")]
    assert "explicitly stated version" in section and "materially changes the answer" in section
    assert "`import sightlab`" in section
    assert "Do not guess from the wording" not in section
    for wrapper, host in host_sections.HOST["sightlab-2"].items():
        assert "then size the request" in host and "Size the request first" not in host, wrapper


def test_no_version_x_baggage(kit: Path):
    """2026.11.4 (Andy): the generation is 'SightLab 2', not '2.x'; the skill is sightlab-2; no 0.80.x folder.
    The old spellings are built by concatenation so a repo-wide rename cannot rewrite this test."""
    old_skill, old_const, old_prose, old_folder = "sightlab-2" + "x", "SKILL_2" + "X", "SightLab 2" + ".x", "SightLab-VR-Assistant-0.80" + ".6"
    assert (kit / "src" / "sightlab-2" / "SKILL.md").is_file() and not (kit / "src" / old_skill).exists()
    assert not (kit / old_folder).exists()
    assert (kit / "templates" / "openai-plugin" / ".codex-plugin" / "plugin.json").is_file()
    historical = {"CHANGELOG.md", "2026-11-03-trial-notes.md"}
    files = [p for p in list((kit / "src").rglob("*")) + list((kit / "templates").rglob("*")) + list((kit / "tools").glob("*.py")) + list((kit / "tools" / "tests").glob("*.py")) + list((kit / "docs").rglob("*.md")) + [kit / "README.md"]
             if p.is_file() and "reference" not in p.parts and p.suffix in (".md", ".py", ".json", ".yaml") and p.name not in historical]
    for path in files:
        text = "\n".join(line for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if "2026.11.2" not in line)  # migration notes may name the old plugin
        assert old_skill not in text and old_prose not in text and old_const not in text and old_folder not in text, path


# --- 2026.11.6: Sado's pre-submission review -------------------------------------------------

APPROVED_TERMS = "https://help.worldviz.com/sightlab/sightlab-assistant-privacy-policy/#part-2-assistant-terms"


def test_license_defers_to_the_approved_assistant_terms(kit: Path):
    """The LICENSE must not contradict the Assistant Terms OpenAI already approved: same entity, open to
    prospective customers, no absolute liability exclusion; the harness is an amendment, not a new license."""
    for wrapper in ("claude-plugin", "openai-plugin"):
        text = (kit / "templates" / wrapper / "LICENSE").read_text(encoding="utf-8")
        assert APPROVED_TERMS in text and "WorldViz Inc." in text, wrapper
        assert "WorldViz LLC" not in text and "licensees of" not in text and "is not liable" not in text, wrapper
        assert "check.py" in text and "autopilot.py" in text  # the amendment names the utilities it covers
    assert "WorldViz LLC" not in (kit / "README.md").read_text(encoding="utf-8")


def test_kit_answers_how_to_create_a_first_experiment(kit: Path):
    """Validation question (Sado's list, item 2): the intended workflow starts from the installed projects folder."""
    skill = kit / "src" / "sightlab-2"
    rules = (skill / "rules" / "gui-vs-code.md").read_text(encoding="utf-8")
    for must in ("Documents\\Sightlab2\\Projects", "BlankProject", "SampleProject", "SightLab_VR.py",
                 "SightLabVR_NonGUI.py", "first experiment", "GUI only", "**Code:**", "**Both:**", "writes code by default", "computer use"):
        assert must in rules, must
    assert "never operates" not in rules  # computer use can drive the GUI; code is the default, not the limit
    assert "How do I create my first SightLab experiment?" in (skill / "evals" / "README.md").read_text(encoding="utf-8")


def test_register_references_resolve(kit: Path):
    """The capabilities register replaced cannot.md; every `register/<file>` the skill or a command names must ship."""
    import re
    skill = kit / "src" / "sightlab-2"
    sources = [skill / "SKILL.md"] + list((kit / "templates").rglob("commands/*.md"))
    named = {m for p in sources for m in re.findall(r"register/[\w.-]+\.md", p.read_text(encoding="utf-8"))}
    assert "register/capabilities-and-custom-development.md" in named
    for ref in named:
        assert (skill / ref).is_file(), ref
    assert not (skill / "register" / "cannot.md").exists()


def test_skill_assumes_sightlab_2_when_nothing_decides(kit: Path):
    """Customers run SightLab 2 today; asking every undecided request which generation is friction (Sado)."""
    text = (kit / "src" / "sightlab-2" / "SKILL.md").read_text(encoding="utf-8")
    section = text[text.index("## Which SightLab"):text.index("<!-- host-section -->")]
    assert "Default to SightLab 2" in section and "Ask once" not in section
    assert "assuming SightLab 2" in section  # the assumption is stated, so a SightLab 3 user can correct it


def test_autopilot_ask_is_a_chat_question_and_skipped_when_the_run_was_requested(kit: Path):
    """Codex desktop (Sado): the agent asked in its final message and the turn ended, which read as a missing
    approval button; and it asked although the researcher had already said 'build and test it'."""
    import host_sections
    text = (kit / "src" / "sightlab-2" / "SKILL.md").read_text(encoding="utf-8")
    build = text[text.index("## 4. The build"):]
    assert "already asks for a run or a test" in build and "plain chat question" in build
    assert "approval dialog" in build or "approval button" in build
    for path in (kit / "tools" / "host_sections.py", kit / "templates" / "claude-plugin" / "commands" / "check.md",
                 kit / "templates" / "claude-plugin" / "README.md", kit / "templates" / "openai-plugin" / "README.md", kit / "README.md"):
        t = path.read_text(encoding="utf-8")
        assert "unless the request already asked for" in t or "unless you asked for" in t, path
