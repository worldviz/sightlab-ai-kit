# Gaze objects and data

## Registering objects is what records data

- SightLab records gaze on an object only if the object is registered:
  `sightlab.addSceneObject('name', node, gaze=True)`. A node that is merely in the scene
  produces no dwell, fixation or view-count data.
- Make an object grabbable with the same call: `sightlab.addSceneObject('name', node,
  gaze=True, grab=True)`. Register after the node exists.
- Regions rather than objects: `sightlab.addRegionOfInterest(regionObject)`.
- Registered objects are reachable later as `sightlab.sceneObjects[GAZE_OBJECTS]['name']` and
  `sightlab.sceneObjects[GRAB_OBJECTS]['name']`.
- In GUI mode (`gui=True`) the researcher registers objects in the GUI instead; code
  registration is still allowed and adds to the GUI's list.
- A pool of objects shown in different subsets per trial: register all of them once, hide
  with `visible(viz.OFF)`, show per trial (`patterns/show-hide-objects-per-trial.md`).

## Gaze events are built in

- Do not write gaze detection. SightLab already intersects the gaze ray with registered
  objects every frame and raises events. Subscribe with `vizact.addCallback`:
  ```python
  def gazeActionStart(e):
      if e.object == sightlab.sceneObjects[GAZE_OBJECTS]['cube']:
          cube.color(viz.BLUE)

  def gazeActionEnd(e):
      if e.object == sightlab.sceneObjects[GAZE_OBJECTS]['cube']:
          cube.color(viz.RED)

  vizact.addCallback(sightlab.GAZE_TIME_EVENT, gazeActionStart)
  vizact.addCallback(sightlab.GAZE_END_EVENT, gazeActionEnd)
  ```
- `GAZE_BEGIN_EVENT` fires on first contact, `GAZE_TIME_EVENT` once the dwell threshold
  (`setDwellTimeThreshold`, default 0.5 s) is reached, `GAZE_END_EVENT` when gaze leaves.
- Grab and release events: see `examples/Grab_Events` for the callbacks SightLab raises.

## What gets written, per trial

Under the script's folder, `data/<date>_<participant>_experiment_data/`:

| File | Contents |
|---|---|
| `trial_data/..._trial_data_N.csv` | per-frame tracking: timestamp, combined and per-eye gaze intersections and angles, head position, flags |
| `..._experiment_summary.csv` | one row per registered object per trial: dwell visits, fixation count, total and average dwell time, time to first fixation, saccade statistics |
| `trial_data/..._trial_timeline_dwell_N.csv` | each dwell on each object with start, end, duration |
| `trial_data/..._trial_timeline_fixation_saccade_N.csv` | each fixation and saccade with dispersion and velocity |
| `replay_data/..._replay_data_N.rply` | everything the Replay tool needs to play the trial back |
| `config.json` | the settings the trial ran with |

- Per-trial saving is the default (`datafilesaving=PER_TRIAL`); nothing is written until
  `endTrial` finishes, so a crash mid-trial loses that trial.
- Trial timing: `sightlab.hud.getCurrentTime()` is the current trial time in seconds.

## Adding your own columns

- One value per trial (a response, a condition label, a score):
  `sightlab.setExperimentSummaryData('Response', value)` before `endTrial`. It lands on the
  trial's `ENTIRE_SCENE` row of the summary file; the per-object rows above it do not carry
  these columns.
- A mark on the moment something happened: `sightlab.setCustomTrialData('target shown')` (or
  with `columnName='Event'`) stamps the current frame in the trial's `trial_data` file and
  clears on the next frame. It is a per-frame flag, not a summary column.
- A tracked object's pose on every frame:
  `sightlab.addTrackingTrialDataColumn('hand', handNode)` once, before the trials start.
- Condition labels: `sightlab.setConditionName('A')` or `startTrial(trialLabel='A')`, plus a
  summary column via `setExperimentSummaryData('Condition', 'A')`. (`startTrial(condition=...)`
  is the GUI's start-condition event, not a label.)
- See `examples/Custom Data Saving` and `patterns/randomized-conditions.md`.
