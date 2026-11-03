#!/usr/bin/env python3
"""Copy a curated set of shipped example scripts into src/examples/curated/ (Task 9).

Each copy gets a two-line header naming its source, then the script unchanged. Every copy
must pass harness/check.py with no errors; one that does not is refused and named.

Usage: curate_examples.py [--sources DIR] [--list tools/curated-list.txt]
The list file has one `Folder/script.py` per line (paths under ExampleScripts/).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / "src" / "harness"))
from check import check_script, load_api  # noqa: E402

DEFAULT_SOURCES = Path.home() / "development" / "sightlab-2x-sources"


def slug(rel: str) -> str:
    folder, name = rel.rsplit("/", 1)
    base = re.sub(r"[^A-Za-z0-9]+", "_", f"{folder}__{Path(name).stem}").strip("_")
    return base + ".py"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    p.add_argument("--list", type=Path, default=KIT / "tools" / "curated-list.txt")
    p.add_argument("--out", type=Path, default=KIT / "src" / "examples" / "curated")
    a = p.parse_args(argv)

    api = load_api(KIT / "src" / "api" / "sightlab-api.json")
    rels = [l.strip() for l in a.list.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    a.out.mkdir(parents=True, exist_ok=True)
    for old in a.out.glob("*.py"):
        old.unlink()
    failed = []
    for rel in rels:
        src = a.sources / "ExampleScripts" / rel
        if not src.is_file():
            failed.append((rel, "not found"))
            continue
        body = src.read_text(encoding="utf-8-sig", errors="replace").replace("\r\n", "\n")
        header = (f"# Source: ExampleScripts/{rel}\n"
                  f"# SightLab 2.x shipped example, copied unchanged below this header by the AI Kit on {date.today().isoformat()}.\n")
        out = a.out / slug(rel)
        out.write_text(header + body, encoding="utf-8", newline="\n")
        report = check_script(out, api, None)
        if report["errors"]:
            failed.append((rel, ", ".join(f["code"] for f in report["errors"])))
            out.unlink()
    for rel, why in failed:
        print(f"refused {rel}: {why}", file=sys.stderr)
    n = len(list(a.out.glob("*.py")))
    print(f"{n} curated examples in {a.out}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
