# Instructions for coding agents

This is a SightLab 2.x (Vizard, Windows) experiment project. The SightLab AI kit is an
installed plugin, not a folder in this project.

1. Use the SightLab VR Assistant plugin's skill for anything SightLab. If it is not installed:
   `codex plugin marketplace add worldviz/sightlab-ai-kit`, then install the SightLab VR
   Assistant from `/plugins` and start a new session. (Claude Code reads `CLAUDE.md` instead.)
2. The skill sizes the request first: a question gets an answer, a small edit gets the static
   check, a build gets the full workflow with the autopilot (`autopilot.py`, the experiment
   unattended in desktop mode) and `REVIEW.md`.
3. The checks run from the plugin's skill folder, never from a copy here, and take the
   script's absolute path; runs land in `.autopilot/` beside the script. An empty file named
   `NO_AUTOPILOT` in this folder stops the autopilot; the harness refuses on its own when it
   sees one.
4. The brief lives in `brief/`; experiment data goes to `data/`.

Kit version 2026.11.3, generated from sightlab_utils 2.8.21 on 2026-11-03.
