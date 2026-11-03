"""Task 8: build_kit.py produces allowlisted wrappers with identical skill text and no secrets."""
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path

import pytest

from build_kit import SecretsFound, build, skill_body

OPENAI_NAME = "gpt-8fac8a955f2dc675005d97a73ee481f2"


@pytest.fixture()
def kit_copy(tmp_path: Path, kit: Path) -> Path:
    """A private copy of src/ so tests can plant files without touching the kit."""
    shutil.copytree(kit / "src", tmp_path / "src")
    return tmp_path


def _build(kit: Path, root: Path, version: str = "2026.11.0-test") -> dict:
    return build(root / "src", kit / "templates", root / "dist", version, kit / "SightLab-VR-Assistant-0.80.6")


def test_build_outputs_exist(kit, kit_copy):
    info = _build(kit, kit_copy)
    d = kit_copy / "dist"
    for rel in (
        "claude-plugin/.claude-plugin/plugin.json", "claude-plugin/skills/sightlab-2x/SKILL.md",
        "claude-plugin/commands/sightlab-new.md",
        "openai-plugin/.codex-plugin/plugin.json", "openai-plugin/skills/instructions/SKILL.md",
        "openai-plugin/skills/instructions/agents/openai.yaml", "openai-plugin/assets/gpt-icon.png",
        "openai-plugin/skills/instructions/harness/autopilot.py", "openai-plugin/README.md",
        "claude-plugin/README.md", "claude-plugin/LICENSE",
        "starter-project/CLAUDE.md", "starter-project/AGENTS.md", "starter-project/README.md",
        "starter-project/brief/TEMPLATE.md", "starter-project/brief/EXAMPLE-gaze-dwell.md", "starter-project/.gitignore",
        "chat-bundle.zip", "openai-plugin.zip", "BUILD.json",
    ):
        assert (d / rel).is_file(), rel
    assert info["version"] == "2026.11.0-test" and info["sightlab_utils_version"].startswith("2.")
    names = zipfile.ZipFile(d / "chat-bundle.zip").namelist()
    assert any(n.endswith("SKILL.md") for n in names)


def test_unlisted_file_never_ships(kit, kit_copy):
    """A file dropped into src/ that no allowlist names is simply not shipped."""
    (kit_copy / "src" / "api" / "scratch-notes.md").write_text("# scratch\n\nFINGERPRINT-7f3a9c\n", encoding="utf-8")
    _build(kit, kit_copy)
    for path in (kit_copy / "dist").rglob("*"):
        if path.is_file() and path.suffix != ".zip":
            assert path.name != "scratch-notes.md", path
    for name in zipfile.ZipFile(kit_copy / "dist" / "chat-bundle.zip").namelist():
        assert not name.endswith("scratch-notes.md")


def test_source_sized_block_fails_build(kit, kit_copy, SOURCES):
    """A 200+ line script dump inside a rule fails the build: patterns stay patterns."""
    from build_kit import ContentShape
    real = (SOURCES / "sightlab_utils" / "sightlab.py").read_text(encoding="utf-8-sig", errors="replace")
    (kit_copy / "src" / "rules" / "renamed-core.md").write_text("# not really a rule\n\n```python\n" + real[:20000] + "\n```\n")
    with pytest.raises(ContentShape):
        _build(kit, kit_copy)


def test_secret_fails_build(kit, kit_copy):
    (kit_copy / "src" / "rules" / "common-mistakes.md").write_text(
        "# oops\n\nUse key AKIA" + "ABCDEFGHIJKLMNOP" + " for S3.\n", encoding="utf-8")
    with pytest.raises(SecretsFound):
        _build(kit, kit_copy)


def _wrapper_bodies(dist: Path) -> dict:
    out = {
        "claude-plugin": (dist / "claude-plugin" / "skills" / "sightlab-2x" / "SKILL.md").read_bytes(),
        "openai-plugin": (dist / "openai-plugin" / "skills" / "instructions" / "SKILL.md").read_bytes(),
    }
    with zipfile.ZipFile(dist / "chat-bundle.zip") as z:
        out["chat-bundle"] = next(z.read(n) for n in z.namelist() if n.endswith("SKILL.md"))
    return {k: skill_body(v.decode("utf-8")) for k, v in out.items()}


def test_skill_text_identical_modulo_host(kit, kit_copy):
    _build(kit, kit_copy)
    bodies = _wrapper_bodies(kit_copy / "dist")
    assert len(set(bodies.values())) == 1, {k: hashlib.sha256(v.encode()).hexdigest()[:8] for k, v in bodies.items()}
    # Review Focus 5: a CRLF source must build to the same body.
    skill = kit_copy / "src" / "SKILL.md"
    skill.write_bytes(skill.read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8"))
    _build(kit, kit_copy)
    assert set(_wrapper_bodies(kit_copy / "dist").values()) == set(bodies.values())


def test_host_sections_differ(kit, kit_copy):
    _build(kit, kit_copy)
    claude = (kit_copy / "dist" / "claude-plugin" / "skills" / "sightlab-2x" / "SKILL.md").read_text()
    openai = (kit_copy / "dist" / "openai-plugin" / "skills" / "instructions" / "SKILL.md").read_text()
    assert "## On this host" in claude and "## On this host" in openai
    assert claude != openai and "<!-- host-section -->" not in claude + openai
    assert "{{SIGHTLAB_VERSION}}" not in claude and "{{KIT_DATE}}" not in claude


def test_openai_identity_kept(kit, kit_copy):
    _build(kit, kit_copy, version="0.90.0")
    manifest = json.loads((kit_copy / "dist" / "openai-plugin" / ".codex-plugin" / "plugin.json").read_text())
    assert manifest["name"] == OPENAI_NAME and manifest["version"] == "0.90.0"
    skill = (kit_copy / "dist" / "openai-plugin" / "skills" / "instructions" / "SKILL.md").read_text()
    assert re.search(r"^name:\s*instructions\s*$", skill.split("---")[1], re.M)
    claude_manifest = json.loads((kit_copy / "dist" / "claude-plugin" / ".claude-plugin" / "plugin.json").read_text())
    assert claude_manifest["version"] == "0.90.0"


def test_harness_ships_in_both_plugins_only(kit, kit_copy):
    """2026-11-03: Codex users install the OpenAI plugin, so it carries the harness too; the starter and the chat bundle never do."""
    _build(kit, kit_copy)
    d = kit_copy / "dist"
    assert (d / "claude-plugin" / "skills" / "sightlab-2x" / "harness" / "check.py").is_file()
    assert (d / "openai-plugin" / "skills" / "instructions" / "harness" / "check.py").is_file()
    assert not list((d / "starter-project").rglob("check.py"))
    assert not any(n.endswith("check.py") for n in zipfile.ZipFile(d / "chat-bundle.zip").namelist())
    assert not list(d.rglob("fixtures"))


def test_starter_is_template_only(kit, kit_copy):
    """The kit is installed once as a plugin; the starter project carries no copy of it."""
    _build(kit, kit_copy)
    sp = kit_copy / "dist" / "starter-project"
    assert not (sp / ".claude").exists() and not (sp / "harness").exists()
    names = {p.relative_to(sp).as_posix() for p in sp.rglob("*") if p.is_file()}
    assert names == {"CLAUDE.md", "AGENTS.md", "README.md", ".gitignore", ".vscode/settings.json",
                     "brief/TEMPLATE.md", "brief/EXAMPLE-gaze-dwell.md"}, names
    assert "{{VERSION}}" not in (sp / "CLAUDE.md").read_text()


def test_marketplace_manifests_match_version(kit, kit_copy):
    """The repo root is a marketplace for Claude Code/claude.ai and for Codex; both entries carry the build's version."""
    _build(kit, kit_copy, version="0.90.0")
    claude = json.loads((kit_copy / ".claude-plugin" / "marketplace.json").read_text())
    codex = json.loads((kit_copy / ".agents" / "plugins" / "marketplace.json").read_text())
    assert claude["name"] == "worldviz" and claude["owner"]["name"]
    entry = claude["plugins"][0]
    assert entry["name"] == "sightlab-2x" and entry["source"] == "./dist/claude-plugin" and entry["version"] == "0.90.0"
    assert (kit_copy / entry["source"]).is_dir()
    assert codex["name"] == "worldviz" and codex["interface"]["displayName"]
    centry = codex["plugins"][0]
    assert centry["name"] == OPENAI_NAME and centry["source"] == {"source": "local", "path": "./dist/openai-plugin"}
    assert centry["category"] and centry["policy"]["installation"] == "AVAILABLE"


def test_plugin_folders_have_readme_and_license(kit, kit_copy):
    """The Claude directory blocks a plugin without a README of 40+ words and a LICENSE."""
    _build(kit, kit_copy)
    for wrapper in ("claude-plugin", "openai-plugin"):
        readme = (kit_copy / "dist" / wrapper / "README.md").read_text(encoding="utf-8")
        assert len(re.sub(r"```.*?```", "", readme, flags=re.S).split()) >= 40
        assert "winviz.exe" in readme and "check.py" in readme  # the README says what the plugin runs
        assert (kit_copy / "dist" / wrapper / "LICENSE").is_file()


def test_openai_zip_mirrors_folder(kit, kit_copy):
    """The directory submission is a ZIP of the OpenAI plugin folder, with the manifest at .codex-plugin/plugin.json."""
    _build(kit, kit_copy)
    d = kit_copy / "dist"
    names = set(zipfile.ZipFile(d / "openai-plugin.zip").namelist())
    on_disk = {p.relative_to(d / "openai-plugin").as_posix() for p in (d / "openai-plugin").rglob("*") if p.is_file()}
    assert names == on_disk and ".codex-plugin/plugin.json" in names


def test_dist_check_runs_without_flags(kit, kit_copy):
    """Review fix 1: the documented command works from the starter project and the plugin."""
    import subprocess
    import sys
    _build(kit, kit_copy)
    fixture = kit / "src" / "harness" / "fixtures" / "ok_nongui.py"
    op = kit_copy / "dist" / "openai-plugin"
    r = subprocess.run([sys.executable, "skills/instructions/harness/check.py", str(fixture)], capture_output=True, text=True, cwd=op)
    assert r.returncode == 0 and "0 error(s)" in r.stdout, r.stderr
    cp = kit_copy / "dist" / "claude-plugin"
    r = subprocess.run([sys.executable, "skills/sightlab-2x/harness/check.py", str(fixture)], capture_output=True, text=True, cwd=cp)
    assert r.returncode == 0 and "0 error(s)" in r.stdout, r.stderr


def test_dist_check_flags_env_without_flags(kit, kit_copy):
    """E2E follow-ups Review Focus 5: the starter project and the plugin find resources.json by themselves."""
    import subprocess
    import sys
    _build(kit, kit_copy)
    fixture = kit / "src" / "harness" / "fixtures" / "bad_env.py"
    for cwd, cmd in ((kit_copy / "dist" / "openai-plugin", "skills/instructions/harness/check.py"), (kit_copy / "dist" / "claude-plugin", "skills/sightlab-2x/harness/check.py")):
        r = subprocess.run([sys.executable, cmd, str(fixture)], capture_output=True, text=True, cwd=cwd)
        assert r.returncode == 0 and "W_UNKNOWN_ENVIRONMENT" in r.stdout, (cwd, r.stdout, r.stderr)


def test_curated_source_copy_fails_build(kit, kit_copy, SOURCES):
    """curated/ holds curated examples only: a long or unheaded .py there fails the build."""
    from build_kit import ContentShape
    real = (SOURCES / "sightlab_utils" / "sightlab.py").read_text(encoding="utf-8-sig", errors="replace")
    (kit_copy / "src" / "examples" / "curated" / "core_copy.py").write_text(real, encoding="utf-8")
    with pytest.raises(ContentShape):
        _build(kit, kit_copy)
    (kit_copy / "src" / "examples" / "curated" / "core_copy.py").unlink()
    (kit_copy / "src" / "examples" / "curated" / "no_header.py").write_text("print('hi')\n", encoding="utf-8")
    with pytest.raises(ContentShape):
        _build(kit, kit_copy)


def test_claude_host_section_uses_plugin_root(kit, kit_copy):
    """Review fix 3: inside the plugin the harness lives under the plugin root, not the project."""
    _build(kit, kit_copy)
    claude = (kit_copy / "dist" / "claude-plugin" / "skills" / "sightlab-2x" / "SKILL.md").read_text()
    assert "${CLAUDE_PLUGIN_ROOT}/skills/sightlab-2x/harness/check.py" in claude
    cmd = (kit_copy / "dist" / "claude-plugin" / "commands" / "sightlab-check.md").read_text()
    assert "${CLAUDE_PLUGIN_ROOT}/skills/sightlab-2x/harness/check.py" in cmd


def test_autopilot_documented_everywhere(kit, kit_copy):
    """Autopilot plan Task 3: once the harness ships, nothing says 'when present' any more."""
    _build(kit, kit_copy)
    d = kit_copy / "dist"
    files = [
        kit / "src" / "SKILL.md", kit / "src" / "harness" / "README.md",
        kit / "templates" / "claude-plugin" / "commands" / "sightlab-check.md",
        kit / "templates" / "starter-project" / "CLAUDE.md", kit / "templates" / "starter-project" / "AGENTS.md",
        kit / "templates" / "starter-project" / "README.md",
        d / "claude-plugin" / "skills" / "sightlab-2x" / "SKILL.md",
        d / "openai-plugin" / "skills" / "instructions" / "SKILL.md",
    ]
    for f in files:
        text = f.read_text(encoding="utf-8")
        assert "autopilot.py" in text, f
        assert "when present" not in text and "when this kit version ships" not in text and "when that file is present" not in text, f
    assert (d / "openai-plugin" / "skills" / "instructions" / "harness" / "README.md").is_file()


def test_build_json_lists_every_file(kit, kit_copy):
    _build(kit, kit_copy)
    info = json.loads((kit_copy / "dist" / "BUILD.json").read_text())
    for wrapper in ("claude-plugin", "openai-plugin", "starter-project"):
        on_disk = {p.relative_to(kit_copy / "dist" / wrapper).as_posix() for p in (kit_copy / "dist" / wrapper).rglob("*") if p.is_file()}
        assert set(info["files"][wrapper]) == on_disk, wrapper
        assert all(len(h) == 64 for h in info["files"][wrapper].values())


# --- 2026-10-31, Andy: customers always get the full source; ship it --------------------------

def test_reference_source_ships_in_every_wrapper(kit, tmp_path):
    """sightlab.py, viz.py and replay.py ship under reference/ in all four wrappers, chat bundle included."""
    shutil.copytree(kit / "src", tmp_path / "src")
    build(tmp_path / "src", kit / "templates", tmp_path / "dist", "0.0.0-test", kit / "SightLab-VR-Assistant-0.80.6")
    d = tmp_path / "dist"
    for base in ("claude-plugin/skills/sightlab-2x", "openai-plugin/skills/instructions"):
        for name in ("sightlab.py", "viz.py", "replay.py", "README.md"):
            assert (d / base / "reference" / name).is_file(), f"{base}/reference/{name}"
    names = zipfile.ZipFile(d / "chat-bundle.zip").namelist()
    for name in ("sightlab.py", "viz.py", "replay.py"):
        assert any(n.endswith("reference/" + name) for n in names), name


def test_codex_marketplace_entry_carries_version(kit, kit_copy):
    _build(kit, kit_copy, version="0.91.0")
    codex = json.loads((kit_copy / ".agents" / "plugins" / "marketplace.json").read_text())
    assert codex["plugins"][0]["version"] == "0.91.0"


def test_claude_plugin_has_icon(kit, kit_copy):
    """Review I-5: the directory takes the listing icon from the first save only; ship it from day one."""
    _build(kit, kit_copy)
    assert (kit_copy / "dist" / "claude-plugin" / ".claude-plugin" / "icon.png").is_file()


def test_claude_validate_passes_when_cli_present(kit, kit_copy):
    """Review focus 5: the built plugin and the marketplace root validate with the real CLI (skipped without it)."""
    import shutil as _sh
    import subprocess
    if not _sh.which("claude"):
        pytest.skip("claude CLI not installed")
    _build(kit, kit_copy)
    for target in (str(kit_copy / "dist" / "claude-plugin"), str(kit_copy)):
        r = subprocess.run(["claude", "plugin", "validate", target], capture_output=True, text=True)
        assert r.returncode == 0 and "Validation passed" in r.stdout, (target, r.stdout, r.stderr)
