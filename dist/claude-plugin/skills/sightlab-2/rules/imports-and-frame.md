# Imports and the experiment frame

Every SightLab 2 experiment is built on the same frame. Keep it; add to it.

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
- `hardwareconfig='Desktop'` selects the vizconnect configuration without the chooser
  dialog; the name must be an exact key of `VIZCONNECT_DICT` or Vizard quits
  (`guides/hardware.md`).
- `biopac=True` turns on BIOPAC marker sending; see `patterns/biopac-markers.md`.
- The full list, with defaults, is in `api/sightlab-api.md` under `class SightLab`.

## Global settings (`settings.py`)

`sightlab_utils/settings.py` holds global defaults: `START_TEXT`, the dwell, fixation and
saccade thresholds, `VIZCONNECT_DICT` and `VIZCONNECT_CONFIG_LIST`, `PARTICIPANT_INFO1`/`2`
(which rename the summary's participant columns), fades, video compression, `LANGUAGE`.

- Prefer a constructor argument or a method when one exists (`setStartText`,
  `vizconnectconfig=`, `setFixationSaccadeThresholds`, ...).
- Never edit the installed `settings.py`: it is shared by every project on the PC, sits under
  Program Files, and the next SightLab install replaces it.
- To change a value for one script, set it before SightLab is imported, because
  `sightlab.py` copies the settings when it loads:
  ```python
  from sightlab_utils import settings
  settings.START_TEXT = 'Press the trigger to begin'
  import sightlab_utils.sightlab as sl
  from sightlab_utils.settings import *
  ```
- `LANGUAGE` cannot be changed this way: it is applied the moment `settings.py` is first
  imported.

## Adding SightLab to an existing Vizard script

- SightLab starts Vizard and loads vizconnect itself: delete the script's own `viz.go()` and
  `vizconnect.go(...)`. A custom vizconnect file goes in `vizconnectconfig=`
  (`guides/hardware.md`).
- Then the usual frame: `sl.SightLab(gui=False)`, `setEnvironment(env)`, `addSceneObject` for
  anything that needs data, `yield sightlab.startTrial()` and `yield sightlab.endTrial()`
  around the session (after `yield viztask.waitEvent(EXPERIMENT_START)` when it starts at
  once), and
  `viztask.schedule(sightlab.runExperiment)` after the scene is built.
- For replay, copy `SightLabVR_Replay.py` from `Projects\SampleProject` beside the script.
- To run a Vizard script under SightLab without recording anything:
  `sl.SightLab(gui=False, pid=False, fadequad=False, headlight=True)`.
