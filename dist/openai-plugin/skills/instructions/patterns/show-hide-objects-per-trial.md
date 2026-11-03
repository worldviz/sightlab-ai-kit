# Show and hide registered objects per trial

## Intent

A study has a pool of objects and shows a different subset each trial (a pair, a set of
three, a probe). SightLab records gaze only on registered objects, and the summary file
keeps one row per registered object per trial, so the right move is to register every object
once at start, hide them all, and show each trial's subset at its positions. Removing and
re-adding objects between trials breaks the data layout; `visible(viz.OFF)` does not.

## Script

```python complete
import sightlab_utils.sightlab as sl
from sightlab_utils.settings import *
import random

sightlab = sl.SightLab(gui=False)
env = vizfx.addChild('sightlab_resources/environments/whiteroom.osgb')
sightlab.setEnvironment(env)

# The pool: shipped files from sightlab_resources/objects/ (names from api/resources.md).
POOL = ['Plant.osgb', 'guitar.osgb', 'chair.osgb', 'crate.osgb', 'flashlight.osgb', 'computer_monitor.osgb']
SLOTS = [[-0.6, 1.5, 2.0], [0.6, 1.5, 2.0]]   # two positions, left and right

objects = {}
for name in POOL:
    node = vizfx.addChild('sightlab_resources/objects/' + name)
    node.visible(viz.OFF)
    sightlab.addSceneObject(name, node, gaze=True)   # registered once, for the whole session
    objects[name] = node

pairs = [POOL[i:i + 2] for i in range(0, len(POOL), 2)]   # three pairs from six objects
random.shuffle(pairs)
sightlab.setTrialCount(len(pairs))


def hideAll():
    for node in objects.values():
        node.visible(viz.OFF)


def show(names):
    for name, pos in zip(names, SLOTS):
        objects[name].setPosition(pos)
        objects[name].visible(viz.ON)


def sightLabExperiment():
    yield viztask.waitEvent(EXPERIMENT_START)
    for i in range(sightlab.getTrialCount()):
        names = pairs[i]
        hideAll()
        yield sightlab.startTrial(trialLabel='-'.join(names), startTrialText='Press the trigger when ready.')
        sightlab.setExperimentSummaryData('Left', names[0])
        sightlab.setExperimentSummaryData('Right', names[1])
        show(names)
        yield viztask.waitTime(8)
        hideAll()
        yield sightlab.endTrial()


viztask.schedule(sightlab.runExperiment)
viztask.schedule(sightLabExperiment)
viz.callback(viz.getEventID('ResetPosition'), sightlab.resetViewPoint)
```

## Gotchas

- Register before the trials and never again. Re-registering a name, or removing a node and
  adding a new one, changes the object set between trials and confuses the summary.
- Hidden objects still count as registered: their summary rows show zero dwell, which is
  correct and expected. Do not drop those rows in analysis without saying so.
- Set positions when showing, not when loading: a node keeps its last position, and a pool
  object may appear in different slots on different trials.
- `visible(viz.OFF)` also removes the object from gaze intersection, so a hidden object
  cannot collect stray dwell.
- **Every prompt and rating screen shows your hidden objects again.** When `showInstructions`,
  a `startTrial`/`endTrial` with text, or `showRatings` closes, SightLab's `sceneToggle(viz.ON)`
  sets `visible(viz.ON)` on every object added with `addSceneObject` (environment children are
  left alone). Call `hideAll()` again right after any of those, and park hidden objects out of
  the scene as well (for example `setPosition([0, -50, 0])` when hiding), so that a re-shown
  object is never at the participant's feet. Verified in 2.9.3: five hidden pool objects
  reappeared at the origin after the start text.
- Use shipped names from `api/resources.md`; a file that does not exist loads as an invalid
  node and `addSceneObject` registers nothing useful. Check the console at start.
- Shipped models load at their own scale and origin; `setScale` and a small `setPosition`
  offset per object, kept in a dict beside `POOL`, is the usual fix.

## Data produced

Standard files; one summary row per pool object per trial (six here); custom columns `Left`
and `Right` naming what was shown; `Label` carrying the pair.

## Shows up in

`examples/Memory_Experiment`, `examples/Choice Comparison`, `examples/VisualSearch`,
`examples/Swap_Environments` (the same idea for environments).

## Needs

Nothing beyond SightLab.
