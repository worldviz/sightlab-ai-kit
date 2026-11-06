# Session replay

Sources: help.worldviz.com/sightlab session-replay; the earlier assistant's `replay.py` notes.

When to read: the researcher wants to watch a recorded session, see gaze paths or heatmaps,
replay 360 media, or show custom state (an object's colour, visibility) in the replay.

## What it is

Every SightLab session writes `replay_data/*.rply` beside its CSVs. `SightLabVR_Replay.py`
(a copy ships in every example folder; the Dashboard's Replay button runs it) plays a chosen
trial back: gaze path, gaze point, dwell events, heatmaps, the moving objects, and the
participant's view. It is a separate script, not part of the experiment script.

- Controls: free camera with `WASD` and `ZX`, or look around in VR; a trial selector; a
  button to open the session's data folder; `Ctrl+F12` records an uncompressed video.
- Heatmaps: static (whole trial at once), occlusion-aware (respects walls), or a gradient
  that fades over time. Long trials (over 2–3 minutes) can switch to the faster heatmap.
- Noise filter: `replay = Replay.SightLabReplay(noiseFilter=True)` averages gaze over a
  window.
- 360 media: fixed viewpoint, look around with Follow Mode off.

## Custom flags: show experiment state in the replay

During the experiment, record state as it changes:

```python
def changeColor():
    basketball.color(viz.BLUE)
    sightlab.setCustomReplayFlag('color', basketball.getColor())

vizact.onkeydown('a', changeColor)
```

In the replay script, read it back and apply it:

```python
def onFlag():
    flag_data = replay.getCurrFlag()
    if 'color' in flag_data:
        replay.sceneObjects[GAZE_OBJECTS]['basketball'].color(flag_data['color'])
```

Any JSON-able value works (visibility, position, a condition name).

## Group heatmaps

`examples/Group_Heatmap_Replay` shows where people looked across many recordings of the
same scene: different participants, or one participant over several trials and sessions.
It works for 3D environments and 360 media.

1. `merge_sessions.py`: pick the project's data folder (the one holding the
   `<date>_experiment_data` folders, not the example's own `data`). Every scene recorded at
   least `MIN_RECORDINGS` times (default 2) becomes one trial of a new session ending in
   `_GROUP`, in the example's `data` folder. Each recording becomes a client, resampled onto
   a shared `RESAMPLE_HZ` (60 Hz) timeline from the trial start; the longest recording
   drives the scene.
2. `group_heatmap_replay.py`: pick the `_GROUP` session. One heatmap adds up everyone's
   gaze; the Client ID list shows one participant alone. Normal sessions also play here.

`group_heatmap_config.py`: `SOURCE_DATA_FOLDER`, `GROUP_NAME` (no underscores),
`TRIAL_NUMBERS` and `TRIAL_LABELS` (merge only those trials or conditions),
`MIN_RECORDINGS`, `MIN_DURATION` (skip short or aborted runs), `HEATMAP_NORMALIZATION`
(`'mean'` dwell per recording, to compare groups of different sizes, or `'sum'`),
`HIDE_PARTICIPANT_OVERLAYS`, and `HEATMAP_START_TIME` with `HEATMAP_END_TIME` to limit it
to a time window (for 360 video, in video time).

- Originals are only read. `group_manifest.csv` in each merged session lists which
  recording each client came from; every merge is a new session, so delete old ones.
- Merged sessions point at the project's environment and media files: moving or renaming
  the project means merging again.
- It suits studies where everyone saw the same content, since one recording drives the scene.

## Gotchas

- A script that renames the standard data folders or files breaks the replay; keep
  SightLab's layout.
- Objects added after the trial started are not in the replay unless registered with
  `addSceneObject`.
- The replay uses the same environment file; a researcher's own model must stay where the
  script found it.
- Replay cannot be driven by the autopilot; a person runs it, or an agent with computer use.

## Shipped examples

`examples/Replay_Events`, `examples/Group_Heatmap_Replay`, `examples/360 non GUI` (360 replay),
`examples/Virtual 2D Screen` (video-synchronised replay).
