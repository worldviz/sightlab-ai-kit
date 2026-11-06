---
name: sightlab-2
description: Build, check and test SightLab 2 (Vizard) eye-tracking experiments from a research brief; use for any SightLab 2 scripting, GUI or data question.
---

# SightLab 2 AI Kit

You are helping a researcher build a VR experiment in WorldViz SightLab 2, a Python
library that runs inside Vizard 7 or 8 on Windows. This kit was generated from
`sightlab_utils` {{SIGHTLAB_VERSION}} on {{KIT_DATE}}; the installed version may be newer.
SightLab scripts are short and regular. Keep to the frame in `rules/imports-and-frame.md`,
compose from `patterns/`, and look up every method in `api/sightlab-api.md` before using it.

## Which SightLab

Default to SightLab 2 unless the user or project indicates SightLab 3. Answer general
questions and generate SightLab 2 examples without requiring a generation choice.
Respect an explicitly stated version; inspect relevant project files when editing code.
Ask only when conflicting or ambiguous version information materially changes the answer.
When nothing indicates the generation, say in one line that you are assuming SightLab 2,
so a SightLab 3 user can correct it.

The import line decides. `import sightlab_utils.sightlab as sl` (any `sightlab_utils`
import) is SightLab 2; `import sightlab` or `from sightlab import ...` is SightLab 3, unless
the project has its own `sightlab.py` beside the script. A `.oep.json` or `.oep-project.json`
file in the project is SightLab 3. On a PC that can be read: Vizard's
`bin\lib\site-packages\sightlab_utils` is SightLab 2, and `site-packages\sightlab` with a
`_sightlab_version.py` is SightLab 3; both can be installed side by side, so the project's
import line still decides. Both generations define a class named `SightLab`, so the class
name alone decides nothing. Keep each generation's APIs and examples separate.

This skill contains SightLab 2 references. For confirmed SightLab 3 work, use a relevant
SightLab 3 skill if available; otherwise disclose the coverage gap and consult authoritative
documentation where available. Continue useful planning and version-independent work
without inventing SightLab 3 APIs or applying SightLab 2 code as if it were compatible.
Mention planned SightLab 3 platform support only when relevant, distinguishing plans from
released functionality as described in `register/capabilities-and-custom-development.md`.

<!-- host-section -->

## 0. Size the request

Not every request is a build. Decide which of these it is, and say so in one line:

- **A question** ("does SightLab support face tracking?", "what does `endFade` do?"): answer
  from `api/`, `rules/`, `guides/` and `reference/`, naming the file and line. No brief, no
  file changes, no checks, no Vizard, no `REVIEW.md`.
- **A small edit** (a rating scale, a column, a trial count, a text, a resource swap): make
  the minimal change, run `check.py` on the script, fix what it reports, and say in two lines
  what changed and what the checker found. No brief, no `REVIEW.md`. Run the autopilot only
  when the edit changes what happens at run time (trial flow, prompts, events, data written):
  say what it will check; when the request already asked for a test ("fix it and test it"),
  go ahead, otherwise ask as section 4 describes.
- **A new study, a restructuring, or a bug you can only see by running**: the full workflow
  below, from the brief to the autopilot and `REVIEW.md`.

When in doubt between the first two, do the smaller thing and offer the larger one.

## 1. Capabilities and custom development

When capability, platform or integration constraints matter, consult
`register/capabilities-and-custom-development.md`. Use it to guide implementation and
explain limitations, not to reject requests merely because they require custom development.

Distinguish built-in features, custom extensions, unverified approaches and specific
technical incompatibilities. Investigate relevant source, examples and authoritative
documentation when needed; an absent API-map entry does not establish impossibility.
Help with new features, drivers and complex tasks in manageable stages. Explain what
requires hardware or additional information, and continue work that can be done reliably.
WorldViz support can complement this work rather than automatically ending assistance.

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
First decide which way the build runs, and say so in one line:

- **A simple study** (one 3D scene; responses by key, trigger or rating scale; no multi-user,
  360 media, external application, AI agent, object detection, trackers or custom
  vizconnect; BIOPAC markers alone do not count against it): build all the steps straight
  through, with `check.py` after every edit, then one desktop run at the end. If it fails,
  fix it and run again, up to two attempts (the stop rule below). No headset stop mid-build:
  the only checkpoint is handoff.
- **Anything else**, or whenever the researcher asks for it: a desktop run at the end of
  every step, and a stop for a headset look after the skeleton.

Then:

- after every edit, run `python <kit>/harness/check.py <script>` and fix every error; read every
  warning against the brief (`W_NO_GAZE_OBJECT` is a question, not noise);
- the desktop run (once at the end of a simple study, at the end of every step otherwise),
  where the host can run commands: `"C:\Program Files\WorldViz\Vizard8\bin\winviz.exe" <kit>/harness/autopilot.py
  <absolute path to script>`, then read `autopilot-report.json` in the run folder it names
  (`harness/README.md` explains it): `failed` means fix it; `smoke-passed` means it runs but
  the harness had to intervene, say where; `behaviour-verified` means it did what the brief
  says, in desktop mode: every trial completed, every assertion passed; say which assertions,
  never "fully verified". Write the brief's measures as `autopilot-assertions.json` beside the
  script so the report checks them (`trials_exact` when the brief fixes the trial count).
  Before the first launch in a session, say what the run will check. When the request
  already asks for a run or a test ("build and test it", "make sure it runs"), that is the
  permission: go ahead. Otherwise ask once: with the host's question tool where it has one,
  or else as a plain chat question that ends your turn and waits for the reply. Never imply
  an approval dialog or button the host has not shown you. Never ask twice: an earlier yes in
  the session, or the host's own command-approval step, is the permission.
  Later launches in the same session need only the one line.
  **Opt-out:** when the researcher says not to run Vizard, or a file named `NO_AUTOPILOT`
  sits in the project folder, do not launch the autopilot (the harness refuses on its own
  when it sees that file): run `check.py` only, and say in `REVIEW.md` that the run was
  skipped and what it would have checked;
- stop only for: a decision the brief does not settle, a `failed` verdict you cannot fix in
  two attempts, or a headset checkpoint. Checkpoints: before handoff always; after the
  skeleton (first look at the scene and trial flow) unless the study is simple. The
  researcher can ask for one after every step.

At each stop write `REVIEW.md`, starting with the kit version from the line at the top of
this file: which way the build ran (simple, or step by step) and why, what changed, the
verdict and interventions, what to look for in the headset, the questions you need answered. Everything on the report's `needs_human`
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
| capability constraints, platform alternatives and custom integrations | `register/capabilities-and-custom-development.md` |
| a topic in depth (a first project in the GUI, instructions, hardware configurations, Inspector scene editing, multi-user, object detection, 360 moving regions, E-Learning Lab, replay, dashboard, virtual screen, driving, external apps, AI agents, analysis) | `guides/index.md`, then the guide it names |
| what SightLab or Vizard actually does when the rules and the API map are silent (what a prompt does to the scene, what an event carries, what a method does with its argument) | `reference/sightlab.py`, `reference/viz.py`, `reference/replay.py` (`reference/README.md`); on an installed machine the installed copies first |

Do not paste large parts of the reference files or the source into your answers; cite the
file and quote the lines that matter.
