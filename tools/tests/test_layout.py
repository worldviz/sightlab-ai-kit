"""2026.11.3: one folder per skill under src/, so a SightLab 3 skill can sit beside the 2.x one."""
from pathlib import Path


def test_src_holds_one_folder_per_skill(kit: Path):
    from kit_paths import SRC, skill_dirs
    assert not (kit / "src" / "SKILL.md").exists()
    assert (kit / "src" / "sightlab-2" / "SKILL.md").is_file()
    assert [d.name for d in skill_dirs(SRC)] == ["sightlab-2"]


def test_codex_ui_metadata_lives_in_the_skill(kit: Path):
    yaml = kit / "src" / "sightlab-2" / "agents" / "openai.yaml"
    assert yaml.is_file() and "short_description" in yaml.read_text(encoding="utf-8")
    assert not (kit / "templates" / "openai-plugin" / "skills").exists()


def test_openai_subtitles_fit_the_directory_limit():
    """OpenAI's directory caps the short description at 30 characters (Sado, 2026-11-05)."""
    import json, re
    from kit_paths import KIT, SKILL_2
    yaml = (SKILL_2 / "agents" / "openai.yaml").read_text(encoding="utf-8")
    short = re.search(r"short_description:\s*(.+)", yaml).group(1).strip()
    assert len(short) <= 30 and "SightLab 2" in short, short
    manifest = json.loads((KIT / "templates" / "openai-plugin" / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert len(manifest["interface"]["shortDescription"]) <= 30, manifest["interface"]["shortDescription"]
    assert "check" in manifest["interface"]["longDescription"] and "Vizard" in manifest["interface"]["longDescription"]


def test_claude_manifest_carries_the_directory_listing_fields():
    """The Claude directory reads displayName and the policy/support links from plugin.json (portal, 2026-11-05)."""
    import json
    from kit_paths import KIT
    m = json.loads((KIT / "templates" / "claude-plugin" / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert m["displayName"] == "SightLab AI Kit"
    assert m["repository"] == "https://github.com/worldviz/sightlab-ai-kit"
    for key in ("documentationUrl", "supportUrl", "privacyPolicyUrl", "termsOfServiceUrl"):
        assert m[key].startswith("https://"), key
    assert m["termsOfServiceUrl"].endswith("#part-2-assistant-terms")
