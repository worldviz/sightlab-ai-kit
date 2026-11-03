"""2026.11.3: one folder per skill under src/, so a SightLab 3 skill can sit beside the 2.x one."""
from pathlib import Path


def test_src_holds_one_folder_per_skill(kit: Path):
    from kit_paths import SRC, skill_dirs
    assert not (kit / "src" / "SKILL.md").exists()
    assert (kit / "src" / "sightlab-2x" / "SKILL.md").is_file()
    assert [d.name for d in skill_dirs(SRC)] == ["sightlab-2x"]


def test_codex_ui_metadata_lives_in_the_skill(kit: Path):
    yaml = kit / "src" / "sightlab-2x" / "agents" / "openai.yaml"
    assert yaml.is_file() and "short_description" in yaml.read_text(encoding="utf-8")
    assert not (kit / "SightLab-VR-Assistant-0.80.6" / "skills").exists()
