"""Where the kit's sources live: one folder per skill under src/ (2026.11.3).

`SKILL_2X` is the SightLab 2.x skill; a SightLab 3 skill will sit beside it as `src/sightlab-3/`.
"""
from __future__ import annotations

from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
SRC = KIT / "src"
SKILL_2X = SRC / "sightlab-2x"


def skill_dirs(src: Path) -> list[Path]:
    """Every skill folder under `src`: a direct subfolder that holds a SKILL.md, sorted by name."""
    return sorted(d for d in Path(src).iterdir() if d.is_dir() and (d / "SKILL.md").is_file())
