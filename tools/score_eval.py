#!/usr/bin/env python3
"""Score one evaluation run from a check.py report and an autopilot report (evals plan, Task 2).

A pass is strict and honest: the autopilot verdict is behaviour-verified, check.py found no
errors, and every assertion the harness evaluated names a column the brief actually asks for
(an assertion the brief never mentioned cannot vouch for the brief).

Usage: score_eval.py <slug> --check check.json --autopilot autopilot-report.json
                     --agent "claude-code 2.1.195" --kit 2026.11.0-dev [--tokens N] [--wall S]
                     [--date YYYY-MM-DD] [--notes "..."] [--out docs/evals/<YYYY-MM>.md]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_paths import SKILL_2  # noqa: E402
sys.path.insert(0, str(SKILL_2 / "harness"))
from autopilot_core import COUNTED_KINDS  # noqa: E402

HEADER = "| Eval | Date | Agent | Kit | SightLab | Check E/W | Verdict | Assertions | Forced | Trials | Pass | Tokens | Wall s | Notes |"
SEPARATOR = "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"


def _brief_measures_text(eval_dir: Path) -> str:
    text = (eval_dir / "brief.md").read_text(encoding="utf-8") if (eval_dir / "brief.md").is_file() else ""
    out = []
    for sid in ("dvs", "data-logging"):
        m = re.search(r"<!--\s*id:\s*%s\s*-->(.*?)(?=\n## |\Z)" % sid, text, re.S)
        if m:
            out.append(m.group(1))
    return "\n".join(out)


def _brief_trials(eval_dir: Path) -> int | None:
    """The trial count the brief's §10 states (setTrialCount(N), else its first integer)."""
    p = eval_dir / "brief.md"
    if not p.is_file():
        return None
    m = re.search(r"<!--\s*id:\s*trials\s*-->(.*?)(?=\n## |\Z)", p.read_text(encoding="utf-8"), re.S)
    if not m:
        return None
    sec = m.group(1)
    n = re.search(r"setTrialCount\((\d+)\)", sec) or re.search(r"\b(\d+)\b", sec)
    return int(n.group(1)) if n else None


def _declared_assertions(eval_dir: Path) -> dict:
    p = eval_dir / "autopilot-assertions.json"
    if not p.is_file():
        return {}
    return {a.get("name"): a for a in json.loads(p.read_text(encoding="utf-8")) if isinstance(a, dict)}


def score(eval_dir: Path, check_report: dict | None, autopilot_report: dict | None, meta: dict) -> dict:
    eval_dir = Path(eval_dir)
    measures = _brief_measures_text(eval_dir)
    declared = _declared_assertions(eval_dir)
    row = {
        "eval": eval_dir.name,
        "date": meta.get("date") or date.today().isoformat(),
        "agent": meta.get("agent", "?"),
        "kit_version": meta.get("kit_version", "?"),
        "sightlab_utils_version": (autopilot_report or {}).get("sightlab_version"),
        "check_errors": len((check_report or {}).get("errors", [])) if check_report else None,
        "check_warnings": len((check_report or {}).get("warnings", [])) if check_report else None,
        "verdict": (autopilot_report or {}).get("verdict") if autopilot_report else None,
        "assertions_passed": "-",
        "counted_interventions": 0,
        "trials": "-",
        "brief_trials": _brief_trials(eval_dir),
        "brief_trials_mismatch": False,
        "assertion_mismatch": [],
        "pass": False,
        "cost_tokens": meta.get("tokens"),
        "wall_s": meta.get("wall_s"),
        "notes": meta.get("notes", ""),
    }
    if autopilot_report:
        asserts = autopilot_report.get("assertions", [])
        row["assertions_passed"] = "%d/%d" % (sum(1 for a in asserts if a.get("pass")), len(asserts))
        row["counted_interventions"] = sum(1 for i in autopilot_report.get("interventions", []) if i.get("kind") in COUNTED_KINDS)
        exp = autopilot_report.get("trials_expected")
        row["trials"] = "%s/%s" % (autopilot_report.get("trials_completed", 0), exp if exp is not None else "?")
        # Review Focus 5: the script's own count must be the brief's count.
        if exp is not None and row["brief_trials"] is not None and exp != row["brief_trials"]:
            row["brief_trials_mismatch"] = True
        for a in asserts:
            name = a.get("name")
            column = a.get("column") or declared.get(name, {}).get("column")
            if name not in declared and column is None:
                row["assertion_mismatch"].append(name)
            elif column is not None and column not in measures:
                row["assertion_mismatch"].append(name)
    row["pass"] = bool(
        autopilot_report and row["verdict"] == "behaviour-verified"
        and check_report is not None and row["check_errors"] == 0
        and not row["assertion_mismatch"] and not row["brief_trials_mismatch"]
    )
    return row


def _cell(v) -> str:
    if v is None:
        return "-"
    return str(v).replace("|", "/").replace("\n", " ")


def append_scoreboard(row: dict, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    lines = []
    if HEADER not in existing:
        if not existing:
            lines += ["# Eval scoreboard", "", "One row per run; `tools/score_eval.py` appends them. A pass needs `behaviour-verified`,", "zero `check.py` errors and assertions that match the brief (`docs/evals/README.md`).", ""]
        lines += [HEADER, SEPARATOR]
    check = "-" if row["check_errors"] is None else "%d/%d" % (row["check_errors"], row["check_warnings"])
    mismatch = (" mismatch: " + ", ".join(row["assertion_mismatch"])) if row["assertion_mismatch"] else ""
    if row["brief_trials_mismatch"]:
        mismatch += " brief says %s trials" % row["brief_trials"]
    lines.append("| %s |" % " | ".join(_cell(x) for x in (
        row["eval"], row["date"], row["agent"], row["kit_version"], row["sightlab_utils_version"], check,
        row["verdict"], row["assertions_passed"], row["counted_interventions"], row["trials"],
        "✔" if row["pass"] else "✘", row["cost_tokens"], row["wall_s"], (row["notes"] + mismatch).strip(),
    )))
    with open(path, "a", encoding="utf-8") as fh:
        if existing and not existing.endswith("\n"):
            fh.write("\n")
        fh.write("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("slug")
    p.add_argument("--check", type=Path, default=None, help="check.py --json output")
    p.add_argument("--autopilot", type=Path, default=None, help="autopilot-report.json")
    p.add_argument("--agent", required=True)
    p.add_argument("--kit", required=True)
    p.add_argument("--tokens", type=int, default=None)
    p.add_argument("--wall", type=float, default=None)
    p.add_argument("--date", default=None)
    p.add_argument("--notes", default="")
    p.add_argument("--out", type=Path, default=None)
    a = p.parse_args(argv)
    eval_dir = SKILL_2 / "evals" / a.slug
    if not eval_dir.is_dir():
        print("no such eval: %s" % a.slug, file=sys.stderr)
        return 2
    check = json.loads(a.check.read_text(encoding="utf-8")) if a.check else None
    auto = json.loads(a.autopilot.read_text(encoding="utf-8")) if a.autopilot else None
    meta = {"agent": a.agent, "kit_version": a.kit, "tokens": a.tokens, "wall_s": a.wall, "date": a.date, "notes": a.notes}
    row = score(eval_dir, check, auto, meta)
    out = a.out or (KIT / "docs" / "evals" / ("%s.md" % row["date"][:7]))
    append_scoreboard(row, out)
    print(json.dumps(row, indent=1))
    print("appended to %s" % out)
    return 0 if row["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
