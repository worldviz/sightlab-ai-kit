"""Evals plan, Task 3: guides for agents, short, linked, and free of install steps."""
import json
import re
from pathlib import Path

from lint_kit import lint

GUIDES = ["data-recorder", "replay", "dashboard", "virtual-screen", "instructions", "driving", "ai-agents", "analysis-and-visualization"]


def test_guides_present(kit: Path):
    folder = kit / "src" / "sightlab-2x" / "guides"
    for g in GUIDES:
        assert (folder / f"{g}.md").is_file(), g
    assert (folder / "index.md").is_file()


def test_guides_are_short(kit: Path):
    for g in GUIDES:
        text = (kit / "src" / "sightlab-2x" / "guides" / f"{g}.md").read_text(encoding="utf-8")
        assert text.count("\n") <= 250, g


def test_index_links_every_guide(kit: Path):
    index = (kit / "src" / "sightlab-2x" / "guides" / "index.md").read_text(encoding="utf-8")
    for g in GUIDES:
        assert f"{g}.md" in index, g


def test_guides_name_their_sources(kit: Path):
    for g in GUIDES:
        text = (kit / "src" / "sightlab-2x" / "guides" / f"{g}.md").read_text(encoding="utf-8")
        assert re.search(r"^Sources?:", text, re.M), g


def test_guides_lint_clean(kit: Path):
    api = json.loads((kit / "src" / "sightlab-2x" / "api" / "sightlab-api.json").read_text())
    index = json.loads((kit / "src" / "sightlab-2x" / "examples" / "index.json").read_text())
    problems = [p for p in lint(kit / "src" / "sightlab-2x", api, index) if p.startswith("guides/")]
    assert problems == []


def test_text_continue_key_semantics(kit: Path):
    """Review fix 1: textContinueKey REPLACES the trigger wait (sightlab.py startTrial); say so everywhere."""
    for rel in ("guides/instructions.md", "rules/trials-and-instructions.md"):
        text = (kit / "src" / "sightlab-2x" / rel).read_text(encoding="utf-8")
        para = next(p for p in text.split("\n\n") if "textContinueKey" in p)
        assert "replaces" in para, rel
        assert "also dismisses" not in text and "or `textContinueKey" not in text, rel


def test_skill_points_at_guides_index(kit: Path):
    assert "guides/index.md" in (kit / "src" / "sightlab-2x" / "SKILL.md").read_text(encoding="utf-8")
