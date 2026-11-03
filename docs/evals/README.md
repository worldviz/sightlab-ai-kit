---
created: 2026-10-31
author: Claude (Fable 5.1)
---

# Running and scoring an eval

The four evals live in `src/evals/` (and in every shipped wrapper). This folder holds the
scoreboards, one Markdown file per month, appended by `tools/score_eval.py`.

## By hand

1. Build the kit (`tools/build_kit.py --version <v>`), copy `dist/starter-project/` to a new
   folder, copy `src/evals/<slug>/brief.md` into its `brief/`. The starter carries no copy of
   the kit: load the built plugin with `--plugin-dir dist/claude-plugin` (or install it).
2. Have the agent build the study from the brief (Claude Code: `claude -p --plugin-dir
   dist/claude-plugin "..."` or interactively with `/sightlab:new`). Ask for the
   complete build, through the responses and data checkpoints, taking the kit's defaults for
   open questions and marking them `(assumed)`; "stop after the skeleton checkpoint" is read
   literally by some runs and then needs a second "carry on" message (2026-10-31, evals 3–4).
3. `python dist/claude-plugin/skills/sightlab-2/harness/check.py <script> --json > check.json`.
4. On the Vizard machine, with the plugin's skill folder staged beside the experiment:
   `winviz.exe <skill>\harness\autopilot.py <absolute script path> --assertions
   <eval>\autopilot-assertions.json`; copy back `autopilot-report.json`.
5. `python tools/score_eval.py <slug> --check check.json --autopilot autopilot-report.json
   --agent "<agent version>" --kit <v> --tokens <n> --wall <s>`.
6. Do the feel pass from `acceptance.md` and add a word to the row's Notes if it fails.

## Columns

| Column | Meaning |
|---|---|
| Check E/W | `check.py` errors / warnings on the agent's script |
| Verdict | the autopilot verdict (`failed`, `smoke-passed`, `behaviour-verified`) |
| Assertions | passed / evaluated, from the eval's `autopilot-assertions.json` |
| Forced | interventions that count against the behaviour tier |
| Trials | completed / expected |
| Pass | ✔ only when verdict is `behaviour-verified`, Check E is 0 and no assertion is a mismatch |
| Tokens, Wall s | what the agent run cost, from its own output |
| Notes | feel-pass remarks; `mismatch:` lists assertions whose column the brief never asked for |

An assertion mismatch means the eval was scored against something the brief did not
specify; it fails the eval, not the harness, and the assertions file should be fixed.
