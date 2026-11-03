---
name: sightlab-2x
description: Build, check and test SightLab 2.x (Vizard) eye-tracking experiments from a research brief; use for any SightLab 2 scripting, GUI or data question.
---

# SightLab 2.x AI Kit

You are helping a researcher build a VR experiment in WorldViz SightLab 2.x, a Python
library that runs inside Vizard 7 or 8 on Windows. This kit was generated from
`sightlab_utils` 2.8.21 on 2026-11-03; the installed version may be newer.
SightLab scripts are short and regular. Keep to the frame in `rules/imports-and-frame.md`,
compose from `patterns/`, and look up every method in `api/sightlab-api.md` before using it.

## On this host

You are running as the `sightlab-2x` Claude Code plugin with file and command access. The
kit's files live under the plugin root, not in the researcher's project: `<kit>` is
`${CLAUDE_PLUGIN_ROOT}/skills/sightlab-2x`. Size the request first (section 0); for a build
the checks are expected, not optional:

- `python "${CLAUDE_PLUGIN_ROOT}/skills/sightlab-2x/harness/check.py" <script> --sightlab-utils "<installed package dir>"`
  after every edit (the package dir is in "Find the install"; any Python 3.8+ runs the
  checker, Vizard is not needed for it);
- `"C:\Program Files\WorldViz\Vizard8\bin\winviz.exe" "${CLAUDE_PLUGIN_ROOT}/skills/sightlab-2x/harness/autopilot.py" "<absolute path to script>"`
  at the end of every build step; read `autopilot-report.json` in the run folder it names;
- `/sightlab-2x:sightlab-new`, `/sightlab-2x:sightlab-check` and `/sightlab-2x:sightlab-review`
  are shortcuts for the brief, the checks and the review note.

If you cannot run Windows programs here (claude.ai chat, Cowork, any non-Windows sandbox),
this is a chat: answer questions from the files, write the brief and the script, list the
checks you could not run, and give the researcher the two commands above to run on the
SightLab PC. Never say a check ran when it did not.


## 0. Size the request

Not every request is a build. Decide which of these it is, and say so in one line:

- **A question** ("does SightLab support face tracking?", "what does `endFade` do?"): answer
  from `api/`, `rules/`, `guides/` and `reference/`, naming the file and line. No brief, no
  file changes, no checks, no Vizard, no `REVIEW.md`.
- **A small edit** (a rating scale, a column, a trial count, a text, a resource swap): make
  the minimal change, run `check.py` on the script, fix what it reports, and say in two lines
  what changed and what the checker found. No brief, no `REVIEW.md`. Run the autopilot only
  when the edit changes what happens at run time (trial flow, prompts, events, data written)
  and the researcher agrees: say what it would check, then ask.
- **A new study, a restructuring, or a bug you can only see by running**: the full workflow
  below, from the brief to the autopilot and `REVIEW.md`.

When in doubt between the first two, do the smaller thing and offer the larger one.

## 1. Scope guard, before any edit or build

Read `register/cannot.md` and classify the request:

- **not possible in SightLab 2** → say so plainly, name the nearest thing that is, and stop;
- **possible, but custom work** (avatar animation, generated worlds, bespoke hardware) → say
  what it will take before starting, and suggest WorldViz support where the register says so;
- **needs hardware** (an eye-tracking headset, BIOPAC, trackers) → build it, and say which
  parts cannot be tested without the device.

Never promise something because it sounds plausible. If the API map has no method for it,
it is not a one-liner.

## 2. Find the install

Prefer the researcher's installed SightLab over anything bundled here, where this host can
read files:

- the package: `C:\Program Files\WorldViz\Vizard8\bin\lib\site-packages\sightlab_utils` (or
  `Vizard7`); its `__init__.py` has `__version__`. The registry key
  `HKLM\SOFTWARE\WorldViz\Sightlab2` has a `Path` value written by the SightLab 2 installer
  (seen on a 2.9.3 install: `C:\Program Files\WorldViz\Sightlab2`) that points at the
  resources, not the package;
- the projects folder with `ExampleScripts/`: `Documents\Sightlab2`;
- resources: `C:\Program Files\WorldViz\Sightlab2\sightlab_resources`;
- Vizard: `C:\Program Files\WorldViz\Vizard8\bin\winviz.exe`.

For an edit or a build, note the installed version in your first message (a question needs
it only when the answer depends on the version). When you can read the install, run
`python <kit>/harness/check.py <script> --sightlab-utils <package dir>` so the checks use the
real API.

`<kit>` is the folder this `SKILL.md` lives in (the plugin's skill folder; the host section
above gives its exact form). The harness runs from there, never from a copy in the project,
and takes the script's absolute path; everything it writes goes to `.autopilot/` beside the
script.

## 3. The brief

The researcher does not fill in a form. They describe the study, paste a paper, or bring a
brief from the hosted Fit Check. You assemble `brief/TEMPLATE.md` from that:

- ask only about ambiguities that change what gets built: how a response is given, what one
  trial is, how many, which hardware is in the room;
- fill everything else with sensible defaults marked `(assumed)` so they can be corrected;
- a Fit Check brief arrives with eleven of twelve sections; ask one targeted hardware question.

Start the skeleton as soon as design, procedure, responses, trials and hardware are settled.
`brief/EXAMPLE-gaze-dwell.md` shows a finished one.

## 4. The build

Work through these steps on your own: **skeleton → trials → responses → data → polish.**

- after every edit, run `python <kit>/harness/check.py <script>` and fix every error; read every
  warning against the brief (`W_NO_GAZE_OBJECT` is a question, not noise);
- at the end of every build step, where the host can run commands, run the experiment in
  desktop mode: `"C:\Program Files\WorldViz\Vizard8\bin\winviz.exe" <kit>/harness/autopilot.py
  <absolute path to script>`, then read `autopilot-report.json` in the run folder it names
  (`harness/README.md` explains it): `failed` means fix it; `smoke-passed` means it runs but
  the harness had to intervene, say where; `behaviour-verified` means it did what the brief
  says, in desktop mode. Write the brief's measures as `autopilot-assertions.json` beside the
  script so the report checks them. Say what the run will check, and ask once, before the
  first launch in a session; later launches in the same session need only the one line.
  **Opt-out:** when the researcher says not to run Vizard, or a file named `NO_AUTOPILOT`
  sits in the project folder, do not launch the autopilot (the harness refuses on its own
  when it sees that file): run `check.py` only, and say in `REVIEW.md` that the run was
  skipped and what it would have checked;
- stop only for: a decision the brief does not settle, a `failed` verdict you cannot fix in
  two attempts, or a headset checkpoint. Default checkpoints: after the skeleton (first look
  at the scene and trial flow) and before handoff. The researcher can ask for one after
  every step.

At each stop write `REVIEW.md`, starting with the kit version from the line at the top of
this file: what changed, the verdict and interventions, what to look for in the headset, the
questions you need answered. Everything on the report's `needs_human`
list (real eye tracking, BIOPAC delivery, timing feel) is always theirs to check.

## 5. Rules

Read these before writing code; they are short and each one has cost someone a day:

- `rules/imports-and-frame.md` — the two imports, the frame, the three closing lines, waits
- `rules/gaze-objects-and-data.md` — `addSceneObject(..., gaze=True)`, built-in gaze events, what is written
- `rules/gui-vs-code.md` — GUI, code or both; what each side owns
- `rules/environments-and-resources.md` — shipped environments, `vizfx.addChild`, `headlight`
- `rules/trials-and-instructions.md` — `startTrial`/`endTrial` arguments, prompts, timing
- `rules/common-mistakes.md` — the checker's codes and the mistakes behind them

Write BIOPAC in capitals.

## 6. When to read what

| Need | Read |
|---|---|
| the exact name, arguments and defaults of a method | `api/sightlab-api.md` (generated from the source; trust it over memory) |
| how to do a kind of study (gaze-contingent, ratings, STIM files, conditions, BIOPAC markers) | `patterns/<name>.md`, then copy its complete script |
| a shipped example to learn from or copy | `examples/index.md`, then the script in the researcher's `ExampleScripts/` or `examples/curated/` here |
| whether an environment, object or media file ships, and its exact name | `api/resources.md` (never guess a file name) |
| whether something can be done at all | `register/cannot.md` |
| a topic in depth (instructions, replay, dashboard, virtual screen, driving, external apps, AI agents, analysis) | `guides/index.md`, then the guide it names |
| what SightLab or Vizard actually does when the rules and the API map are silent (what a prompt does to the scene, what an event carries, what a method does with its argument) | `reference/sightlab.py`, `reference/viz.py`, `reference/replay.py` (`reference/README.md`); on an installed machine the installed copies first |

Do not paste large parts of the reference files or the source into your answers; cite the
file and quote the lines that matter.
