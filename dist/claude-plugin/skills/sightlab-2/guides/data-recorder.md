# External Data Recorder

Sources: `examples/External Data Recorder 2` (`External_Data_Recorder.py` "Version: 2.0" and its
config, calibration, postprocessing and replay scripts); help.worldviz.com/sightlab
external-data-recorder and its sub-pages. Where they disagree, this guide follows the code.

When to read: the participant uses an application that is not a SightLab scene (a SteamVR or
OpenXR game, a Unity or Unreal build, web VR, a standalone headset app cast to the PC, a
desktop program) and the researcher still wants eye tracking, physiology and events recorded
and replayable.

## Recorder or SightLab scene

The recorder only sees the window it records: gaze is a 2D point on the video, objects come
from AI detection after the session, and depth and head pose are not recorded. Use it when the
stimulus is someone else's application. Content that can be built or loaded in SightLab is
better as a scene (gaze on named 3D objects, head tracking, 3D replay); a window or video shown
inside VR is `guides/virtual-screen.md`, live detection in a trial `guides/object-detection.md`.

It is configured, not programmed: an agent edits and explains `Data_Recorder_Config.py` and
`Postprocess_Config.py`. Setup (Python packages with PyTorch, OBS Studio with its WebSocket
server on port 4455 and authentication off, the SRanipal driver for Vive) is done by a person
with the installer in the example's `installer` folder or the Setup section of the documentation.

## How a 2.0 session runs

1. `External_Data_Recorder.py` (Dashboard: Tools/Features > External Data Recorder 2.0) opens a
   console (Alt+Tab to it for progress) and OBS if it is not running, asks for the hardware,
   then the window to record: the headset's mirror (SteamVR `VR View`, Oculus Mirror,
   `Pimax Mirror - Right`, a browser casting tab) or the desktop app.
2. Eye-tracked configurations calibrate (*New* or an old file): `Eye_Calibration.py` runs in the
   headset, 9 dots located in the mirror by their red pixels, then 5 validation dots scored in
   degrees, up to 3 rounds (`a` accepts a failing one). Others write a stand-in calibration.
3. Prompts: seconds to record (default 10); for `Meta Quest Pro` and `Pimax Dream Air` the
   external app's window (focused at trial start); the participant form; an LSL stream.
4. Space (or a network start) begins the trial: OBS records the window's client area at
   `TARGET_FPS`, SightLab records eye data each frame, and a live copy of the window shows the
   gaze (`REAL_TIME_STREAMING`). The timer ends it; space ends it early.
5. With `AUTO_POSTPROCESS`, `Postprocessor.py` aligns frames to gaze, detects objects and writes
   the CSVs and videos.

## Choosing the hardware configuration

Names are the recorder's own `HARDWARE_CONFIGS` keys, not SightLab's (`guides/hardware.md`); most
point at a desktop vizconnect file so the external app keeps the headset. Pages are under
help.worldviz.com/sightlab/external-data-recorder/.

| Headset or setup | Configuration | Page | Gaze recorded |
|---|---|---|---|
| Vive Focus Vision, Focus 3, Pro Eye, wired (SRanipal) | `Vive Focus Vision Recorder`, `Vive Focus 3 Recorder`, `Vive Pro Eye` | vive_guide | eye; openness, `Pupil Data` |
| Meta Quest Pro over Meta Horizon Link | `Meta Quest Pro` | meta-guide | eye (OpenXR) |
| Quest Pro, Vive Focus Vision, Steam Frame over Steam Link | `Steamlink` | steam_link_guide | eye (OSC, `STEAMLINK_OSC_PORT` 9000); openness |
| Pimax Dream Air | `Pimax Dream Air` | pimax_dream_air_guide | eye (Tobii stream) |
| Quest 3, 3S, 2 (Link, Steam Link, or casting a standalone app) | `Meta Quest 3 Recorder` | meta-guide, steam_link_guide, meta_hmd_standalone_app_guide | centre of view |
| Desktop app with a free mouse | `Desktop` | desktop_and_desktop_fps_guide | mouse cursor |
| Desktop first-person game | `Desktop First Person Game` | desktop_and_desktop_fps_guide | centre of screen |
| HP Omnicept, Varjo, other OpenXR | `Omnicept Recorder`, `Varjo`, `OpenXR Recorder` | none yet | see Gotchas |

Label centre-of-view and mouse data as such, never as eye tracking. Screen-based trackers
(EyeLogic, Tobii Spark) use a separate 1.0-based recorder (screen_based_eyetrackers_guide).

## Scripts and Dashboard actions

Dashboard buttons: **Run: External Data Recorder**; **Replay** (`External_Data_Replay.py`);
**Postprocessor** (`Postprocessor.py`); **Config** and **Postprocess Config**; **SRAnipal
EyeTrackerTest** (checks Vive eye data and can start SRanipal; close it before recording). From
Vizard only: `Eye_Calibration.py` (calibration alone, saved as
`<datetime>_standalone_eye_calibration.json`), `Pimax_Gaze_Probe.py`, `Steamlink_Gaze.py`.

## Configuration keys that matter (defaults from the code)

`Data_Recorder_Config.py`: `PID` True, `DEFAULT_PARTICIPANT_ID` "0", `SET_NUMBER_OF_TRIALS` 1,
`TRIAL_CONDITION` 'A' (label), `USE_TIMER` True, `DEFAULT_TIMER_LENGTH` 10, `PLAY_END_SOUND` True,
`RECORD_VIDEO` True, `TARGET_FPS` 60, `AUTO_POSTPROCESS` True, `BIOPAC_ON` True, `SAVE_LSL_DATA`
True, `RECORD_FACE_TRACKER_DATA` False, `LOCK_TRANSPORT` True, `RUN_CALIBRATION` True,
`MIRROR_EYE` `viz.RIGHT_EYE`, `DOT_EXTENT_DEG` (18, 12) ((18, 24) for Quest Pro), `FOCUS_SIZE`
[2,2,2], `VALIDATION_MAX_MEAN_DEG` 2.0, `POST_EXPERIMENT_VALIDATION` False.
`Postprocess_Config.py`: `USE_OBJECT_DETECTION` True, `USE_OVD` False, `CONFIDENCE_THRESHOLD`
0.5, `BANNED_CLASSES` `set()`, `MAX_BOX_AREA_FRACTION` 1.00, `USE_FP16` False, `DWELL_THRESHOLD`
0.5, `DWELL_GRACE_S` 0.1, `INTERACTIVE` True, `TRIAL_NUM` 1.

## Network events from the external app

All of this needs `USE_NETWORK_EVENT = True`. The recorder opens Vizard's UDP network
(`viz.addNetwork(NETWORK_HOST)`) on `NETWORK_PORT` (defaults `'localhost'`, 4950), sends to it
and listens on it. The app sends one UTF-8 JSON object per datagram:
`{"event": "start_trial"}` or `{"event": "sync"}`.

- `start_trial` (`NETWORK_START_EVENT_NAME`) starts the trial only with `NETWORK_START = True`
  and only while the recorder waits (it is not queued); reply `{"event": "ack_start", "trial": <n>}`.
- `sync`, the `t` key (`NETWORK_SYNC_KEY`) and `triggerPress` (`NETWORK_SYNC_EVENT`) write
  `key pressed` in `Sync Event` and a `sync event` BIOPAC marker; the key and event also send
  `{"src": "vizard", "event": "sync", "t": <secs>, "trial": <n>, "label": <TRIAL_CONDITION>}`.
- Other JSON is only printed; there is no network stop. To save other events, add a branch in
  `onNetwork` that calls `sightlab.setCustomTrialData(value, 'Column')`.

## Outputs and data files

`<id>` is `<date>-<time>_<participant>` (e.g. `09-26-2026-09-32-04_0`), `<n>` the trial.

- `data/<id>_experiment_data/trial_data/`: `<id>_trial_data_<n>.csv` with the recorder's columns
  (`Right/Left/Both Eye Tracker Matrix` and `Tracker ... Eye Yaw/Pitch`, or `Stand-in Eye Tracker
  Matrix`; `Pupil Data`, `Eye OpenL/R/Both`, `Heart Rate` where the hardware has them; `Sync
  Event`; `LSL Data`; `Recording Offset`), the fixation-saccade timeline, and from postprocessing
  `<id>_obj_det_timeline_trial_<n>.csv` (per frame), `_obj_det_summary_` (per tracked object),
  `_class_det_summary_` (per class). Beside it `replay_data/` (`.rply`) and `config.json`.
- `recordings/`: `<id>_experiment_data_trial_<n>.avi` (OBS original), `_transcoded_` (for the
  replay), `_overlay_` (boxes and gaze drawn). `calibration_data/<id>_eye_calibration_trial_1.json`
  (accuracy in degrees); `logs/<id>_logfile.txt`; `data/expressions_<time>.csv` (face tracking).
- `Frame PTS Timestamp` (video time + `Recording Offset`) equals `timestamp (secs)` in the trial
  data. SightLab's dwell, intersect and head columns do not apply to external apps.

## Postprocessing: AI object detection on the recording

- Not the live YOLOX detector of `guides/object-detection.md`: RT-DETRv2 (the 80 COCO classes)
  or, with `USE_OVD = True`, OmDet-Turbo (`OVD_CLASSES` as plain phrases, optional `OVD_TASK`),
  ByteTrack ids, every frame, on a CUDA GPU.
- Gaze goes to the smallest box holding it, else to a near miss within the calibration's
  validation `rms_deg`. A dwell counts after `DWELL_THRESHOLD` s; gaps up to `DWELL_GRACE_S`
  do not split it.
- `Desktop First Person Game` and `Meta Quest 3 Recorder` with `INTERACTIVE = True`: a person
  crops the video (`c` corners, `a` accept, `t` reset, `r` redo) and places the centre point
  (arrows or `c`, then `a`); saved and reused. Otherwise `CROP_REGION`, `CENTERPOINT_POSITION`.
- Reprocess: set `EXPERIMENT_ID`, `CALIBRATION_ID` (the session ID, or `<datetime>_standalone`)
  and `TRIAL_NUM` in `Postprocess_Config.py`, run `Postprocessor.py`; outputs are overwritten.

## Session replay

`External_Data_Replay.py` uses SightLab's replay (`guides/replay.md`) in desktop view: pick the
session, the calibration (*Same as video* if calibrated in that session or not calibrated) and
the overlay or transcoded video. The video plays on a head-locked screen with the gaze point
projected on it (hidden for the overlay video, which has its own); `t` switches videos;
scrubbing also moves AcqKnowledge. `REPLAY_SCREEN_FOV_OVERRIDE_DEG` resizes uncalibrated ones.

## BIOPAC and LSL

- `BIOPAC_ON = True` passes `biopac=True` to SightLab (trial markers, `patterns/biopac-markers.md`);
  the recorder adds `video start` when recording begins and `sync event` on each sync. Signals
  stay in AcqKnowledge: the script's channel-saving block is off and marked unfinished.
- `SAVE_LSL_DATA = True`: each trial lists the LSL streams and asks which to record; each frame
  writes the latest sample to `LSL Data` and `LSL Timestamp`.

## Limitations

2D only (gaze in video pixels, no depth, no head position or rotation); headset apps go through
a mirror window kept at the calibrated size; dialogs, calibration and cropping need a person, so
the autopilot cannot run the recorder.

## Gotchas

- Never minimize the recorded window (covering it is fine); `MIRROR_EYE` must match the eye the
  mirror shows. A size change while recording is printed as "CALIBRATION INVALIDATED".
- `USE_TIMER = False` also needs `PLAY_END_SOUND = False`: the key wait is the sound's `else`
  branch, so with the sound on the trial ends at once.
- `RUN_CALIBRATION = False` on an eye-tracked configuration writes a stand-in calibration that
  reads `Stand-in Eye Tracker Matrix`, written only by the no-eye-tracker configurations, so
  postprocessing finds no gaze. For a Quest Pro casting a standalone app use `Meta Quest 3 Recorder`.
- `Omnicept Recorder`, `Varjo` and `OpenXR Recorder` write no `<eye> Eye Tracker Matrix` column
  in 2.0, so postprocessing has no gaze; `Stand-Alone`, also in the table, is unfinished.
- Calibration takes the headset: on single-app runtimes (Pimax, SteamVR) reopen the external app
  afterwards. An old calibration after the headset moved costs accuracy.
- The recorder leaves OBS's record folder, canvas size and frame rate changed.
- Postprocessing calls `ffmpeg` and `ffprobe` from the PATH, which the documentation does not
  mention; if it stops at "Probing for video information", a person checks they are installed.
- SightLab's pupil columns follow its own names (`guides/hardware.md`); use the recorder's
  `Pupil Data` (real on Omnicept and Vive Pro Eye; Focus Vision reads 0, per the docs).

## Shipped examples

`examples/External Data Recorder 2` (Dashboard title "External Data Recorder 2.0"). Related:
`examples/AI_AR_Object_Detection` (live detection on another app's window),
`examples/Virtual_Screencast` (a desktop window in a SightLab scene), `examples/LSL_Sample`,
`examples/Biopac Saving to Data Files`, `examples/Face_Tracking_Data` (charts of the
expressions file). `examples/Screen Based Eyetrackers` is a SightLab scene, not the recorder.
