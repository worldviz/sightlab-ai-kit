# SightLab 2.x AI Kit

A plugin for building, checking and testing WorldViz SightLab 2.x experiments, the Python
eye-tracking library that runs inside Vizard on Windows. It gives Claude the workflow a
SightLab engineer follows: size the request, assemble a brief, build the script in steps,
run the static checker after every edit, run the experiment unattended in desktop mode, and
hand over a review note with what the headset still has to confirm.

## What it contains

- `skills/sightlab-2x/SKILL.md`: the workflow, with the rules, patterns, guides and the API
  map generated from the SightLab source beside it.
- `skills/sightlab-2x/reference/`: `sightlab.py`, `viz.py` and `replay.py`, the SightLab and
  Vizard source that every SightLab licensee receives, so answers cite real lines.
- `skills/sightlab-2x/harness/`: `check.py` (static checks, any Python 3.8+) and
  `autopilot.py` (runs the experiment in Vizard's desktop mode and writes a report).
- Three commands: `/sightlab-2x:sightlab-new`, `/sightlab-2x:sightlab-check`,
  `/sightlab-2x:sightlab-review`.

## What it runs, sends and fetches

In Claude Code on a Windows PC with SightLab 2 and Vizard 8 installed, the skill may run
`python .../harness/check.py <script>` and
`"C:\Program Files\WorldViz\Vizard8\bin\winviz.exe" .../harness/autopilot.py <script>`, which
launches Vizard on that PC for about a minute and writes `.autopilot/` beside the script. It
says what the run will check and asks once per session before the first launch, and never
launches when a file named `NO_AUTOPILOT` is in the project folder. Where it cannot run
Windows programs (claude.ai chat, Cowork) it answers from its files and writes scripts for
you to run. The plugin sends nothing anywhere and fetches nothing from the network. In
claude.ai chat it answers from its files and writes scripts for you to run.

## Install

Claude Code: `claude plugin install sightlab-2x --marketplace worldviz/sightlab-ai-kit`.
claude.ai: Customize, Plugins, Add marketplace, `worldviz/sightlab-ai-kit`.
Source, releases and the Codex version: https://github.com/worldviz/sightlab-ai-kit

Kit version {{VERSION}}, generated from sightlab_utils {{SIGHTLAB_VERSION}} on {{KIT_DATE}}.
