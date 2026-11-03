---
created: 2026-11-03
author: Claude (Fable 5.1), for Sado Rabaudi
---

# SightLab 2.x AI Kit 2026.11.1: what changed since your review, and what to try

Your 2026-11-03 findings and Astra's review drove this version. In order:

| Finding | What changed |
|---|---|
| Install should be once, not per project | The kit is a plugin installed from this repository (see `README.md`). The starter project is an empty template; nothing is copied into projects. |
| Overhead on small requests (97 s vs 49 s) | `SKILL.md` §0 "Size the request": a question gets an answer, a small edit gets the edit plus `check.py`, only a build or a run-time bug gets the autopilot and `REVIEW.md`. The agent says what a run will check and asks before launching. |
| Relative launch paths | The harness runs from the plugin's own folder and takes the script's absolute path; the skill says so everywhere. |
| Parked target 50 m below the scene | The look-at skips any object more than 30 m from the eye. |
| Rating always 1 | The harness now picks the first, middle and last option on successive rating prompts (`rating-selected` in the report). |
| `endFade=False` wording | Fixed in `patterns/rating-after-trial.md`: the scene is hidden behind the scale regardless; `endFade` only controls the fade-out after the choice, while a trial is running. |
| NO_AUTOPILOT only in instructions | `autopilot.py` refuses on its own (exit 3) when the file is in the experiment folder. |
| Codex untested | Still untested end to end by us; the Codex marketplace route below is what to try. |

## What to try

1. **Claude Code, install once:** `claude plugin install sightlab-2x --marketplace worldviz/sightlab-ai-kit`.
   Then, in any study folder, `claude`. Ask one question ("what does `endFade` do?"), one small
   edit (add a 1–7 rating to an existing script), and one build (two sentences describing a
   study). Time each; the first two should be well under a minute and launch nothing.
2. **Codex, install once:** `codex plugin marketplace add worldviz/sightlab-ai-kit`, then
   `codex`, `/plugins`, install SightLab VR Assistant, start a new session. Repeat the three
   requests. Tell us whether the plugin appears in the ChatGPT desktop app's Plugins tab too.
3. **claude.ai:** Customize > Plugins > Add marketplace `worldviz/sightlab-ai-kit`, add the
   plugin, ask the `endFade` question in chat; it should quote `reference/sightlab.py`.
4. **The harness on one of your scripts**, from the installed plugin's folder (Claude Code
   caches it under `~/.claude/plugins/`; `claude plugin list` prints the path):
   `winviz.exe "<plugin>\skills\sightlab-2x\harness\autopilot.py" "<absolute script path>"`.
   Look for `rating-selected` interventions and no look-at at a parked object.
5. **The OpenAI directory:** `dist/openai-plugin.zip` is the upload for the SightLab VR
   Assistant listing; `docs/submission/openai-directory.md` lists the fields and the
   wording that is yours to settle.

## What to report

Same list as before, most useful first: where the kit is wrong about SightLab (file and
line); scripts the harness could not drive, with the report; anything called
`behaviour-verified` the headset disagreed with; anything that annoyed you, with the time
it cost.
