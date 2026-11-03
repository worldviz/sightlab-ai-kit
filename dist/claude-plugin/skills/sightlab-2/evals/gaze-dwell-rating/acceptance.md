# gaze-dwell-rating: acceptance

## Pass means
- `check.py`: 0 errors; the only acceptable warning is none.
- `autopilot.py --assertions`: `behaviour-verified`; all five assertions pass; interventions
  limited to `forced-kwarg`, `prompt-continue`, `rating-confirmed`, `look-at`.
- The summary file has one row per registered object per trial (eight objects × four
  trials) plus the four custom columns.

## Feel pass (human)
- In the headset, both objects of a pair are at a comfortable distance and height and do
  not overlap.
- The two rating prompts name which object they ask about (left / right).
- Pair order differs between two sessions.

## Known hard parts
- Hiding the six unused objects each trial without unregistering them.
- Two `showRatings` calls per trial, each stored under its own column before `endTrial`.
- Choosing shipped object files that exist (`examples/index.md` and the install's
  `sightlab_resources/objects/`).
