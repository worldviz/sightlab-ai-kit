# External Data Recorder

Sources: the earlier assistant's `external-application-data-recorder.md` and `New-External-Data Recorder 2.0 guide.md`; help.worldviz.com/sightlab external-data-networking.

When to read: the participant uses an application that is not a SightLab scene (a SteamVR
game, an Unreal or Unity build, a desktop program, a standalone headset app) and the
researcher still wants eye tracking, physiology and events recorded and replayable.

## What it does

It records the headset's mirror window (or an app window) as video while SightLab records
eye tracking, BIOPAC and event data on the same timeline, then lets you replay the video
with the gaze point and heatmaps on it. The shipped folder, `examples/External Data Recorder 2`,
is the 2.0 line: it records through OBS, runs AI object detection over every frame
(`Postprocessor.py`, `Postprocess_Config.py`), supports cropping, and can reprocess old
sessions. The recording set-up (OBS and its WebSocket service, the detection models) is done
by a person following the SightLab documentation, not by the agent.

Flow: choose the window and hardware → calibrate gaze onto the window's pixels
(`Eye_Calibration.py`) → record for a set number of seconds (space bar starts) → postprocess
→ data files, videos and replay (`External_Data_Replay.py` or the Dashboard's Replay).

## Configuration, not code

The recorder is configured in `Data_Recorder_Config.py` (recording length, participant,
BIOPAC and network sync, replay calibration, timers) and, for 2.0, `Postprocess_Config.py`
(detection model, classes as plain phrases, thresholds). An agent helping with it edits those
files and explains them; it does not write a SightLab experiment script.

## Network events from the external app

The external application can send named events over the network (UDP/TCP as configured) that
the recorder logs with timestamps and forwards to BIOPAC as markers: enable network control in
`Data_Recorder_Config.py`, set the port, and list the event names the app sends. The app side
is a few lines in any language; the names must match exactly.

## Outputs

`data/`: gaze CSV, fixations and saccades, events, custom markers, face tracking where the
headset has it, and (2.0) gaze on detected objects. `recordings/`: the original video, a
transcoded copy for the replay, and (2.0) an overlay video with detections and the gaze point.

## Gotchas

- Calibration is per window size and position; the same window must be used for the
  recording, or the gaze mapping is off.
- Standalone headset apps (Quest) need the headset's mirror on the desktop; the hardware
  guides list which configurations have real eye tracking and which use the view centre.
- The 2.0 beta needs extra packages and OBS set up by a person; that is WorldViz support's
  job, not the agent's.
- BIOPAC synchronisation here uses the same NDT link as a SightLab experiment
  (`patterns/biopac-markers.md`).

## Shipped examples

`examples/External Data Recorder 2`, `examples/Screen Based Eyetrackers`,
`examples/AI_AR_Object_Detection`.
