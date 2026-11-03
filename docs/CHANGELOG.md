# SightLab 2.x AI Kit — changelog

Entries before 2026.11.1 cite `docs/audits/`, `docs/plans/` and `tools/fetch_sources.sh`,
which live in the team's internal repository, not here.

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
