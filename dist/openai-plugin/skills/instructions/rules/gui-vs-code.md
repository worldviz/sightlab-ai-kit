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

## The agent's default

Experiments built by an agent from a brief use `gui=False` with settings in code, because
the whole study is then visible in one file, reviewable in a diff, and testable by the
harness. This is a default, not a rule: a researcher who works from the GUI keeps doing so,
and gets a saved config plus a script that loads it with `configpath=`.
