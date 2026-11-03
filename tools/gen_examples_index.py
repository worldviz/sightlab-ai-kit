#!/usr/bin/env python3
"""Generate the examples index from a shipped `ExampleScripts` folder (design §6.4, Task 3).

For every example folder: its scripts, a one-line summary, the SightLab methods it calls,
what it demonstrates (gaze, grab, BIOPAC, ratings, STIM files, multi-user) and the hardware
it hints at. Output: index.json (for tools) and index.md (for the agent).

Usage: gen_examples_index.py [--sources DIR] [--api src/api/sightlab-api.json] [--out src/examples]
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
import warnings
from pathlib import Path

SKIP_FOLDERS = {"_dashboard", "_downloaded", "regenerate_test", "__pycache__"}
SKIP_SCRIPTS = {"SightLabVR_Replay.py", "ReadMe.py", "README.py", "customSettings.py"}
README_NAMES = ("ReadMe.py", "README.py", "ReadMe.md", "README.md", "readme.md", "ReadMe.txt", "README.txt", "readme.txt")
HARDWARE_HINTS = (
    "Vive Pro Eye", "Vive Focus", "Vive", "Quest Pro", "Quest 3", "Quest", "Omnicept", "Varjo", "Pupil Labs",
    "Pimax", "StarVR", "SteamVR", "Steamlink", "Optitrack", "Mocopi", "Manus", "Tobii", "LSL",
    "Kinect", "Vive Trackers", "Screen Based EyeTracker", "Projection",
)  # BIOPAC is not a word hint: it comes from flags["biopac"], which needs real use (see _entry)
DEFAULT_SOURCES = Path.home() / "development" / "sightlab-2x-sources"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def _first_text_block(text: str) -> str:
    """First docstring or leading comment block of a script, or first paragraph of prose."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # shipped scripts have invalid escapes; not our concern here
            doc = ast.get_docstring(ast.parse(text))
        if doc:
            return doc
    except SyntaxError:
        pass
    lines = text.splitlines()
    block: list[str] = []
    for line in lines:
        s = line.strip()
        if s.startswith("#"):
            block.append(s.lstrip("#").strip())
        elif block:
            break
        elif s and not s.startswith("#"):
            break
    if block:
        return " ".join(b for b in block if b)
    # Prose files only: a code paragraph is never a summary.
    for para in re.split(r"\n\s*\n", text.strip()):
        p = para.strip()
        if p and not p.startswith("#") and not re.match(r"^(import|from|def|class|\w+\s*=|@)", p):
            return p
    return ""


def _one_line(text: str, limit: int = 160) -> str:
    s = re.sub(r"\s+", " ", text).replace("|", "/").strip()
    s = re.sub(r"^(#+\s*|\"\"\"|''')", "", s).strip()
    return (s[: limit - 1] + "…") if len(s) > limit else s


def _api_method_names(api: dict) -> set[str]:
    names: set[str] = set()
    for mod in api["modules"].values():
        for cls in mod["classes"].values():
            names.update(cls["methods"].keys())
        names.update(mod["functions"].keys())
    return names


def _scan_script(text: str, method_names: set[str]) -> dict:
    found: dict = {"methods": set(), "gui": None, "gaze": False, "grab": False, "environments": set()}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tree = ast.parse(text)
    except SyntaxError:
        tree = None
    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                name = fn.attr if isinstance(fn, ast.Attribute) else (fn.id if isinstance(fn, ast.Name) else None)
                if name in method_names:
                    found["methods"].add(name)
                if name == "SightLab":
                    for kw in node.keywords:
                        if kw.arg == "gui" and isinstance(kw.value, ast.Constant):
                            found["gui"] = bool(kw.value.value)
                for kw in node.keywords:
                    if kw.arg in ("gaze", "grab") and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        found[kw.arg] = True
            elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.lower().endswith(".osgb"):
                found["environments"].add(Path(node.value).name)
    else:
        for m in re.finditer(r"\.(\w+)\(", text):
            if m.group(1) in method_names:
                found["methods"].add(m.group(1))
    return found


def _entry(folder: Path, method_names: set[str]) -> dict | None:
    # is_file(): a shipped folder is literally named "HR detection task.py" (Biofeedback).
    scripts = sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*.py") if p.is_file() and "__pycache__" not in p.parts)
    if not scripts:
        return None
    readme = next((folder / n for n in README_NAMES if (folder / n).is_file()), None)
    main_candidates = [s for s in scripts if "/" not in s and Path(s).name not in SKIP_SCRIPTS] or [s for s in scripts if Path(s).name not in SKIP_SCRIPTS] or scripts
    main = sorted(main_candidates, key=lambda s: (len(s), s))[0]
    text_all = "\n".join(_read(folder / s) for s in scripts)
    scan = _scan_script(_read(folder / main), method_names)
    for s in scripts:
        if s != main:
            more = _scan_script(_read(folder / s), method_names)
            scan["methods"] |= more["methods"]
            scan["environments"] |= more["environments"]
            scan["gaze"] = scan["gaze"] or more["gaze"]
            scan["grab"] = scan["grab"] or more["grab"]
    summary = _one_line(_first_text_block(_read(folder / main)))
    if not summary and readme is not None:
        summary = _one_line(_first_text_block(_read(readme)))
    low = text_all.lower()
    flags = {
        "gui": scan["gui"],
        "gaze": scan["gaze"],
        "grab": scan["grab"],
        # BIOPAC means the example actually uses it, not that a comment or a False flag mentions it.
        "biopac": bool(re.search(r"biopac\s*=\s*True|BIOPAC_ON\s*=\s*True|import\s+biopacndt|from\s+sightlab_utils\s+import\s+biopacndt", text_all)),
        "ratings": ("startratings" in low) or ("endratings" in low) or ("ratingscale" in low) or ("rating_scale" in low),
        "stim_files": (".stim" in low) or ("stim_reader" in low) or ("stim file" in low) or ("stim_file" in low),
        "multi_user": ("sightlabserver" in low) or ("sightlabclient" in low),
    }
    # Whole words only: "question" is not a Quest.
    hints = [h for h in HARDWARE_HINTS if re.search(r"(?<![a-z0-9])" + re.escape(h.lower()) + r"(?![a-z0-9])", low)]
    # Drop generic hints shadowed by a more specific one ("Vive" when "Vive Pro Eye" matched).
    hints = [h for h in hints if not any(o != h and h in o for o in hints)]
    return {
        "folder": folder.name,
        "scripts": scripts,
        "main_script": main,
        "readme": readme.name if readme else None,
        "summary": summary,
        "methods": sorted(scan["methods"]),
        "flags": flags,
        "hardware_hints": hints,
        "environments": sorted(scan["environments"]),
    }


def build_examples_index(examples_dir: Path, api: dict) -> list[dict]:
    examples_dir = Path(examples_dir)
    names = _api_method_names(api)
    out: list[dict] = []
    for folder in sorted(p for p in examples_dir.iterdir() if p.is_dir() and p.name not in SKIP_FOLDERS):
        e = _entry(folder, names)
        if e is not None:
            out.append(e)
    return out


def _needs(e: dict) -> str:
    parts = list(e["hardware_hints"])
    if e["flags"]["biopac"] and "BIOPAC" not in parts:
        parts.append("BIOPAC")
    if e["flags"]["multi_user"]:
        parts.append("two machines")
    return ", ".join(parts) if parts else "none"


def write_examples_index(index: list[dict], out_dir: Path) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.json").write_text(json.dumps(index, indent=1) + "\n", encoding="utf-8")
    lines = [
        "# Shipped example scripts",
        "",
        f"{len(index)} folders under the SightLab 2 projects folder `ExampleScripts/`. Generated by",
        "`tools/gen_examples_index.py`; do not edit. Read the script itself before copying from it.",
        "",
        "| Folder | What it shows | SightLab calls | Needs |",
        "| --- | --- | --- | --- |",
    ]
    for e in index:
        calls = ", ".join(f"`{m}`" for m in e["methods"][:8]) + (" …" if len(e["methods"]) > 8 else "")
        shows = e["summary"] or f"main script `{e['main_script']}`"
        tags = [k for k, v in e["flags"].items() if v is True and k != "gui"]
        if tags:
            shows += " _(" + ", ".join(tags) + ")_"
        lines.append(f"| `{e['folder']}` | {shows} | {calls or '—'} | {_needs(e)} |")
    lines.append("")
    (out_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    kit = Path(__file__).resolve().parents[1]
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    p.add_argument("--api", type=Path, default=kit / "src" / "api" / "sightlab-api.json")
    p.add_argument("--out", type=Path, default=kit / "src" / "examples")
    a = p.parse_args(argv)
    api = json.loads(a.api.read_text(encoding="utf-8"))
    index = build_examples_index(a.sources / "ExampleScripts", api)
    write_examples_index(index, a.out)
    print(f"{len(index)} examples indexed -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
