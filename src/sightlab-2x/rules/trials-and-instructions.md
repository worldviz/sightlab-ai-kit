# Trials, prompts and instructions

## Starting and ending a trial

`yield sightlab.startTrial(...)` and `yield sightlab.endTrial(...)` bracket every trial. The
useful arguments:

| Argument | On | What it does |
|---|---|---|
| `startTrialText='...'` | `startTrial` | shows the text and waits for the continue event before the trial begins |
| `startExperimentText='...'` | `startTrial` | same, but only before the first trial |
| `endTrialText='...'` / `endExperimentText='...'` | `endTrial` | text after the trial / after the last trial |
| `trialLength=10` | `startTrial` | ends the trial automatically after 10 s |
| `trialLabel='practice'` | `startTrial` | the label written to the data's `Label` column (also `setConditionName`) |
| `condition=[...]` | both | the GUI's start/end condition event (timer, key, event) in the GUI's list form; **not** a condition label |
| `startRatings=[...]` / `endRatings=[...]` | `startTrial` / `endTrial` | rating scales shown before / after the trial (`patterns/rating-after-trial.md`) |
| `textContinueEvent='triggerPress'` | both | the event that dismisses the text; default is the controller trigger, which the Desktop configuration maps to the left mouse button |
| `textContinueKey=' '` | both | a keyboard key that **replaces** the event wait: with it set, the trigger no longer dismisses the text; desktop-only studies only |

- When a prompt text is given, SightLab waits for the continue event itself. Do not add a
  second wait before `startTrial` for the same purpose.
- Never pair `textContinueKey` with text that tells the participant to press the trigger:
  the key replaces the trigger, so a headset participant has no way on
  (`harness/check.py` reports `W_KEY_REPLACES_TRIGGER`).
- Without a prompt text, nothing waits: put your own `yield viztask.waitKeyDown(' ')` or
  `yield viztask.waitTime(...)` where the trial should start and end.
- `trialLength` is simplest for fixed-duration trials; otherwise the script decides when to
  call `endTrial` (a key, a timer, a gaze event, a proximity sensor).

## Instructions and text

- Trial-level text: the arguments above.
- Free-standing instructions at any point: `yield sightlab.showInstructions('text')`,
  optionally with `image=` and `pauseTimer=True`.
- The HUD start line ("Press SPACEBAR to Start") is `sightlab.setStartText('...')`.
- See `examples/Instructions` for every variant, including images.

## Timing and sequencing

- `sightlab.hud.getCurrentTime()` is the current trial time in seconds.
- Fixed delays: `yield viztask.waitTime(seconds)`. Keys: `yield viztask.waitKeyDown('key')`.
  Several possibilities at once: `yield viztask.waitAny([...])`.
- Proximity-triggered events use Vizard's `vizproximity` (a `Manager`, `Sensor`s and a
  `Target`); `examples/Proximity Sensors` is the model.
- Repetitions of the whole trial set: `sl.SightLab(repetitions=2)`; data files then carry a
  `block_N` part in their names.
