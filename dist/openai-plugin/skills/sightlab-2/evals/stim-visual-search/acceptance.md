# stim-visual-search: acceptance

## Pass means
- `check.py`: 0 errors.
- `autopilot.py --assertions`: `behaviour-verified`; the harness's `look-at` on the target
  ends each trial before the 20 s limit (no `forced-advance`); all five assertions pass.
- `stim/search.csv` exists with four rows and the script reads the trial count from it.

## Feel pass (human)
- Editing a row in the CSV changes that trial without any code change.
- The target turns green when looked at for a second, and the trial then ends.
- Distractors never hide the target.

## Known hard parts
- Ending a trial from a gaze event: set a flag or send an event the generator waits on,
  rather than calling `endTrial` inside the callback.
- A per-trial timeout racing the dwell event (`viztask.waitAny`).
- Dwell threshold: `setDwellTimeThreshold(1)` before the trials.
