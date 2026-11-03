# `nback-biopac-markers`: acceptance

## Pass means
- `check.py`: 0 errors.
- `autopilot.py --assertions`: `behaviour-verified`; both blocks complete on their timers
  with no `blind-continue`; marker calls ≥ 4 (on the desktop with no AcqKnowledge the
  connection may fail at start-up: then the run is `failed` and that is the honest result on
  a machine without BIOPAC; score it on a machine with AcqKnowledge in NDT mode).
- Summary columns `Hits`, `False alarms`, `Misses`, `RT hits (s)` present for both blocks.

## Feel pass (human)
- Items are clearly distinguishable at 1.5 s; the blank between items is visible.
- The marker list in AcqKnowledge shows one event per item with the item name and a
  repeat flag, plus trial start/end.
- A deliberate press on a repeat registers as a hit, on a non-repeat as a false alarm.

## Harness note
Run the autopilot with `--seconds-per-trial 30`: each block is a 16 s timer with no trial
progress events, and the default 15 s stall limit would press the space bar mid-block,
which the script would count as a response.

## Known hard parts
- Responses arrive in a callback while the generator is sleeping: the script needs a small
  state object for "current item" and "responded".
- Sequence generation with exactly three repeats and no two repeats in a row.
- `biopac=True` with no AcqKnowledge present: the script should say so plainly in REVIEW.md.
