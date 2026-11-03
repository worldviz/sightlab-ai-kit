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

`examples/Group_Heatmap_Replay` merges several sessions of the same scene (different
participants, or one participant across sessions) into one `_GROUP` session and replays
the combined heatmap, with a per-client filter. Originals are read, never changed.

## Gotchas

- A script that renames the standard data folders or files breaks the replay; keep
  SightLab's layout.
- Objects added after the trial started are not in the replay unless registered with
  `addSceneObject`.
- The replay uses the same environment file; a researcher's own model must stay where the
  script found it.
- Replay cannot be driven by the autopilot; it is a human tool.

## Shipped examples

`examples/Replay_Events`, `examples/Group_Heatmap_Replay`, `examples/360 non GUI` (360 replay),
`examples/Virtual 2D Screen` (video-synchronised replay).
