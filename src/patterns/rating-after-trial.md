# Rating after a trial

## Intent

After viewing, the participant answers a question on a scale (Likert, yes/no/unsure, 0–10),
and the answer is stored with the trial's data.

## Script

```python complete
import sightlab_utils.sightlab as sl
from sightlab_utils.settings import *

sightlab = sl.SightLab(gui=False)
env = vizfx.addChild('sightlab_resources/environments/Business_Office.OSGB')
sightlab.setEnvironment(env)

plant = env.getChild('Plant')
sightlab.addSceneObject('Plant', plant, gaze=True)
sightlab.setTrialCount(2)

SCALE = ['1', '2', '3', '4', '5', '6', '7']


def sightLabExperiment():
    yield viztask.waitEvent(EXPERIMENT_START)
    for i in range(sightlab.getTrialCount()):
        yield sightlab.startTrial(startTrialText='Look at the plant. Press the trigger to begin.')
        yield viztask.waitTime(8)
        yield sightlab.showRatings('How attractive was the plant? (1 = not at all, 7 = very)',
                                   ratingScale=SCALE, pauseTimer=True, endFade=False)
        sightlab.setExperimentSummaryData('Rating', sightlab.ratingChoice)
        yield viztask.waitTime(0.1)
        yield sightlab.endTrial()


viztask.schedule(sightlab.runExperiment)
viztask.schedule(sightLabExperiment)
viz.callback(viz.getEventID('ResetPosition'), sightlab.resetViewPoint)
```

## Gotchas

- `showRatings` is a generator: `yield` it. It returns after the participant chooses; the
  choice is then in `sightlab.ratingChoice`.
- Store the choice with `setExperimentSummaryData('Rating', ...)` *before* `endTrial`, or it
  goes nowhere. One column per question; name them as the brief names the measures.
- `pauseTimer=True` stops the trial clock while the scale is up, so dwell times are not
  inflated by rating time. The scene is hidden behind the scale regardless (`showRatings`
  calls `sceneToggle(viz.OFF)`); `endFade` only decides whether the screen fades out after
  the choice, and only while a trial is running (`hideRatings` in `reference/sightlab.py`).
- `ratingScale` entries are strings; the participant picks with the controller trigger or,
  on the desktop, the mouse.
- Several questions: call `showRatings` several times in a row, storing each answer.
- Questions from a file: `examples/RatingScale_GUI` has a `Questions_From_CSV_Example`.
- `startTrial(startRatings=...)` and `endTrial(endRatings=...)` exist for GUI-configured
  scales; in code, `showRatings` is clearer.

## Data produced

The summary file has one row per gaze object and then one `ENTIRE_SCENE` row per trial;
only the `ENTIRE_SCENE` row carries the `setExperimentSummaryData` columns (here `Rating`).
Read ratings from that row, not from the object rows above it.

## Shows up in

`examples/RatingScale_GUI` (`RatingScale_Sample.py`, `RatingScale_GUI.py`, `Surveys.py` for
`vizinput` questionnaires), `examples/Gaze_Based_Interactions`
(`SightLabVR_Rating_after_view.py`).

## Needs

Nothing beyond SightLab.
