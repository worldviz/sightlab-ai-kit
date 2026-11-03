# SightLab 2.x project template

An empty project folder for building a SightLab 2.x experiment with an AI coding agent
(Claude Code, Codex, or their VS Code extensions). The kit itself is a plugin you install
once; this folder only gives a new study a tidy place to live.

## Set-up

1. Install SightLab 2 (core, Resources and Projects) and Vizard 8 on a Windows PC.
2. Install the kit once, for every project on the PC:
   - Claude Code: `claude plugin install sightlab-2x --marketplace worldviz/sightlab-ai-kit`
   - Codex: `codex plugin marketplace add worldviz/sightlab-ai-kit`, then install the
     SightLab VR Assistant from `/plugins`.
   Both come from https://github.com/worldviz/sightlab-ai-kit, which also says how to update.
3. Copy this folder next to your other SightLab projects (for example
   `Documents\Sightlab2\MyStudy`) and open a terminal in it: `claude` or `codex`.
4. Tell the agent what the study is. It assembles `brief/MyStudy.md`, builds the script step
   by step, checks it with the kit's harness, runs it unattended in desktop mode (the
   autopilot, `autopilot.py`), and writes `REVIEW.md` when it needs you. For a question or a
   small edit it does only what that needs.

## What is here

| Path | Purpose |
|---|---|
| `CLAUDE.md`, `AGENTS.md` | the agent's entry points; both point at the installed plugin |
| `brief/` | the brief template and a filled example |
| `.vscode/settings.json` | sensible editor defaults for Vizard Python |
| `.gitignore` | keeps `data/` and `.autopilot/` out of version control |

Put an empty file named `NO_AUTOPILOT` here to keep Vizard from being launched for tests.

Kit version 2026.11.1, generated from sightlab_utils 2.8.21 on 2026-11-03.
