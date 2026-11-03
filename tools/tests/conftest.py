"""Shared fixtures for the kit's tool tests.

SOURCES is the read-only fetch made by tools/fetch_sources.sh. Tests that need
it skip when it is absent so the suite still runs on a machine without
Assembla access.
"""
import os
import sys
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KIT / "tools"))
from kit_paths import SKILL_2  # noqa: E402

sys.path.insert(0, str(SKILL_2 / "harness"))


@pytest.fixture(scope="session")
def SOURCES() -> Path:
    root = Path(os.environ.get("SL2_SOURCES", Path.home() / "development" / "sightlab-2-sources"))
    if not (root / "VERSION").is_file():
        pytest.skip(f"SightLab 2 sources not fetched at {root}; run tools/fetch_sources.sh")
    return root


@pytest.fixture(scope="session")
def kit() -> Path:
    return KIT


@pytest.fixture(scope="session")
def skill_src() -> Path:
    """The SightLab 2 skill folder, src/sightlab-2."""
    return SKILL_2
