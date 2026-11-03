# BIOPAC markers and synchronisation

## Intent

Physiology is recorded in BIOPAC AcqKnowledge; the VR trial timeline must be visible in that
recording. With `biopac=True` SightLab connects to AcqKnowledge over the network data
transfer (NDT) link and sends an event at every trial start and end, so the two recordings
line up on the same trial markers. Channel values can also be streamed back into SightLab's
data files.

## Script

```python complete
import sightlab_utils.sightlab as sl
from sightlab_utils.settings import *

sightlab = sl.SightLab(gui=False, biopac=True)
env = vizfx.addChild('sightlab_resources/environments/lab_empty.osgb')
sightlab.setEnvironment(env)
sightlab.setTrialCount(4)


def sightLabExperiment():
    yield viztask.waitEvent(EXPERIMENT_START)
    for i in range(sightlab.getTrialCount()):
        if i == 0:
            yield sightlab.startTrial(startExperimentText='Press the space bar to start.',
                                      textContinueKey=' ')
        else:
            yield viztask.waitKeyDown(' ')
            yield sightlab.startTrial()
        yield viztask.waitTime(20)
        yield sightlab.endTrial()


viztask.schedule(sightlab.runExperiment)
viztask.schedule(sightLabExperiment)
viz.callback(viz.getEventID('ResetPosition'), sightlab.resetViewPoint)
```

## Gotchas

- `biopac=True` is the switch; in GUI mode it is the BIOPAC toggle. Without it no events are
  sent and nothing complains.
- AcqKnowledge must be running with NDT enabled and the network server allowed before the
  script starts; otherwise the connection fails at start-up. Say this in `REVIEW.md`.
- Markers are automatic for trial start and end, dwell onset and end on every registered
  gaze object, and grab and release. Extra markers at custom moments (stimulus onset, a
  response) go through the same connection:
  `sightlab.acqServer.insertGlobalEvent('Stimulus onset', 'stim', '')`.
- Streaming channel values into the trial data: `examples/Biopac Saving to Data Files`
  registers a callback with `biopacndt.AcqNdtDataServer` and writes each channel with
  `setCustomTrialData`. Start and stop the data server inside each trial as that example does.
- Timing: markers arrive at frame rate on the VR side and at the NDT update rate on the
  BIOPAC side; for sub-frame alignment use the marker pair at trial start as the anchor.
- The harness counts the markers the script and SightLab would send: through the real
  connection when AcqKnowledge is running, otherwise through a stand-in it installs in place of
  the server (the report says `biopac: stub`). It cannot confirm delivery; delivery is a
  `needs_human` item every time.

## Data produced

Standard SightLab files; in AcqKnowledge, event markers at every trial start and end. With
channel streaming, extra `Channel_N` columns in the trial data via `setCustomTrialData`.

## Shows up in

`examples/Biopac Saving to Data Files` (streaming and summary variants), `examples/Walk the Plank`
(markers in a fear-of-heights task), `examples/Biofeedback`.

## Needs

A BIOPAC MP160/MP36 with AcqKnowledge and the NDT licence, on the same network as the VR PC.
