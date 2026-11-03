# The SightLab Dashboard

Sources: help.worldviz.com/sightlab sightlab-dashboard; the earlier assistant's `sightlab-dashboard.md`.

When to read: the researcher launches things from the Dashboard, wants the new study to
appear there, or asks for the built-in chart tools.

## What it is

A browsable, searchable launcher for projects, example scripts and tools, installed with
SightLab 2 and opened from the Start menu or `SightLab Dashboard.py` in the projects folder.
Cards are grouped in tabs (Experiment Templates, Additional Examples, Tools/Features,
Projects); search filters across all of them. A card's detail page shows its scripts and
actions.

## What a project needs to show up well

- Put it under the SightLab 2 projects folder (`Documents\Sightlab2\Projects\<Name>` by
  default) or next to the examples; the Dashboard scans those folders.
- A primary script (the experiment). Several scripts in one folder appear as "Run: name"
  alternates; right-click a script button to make it primary or hide it.
- A `SightLabVR_Replay.py` beside the experiment gives the card a Replay button (copy it
  from any example; it needs no changes for a standard data layout).
- A config file (`*_Config.py`) gets a Config button; an `Analysis/` folder with scripts gets
  an Analysis button.
- A thumbnail: right-click the card, Swap Thumbnail. Description, tags and category are
  editable in place and persist.

## Actions on a card

Run (in a new Vizard window or embedded), Replay, Edit Code (opens the Vizard IDE), Config,
Analysis, Copy Script Path. Multi-user examples show their server and client scripts.

## Built-in analysis

On a project's detail page, "Generate Barchart" reads an experiment summary CSV and draws
grouped bar charts of dwell time per object with no AI involved; "Generate Visualizations"
uses an LLM (a local model through Ollama, OpenAI, or Anthropic) to propose a set of charts
from a CSV. See `guides/analysis-and-visualization.md`.

## Gotchas

- The Assistant shortcut in the header opens the WorldViz AI assistant in the browser; it is
  not a Dashboard feature the agent can call.
- The Dashboard launches scripts with Vizard's own Python; a script that imports packages not
  installed in Vizard fails there even if it runs from an editor with another interpreter.
- Custom categories are free text; keep the researcher's naming.
