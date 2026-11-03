# Randomized and counterbalanced conditions

## Intent

Each trial belongs to a condition; the order is shuffled once per participant, optionally
balanced so every condition appears equally often; the condition is written into the data
so analysis can group by it.

## Script

```python complete
import sightlab_utils.sightlab as sl
from sightlab_utils.settings import *
import vizshape
import random

sightlab = sl.SightLab(gui=False, headlight=True)
env = vizfx.addChild('sightlab_resources/environments/whiteroom.osgb')
sightlab.setEnvironment(env)

sphere = vizshape.addSphere(radius=0.15)
sphere.setPosition([0, 1.5, 2])
sightlab.addSceneObject('sphere', sphere, gaze=True)

CONDITIONS = {'near': 1.5, 'far': 4.0}
REPEATS = 3
# One shuffled list per session: each condition REPEATS times, balanced by construction.
order = [name for name in CONDITIONS for _ in range(REPEATS)]
random.shuffle(order)
sightlab.setTrialCount(len(order))


def sightLabExperiment():
    yield viztask.waitEvent(EXPERIMENT_START)
    for i in range(sightlab.getTrialCount()):
        name = order[i]
        sphere.setPosition([0, 1.5, CONDITIONS[name]])
        sightlab.setConditionName(name)
        yield sightlab.startTrial(trialLabel=name, startTrialText='Look at the sphere. Press the trigger to start.')
        sightlab.setExperimentSummaryData('Condition', name)
        sightlab.setExperimentSummaryData('Distance (m)', CONDITIONS[name])
        yield viztask.waitTime(6)
        yield sightlab.endTrial()


viztask.schedule(sightlab.runExperiment)
viztask.schedule(sightLabExperiment)
viz.callback(viz.getEventID('ResetPosition'), sightlab.resetViewPoint)
```

## Gotchas

- `startTrial(condition=...)` is **not** a condition label. It is the GUI's start-condition
  event (timer, key, event) and expects the GUI's own list form. Label conditions with
  `trialLabel=` or `setConditionName`, and write them with `setExperimentSummaryData`.
- Shuffle once, before the loop, with `random.shuffle`. For a fixed order per participant
  (reproducibility, or counterbalancing by participant number), seed from the participant
  ID: `random.seed(sightlab.participantData[ID])` after construction, or take the order from
  a STIM file (`patterns/stim-file-stimuli.md`).
- Latin-square or alternating left/right assignments are plain Python on `order`; keep the
  scheme in one place and write what was used into the summary.
- Blocks of trials: `sl.SightLab(repetitions=2)` runs the whole trial set twice and names the
  files `block_1`, `block_2`; `getCurrentRepetition()` tells you which block you are in.
- `examples/Randomize` shows the GUI route: randomisation configured in the GUI and loaded
  with `configpath=`.

## Data produced

Standard files; `Label` carries the condition name; summary columns `Condition` and
`Distance (m)` from `setExperimentSummaryData`.

## Shows up in

`examples/Randomize` (GUI and block variants), `examples/STIM Files`, `examples/Memory_Experiment`.

## Needs

Nothing beyond SightLab.
