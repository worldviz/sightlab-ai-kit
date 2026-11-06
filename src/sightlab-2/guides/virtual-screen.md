# Virtual screens: 2D video and images inside VR

Sources: help.worldviz.com/sightlab virtual-screen and virtual-screencasting; the earlier assistant's `virtual-screen.md`.

When to read: the stimuli are videos, slides or images shown on a screen in the scene
(a cinema, a monitor, a picture frame), with gaze recorded on regions of the screen.

## The shipped example

`examples/Virtual 2D Screen` is the base. Its scripts:

| Script | Use |
|---|---|
| `2D_Screen.py` | a flat screen in the chosen environment showing one video |
| `3D_Screen.py` | the same with a stereoscopic video |
| `Video_Player.py` | a screen the participant can grab and move (trigger), resize (`m`/`n`) and whose position `t` prints for use in code |
| `Video_Player_STIM_File.py` | one video per trial from a STIM file |
| `2D_Screen_GUI.py`, `Video_Player_GUI.py` | GUI-mode variants |
| `Cycle Videos/` | several videos in sequence via `media_player.VideoPlayer(screen=..., video_directory=...)` |
| `*_replay.py` | replays with the video synchronised |

Settings live in `VideoScreenConfig.py` (and `VideoScreenConfig2.py` for the STIM variant):
environment (an `empty` one for mixed reality), `VIDEO_TYPE` (`"Mono"` or `"Stereo"`),
`STEREO_VIDEO_FORMAT` (`"Top_Bottom"` or `"Left_Right"`), the media path or a folder, and the
keys: `VIDEO_PLAYBACK_KEY = "v"` (pause/play), `VIDEO_RESET_KEY = "k"`, `NEXT_VIDEO_KEY = "c"`.

## Running a session

The space bar or the right trigger starts the video and the data recording together; `v`
pauses; `k` restarts; `r` recentres the view; the highlighter tool (right grip, then trigger)
also plays. Data goes to the standard `data/` folder; the replay script plays the session
with the video.

## Gaze on the screen

Register regions of the screen (or the whole screen) with `addSceneObject(..., gaze=True)`,
including region nodes (not `addRegionOfInterest`, which records nothing in 2.9.3), so dwell
and fixation data exist per region.
Shipped videos for testing: `sightlab_resources/media_2D/`.

## Gotchas

- Vizard plays common MP4s; 8K and some stereo formats need the extra codec package that
  WorldViz provides separately.
- Starting the video with the space bar is what starts the trial's recording in these
  examples; a study that starts trials differently must call `startTrial` itself.
- Two screens or video plus a 3D task: copy the screen set-up from `Video_Player.py` into the
  frame rather than running two examples at once.

## Shipped examples

`examples/Virtual 2D Screen`, `examples/Virtual_Screencast` (mirroring a desktop window into
VR), `examples/Image_Viewer`.
