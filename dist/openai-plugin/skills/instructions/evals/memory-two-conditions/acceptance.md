# memory-two-conditions: acceptance

## Pass means
- `check.py`: 0 errors.
- `autopilot.py --assertions`: `behaviour-verified`; the harness confirms the Yes/No scale
  on each trial (`rating-confirmed`); all five assertions pass; the `Label` column carries
  the condition.
- Two trials of each condition; probe old/new balanced across the four.

## Feel pass (human)
- The study phase is visibly shorter in the short condition.
- The probe is shown alone, in the same place as the studied objects.
- The question wording matches the brief.

## Known hard parts
- Keeping eight objects registered while showing three, then one, per trial.
- Scoring `Correct` from the response and the probe type before `endTrial`.
- A balanced shuffle (not `random.choice` per trial).
