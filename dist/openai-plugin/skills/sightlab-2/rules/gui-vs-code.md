# GUI, code, or both

SightLab 2 supports three ways of working. Decide which one the researcher is in before
writing anything, and say which one the script assumes.

| Mode | How it is chosen | Who sets environment, objects, trials |
|---|---|---|
| GUI | `sl.SightLab()` or `sl.SightLab(gui=True)` | the researcher, in SightLab's windows; settings are saved as a config under `sightlab_configs/` |
| Code | `sl.SightLab(gui=False)` | the script: `setEnvironment`, `addSceneObject`, `setTrialCount`, conditions |
| Both | `gui=True` plus code calls | the GUI for the basics, code for behaviour, events and custom data |

## Rules for GUI mode (`gui=True`, the default)

- Do not call `setEnvironment` or `setTrialCount`; the GUI provides them. Calling them
  anyway overrides what the researcher chose, which surprises them.
- The experiment generator still needs the frame. Wait on `EXPERIMENT_START`, then on each
  trial's `TRIAL_START` when the GUI drives trial starts:
  ```python
  def sightLabExperiment():
      yield viztask.waitEvent(EXPERIMENT_START)
      for trial in range(sightlab.getTrialCount()):
          yield viztask.waitEvent(TRIAL_START)
          yield viztask.waitEvent(TRIAL_END)
  ```
- Instructions before the trials: `yield sightlab.showInstructions('text')`.
- A saved GUI config can be loaded without the windows: `sl.SightLab(configpath='sightlab_configs/MyStudy.stlb')`.
  This is also how an automated test runs a GUI-built study.

## Rules for code mode (`gui=False`)

- The script must add an environment (`rules/environments-and-resources.md`), register the
  objects it wants data on, and set the trial count.
- Trials start when the script says: `startTrial(...)`, optionally after a key or a timer.
- Everything the GUI can do has a method: per-trial environments, 360 media, conditions,
  grab objects, BIOPAC events, repetitions. Look it up in `api/sightlab-api.md` rather than
  guessing a name.

## The projects folder, and "how do I create my first experiment?"

SightLab 2 installs `Documents\Sightlab2\Projects\` with two starting points:

- `BlankProject`: `SightLab_VR.py` (the GUI script: `sl.SightLab()` and the trial loop above),
  `SightLabVR_NonGUI.py` (the code template: `gui=False`, an environment, a trial count, one
  gaze and grab object, the space bar starts and ends trials), `SightLabVR_Replay.py`,
  `SightLab_VR_Server.py` and `SightLab_VR_Client.py` for multi-user, and `Resources/`
  (`environments`, `media`, `scene_objects`). `sightlab_configs/`, `data/` and `recordings/`
  appear on the first run.
- `SampleProject`: the same layout with a worked study and its assets; a guide to how a
  finished project is organised.

A new user who asks how to create their first experiment hears the three routes and picks:

1. **GUI only, no code:** copy `BlankProject` to a new folder under `Projects` (the Dashboard
   lists it there), run `SightLab_VR.py`, choose the environment, scene objects and trials in
   the GUI, and save the configuration. Their own models go in `Resources/environments`.
2. **Code:** start from `SightLabVR_NonGUI.py` (or the frame in `rules/imports-and-frame.md`)
   and put the whole study in the script. This is what the agent builds from a brief.
3. **Both:** the GUI for environment, objects and trials; code added to `SightLab_VR.py`
   for events, custom data and logic.

When the agent creates something, it writes code by default: it adds code to a GUI
project's script (`gui=True`) or writes a code project. A GUI-style project from scratch
follows `BlankProject` and `SampleProject` (the folder layout and `SightLab_VR.py`), and
either loads a saved config with `configpath=` or leaves the GUI choices to the researcher.
Where the host gives the agent computer use (control of the screen, mouse and keyboard) and
the researcher wants the GUI route, the agent can also work in SightLab's windows itself: the
GUI, Inspector, the Dashboard and Replay.

## The agent's default

Experiments built by an agent from a brief use `gui=False` with settings in code, because
the whole study is then visible in one file, reviewable in a diff, and testable by the
harness. This is a default, not a rule: a researcher who works from the GUI keeps doing so,
and gets a saved config plus a script that loads it with `configpath=`.
