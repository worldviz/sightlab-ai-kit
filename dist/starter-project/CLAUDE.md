# SightLab 2 experiment project

This folder holds one SightLab 2 (Vizard) experiment. The SightLab AI kit is the installed
`sightlab` plugin (its `sightlab-2` skill); nothing of it is copied here.

- Use the `sightlab-2` skill for anything SightLab. It sizes the request first (a question,
  a small edit, or a build) and names the checks each one needs. If the skill is missing,
  install it once: `claude plugin install sightlab --marketplace worldviz/sightlab-ai-kit`.
- The brief lives in `brief/` (start from `TEMPLATE.md`; `EXAMPLE-gaze-dwell.md` is a finished one).
- The checks run from the plugin's folder, never from here: `check.py` after every edit; the
  autopilot (`autopilot.py`, the experiment unattended in desktop mode) for builds and for
  edits that change what happens at run time, after saying what it will check. An empty file
  named `NO_AUTOPILOT` in this folder stops it; the harness refuses on its own when it sees one.
- Experiment data goes to `data/` and test runs to `.autopilot/`; both are git-ignored.
- Kit version 2026.11.8, generated from sightlab_utils 2.9.3 on 2026-11-05.
