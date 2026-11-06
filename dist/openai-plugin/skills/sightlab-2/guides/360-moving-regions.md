# 360 moving regions of interest

Sources: `examples/360 Moving Regions of Interest` (`moving_rois.py`, `360_ROI_Path_Tracer.py`,
`360_moving_RegionsOfInterest.py`, `Replay.py`, sample config and session) and
`reference/sightlab.py` (2.9.3); help.worldviz.com/sightlab 360-moving-regions-of-interest, 360-media.

When to read: a 360 video study needs gaze data on something that moves (a person, a vehicle, a
ball); the researcher asks to trace, write or fix a region file; or the console shows
`[moving_rois]` messages.

## What it is

A 360 region of interest (ROI) drawn in the SightLab GUI stays where it was placed; use those for
360 images and for things that do not move. The example's `moving_rois.py` moves ROIs along paths
stored per video, timed to the video, and gaze on them is recorded under the region's name as for
a static ROI. 360 basics (`mode=MEDIA_360`, `mediaFormat`) are in
`rules/environments-and-resources.md`.

## Workflow

1. A person runs `360_ROI_Path_Tracer.py` (desktop and mouse) and drops the video on it. A video
   from outside the project is copied into `resources/media`. The format comes from a config trial
   that plays it, else a square frame means `Stereoscopic T/B`, else the person picks (F changes it).
2. If no trial plays it, the tracer asks which trial of the config SightLab opens on start
   (`sightlab_configs/recent_config.stlb` or the config it names) should; that trial's media is set
   and its old ROIs are replaced.
3. Trace: N new region, F2 rename (the name is the ROI name in the data), hold the left button on
   the object while the video plays; wheel sizes, Q/W tilt, B cycles sphere, box and triangle, E ends
   the region, Z undoes. J combines Ctrl+clicked regions into one. F1 lists all controls; P previews
   with the mouse as gaze.
4. It saves as it goes: the paths to `moving_rois/<video name>_regions.csv`, and each config trial
   playing the video gets one ROI per region, keyed `moving:<name>` (a GUI ROI with that name is used
   instead). The config is backed up to `.bak` once per session.
5. Run `360_moving_RegionsOfInterest.py` (in its GUI, Space previews the regions moving), then
   `Replay.py`.

## The region file

```text
Region,Time,Azimuth,Elevation,Radius,Aspect,Roll,Visible,Shape
Rider1,0.000,-45.08,-2.81,6.36,1.667,0.0,1,box
```

One row per keyframe; only the first four columns are required. `Time`: seconds of video.
`Azimuth`: degrees, 0 straight ahead, positive right. `Elevation`: degrees, positive up. `Radius`:
angular half-width in degrees (default 8, clamped 0.5 to 60). `Aspect`: height over width (default
1, clamped 0.2 to 5). `Roll`: degrees clockwise as seen. `Visible`: 0 hides until the next keyframe.
`Shape`: `sphere` (default), `box`, `triangle`, or a combined shape whose parts are joined by ` + `,
each `shape x y size aspect roll` in units of `Radius`; the same on every row of a region.

- Hidden before its first keyframe, held at its last until the video ends. Between keyframes the
  direction follows the great circle; size, aspect and roll change linearly.
- Angles are relative to the 360 sphere, so a region stays on the video wherever the head is.
- Box, triangle and combined regions are thin panels facing the viewer; gaze counts only on the shape.

## Using moving regions in your own script

Copy `moving_rois.py` and the `moving_rois` folder beside the script. The shipped script:

```python
import sightlab_utils.sightlab as sl
from sightlab_utils.settings import *
import moving_rois

sightlab = sl.SightLab()
regions = moving_rois.MovingRegions(sightlab, show=True)   # before runExperiment: also previews in the GUI

def sightLabExperiment():
	yield viztask.waitEvent(EXPERIMENT_START)
	for trial in range(sightlab.getTrialCount()):
		yield viztask.waitEvent(TRIAL_START)
		regions.start()
		yield viztask.waitEvent(TRIAL_END)
		regions.stop()
		sightlab.getMediaObject().pause()

viztask.schedule(sightlab.runExperiment)
viztask.schedule(sightLabExperiment)
```

- `show=False` hides all regions and still records gaze. `folder=` changes where files are looked
  up (default `moving_rois` beside `moving_rois.py`, then a `moving_rois` folder beside or above
  the video).
- `start()` loads the file named after the trial's video and moves each ROI whose name matches a
  region; other ROIs stay put, so static and moving ROIs can share a trial.
- The ROIs come from the trial's config; in 2.9.3 `addRegionOfInterest` does nothing, so keep the
  GUI mode as the example does.
- In a replay script, `moving_rois.show_shapes_in_replay(replay)` draws non-sphere regions in shape.

## Creating the regions with an AI assistant

The documentation gives a prompt for an agent that can run code and look at images: it finds the
objects in the video's frames and writes the region file (the warehouse sample was made this way).

- Change only `moving_rois/<video name>_regions.csv`, one region per object, named exactly as the
  researcher says (`moving_rois.Region`, `make_key`, `save_regions`, or plain CSV). Keep scratch
  scripts and images outside the project.
- Frame mapping (documentation; check it on a frame): azimuth = 360 x column / width from the eye
  image's left edge, which is straight ahead; elevation 90 at its top to -90 at its bottom. For
  `Stereoscopic T/B` use the top half (left eye).
- A keyframe about every 0.1 s while an object moves; `Visible` 0 while it is out of the scene.
  For an object that waits and then moves, repeat its still position just before it moves: the
  file interpolates between any two visible keyframes.
- Check by drawing the regions over many frames (fast motion, close passes, overlaps) and say where
  those images are. A static camera works best.
- Then a person opens the video in the tracer, which brings the trial's ROIs in line with the file,
  and checks with P. Missing image libraries are set up by a person following the SightLab
  documentation.

## Data per region

Same files as static ROIs, under the region's name: the experiment summary (`ROI/Object` rows),
`trial_timeline_dwell` (one row per visit), `trial_timeline_fixation_saccade` and the per-sample
`view status` column of `trial_data`. The replay stores each ROI's position, orientation and scale
every frame; the path itself is only in the region file, so keep it with the data. A combined
region is one name; for data per part, trace separate regions.

## Gotchas

- Names must match exactly (the ROI's name, not its `moving:` key); otherwise the console says
  `Region "X" has no region of interest with that name in this trial`. Press C in the tracer.
- Renaming the video means renaming its region file.
- A Timer end shorter than the video stops the regions; end the trial on Media End.
- The GUI size slider does nothing to a moving region. A hidden region cannot be gazed at.
- Excel holding the region file open blocks saving ("NOT SAVED").
- Top/bottom stereo opened as Monoscopic misaligns the regions. Videos wider than 4096 pixels
  play only at normal speed in the tracer.
- The replay draws the shape in the file now; settle shapes before collecting data.
- `sightlab.getRegionOfInterest(name)` returns `None` in 2.9.3 for ROIs the GUI or tracer saves: it
  compares the key's last element, which is the Z scale. Match `key[4]` in
  `sightlab.sceneObjects[REGIONS_OF_INTEREST]` instead, as `moving_rois.py` does.
- The tracer is interactive: a person runs it, or an agent with computer use.

## Shipped examples

`examples/360 Moving Regions of Interest` (`01_Warehouse.avi`, two box regions `Rider1` and `Rider2`
over 15 s, a sample session), `examples/360 non GUI` (360 basics).
