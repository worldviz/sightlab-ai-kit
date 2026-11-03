#!/usr/bin/env python3
"""Lint the kit's Markdown against the generated API map and examples index (Task 5).

Problems reported (each a one-line string naming the file):
  - SKILL.md missing, without front matter (name + description), or without exactly one
    `<!-- host-section -->` marker
  - a backticked `sightlab.<method>(` whose method does not exist on SightLab, or a
    `SightLab(` call with a keyword the constructor does not take
  - an `examples/<Folder>` reference whose folder is not in the examples index
  - "Biopac"/"biopac" in prose (must be BIOPAC; code spans and fences are exempt)
  - a ```python complete``` block that check.py reports errors for

Usage: lint_kit.py [--src src] [--api src/api/sightlab-api.json] [--index src/examples/index.json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / "src" / "harness"))
from check import check_script  # noqa: E402

HOST_MARKER = "<!-- host-section -->"
GENERATED = {"api", "examples/index.md"}
FENCE_RE = re.compile(r"```([^\n]*)\n(.*?)```", re.S)
SPAN_RE = re.compile(r"`([^`\n]+)`")
METHOD_RE = re.compile(r"\bsightlab\.(\w+)\(")
CTOR_RE = re.compile(r"\bSightLab\(([^)]*)\)")
EXAMPLE_RE = re.compile(r"examples/([^`\n)\]|>]+)")
RESOURCE_NAME_RE = re.compile(r"([A-Za-z0-9_\-]+\.(?:osgb|ive|mp4|avi|mpg|wav|mp3|jpg|jpeg|png))\b", re.I)
BIOPAC_RE = re.compile(r"\b(?!BIOPAC\b)[Bb][Ii][Oo][Pp][Aa][Cc]\b")


def _sightlab_methods(api: dict) -> tuple[set, set]:
    classes = api["modules"]["sightlab"]["classes"]
    methods: set = set()
    for cname in ("SightLab", "SightLabServer", "SightLabClient"):
        if cname in classes:
            methods.update(classes[cname]["methods"].keys())
    init = {p["name"] for p in classes.get("SightLab", {}).get("init_params", [])}
    return methods, init


def _strip_code(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Return prose with fences and spans removed, plus the fenced blocks (info, body)."""
    fences = [(m.group(1).strip(), m.group(2)) for m in FENCE_RE.finditer(text)]
    prose = FENCE_RE.sub(" ", text)
    prose = SPAN_RE.sub(" ", prose)
    return prose, fences


def _lint_skill(src: Path) -> list[str]:
    skill = src / "SKILL.md"
    if not skill.is_file():
        return ["SKILL.md: missing"]
    text = skill.read_text(encoding="utf-8-sig")
    problems = []
    fm = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.S)
    if not fm or not re.search(r"^name:\s*\S", fm.group(1), re.M) or not re.search(r"^description:\s*\S", fm.group(1), re.M):
        problems.append("SKILL.md: missing front matter with name and description")
    n = text.count(HOST_MARKER)
    if n != 1:
        problems.append(f"SKILL.md: {HOST_MARKER} must appear exactly once (found {n})")
    return problems


def _shipped_names(src: Path) -> set | None:
    """Basenames of every shipped resource, from src/api/resources.json; None when it is absent."""
    p = src / "api" / "resources.json"
    if not p.is_file():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    return {Path(x).name for x in data.get("all", [])}


def _lint_markdown(path: Path, rel: str, methods: set, init: set, folders: set, api: dict, shipped: set | None = None) -> list[str]:
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    problems: list[str] = []
    prose, fences = _strip_code(text)
    # Resource file names in code spans and fences must ship (e2e follow-ups).
    if shipped is not None:
        lower = {s.lower(): s for s in shipped}
        spans = [m.group(1) for m in SPAN_RE.finditer(text)] + [body for _info, body in fences]
        for span in spans:
            for m in RESOURCE_NAME_RE.finditer(span):
                name = m.group(1)
                before = span[max(0, m.start() - 1):m.start()]
                after = span[m.end():m.end() + 1]
                if before in ("<", "*") or after in (">", "*"):
                    continue  # a placeholder like <name>.osgb or a glob, not a file
                if name in shipped:
                    continue
                if name.lower() in lower:
                    problems.append(f"{rel}: `{name}` is spelled `{lower[name.lower()]}` in the shipped resources; use that spelling")
                else:
                    problems.append(f"{rel}: `{name}` is not a shipped resource (see api/resources.md)")
                break
    # Method and constructor mentions, inside spans and fences.
    code_text = " ".join(m.group(1) for m in SPAN_RE.finditer(text)) + " " + " ".join(body for _info, body in fences)
    for m in METHOD_RE.finditer(code_text):
        if m.group(1) not in methods:
            problems.append(f"{rel}: `sightlab.{m.group(1)}()` is not a SightLab method")
    for m in CTOR_RE.finditer(code_text):
        for kw in re.findall(r"(\w+)\s*=", m.group(1)):
            if kw not in init:
                problems.append(f"{rel}: `SightLab({kw}=...)` is not a constructor argument")
    # Example folder references anywhere. Folder names may contain spaces ("Custom Data
    # Saving"), so match the longest indexed folder that the reference starts with.
    for m in EXAMPLE_RE.finditer(text):
        rest = m.group(1).rstrip("/.,:;")
        if rest in ("index.md", "index.json", "curated") or rest.startswith("curated/"):
            continue
        if not any(rest == f or rest.startswith(f + " ") or rest.startswith(f + "/") for f in folders):
            problems.append(f"{rel}: examples/{rest.split()[0] if rest else ''} is not an indexed example folder")
    # Spelling in prose.
    for m in BIOPAC_RE.finditer(prose):
        problems.append(f"{rel}: write BIOPAC in capitals (found '{m.group(0)}')")
        break
    # Guides describe features; they never turn the agent into an installer (Review Focus 3).
    if rel.startswith("guides/"):
        if text.count("\n") > 250:
            problems.append(f"{rel}: guide is {text.count(chr(10))} lines; the cap is 250")
        if re.search(r"pip install|download and run|\.exe\b", prose, re.I):
            problems.append(f"{rel}: guides may not contain install steps (pip install, download and run, .exe links)")
    # Complete scripts must pass the static checker.
    for info, body in fences:
        if "complete" in info.split() and info.split()[0] == "python":
            with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as fh:
                fh.write(body)
                tmp = fh.name
            report = check_script(tmp, api, None)
            Path(tmp).unlink(missing_ok=True)
            for f in report["errors"]:
                problems.append(f"{rel}: complete script fails check.py: {f['code']} {f['message']}")
    return problems


def lint(src_dir: Path, api: dict, index: list) -> list[str]:
    src = Path(src_dir)
    methods, init = _sightlab_methods(api)
    folders = {e["folder"] for e in index}
    shipped = _shipped_names(src)
    problems = _lint_skill(src)
    for path in sorted(src.rglob("*.md")):
        rel = path.relative_to(src).as_posix()
        if rel.split("/")[0] in GENERATED or rel in GENERATED:
            continue
        problems += _lint_markdown(path, rel, methods, init, folders, api, shipped)
    return problems


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--src", type=Path, default=KIT / "src")
    p.add_argument("--api", type=Path, default=KIT / "src" / "api" / "sightlab-api.json")
    p.add_argument("--index", type=Path, default=KIT / "src" / "examples" / "index.json")
    a = p.parse_args(argv)
    problems = lint(a.src, json.loads(a.api.read_text()), json.loads(a.index.read_text()))
    for line in problems:
        print(line)
    print(f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
