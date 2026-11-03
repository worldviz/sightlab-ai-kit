"""Task 1: the fetched SightLab 2 sources are what the generators expect."""
from pathlib import Path

BINARY = {".osgb", ".png", ".jpg", ".jpeg", ".avi", ".mp4", ".wav", ".mp3", ".ive", ".fbx", ".glb"}


def test_version_stamp(SOURCES: Path):
    first = (SOURCES / "VERSION").read_text().splitlines()[0]
    assert first.startswith("sightlab_utils 2.")


def test_core_present(SOURCES: Path):
    core = SOURCES / "sightlab_utils" / "sightlab.py"
    assert core.is_file() and core.stat().st_size > 500_000
    assert (SOURCES / "sightlab_utils" / "resources" / "EXCLUDED.txt").is_file()
    for folder in ("sightlab_utils", "ExampleScripts"):
        binaries = [p for p in (SOURCES / folder).rglob("*") if p.suffix.lower() in BINARY]
        assert binaries == [], binaries[:5]


def test_examples_present(SOURCES: Path):
    examples = SOURCES / "ExampleScripts"
    with_py = [d for d in examples.iterdir() if d.is_dir() and any(d.rglob("*.py"))]
    assert len(with_py) >= 90
    assert (examples / "Sample Code" / "SightLabVR_NonGUI.py").is_file()


def test_resources_list(SOURCES: Path):
    lines = (SOURCES / "resources-list.txt").read_text().splitlines()
    assert len(lines) > 100
    assert "environments/" in lines
