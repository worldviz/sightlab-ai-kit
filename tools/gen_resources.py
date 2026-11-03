#!/usr/bin/env python3
"""Generate the shipped resource names (api/resources.json + resources.md) from resources-list.txt.

Names only: what ships under sightlab_resources/, grouped by top folder, so the agent and the
checker can confirm a file exists instead of guessing (e2e follow-ups, Task 1).

Usage: gen_resources.py [--sources DIR] [--out src/api]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_SOURCES = Path.home() / "development" / "sightlab-2x-sources"
MEDIA = {".osgb", ".ive", ".obj", ".fbx", ".gltf", ".glb", ".mp4", ".avi", ".mpg", ".wav", ".mp3", ".ogg", ".jpg", ".jpeg", ".png", ".cfg", ".py", ".txt", ".csv", ".json"}


SIZED_FOLDERS = ("objects", "scene_objects", "environments")
CLASSED_FOLDERS = ("objects", "scene_objects")


def size_class(size) -> str:
    """hand-held (fits a hand, ≤ 0.35 m), table-top (≤ 0.8 m), large (furniture and up), by the longest side."""
    longest = max(float(v) for v in size)
    if longest <= 0.35:
        return "hand-held"
    if longest <= 0.8:
        return "table-top"
    return "large"


def fold_sizes(measurements: dict) -> dict:
    """{folder/name: {size, center, bottom[, class]}} from measure_resources.py output (metres)."""
    out = {}
    for folder in SIZED_FOLDERS:
        for name, m in (measurements.get("folders", {}).get(folder) or {}).items():
            size = [round(float(v), 3) for v in m["size"]]
            center = [round(float(v), 3) for v in m["center"]]
            entry = {"size": size, "center": center, "bottom": round(center[1] - size[1] / 2, 3)}
            if folder in CLASSED_FOLDERS:
                entry["class"] = size_class(size)
            out[folder + "/" + name] = entry
    return out


def build_resources(list_path: Path, measurements: dict | None = None) -> dict:
    lines = [l.strip().replace("\\", "/") for l in Path(list_path).read_text(encoding="utf-8").splitlines() if l.strip()]
    files = [l for l in lines if not l.endswith("/") and not l.startswith("/") and ".." not in l]
    folders: dict[str, list[str]] = {}
    for p in files:
        parts = p.split("/")
        if len(parts) < 2:
            folders.setdefault("(root)", []).append(parts[0])
            continue
        top = parts[0]
        folders.setdefault(top, []).append("/".join(parts[1:]))
    for k in folders:
        folders[k] = sorted(set(folders[k]), key=str.lower)
    res = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "root": "sightlab_resources",
        "folders": folders,
        "all": sorted(set(files), key=str.lower),
    }
    if measurements:
        res["sizes"] = fold_sizes(measurements)
        res["measured"] = measurements.get("generated")
    return res


def _md(res: dict) -> str:
    lines = [
        "# Shipped resources (`sightlab_resources/`)",
        "",
        f"Generated {res['generated']} by `tools/gen_resources.py` from the SightLab 2 resource folder; names only.",
        "Load an environment with `vizfx.addChild('sightlab_resources/environments/<name>')` and an object with",
        "`vizfx.addChild('sightlab_resources/objects/<name>')`. Use the spelling shown here: the shipped",
        "files are found through the Windows file system, which forgives case, but the GUI lists and any",
        "case-sensitive copy of the resources do not.",
        "A file not listed here does not ship; use a primitive or the researcher's own model instead.",
        "",
    ]
    sizes = res.get("sizes")
    if sizes:
        lines += [
            f"Sizes are bounding boxes in metres (width × height × depth) measured in Vizard on {res.get('measured', '?')}.",
            "The models are built at real-world size unless the table says otherwise; pick by class: **hand-held**",
            "(longest side ≤ 0.35 m) for things held, grabbed or set out on a table, **table-top** (≤ 0.8 m),",
            "**large** (furniture, vehicles, rooms). To change a size, `setScale` once, to the size the brief",
            "implies, and record it in the brief. `bottom` is the lowest point relative to the model's own",
            "origin: to stand a model on a surface at height h, set its y to `h - bottom`. The centre may be",
            "off the origin (for example `Table.osgb`), so place by the listed centre, not by the origin.",
            "",
        ]
    order = ["environments", "objects", "scene_objects", "avatar", "media", "media_2D", "audio", "example_resources", "icons"]
    for folder in order + sorted(k for k in res["folders"] if k not in order):
        names = res["folders"].get(folder)
        if not names:
            continue
        lines += [f"## {folder}", "", f"{len(names)} files.", ""]
        if sizes and folder in SIZED_FOLDERS:
            classed = folder in CLASSED_FOLDERS
            lines.append("| file | w × h × d (m) | class | bottom (m) | centre (x, y, z) |" if classed
                         else "| file | w × h × d (m) | floor y (m) | centre (x, y, z) |")
            lines.append("|---|---|---|---|---|" if classed else "|---|---|---|---|")
            for n in names:
                m = sizes.get(folder + "/" + n)
                if m is None:
                    lines.append(f"| `{n}` | unmeasured | | |" + (" |" if classed else ""))
                    continue
                dims = " × ".join(f"{v:.2f}" for v in m["size"])
                centre = ", ".join(f"{v:.2f}" for v in m["center"])
                if classed:
                    lines.append(f"| `{n}` | {dims} | {m['class']} | {m['bottom']:.2f} | {centre} |")
                else:
                    lines.append(f"| `{n}` | {dims} | {m['bottom']:.2f} | {centre} |")
        elif folder in ("environments", "objects", "scene_objects", "avatar", "media", "media_2D", "audio"):
            lines.append(", ".join(f"`{n}`" for n in names))
        else:
            lines.append(", ".join(f"`{n}`" for n in names[:40]) + (" …" if len(names) > 40 else ""))
        lines.append("")
    return "\n".join(lines)


def write_resources(res: dict, out_dir: Path) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "resources.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    (out_dir / "resources.md").write_text(_md(res), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    kit = Path(__file__).resolve().parents[1]
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    p.add_argument("--out", type=Path, default=kit / "src" / "api")
    p.add_argument("--measurements", type=Path, default=kit / "tools" / "data" / "resource-measurements.json",
                   help="output of tools/vm/measure_resources.py; sizes are omitted when the file is absent")
    a = p.parse_args(argv)
    measurements = json.loads(a.measurements.read_text(encoding="utf-8")) if a.measurements.is_file() else None
    res = build_resources(a.sources / "resources-list.txt", measurements=measurements)
    write_resources(res, a.out)
    print(f"{len(res['all'])} resource names in {len(res['folders'])} folders -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
