# Imports and the experiment frame

Every SightLab 2.x experiment is built on the same frame. Keep it; add to it.

## The two imports

- Always start with these two lines. The second brings in the event names
  (`EXPERIMENT_START`, `TRIAL_START`, `TRIAL_END`, `EXPERIMENT_END`), the object-group keys
  (`GAZE_OBJECTS`, `GRAB_OBJECTS`) and the Vizard modules the frame uses (`viz`, `vizact`,
  `viztask`, `vizfx`).
  ```python
  import sightlab_utils.sightlab as sl
  from sightlab_utils.settings import *
  ```
- The class is `SightLab` with a capital L: `sl.SightLab(...)`. `sl.Sightlab` does not exist.

## The frame

```python complete
import sightlab_utils.sightlab as sl
from sightlab_utils.settings import *
import vizshape

sightlab = sl.SightLab(gui=False, headlight=True)
env = vizfx.addChild('sightlab_resources/environments/complete_scene.osgb')
sightlab.setEnvironment(env)

cube = vizshape.addCube(size=0.2)
cube.setPosition([0, 1.5, 1.5])
sightlab.addSceneObject('cube', cube, gaze=True)
sightlab.setTrialCount(3)


def sightLabExperiment():
    yield viztask.waitEvent(EXPERIMENT_START)
    for i in range(sightlab.getTrialCount()):
        yield sightlab.startTrial(startTrialText='Look at the cube.')
        yield viztask.waitTime(10)
        yield sightlab.endTrial()


viztask.schedule(sightlab.runExperiment)
viztask.schedule(sightLabExperiment)
viz.callback(viz.getEventID('ResetPosition'), sightlab.resetViewPoint)
```

- The three closing lines are not optional. `viztask.schedule(sightlab.runExperiment)` runs
  SightLab's own loop (loading, data saving, HUD); `viztask.schedule(sightLabExperiment)` runs
  the study; the `ResetPosition` callback lets the researcher press `r` to recentre.
- Never call `viz.go()`. SightLab starts Vizard itself; a second `viz.go()` is at best ignored.
- `startTrial` and `endTrial` are generators: always `yield` them. Every `startTrial` has a
  matching `endTrial`, in the same generator.
- Wait before the first `startTrial`. SightLab sends `EXPERIMENT_START` itself once trial 1
  has loaded; a generator that calls `startTrial` immediately runs before setup is complete and
  SightLab silently does nothing. The shipped examples wait on `EXPERIMENT_START` or on the
  space key (`yield viztask.waitKeyDown(' ')`); either is right.
- With `gui=False`, call `sightlab.setTrialCount(n)` (or pass `trialcount=n` to the
  constructor). Without it `getTrialCount()` returns 1 and a `range(...)` loop runs once.
- Units are metres; rotations are Euler angles in degrees; positions are relative to the
  parent object. A comfortable place for a demonstration object is `[0, 1.5, 1.5]`.

## Constructor arguments worth knowing

```python
SightLab(gui=True, pid=True, biopac=None, headlight=False, console=..., screenrecord=False,
         trialcount=None, repetitions=1, hardwareconfig=None, configpath=None, ...)
```

- `gui`: `True` takes environment, objects and trial settings from the SightLab GUI (see
  `rules/gui-vs-code.md`); `False` means the script sets everything.
- `headlight=True` whenever the scene uses `vizshape` primitives or an unlit model.
- `pid=False` skips the participant-ID dialog (useful for tests; keep `True` for real runs).
- `hardwareconfig='Desktop'` (or another name from the hardware list) selects the vizconnect
  configuration without the chooser dialog.
- `biopac=True` turns on BIOPAC marker sending; see `patterns/biopac-markers.md`.
- The full list, with defaults, is in `api/sightlab-api.md` under `class SightLab`.
