# SightLab AI Kit — changelog

Entries before 2026.11.1 cite `docs/audits/`, `docs/plans/` and `tools/fetch_sources.sh`,
which live in the team's internal repository, not here.

## 2026.11.10 (2026-11-06)

- Host sections decide what to run from the session's tools and environment, not the
  product's name. The static check needs the script, the skill folder and Python 3.8+; the
  Vizard test also needs Windows with SightLab 2 and Vizard 8, and the researcher's
  permission. Anything that cannot run is handed to the researcher with the command, and the
  assistant says which checks were not performed. The OpenAI section no longer says
  "in ChatGPT (no local files): you cannot run the checks"; the Claude section no longer
  calls every non-Windows session "a chat", since `check.py` needs only Python. The chat
  bundle says why it cannot run the checks: it carries no harness.

## 2026.11.9 (2026-11-05)

- "Which SightLab" decides by the import line again: `sightlab_utils` is SightLab 2;
  `import sightlab` or `from sightlab import ...` is SightLab 3 (unless the project has its
  own `sightlab.py`), as is a `.oep.json` or `.oep-project.json` file; on the PC,
  `site-packages\sightlab` with `_sightlab_version.py` is SightLab 3. When nothing decides,
  it still assumes SightLab 2 and says so.

## 2026.11.8 (2026-11-05)

SightLab 2.9.3, the capabilities register, and the rest of Sado's review.

- Capabilities register: `register/cannot.md` is replaced by
  `register/capabilities-and-custom-development.md`, which guides custom work instead of
  gating it; SKILL section 1 and `/sightlab:new` point to it. "Which SightLab" defaults to
  SightLab 2, says so in one line, and no longer treats a bare `import sightlab` as proof of
  SightLab 3.
- SightLab 2.9.3: API map regenerated from the installed `sightlab_utils` 2.9.3 (no public API
  change since 2.8.21); `reference/sightlab.py` and `replay.py` from 2.9.3; examples index
  from the current `ExampleScripts` (four entries gained scripts). The resource list was
  checked against the shipped `sightlab_resources` (unchanged) and now says more can come from
  the WorldViz Asset Browser.
- New guides: `hardware.md` (exact configuration names, which configurations write pupil
  data, controller events, custom vizconnect files), `inspector.md`, `object-detection.md`,
  `multi-user.md`; the Group Heatmap Replay section of `replay.md` follows the current example.
- Corrections found against the 2.9.3 source: `addRegionOfInterest()` records nothing (region
  nodes are registered with `addSceneObject(..., gaze=True)`); `setEnvironment(trial=)` is
  ignored for 3D models; time to first fixation is `-1` for objects never looked at; the
  start-point node is `SIGHTLAB_START_POINT`; `addCustomTrialDataColumn` does not exist.
- Rules: the projects folder and "how do I create my first experiment?" (BlankProject,
  SampleProject; GUI only, code, or both; code stays the agent's default and computer use can
  drive the GUI); per-script `settings.py` overrides; adding SightLab to an existing script;
  per-trial logging switches, no underscores in participant IDs, `vizinput` on the desktop
  only; ground following and physics; 360 `mediaFormat` values.
- Build workflow: a simple study (one 3D scene, standard responses, no multi-user, 360,
  external application, AI agent, detection, trackers or custom vizconnect) is built straight
  through with one desktop run at the end and no mid-build stop; anything else keeps a run
  per step and the skeleton checkpoint. A small edit honours a request that already asked for
  a test; asking uses the host's question tool where there is one, and never twice.
- Autopilot: run copies also skip keys and credentials (`keys/`, `*api_key*`,
  `*credentials*`, `*.pem`, `*.key`, `*.pfx`, `*.p12`); the report names what it left out and
  adds what needed it to `needs_human`. Harness version 2026.11.8.
- Listing description and LICENSE: the kit sends nothing to WorldViz and runs no service of
  its own; experiments it runs, and the installed SightLab and Vizard, may communicate with
  the devices and services they are set up to use.
- The GitHub distribution is marked as a preview in the READMEs and the install guide.
- Tests: the first-experiment answer, register references, the key exclusions; the
  scoreboard test reads UTF-8 so it passes on Windows.

## 2026.11.7 (2026-11-05)

Claude manifest only: `displayName` "SightLab AI Kit" and the repository, documentation,
support, privacy and terms links the Claude directory shows on a listing. No content change.

## 2026.11.6 (2026-11-05)

Sado's pre-submission review, the items that gate the OpenAI directory update:

- LICENSE now defers to the approved SightLab VR Assistant Terms (WorldViz Inc.; open to
  prospective customers; warranties and liability as the Terms state them) with a short
  amendment covering `check.py` and `autopilot.py`; the reference source keeps its
  no-redistribution request, separately from the adaptable examples.
- OpenAI subtitle is "Build SightLab 2 experiments" (28 characters; the directory allows 30);
  the long description and the plugin READMEs now describe the optional local checks, the
  Vizard runs, what a run writes and keeps, and qualify the "sends nothing" statement.
- Autopilot: run copies skip `.git`, `.env` files, virtualenvs, `node_modules` and
  project-local agent folders; new `trials_exact` assertion for briefs that fix the trial
  count; README says what `behaviour-verified` does and does not claim.
- Skill: when nothing decides the generation it assumes SightLab 2 and says so, instead of
  asking. Before the first Vizard launch it still says what the run will check, but a request
  that already asks for a run or a test counts as the permission; otherwise it asks as a
  plain chat question and never implies an approval dialog.
- CI: GitHub Actions runs the tests and the lint on every push and pull request.

## 2026.11.5 (2026-11-05)

The Codex skill card now reads **SightLab 2 AI Kit / Build, check and test SightLab 2
experiments** (was "SightLab VR Assistant / Build SightLab VR experiments", the same text as
the 0.80.x listing in OpenAI's directory), so a Plugins page that lists both copies tells
them apart. The plugin's own name stays SightLab VR Assistant. No content or harness change.
New: `docs/install.md`, the customer install guide with screenshots.

## 2026.11.4 (2026-11-03)

Naming cleaned up before anyone installs (Andy): the skill is `sightlab-2` (was `sightlab-2x`;
the product calls itself SightLab 2, and the future skill is `sightlab-3`), prose says
"SightLab 2" rather than "2.x", and the OpenAI listing's manifest and icon live in
`templates/openai-plugin/` instead of a folder named after the 0.80.6 build. No content or
harness change. If you installed 2026.11.3, `claude plugin update sightlab@worldviz` is enough.

## 2026.11.3 (2026-11-03)

The plugin is now `sightlab` and carries one skill per SightLab generation (`sightlab-2x`
today), so a SightLab 3 skill can be added without renaming what users installed. If you
installed 2026.11.2: `claude plugin uninstall sightlab-2x@worldviz`, then
`claude plugin install sightlab --marketplace worldviz/sightlab-ai-kit`; in claude.ai remove
**SightLab 2.x AI Kit** and add **SightLab** from the same marketplace; Codex users run
`codex plugin marketplace upgrade worldviz` and reinstall from `/plugins`.

- Commands are `/sightlab:new`, `/sightlab:check`, `/sightlab:review`.
- The skill opens with "Which SightLab": the import line, the project files and what the
  researcher says or pastes decide the generation; it asks once when they do not; SightLab 3
  is named as not covered yet.
- The Codex plugin's skill folder and skill name are `sightlab-2x` (were the 0.80.x
  `instructions`).
- `src/` is one folder per skill; the build loops over them.
- Harness unchanged since 2026.11.2 (VM rerun 2026-11-03: all seven runs met).

## 2026.11.2 (2026-11-03)

Review fixes on 2026.11.1 (never installed by anyone): the agent asks once per session before
the first Vizard launch; claude.ai and Cowork get chat rules; far gaze objects are still looked
at when nothing nearer is visible; the Claude plugin ships its listing icon; migration note for
2026.11.0 starter projects; Codex PowerShell wording; the OpenAI plugin's Codex UI metadata.

## 2026.11.1 (2026-11-03)

Distribution moved to GitHub: `worldviz/sightlab-ai-kit` is a marketplace for Claude Code,
claude.ai and Codex; `dist/` is committed; releases are tags with `openai-plugin.zip` (the
OpenAI directory upload) and `chat-bundle.zip` attached. Internal docs moved to a private repo.

- Skill §0 sizes the request: question / small edit / build; the autopilot runs for builds and
  run-time changes only, after saying what it checks (Sado: 97 s vs 49 s on a two-line edit).
- Harness paths are plugin-relative and scripts are given by absolute path (Sado: relative
  launch paths failed). The OpenAI plugin now carries the harness for Codex users.
- `autopilot.py` refuses on its own when `NO_AUTOPILOT` is present (exit 3).
- Look-at skips objects farther than 30 m (Sado: a parked target 50 m below the scene).
- Rating prompts select first, middle and last options in turn (Sado: always 1).
- `patterns/rating-after-trial.md`: `endFade` wording corrected against `hideRatings`.
- Starter project is a template only (no copy of the kit); plugins carry README and LICENSE.

## 2026.11.0 (2026-11-01, Assembla r14302)

Generated from: `sightlab_utils 2.8.21`, Assembla trunk r14264, fetched 2026-10-31T05:23Z
(`tools/fetch_sources.sh` → `~/development/sightlab-2x-sources/`).

- Design document and Phase 0 plan written (2026-10-30).
- 2026-10-31: `src/reference/` (`sightlab.py` 2.8.21, `replay.py` 2.8.21, `viz.py` from Vizard 8.3.1) ships in
  every wrapper, chat bundle included; the build's source-exclusion guard is gone (decision 2 re-ruled,
  see the design doc). Measured sizes for every shipped model in `api/resources.md`; four evals pass on
  the VM; the harness turns the desktop head tracker and stands in for AcqKnowledge.
- Task 1: sources fetched read-only; 96 example folders with scripts, 678 text files, no media.
- Task 10 (run early): autopilot spike on the VM is a GO — see `docs/audits/2026-10-30-autopilot-spike.md`.
  The VM runs SightLab 2.9.3, whose API is identical to trunk 2.8.21.
- Task 2: `tools/gen_api_map.py` → `src/api/` (178 public methods, 69 undocumented).
- Task 3: `tools/gen_examples_index.py` → `src/examples/index.{md,json}` (94 folders).
- Task 4: `src/harness/check.py` static checker, 13 fixtures; audit over 560 shipped scripts in
  `docs/audits/2026-10-30-check-over-examples.md`.
- Task 5: `src/SKILL.md`, six `src/rules/*.md`, `tools/lint_kit.py`.
- Task 6: `src/brief/TEMPLATE.md`, `src/brief/EXAMPLE-gaze-dwell.md`, `src/register/cannot.md` (draft for Alex and Sado).
- Task 7: five `src/patterns/*.md`, each with a complete script that passes the checker.
- Task 8: `tools/build_kit.py` → `dist/` (Claude plugin, OpenAI plugin, starter project, chat bundle);
  `claude plugin validate` passes on the Claude plugin.
- Task 9: 12 curated shipped examples in `src/examples/curated/`; a `SightLab-VR-Assistant-0.80.7/` build
  (0.80.6 minus the source files) was prepared and later deleted: the source ships (2026-10-31).
- Phase 0 final review (fresh reviewer): 1 Critical + 6 Important fixed; ledger in
  `docs/audits/2026-10-31-phase0-ledger.md`.
- E2E follow-ups plan: `api/resources.{json,md}` (every shipped resource name, generated;
  `check.py` reads it by default, so unknown or wrongly-cased file names are flagged everywhere;
  the lint checks every file name the kit's Markdown mentions); `W_KEY_REPLACES_TRIGGER`;
  pattern `show-hide-objects-per-trial`.
- Evals and guides plan: four evaluation tasks in `src/evals/` (briefs, harness assertions,
  acceptance notes); `tools/score_eval.py` + `docs/evals/`; nine agent guides in `src/guides/`
  (the old plugin's Markdown references are now covered, so the OpenAI wrapper no longer regresses
  the listing); first end-to-end run of the kit by Claude Code (`docs/audits/2026-10-31-e2e-first-run.md`).
  Fix pass after review: `textContinueKey` semantics corrected in the rules and guides (it replaces the
  trigger wait); `autopilot_core.decide()` makes the driver's choices testable and presses a pending key
  during a prompt; the scorer reads the brief's trial count.
- Autopilot plan: `src/harness/autopilot_core.py` (pure, 22 tests) and `src/harness/autopilot.py`
  (Vizard glue) replace the spike; `harness/README.md` documents the report, verdicts, interventions
  and assertions; VM integration runs recorded in `docs/audits/2026-10-31-autopilot-integration.md`.
