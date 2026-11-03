# Evaluation tasks

Four studies, each a complete brief with assertions the harness can check. They measure the
kit: can an agent, given only the brief and this kit, produce a script that `check.py` passes
and `autopilot.py` marks `behaviour-verified`? Every eval fits a trial (demo-mode) install:
at most 4 trials, under 300 s.

| Folder | Study | Patterns exercised |
|---|---|---|
| `gaze-dwell-rating/` | look at two objects, rate each | gaze objects, ratings after trial, custom columns |
| `nback-biopac-markers/` | 1-back on objects with a key response and BIOPAC markers | timed stimuli, key responses, BIOPAC markers, custom columns |
| `stim-visual-search/` | find a target among distractors, trials from a STIM file | STIM files, gaze-contingent trial end, timing |
| `memory-two-conditions/` | study then recognise, short vs long exposure, randomised | randomised conditions, ratings as yes/no, custom columns |

Each folder has:

- `brief.md`: the twelve-section brief, exactly what the agent is given;
- `autopilot-assertions.json`: what the harness checks in the data files and the report;
- `acceptance.md`: what a pass means, what a person still checks, and the known hard parts.

## Running one by hand

1. Copy the starter project to a new folder; copy the eval's `brief.md` into its `brief/`.
2. Ask the agent to build the experiment from that brief (in Claude Code:
   `/sightlab:new` with the brief path, or the same words in any host).
3. `python harness/check.py <script>`: zero errors.
4. On a machine with Vizard and SightLab 2:
   `winviz.exe harness\autopilot.py <script> --assertions <eval>\autopilot-assertions.json`.
5. `python tools/score_eval.py <slug> --check <check.json> --autopilot <report> --agent "<agent and version>" --kit <kit version>`
   appends a row to `docs/evals/<month>.md`.
6. Do the feel pass in `acceptance.md`; note it on the scoreboard.

A pass is `behaviour-verified` with zero `check.py` errors and every assertion matching the
brief. Anything else is recorded as it is; the scoreboard is honest or it is useless.
