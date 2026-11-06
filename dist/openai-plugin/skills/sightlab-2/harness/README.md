# The harness: `check.py` and `autopilot.py`

Two tools that let an agent test its own SightLab 2 work before a person puts a headset
on. Both are standard-library Python written for Vizard's interpreter (Python 3.8 syntax).

| Tool | Needs Vizard? | What it answers |
|---|---|---|
| `check.py` | no | Is the script well-formed: the frame, real methods and arguments, resources that exist? |
| `autopilot.py` | yes | Does the script run, complete its trials, write its data, and do what the brief says, in desktop mode? |

## check.py

```
python check.py <experiment.py> [--sightlab-utils "<installed package dir>"] [--api sightlab-api.json]
                [--resources resources-list.txt] [--json]
```

Exit 1 on any error. Prefer `--sightlab-utils` on a customer machine so the checks use the
installed API; without flags it finds `sightlab-api.json` beside itself or in `../api/`. Both
tools run from the installed plugin's skill folder (`<kit>/harness/`), take the script's
absolute path, and write only beside the script (`autopilot.py`: under `.autopilot/` there, or
under `--run-root`). Findings and their meaning: `rules/common-mistakes.md`.
`W_NO_INSTANCE` means nothing was checked; silence is never a pass.

## autopilot.py

```
"C:\Program Files\WorldViz\Vizard8\bin\winviz.exe" autopilot.py <experiment.py>
      [--trials N] [--seconds-per-trial S=15] [--timeout T=120] [--record]
      [--config PATH.stlb] [--assertions PATH.json] [--run-root DIR]
```

What one run does, in order:

1. Copies the experiment's folder (never its parent, never `data/`) to
   `<experiment folder>/.autopilot/runs/<timestamp>/` and keeps the last five runs. Nothing
   outside that `.autopilot/` folder is written to, and the experiment's own `data/` is never
   touched. `.git`, `.env` files, virtualenvs, `node_modules` and project-local agent folders
   (`.claude`, `.codex`, `.agents`) are not copied either, nor are keys and credentials: a
   `keys/` folder (where SightLab's AI examples keep API keys), `*api_key*`, `*credentials*`,
   `*.pem`, `*.key`, `*.pfx`, `*.p12`. The report's `notes` names what was left out, and
   `needs_human` adds that anything needing those keys (an AI agent, a web API) was not
   tested. A folder with more than 5000 files or 500 MB is refused (move the experiment
   into its own folder).
2. Writes a provisional `autopilot-report.json` (`failed`, not launched) so a dead Vizard
   still leaves a record.
3. Detects demo mode (a SightLab 2 install without a licence key): trials capped at 4, run
   time at 280 s, `demo_mode: true` in the report.
4. Replaces the native dialogs (`vizinput.message/input/choose`) with no-ops that record a
   `popup-suppressed` intervention; nothing inside Vizard can click a native dialog.
5. Forces `hardwareconfig='Desktop'`, `vizconnectconfig=None`, `pid=False` (no participant
   dialog), and with `--record` SightLab's screen recording, by wrapping `SightLab.__init__`;
   records each as `forced-kwarg`. `--config` passes a saved GUI config (`configpath=`) for
   `gui=True` scripts.
6. Caps the trial count at `--trials`, whether set by `setTrialCount()` or by the
   constructor's `trialcount=` (`trial-cap`).
7. Runs the script in the same Vizard process, exactly as the researcher would.
8. Drives it like a person: when a text prompt or rating is up it sends the continue event
   (`prompt-continue`, `rating-confirmed`); before confirming a rating it moves the highlight
   (`rating-selected`): the first rating prompt keeps the first option, the second takes the
   middle one, the third the last, then the cycle repeats, so other values get stored too; when the script waits on a key it presses that
   key (`key-continue`); it turns the head toward each visible gaze object in turn (`look-at`)
   so gaze callbacks fire on the desktop configuration; a screenshot 2 s into each trial and one
   just before each trial ends.
9. If nothing moves for `--seconds-per-trial` (or for the trial's own `trialLength` plus
   5 s, when the script gives one), it sends a blind continue (`blind-continue`); if the
   trial is still open after twice that, it ends the trial itself (`forced-advance`; that end
   is never counted as a completed trial). At `--timeout` it stops (`timeout`).
   **Set `--seconds-per-trial` above the longest trial the script runs on a timer**; a blind
   continue that unblocked nothing is recorded with `effect: "none"` and does not cost the
   behaviour tier, but a forced advance always does.
10. On `EXPERIMENT_END` (or an exception, or the timeout) it collects the data files,
    evaluates the assertions, computes the verdict, and writes the report. Exit code 1 only
    for `failed`.

Before any of that, a file named `NO_AUTOPILOT` in the experiment's folder (the script's folder, or `--run-root`)
makes the harness refuse with exit code 3 and no run folder. The agent's instructions honour
the same file; this is the enforcement that does not depend on the agent remembering.

It never sends SightLab's own events (`EXPERIMENT_START`, `TRIAL_START`, `TRIAL_END`) and
never edits the script.

### The report

`autopilot-report.json` in the run folder:

| Field | Meaning |
|---|---|
| `verdict` | `failed`, `smoke-passed` or `behaviour-verified` (below) |
| `launched`, `demo_mode`, `sightlab_version`, `vizard`, `harness_version` | what ran where |
| `trials_expected`, `trials_completed` | `getTrialCount()` re-read at the end (`-1`, open-ended, becomes null); `endTrial` completions by the script, never the harness's own forced ones |
| `interventions` | every action the harness took, with time and kind |
| `data_folder`, `files`, `columns` | what SightLab wrote, with each CSV's header |
| `assertions` | each assertion with `pass` and a one-line `detail` |
| `gaze_objects`, `gaze_events_seen`, `marker_calls`, `biopac` | registered objects, dwell events seen, BIOPAC marker calls made; `biopac` is `off`, `connected`, or `stub` (no AcqKnowledge, so the harness stood in for the server and counted what would have been sent) |
| `exceptions`, `notes`, `screenshots`, `duration_s` | diagnostics |
| `needs_human` | always: real eye tracking on the headset, BIOPAC marker delivery, timing and interaction feel |

### Verdicts

| Verdict | Means | Say it as |
|---|---|---|
| `failed` | did not launch, raised an exception, or completed no trial | broken |
| `smoke-passed` | ran and wrote files, but the harness had to force its way through, fewer trials completed than expected, an assertion failed, or gaze objects were registered and no gaze event fired | "runs; behaviour not confirmed" |
| `behaviour-verified` | all trials completed with no counted intervention, every assertion passed, gaze events seen where objects were registered | "works as specified, in desktop mode" |

Interventions that count against the behaviour tier: `forced-advance`, `blind-continue`
(unless its `effect` is `none`), `popup-suppressed`, `timeout`. Interventions that do not:
`forced-kwarg`, `trial-cap`, `prompt-continue`, `rating-selected`, `rating-confirmed`, `key-continue`, `look-at`
(a person would have done the same at that point).

Whatever the verdict, the `needs_human` items are the researcher's or the hardware's to
check. A `behaviour-verified` run says that every trial completed without a counted
intervention and that the listed assertions passed, on a desktop. It does not say the study
matches the brief in every respect: only what the assertions checked is verified, so report
which assertions passed and what remains unverified, and never call a run "fully verified".

### Assertions

`autopilot-assertions.json` beside the experiment (or `--assertions`), a JSON list. The agent
writes these from the brief's measures; the evals ship their own.

| `type` | fields | passes when |
|---|---|---|
| `column_present` | `file`, `column` | every matching CSV has the column |
| `column_nonempty` | `file`, `column` | every data row has a non-empty value |
| `value_in` | `file`, `column`, `allowed` | every value is one of `allowed` |
| `min_rows` | `file`, `n` | every matching CSV has at least `n` data rows |
| `trials_completed` | `n` | at least `n` trials completed |
| `trials_exact` | `n` | exactly `n` trials completed; use it when the brief fixes the count, so extra trials fail too |
| `gaze_events_min` | `n` | at least `n` dwell events seen |
| `marker_calls_min` | `n` | at least `n` BIOPAC marker calls made |

`file` is one of `summary` (`*_experiment_summary.csv`), `trial_data`
(`trial_data/*_trial_data_*.csv`), `dwell` (`*_trial_timeline_dwell_*.csv`), `fixation`
(`*_trial_timeline_fixation_saccade_*.csv`). In the summary, `setExperimentSummaryData`
columns exist only on each trial's `ENTIRE_SCENE` row; the shorter per-object rows are
skipped by `column_nonempty` and `value_in`. Example:

```json
[
  {"name": "rating stored", "type": "column_nonempty", "file": "summary", "column": "Rating"},
  {"name": "condition labelled", "type": "value_in", "file": "summary", "column": "Condition", "allowed": ["near", "far"]},
  {"name": "all trials", "type": "trials_completed", "n": 6}
]
```

### Limits

- `gui=True` scripts stop at the GUI; give `--config` a saved `.stlb` or build with `gui=False`.
- On the desktop configuration the gaze ray runs straight ahead from the view, so `look-at`
  turns the Mouse-and-Keyboard head tracker toward each visible gaze object's bounding box in
  turn, as a person would move the mouse; that is how dwell events happen. An object more than
  30 m from the eye is treated as parked (hidden by moving it away) and skipped. Each `look-at`
  records the target point, the head's euler and SightLab's gaze point. Real eye tracking is
  a headset matter.
- BIOPAC: the harness counts marker calls, through a stand-in when AcqKnowledge is not running;
  it cannot see whether a marker arrived.
- Scripts that open their own native dialogs get them suppressed and the run is at best
  `smoke-passed`.
