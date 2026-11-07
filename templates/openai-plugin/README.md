# SightLab AI Kit

The SightLab VR Assistant: a plugin that carries one skill per SightLab generation, `sightlab-2` today, for
building, checking and testing WorldViz SightLab 2 experiments, the Python
eye-tracking library that runs inside Vizard on Windows. It gives the assistant the workflow a
SightLab engineer follows: size the request, assemble a brief, build the script in steps,
run the static checker after every edit, run the experiment unattended in desktop mode, and
hand over a review note with what the headset still has to confirm.

## What it contains

- `skills/sightlab-2/SKILL.md`: the workflow, with the rules, patterns, guides and the API
  map generated from the SightLab source beside it.
- `skills/sightlab-2/reference/`: `sightlab.py`, `viz.py` and `replay.py`, the SightLab and
  Vizard source that every SightLab licensee receives, so answers cite real lines.
- `skills/sightlab-2/harness/`: `check.py` (static checks, any Python 3.8+) and
  `autopilot.py` (runs the experiment in Vizard's desktop mode and writes a report).

## What it runs, sends and fetches

In Codex on a PC with SightLab 2 and Vizard 8 installed, the skill may run
`python .../harness/check.py <script>` and
`"C:\Program Files\WorldViz\Vizard8\bin\winviz.exe" .../harness/autopilot.py <script>`, which
launches Vizard on that PC for about a minute and writes `.autopilot/` beside the script. It
says what the run will check and, unless you asked for the run, asks once per session before
the first launch; it never launches when a file named `NO_AUTOPILOT` is in the project folder.
A run copies the experiment folder (never its `data/`, `.git`, `.env` files, virtualenvs, API
keys or credential files) to
`.autopilot/runs/<timestamp>/`, writes its report and screenshots there, and keeps the last five. The plugin itself sends nothing anywhere and fetches nothing from the network; the
experiment scripts it runs and the installed SightLab and Vizard applications have their
own network behaviour, which this notice does not describe. In
ChatGPT it answers from its files and writes scripts for you to run.

## Install

ChatGPT and Codex: search the Plugins page for SightLab VR Assistant and install it.
Source, releases and the Claude version: https://github.com/worldviz/sightlab-ai-kit

Kit version {{VERSION}}, generated from sightlab_utils {{SIGHTLAB_VERSION}} on {{KIT_DATE}}.
