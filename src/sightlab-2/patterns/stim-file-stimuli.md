# Stimuli driven by a STIM file

## Intent

The trial list lives in a CSV (one row per trial: label, condition, object, size, position,
anything else), so the researcher edits trials without touching code. SightLab's
`stim_reader` loads it; the script sets the trial count from it and reads each row as a
dictionary.

## Script

```python complete
import sightlab_utils.sightlab as sl
from sightlab_utils.settings import *
from sightlab_utils import stim_reader

sightlab = sl.SightLab(gui=False)
env = vizfx.addChild('sightlab_resources/environments/dojo.osgb')
sightlab.setEnvironment(env)

ball = vizfx.addChild('sightlab_resources/objects/basketball.osgb')
sightlab.addSceneObject('basketball', ball, gaze=True)

SIZES = {'small': [0.5, 0.5, 0.5], 'medium': [1, 1, 1], 'large': [2, 2, 2]}
POSITIONS = {'left': [-1, 1, 2], 'centre': [0, 1, 2], 'right': [1, 1, 2]}

reader = stim_reader.StimReader('stim_file_directory/stim_file_example.csv')
reader.fillStimFileEntryList()
entries = reader.getStimFileEntryList()
sightlab.setTrialCount(len(entries))


def sightLabExperiment():
    yield viztask.waitEvent(EXPERIMENT_START)
    for i in range(sightlab.getTrialCount()):
        row = entries[i]
        ball.setScale(SIZES[row['object size']])
        ball.setPosition(POSITIONS[row['object position']])
        yield sightlab.startTrial(trialLabel=row.get('label', ''),
                                  startTrialText='Find the ball. Press the trigger to start.')
        sightlab.setExperimentSummaryData('Object Size', row['object size'])
        sightlab.setExperimentSummaryData('Object Position', row['object position'])
        yield viztask.waitTime(10)
        yield sightlab.endTrial()


viztask.schedule(sightlab.runExperiment)
viztask.schedule(sightLabExperiment)
viz.callback(viz.getEventID('ResetPosition'), sightlab.resetViewPoint)
```

A matching `stim_file_directory/stim_file_example.csv`:

```csv
label,object size,object position
t1,small,left
t2,large,centre
t3,medium,right
```

## Gotchas

- Column headers become dictionary keys exactly as written (lower case, spaces kept). Keep
  them simple and check `row.keys()` once.
- Call `setTrialCount(len(entries))` before the trials; the count is not implied by the file.
- Shuffle `entries` once, before the loop, for random order (`random.shuffle(entries)`);
  never inside the loop.
- Write the row's values into the summary with `setExperimentSummaryData` so the data file
  is self-describing; the STIM file is not copied into the data folder.
- The STIM path is relative to the script's folder.
- Media per trial (images, 360 video) from a STIM file: see `examples/Model and Media Viewer`
  and `examples/Image_Viewer`.

## Data produced

Standard files, plus the summary columns written from the row (`Object Size`,
`Object Position`) and the trial label in `Label`.

## Shows up in

`examples/STIM Files` (`STIM_File_example.py`, `STIM_File_example_random.py`, replay with
`SessionReplay_STIM.py`), `examples/VisualSearch`.

## Needs

Nothing beyond SightLab.
