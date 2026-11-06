# Common mistakes

Each of these is caught by `harness/check.py` where a static check can; the code is the one
it prints.

| Mistake | Why it hurts | Fix | Code |
|---|---|---|---|
| Calling `viz.go()` | SightLab already started Vizard | delete the line | `W_VIZ_GO` |
| Leaving out `viztask.schedule(sightlab.runExperiment)` | nothing loads, no HUD, no data | add the three closing lines of the frame | `E_NO_RUN_EXPERIMENT` |
| `startTrial` before any wait | runs before setup; SightLab silently ignores it | `yield viztask.waitEvent(EXPERIMENT_START)` or a key wait first | `W_START_TRIAL_IMMEDIATE` |
| `gui=False` and no `setTrialCount` | the `range(getTrialCount())` loop runs once | `sightlab.setTrialCount(n)` | `W_NO_TRIAL_COUNT` |
| No `gaze=True` on any object | no dwell, fixation or view data | `addSceneObject('name', node, gaze=True)` | `W_NO_GAZE_OBJECT` |
| A method or argument that does not exist | the script crashes on that line | look it up in `api/sightlab-api.md` | `E_UNKNOWN_METHOD`, `E_UNKNOWN_KWARG` |
| An environment or object file that is not shipped | load fails or the scene is empty | pick from `api/resources.md` or the install | `W_UNKNOWN_ENVIRONMENT` |
| A shipped file spelled in a different case | works on Windows, but not in GUI lists or on a case-sensitive copy | use the spelling in `api/resources.md` | `W_UNKNOWN_ENVIRONMENT` (with the right spelling) |
| `textContinueKey` with text that says "press the trigger" | the key replaces the trigger wait; a headset participant is stuck | drop the key, or change the text to name the key | `W_KEY_REPLACES_TRIGGER` |
| `startTrial` and `endTrial` counts differ | trials never save, or save twice | pair them in one generator | `W_UNPAIRED_TRIAL` |
| Forgetting `yield` on `startTrial`/`endTrial` | the generator object is created and dropped; nothing happens | `yield sightlab.startTrial(...)` | (not static; the harness sees zero trials) |
| `vizshape` objects invisible or black | no light in the scene | `sl.SightLab(..., headlight=True)` and `import vizshape` | — |
| `addCustomTrialDataColumn(...)`, as some documentation pages write it | not a method in 2.9.3; the script crashes | delete it: there is no declare step; `sightlab.setCustomTrialData(value, 'Column Name')` writes the value for the current frame (call it each frame for a continuous value such as heart rate); one value per trial is `setExperimentSummaryData` | `E_UNKNOWN_METHOD` |
| `setEnvironment(env, trial=n)` to give trial n its own 3D scene | `trial=` is ignored for 3D models; the last call wins for every trial | load every scene and switch with `visible()` (`rules/environments-and-resources.md`) | — |
| `sightlab.getRegionOfInterest('name')` to find a 360 ROI | returns `None` in 2.9.3 for ROIs the GUI or the tracer saves (it compares the key's last element, the Z scale) | match `key[4]` in `sightlab.sceneObjects[REGIONS_OF_INTEREST]` (`guides/360-moving-regions.md`) | — |
| `sl.Sightlab(...)` | wrong case; the class is `SightLab` | `sl.SightLab(...)` | `E_SYNTAX`-adjacent: Python raises AttributeError |
| Writing gaze detection by hand | duplicates and fights the built-in events | subscribe to `sightlab.GAZE_TIME_EVENT` and friends | — |
| Calling `setEnvironment` with `gui=True` | overrides what the researcher chose in the GUI | leave it to the GUI, or go `gui=False` | — |
| Writing `Biopac` in prose | the company writes BIOPAC | BIOPAC | (kit lint) |

## When the checker is silent but something is still wrong

- The script runs but the data folder is empty: `endTrial` never completed. Look for a
  missing `yield`, an exception in a callback, or a trial that never ends.
- Gaze events never fire on the desktop: the Desktop configuration uses the view centre as
  the gaze ray; look straight at the object, or test with the harness, which steers the view.
- Text prompts never dismiss: the continue event is the controller trigger (left mouse on
  the desktop); add `textContinueKey=' '` to accept the space bar too.

## Guessing when the source is right there

When a rule, a pattern or the API map does not say what a call does, read it in
`reference/sightlab.py` (or the installed `sightlab_utils/sightlab.py`) before writing code
that depends on it. Every surprise in this file was found that way; none was in the
docstrings.

## Hidden objects come back after a prompt

SightLab hides the scene while a text prompt or rating screen is up and shows it again when
the screen closes, and "the scene" includes every object you added with `addSceneObject`,
hidden or not. A pool object you hid with `visible(viz.OFF)` is visible again after the first
trial's start text and after every `showRatings`. Hide again after each of those, and park
hidden objects away from the participant (`setPosition([0, -50, 0])`) so a re-shown object is
out of sight and out of gaze reach. `patterns/show-hide-objects-per-trial.md`.

