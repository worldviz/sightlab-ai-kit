---
name: sightlab-2
description: Build, check and test SightLab 2 (Vizard) eye-tracking experiments from a research brief; use for any SightLab 2 scripting, GUI or data question.
---

# SightLab 2 AI Kit

You are helping a researcher build a VR experiment in WorldViz SightLab 2, a Python
library that runs inside Vizard 7 or 8 on Windows. This kit was generated from
`sightlab_utils` 2.8.21 on 2026-11-05; the installed version may be newer.
SightLab scripts are short and regular. Keep to the frame in `rules/imports-and-frame.md`,
compose from `patterns/`, and look up every method in `api/sightlab-api.md` before using it.

## Which SightLab

SightLab 2 and SightLab 3 are installed side by side on many machines during the SightLab 3
transition, and they do not share an API. Confirm the generation before sizing the request, in
this order, and say which you found:

1. **The project's files.** A script that imports `sightlab_utils` is SightLab 2. A
   `.oep.json` or `.oep-project.json` file, or a script with `from sightlab import ...` or
   `import sightlab`, is SightLab 3. Both generations define a class named `SightLab`; the
   import line is the signal, never the class name.
2. **What is installed**, for a new project on a host that can read files: Vizard's
   `bin\lib\site-packages\sightlab_utils` is 2.x; `site-packages\sightlab` with a
   `_sightlab_version.py` is 3.
3. **What the researcher says or pastes.** "My SightLab 2 script", "a SightLab 3
   experiment", a pasted script (read its import line) or a pasted `.oep.json` decides. In a
   chat without files this is the only signal, so read the message for it first.
4. **Assume SightLab 2** when nothing above decides it, and say so in one line ("assuming
   SightLab 2; tell me if this is a SightLab 3 project"), because SightLab 2 is what is
   installed today; switch as soon as the researcher corrects you. An explicit statement
   counts as a decision; vocabulary alone ("trial", "gaze object") does not, because both
   generations use the same words.

This skill covers SightLab 2. For a SightLab 3 project, or a request to port a 2.x script to
SightLab 3, use the `sightlab-3` skill if it is installed beside this one; otherwise say that
SightLab 3 (OEP experiments, the Conductor, and Hybrid Python) is not covered by this kit yet,
and stop.

## On this host

This plugin provides instructions and reference material for SightLab 2, plus the harness
under `harness/` in this skill's folder (`<kit>` is the folder that holds this SKILL.md).
Confirm the generation, then size the request (section 0). Whether this host may run the checks depends on the
product you are using and its permissions:

<!-- openai-review-wording -->
- in ChatGPT (no local files): you cannot run the checks; say so, and for a build ask the
  researcher to run them on the SightLab PC with the installed kit (Claude Code:
  `claude plugin install sightlab --marketplace worldviz/sightlab-ai-kit`, then
  `/sightlab:check <script>`; Codex: `codex plugin marketplace add
  worldviz/sightlab-ai-kit`, install the SightLab VR Assistant, ask it to check the script)
  and paste the results back;
- in Codex with command access and the researcher's permission: run the checks as the skill
  describes, from this skill's folder: `python "<kit>/harness/check.py" <script>` after every
  edit, and `"C:\Program Files\WorldViz\Vizard8\bin\winviz.exe" "<kit>/harness/autopilot.py" "<absolute path to script>"`
  at the end of every build step (in PowerShell, Codex's shell on Windows, prefix the quoted
  executable with `&`). Say what a run will check; before the first launch in a session ask, as a
  plain chat question, unless the request already asked for a run or a test.

Generated scripts target the researcher's own licensed SightLab/Vizard installation.


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
  says, in desktop mode: every trial completed, every assertion passed; say which assertions,
  never "fully verified". Write the brief's measures as `autopilot-assertions.json` beside the
  script so the report checks them (`trials_exact` when the brief fixes the trial count).
  Before the first launch in a session, say what the run will check. When the request
  already asks for a run or a test ("build and test it", "make sure it runs"), that is the
  permission: go ahead. Otherwise ask, as a plain chat question that ends your turn and
  waits for the reply; there is no approval dialog or button you can summon, so never imply
  one. The host's own command-approval step, where it has one, is not a reason to ask twice.
  Later launches in the same session need only the one line.
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
