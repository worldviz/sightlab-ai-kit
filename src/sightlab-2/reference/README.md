# Reference source

The real thing, for when a rule, a pattern or the API map does not answer a question about
what SightLab or Vizard does. Read the function before guessing.

| File | What | From |
|---|---|---|
| `sightlab.py` | the `SightLab` class and everything it drives: trials, prompts, ratings, gaze, recording | `sightlab_utils` 2.8.21 (Assembla trunk r14264, 2026-10-31) |
| `replay.py` | the session replay tool | `sightlab_utils` 2.8.21 |
| `viz.py` | Vizard's core module: nodes, events, matrices, constants | Vizard 8.3.1 |

On a machine with SightLab installed, prefer the installed copies (`Find the install` in the
skill): `<Vizard>\python\sightlab_utils\sightlab.py` and `<Vizard>\python\viz.py` are the
versions the researcher runs, and may be newer than these.

Three things the rules learned from these files, as examples of what to look for here:
`textContinueKey` replaces the trigger wait (`showInstructions`); `sceneToggle(viz.ON)` after
any prompt or rating re-shows every `addSceneObject` node; `setExperimentSummaryData`
columns land on the `ENTIRE_SCENE` summary row only.
