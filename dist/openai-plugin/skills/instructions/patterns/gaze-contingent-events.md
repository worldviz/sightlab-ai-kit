# Gaze-contingent events

## Intent

Something happens when the participant looks at an object: it changes colour, a sound plays,
a trial ends, a score is kept. SightLab already detects gaze on registered objects; the
pattern is to subscribe to its events and compare `e.object` with the registered node.

## Script

```python complete
import sightlab_utils.sightlab as sl
from sightlab_utils.settings import *
import vizshape

sightlab = sl.SightLab(gui=False, headlight=True)
env = vizfx.addChild('sightlab_resources/environments/complete_scene.osgb')
sightlab.setEnvironment(env)

target = vizshape.addCube(size=0.2, color=viz.RED)
target.setPosition([0, 1.6, 2])
sightlab.addSceneObject('target', target, gaze=True)
sightlab.setTrialCount(3)
sightlab.setDwellTimeThreshold(0.5)

looks = {'count': 0}


def onGazeTime(e):
    # Fires once the gaze has rested on the object for the dwell threshold.
    if e.object == sightlab.sceneObjects[GAZE_OBJECTS]['target']:
        looks['count'] += 1
        target.color(viz.BLUE)


def onGazeEnd(e):
    if e.object == sightlab.sceneObjects[GAZE_OBJECTS]['target']:
        target.color(viz.RED)


vizact.addCallback(sightlab.GAZE_TIME_EVENT, onGazeTime)
vizact.addCallback(sightlab.GAZE_END_EVENT, onGazeEnd)


def sightLabExperiment():
    yield viztask.waitEvent(EXPERIMENT_START)
    for i in range(sightlab.getTrialCount()):
        looks['count'] = 0
        yield sightlab.startTrial(startTrialText='Look at the red cube to turn it blue.')
        yield viztask.waitTime(10)
        sightlab.setExperimentSummaryData('Dwell events', looks['count'])
        yield sightlab.endTrial()


viztask.schedule(sightlab.runExperiment)
viztask.schedule(sightLabExperiment)
viz.callback(viz.getEventID('ResetPosition'), sightlab.resetViewPoint)
```

## Gotchas

- Register the object with `gaze=True` before the trials start, or no event ever fires.
- Compare against `sightlab.sceneObjects[GAZE_OBJECTS]['name']`, not against a string.
- `GAZE_BEGIN_EVENT` fires on first contact; `GAZE_TIME_EVENT` only after
  `setDwellTimeThreshold` seconds (default 0.5). Use the one the brief means.
- To end a trial from a gaze event, do not call `endTrial` inside the callback directly;
  set a flag or send an event the generator waits on (`yield viztask.waitEvent(...)`), as
  `examples/STIM Files` does with `viztask.schedule(sightlab.endTrial(...))`.
- On the Desktop configuration the gaze ray is the view centre; look straight at the object.

## Data produced

Standard per-object rows in the summary file (`Dwell Visits`, `Fixation Count`,
`Total Dwell Time (secs)`, `Time to First Fixation (secs)`), the per-frame tracking file,
and the dwell timeline file. The custom column `Dwell events` is added by
`setExperimentSummaryData`.

## Shows up in

`examples/Gaze_Based_Interactions` (`Gaze_Based_Interaction_Simple.py` and the GUI variant),
`examples/VisualSearch`, `examples/Jump To Locations`.

## Needs

Nothing beyond SightLab for the mechanics; an eye-tracking headset for real gaze data.
