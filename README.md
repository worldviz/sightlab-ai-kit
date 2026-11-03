# SightLab 2.x AI Kit

One kit that teaches an AI coding agent to build, check and test WorldViz SightLab 2.x
experiments (the Python eye-tracking library that runs inside Vizard on Windows), published
as a plugin for Claude Code, claude.ai, Codex and ChatGPT. This repository is also the
marketplace those tools install from, so one `git tag` is a release.

| Where you work | Install once | Updates |
|---|---|---|
| Claude Code (terminal, VS Code, desktop app Code tab) | `claude plugin install sightlab-2x --marketplace worldviz/sightlab-ai-kit` | `claude plugin update sightlab-2x@worldviz`, or turn on auto-update for the `worldviz` marketplace in `/plugin` > Marketplaces |
| claude.ai chat and Cowork | Customize > Plugins > Add > Add marketplace, enter `worldviz/sightlab-ai-kit`, then add **SightLab 2.x AI Kit** | automatic when **Sync automatically** is on for the marketplace; the same plugin then also appears in your Claude Code as `sightlab-2x@synced` |
| Codex CLI and the ChatGPT desktop app | `codex plugin marketplace add worldviz/sightlab-ai-kit`, then install **SightLab VR Assistant** from `/plugins` (CLI) or the Plugins tab (app) and start a new session | `codex plugin marketplace upgrade worldviz`, then reinstall from `/plugins` |
| ChatGPT web | the **SightLab VR Assistant** plugin in ChatGPT's Plugins directory | automatic, after each version clears OpenAI's review |

The plugins are the same content built two ways: `dist/claude-plugin` (Claude's layout) and
`dist/openai-plugin` (OpenAI's `.codex-plugin` layout, the successor of SightLab VR Assistant
0.80.x). Both carry the test harness; on the web they answer and write scripts, on a PC with
SightLab 2 and Vizard 8 they also check and run them.

## What the agent does with it

1. **Sizes the request.** A question gets an answer with the file and line. A small edit
   gets the edit and the static check. A new study or a run-time bug gets the full workflow.
2. **Builds from a brief** (yours, a paper, or a Fit Check brief) in steps: skeleton, trials,
   responses, data, polish, with `check.py` after every edit.
3. **Runs the experiment itself** at the end of each build step: `autopilot.py` launches
   Vizard in desktop mode, drives the prompts, ratings and gaze targets like a participant,
   and writes `autopilot-report.json` with a verdict (`failed`, `smoke-passed`,
   `behaviour-verified`), every intervention it had to make, and the data files. It asks
   before launching, and never launches when a file named `NO_AUTOPILOT` is in the project.
4. **Writes `REVIEW.md`** at each stop: what changed, the verdict, what to check in the
   headset, the open questions.

`dist/starter-project/` is an optional empty project template (`CLAUDE.md`, `AGENTS.md`, a
brief template). Nothing of the kit is copied into projects; the plugin is the kit.

## Repository layout

| Path | What |
|---|---|
| `src/` | the single source: `SKILL.md`, `rules/`, `patterns/`, `guides/`, `api/` (generated from `sightlab_utils`), `examples/`, `register/`, `brief/`, `evals/`, `harness/`, `reference/` |
| `templates/` | per-wrapper files that are not content: manifests, commands, README, LICENSE, the project template |
| `tools/` | `build_kit.py` (builds `dist/` and the two marketplace manifests), `lint_kit.py`, generators for the API map, examples index and resources, `score_eval.py`, tests |
| `dist/` | the built wrappers, committed so the marketplaces resolve: `claude-plugin/`, `openai-plugin/` (+ `.zip` for the OpenAI directory), `starter-project/`, `chat-bundle.zip`, `BUILD.json` |
| `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json` | the marketplaces for Claude and Codex |
| `docs/` | changelog, release steps, directory submission notes, trial notes, eval scoreboards |

## Building

```
python3 -m venv .venv && .venv/bin/pip install pytest
.venv/bin/python -m pytest tools/tests -q
.venv/bin/python tools/lint_kit.py
.venv/bin/python tools/build_kit.py --version 2026.11.1
claude plugin validate ./dist/claude-plugin && claude plugin validate .
```

`docs/releases.md` has the release steps. Versions are dated (`2026.11.1`). The kit is
generated from `sightlab_utils` 2.8.21; `check.py --sightlab-utils <dir>` reads the installed
version instead, so a newer SightLab is checked against its own API.

## License

Copyright WorldViz LLC; see `dist/claude-plugin/LICENSE`. The bundled `sightlab.py`, `viz.py`
and `replay.py` are the source every SightLab licensee receives, included so the agent can
cite real lines; they are not for redistribution.
