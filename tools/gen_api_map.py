#!/usr/bin/env python3
"""Generate the SightLab 2.x API map from a `sightlab_utils` package, using `ast` only.

No Vizard import is needed, so this runs on any Python 3.9+. Output (design §6.4):

  sightlab-api.json   every module/class/method/param the checker needs (GUI classes included)
  sightlab-api.md     the human/agent page: SightLab, SightLabServer, SightLabClient, functions
  undocumented.md     public methods with no docstring, grouped by class (Sado's backlog)

Usage: gen_api_map.py [--sources DIR] [--out DIR]
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_paths import SKILL_2X  # noqa: E402

MODULES = ("sightlab", "settings", "eye_tracker_utils", "gaze_events")
PAGE_CLASSES_PREFIX = "SightLab"  # classes shown on the Markdown page; GUI/HUD/SessionRecorder stay JSON-only
DEFAULT_SOURCES = Path.home() / "development" / "sightlab-2x-sources"


def _is_public(name: str) -> bool:
    return not name.startswith("_")


def _first_paragraph(doc: str | None) -> str:
    if not doc:
        return ""
    return doc.strip().split("\n\n")[0].replace("\n", " ").strip()


def _params(fn: ast.FunctionDef) -> list[dict]:
    a = fn.args
    out: list[dict] = []
    positional = a.posonlyargs + a.args
    defaults: list[ast.expr | None] = [None] * (len(positional) - len(a.defaults)) + list(a.defaults)
    for arg, default in zip(positional, defaults):
        if arg.arg == "self":
            continue
        out.append({"name": arg.arg, "default": ast.unparse(default) if default is not None else None, "kind": "positional"})
    if a.vararg:
        out.append({"name": a.vararg.arg, "default": None, "kind": "vararg"})
    for arg, default in zip(a.kwonlyargs, a.kw_defaults):
        out.append({"name": arg.arg, "default": ast.unparse(default) if default is not None else None, "kind": "keyword-only"})
    if a.kwarg:
        out.append({"name": a.kwarg.arg, "default": None, "kind": "kwarg"})
    return out


def _signature(fn: ast.FunctionDef) -> str:
    args = ast.unparse(fn.args)
    args = re.sub(r"^self\s*,?\s*", "", args)
    return f"{fn.name}({args})"


def _is_generator(fn: ast.FunctionDef) -> bool:
    for node in ast.walk(fn):
        if isinstance(node, (ast.Yield, ast.YieldFrom)):
            return True
    return False


def _method(fn: ast.FunctionDef) -> dict:
    return {
        "signature": _signature(fn),
        "params": _params(fn),
        "doc": ast.get_docstring(fn),
        "lineno": fn.lineno,
        "is_generator": _is_generator(fn),
    }


def _class(cls: ast.ClassDef) -> dict:
    methods = {}
    init_params: list[dict] = []
    for node in cls.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name == "__init__":
            init_params = _params(node)
        elif _is_public(node.name):
            methods[node.name] = _method(node)
    return {
        "doc": ast.get_docstring(cls),
        "bases": [ast.unparse(b) for b in cls.bases],
        "lineno": cls.lineno,
        "init_params": init_params,
        "methods": methods,
    }


def _constants(tree: ast.Module) -> list[str]:
    names: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id.isupper():
                    names.append(t.id)
    return names


def _module(path: Path) -> dict:
    # utf-8-sig: some modules carry a BOM (eye_tracker_utils.py does), which ast rejects as U+FEFF.
    tree = ast.parse(path.read_text(encoding="utf-8-sig", errors="replace"), filename=str(path))
    classes = {n.name: _class(n) for n in tree.body if isinstance(n, ast.ClassDef) and _is_public(n.name)}
    functions = {n.name: _method(n) for n in tree.body if isinstance(n, ast.FunctionDef) and _is_public(n.name)}
    return {"classes": classes, "functions": functions, "constants": _constants(tree)}


def _version(package_dir: Path) -> str:
    init = package_dir / "__init__.py"
    m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init.read_text(encoding="utf-8", errors="replace")) if init.is_file() else None
    return m.group(1) if m else "unknown"


def build_api_map(package_dir: Path) -> dict:
    package_dir = Path(package_dir)
    modules = {name: _module(package_dir / f"{name}.py") for name in MODULES if (package_dir / f"{name}.py").is_file()}
    return {
        "sightlab_utils_version": _version(package_dir),
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "modules": modules,
        "settings_constants": modules.get("settings", {}).get("constants", []),
    }


def _md_page(api: dict) -> str:
    lines = [
        f"# SightLab 2.x API map (sightlab_utils {api['sightlab_utils_version']})",
        "",
        f"Generated {api['generated']} by `tools/gen_api_map.py`. Do not edit; regenerate.",
        "Signatures are what the installed package exposes; docstrings are the first paragraph only.",
        "",
    ]
    sl = api["modules"].get("sightlab", {})
    for cname, cls in sl.get("classes", {}).items():
        if not cname.startswith(PAGE_CLASSES_PREFIX):
            continue
        bases = f"({', '.join(cls['bases'])})" if cls["bases"] else ""
        lines += [f"## class {cname}{bases}", ""]
        if cls["doc"]:
            lines += [_first_paragraph(cls["doc"]), ""]
        if cls["init_params"]:
            lines += ["Constructor keyword arguments: " + ", ".join(f"`{p['name']}={p['default']}`" if p["default"] is not None else f"`{p['name']}`" for p in cls["init_params"]), ""]
        for mname, m in cls["methods"].items():
            gen = " *(generator: use with `yield`)*" if m["is_generator"] else ""
            lines += [f"### `{m['signature']}`{gen}", ""]
            doc = _first_paragraph(m["doc"])
            lines += [doc if doc else "_No docstring._", ""]
    if sl.get("functions"):
        lines += ["## Module functions (sightlab)", ""]
        for fname, f in sl["functions"].items():
            lines += [f"- `{f['signature']}` — {_first_paragraph(f['doc']) or '_No docstring._'}"]
        lines += [""]
    for mod in ("eye_tracker_utils", "gaze_events"):
        if mod in api["modules"]:
            lines += [f"## {mod}", ""]
            for fname, f in api["modules"][mod]["functions"].items():
                lines += [f"- `{f['signature']}` — {_first_paragraph(f['doc']) or '_No docstring._'}"]
            consts = api["modules"][mod]["constants"]
            if consts:
                lines += ["", "Constants: " + ", ".join(f"`{c}`" for c in consts)]
            lines += [""]
    if api["settings_constants"]:
        lines += ["## settings constants", "", "Available after `from sightlab_utils.settings import *`:", "", ", ".join(f"`{c}`" for c in api["settings_constants"]), ""]
    return "\n".join(lines)


def _md_undocumented(api: dict) -> str:
    sl = api["modules"].get("sightlab", {})
    entries: dict[str, list[str]] = {}
    for cname, cls in sl.get("classes", {}).items():
        for mname, m in cls["methods"].items():
            if not m["doc"]:
                entries.setdefault(cname, []).append(f"{cname}.{m['signature']}")
    total = sum(len(v) for v in entries.values())
    lines = [f"# Undocumented public methods ({total})", "", "Public methods in `sightlab.py` with no docstring, grouped by class. Generated; regenerate after adding docstrings.", ""]
    for cname, items in entries.items():
        lines += [f"## {cname} ({len(items)})", ""]
        lines += [f"- `{i}`" for i in items]
        lines += [""]
    return "\n".join(lines)


def write_api_map(api: dict, out_dir: Path) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "sightlab-api.json").write_text(json.dumps(api, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "sightlab-api.md").write_text(_md_page(api), encoding="utf-8")
    (out_dir / "undocumented.md").write_text(_md_undocumented(api), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--sources", type=Path, default=DEFAULT_SOURCES, help="folder holding sightlab_utils/ (from fetch_sources.sh)")
    p.add_argument("--package", type=Path, default=None, help="a sightlab_utils package dir (overrides --sources)")
    p.add_argument("--out", type=Path, default=SKILL_2X / "api")
    a = p.parse_args(argv)
    package = a.package or (a.sources / "sightlab_utils")
    api = build_api_map(package)
    write_api_map(api, a.out)
    sl = api["modules"]["sightlab"]["classes"]
    n = sum(len(c["methods"]) for c in sl.values())
    und = sum(1 for c in sl.values() for m in c["methods"].values() if not m["doc"])
    print(f"sightlab_utils {api['sightlab_utils_version']}: {len(sl)} classes, {n} public methods, {und} undocumented -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
