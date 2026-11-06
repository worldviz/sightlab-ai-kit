# Full-body avatars (the participant's own body)

Sources: `sightlab_utils` 2.9.3 (`reference/sightlab.py`, `settings.py`, the full-body files in
`vizconnect_configs/`, `body_tracking_ik.py`, `body_tracking_metrics.py`, `custom_skeletons.py`,
`Avatar_Body_MultiUser_IK.py`, `replay.py`, `mirror.py`); help.worldviz.com/sightlab
full-body-avatars, body-tracking-metrics, foot-tracking, hand-tracking-grabbing-and-physics.

When to read: the participant sees their own body (looking down, in a mirror, or as others see
them in multi-user); the study names Vive trackers, Mocopi, OptiTrack or Meta body tracking; the
data needs tracker poses or body movement metrics. Agents and NPCs are a different topic.

## Turning it on

- GUI (single-user, and each multi-user client): in the Avatar section tick **Full Body** and pick
  an avatar beside it (the files in
  `C:\Program Files\WorldViz\Sightlab2\sightlab_resources\avatar\TrackedAvatars`). This empties the
  head and hand models, enables **Seated**, and switches the hardware list to the full-body
  configurations. On a client, Full Body and **Auto Assign** exclude each other. The server GUI
  has no Avatar section: each client chooses its own body.
- Code: the constructor arguments stand for the checkbox and the list.

```python
AVATAR = r'C:\Program Files\WorldViz\Sightlab2\sightlab_resources\avatar\TrackedAvatars\RocketBox_Female1.osgb'
sightlab = sl.SightLab(gui=False, fullbodyavatar=AVATAR)   # client: sl.SightLabClient(..., fullbodyavatar=AVATAR)
```

- Defaults: `fullbody=False`, `fullbodyavatar=None`. A path turns full body on by itself;
  `fullbody=True` alone, in code mode, loads `WV_Mark.osgb` (`AVATAR_MODEL` in
  `sightlab_utils/AvatarMultiUserConfig.py`).
- With `gui=False` and none of `hardwareconfig`, `vizconnectconfig`, `vizconnectconfiglist`, the
  start-up chooser lists `FULL_BODY_VIZCONNECT_CONFIG_LIST`. Passing any of the three skips that
  switch, so name full-body configurations there (`hardwareconfig='Vive Trackers Full Body'`):
  only the full-body files load the avatar file; a head-and-hands name ignores it.
- The body is set up when the first trial loads, so code that touches it
  (`vizconnect.getAvatar('main_avatar').getRaw()`, a mirror) goes after the first
  `yield sightlab.startTrial()`. The code-mode examples also set both hand models to
  `AVATAR_HANDS_RESOURCE_PATH + '/empty.osgb'` there (`sightlab.setAvatarLeftHand(...)` and the
  right-hand twin), so controller models do not cover the hands.

## Hardware: the full-body configuration names

Exact `VIZCONNECT_DICT` keys (how names are used: `guides/hardware.md`).

| Name | Headset and runtime | What moves the body |
|---|---|---|
| `Desktop Full Body` | mouse and keyboard | IK from the simulated head and right hand |
| `Meta Full Body` | Meta PC runtime (`oculus`) | IK from headset and both controllers: upper body, legs keep their pose |
| `Vive Focus Full Body` | OpenXR | same IK |
| `SteamVR Full Body` | SteamVR | same IK |
| `Meta Quest Pro Full Body`, `Meta Quest 3 Full Body` | OpenXR | Meta body tracking (`getBodyTrackerFB`) poses the bones; Vizard exits with "OpenXR runtime does not support FB body tracking" without it |
| `Pimax Full Body` | OpenXR, same file as `Meta Quest Pro Full Body` | see Gotchas |
| `Vive Trackers Full Body` | SteamVR headset, controllers, 3 trackers | IK from head, hands, pelvis and both feet |
| `Vive Trackers Full Body Focus Vision` | OpenXR headset and controllers, 3 SteamVR trackers | same |
| `Mocopi Full Body`, `Mocopi Full Body Quest 3` | OpenXR headset and controllers, Mocopi as 3 SteamVR trackers | same |
| `Optitrack Full Body` | SteamVR display, every body part from Motive | IK from head, hands, forearms, pelvis and feet |

- Trackers are taken by position in SteamVR's tracker list, not by role: 0 pelvis, 1 left foot,
  2 right foot. A missing one logs "Not able to connect to tracker at index N" and an empty
  placeholder stands in. No Vive or Mocopi file uses chest or elbow trackers. Mocopi's sensors reach
  SightLab through its SteamVR application (set up by a person following the documentation).
- OptiTrack: Motive on `localhost` and a skeleton named `Anthony` (`Anthony_Head`, `Anthony_Hips`,
  ...) are fixed in the file; another name or Motive PC needs a custom copy (`guides/hardware.md`).
- Fingers: the IK files (not OptiTrack) curl Mixamo and ReadyPlayerMe fingers on the trigger. Hand
  tracking (`Meta Pro Hand`, `Meta Quest 3 Hand`, `Focus Vision Hand`) and Manus gloves
  (`Manus OpenXR`, `Manus SteamVR`, `Manus head and hands`) are head-and-hands configurations.
  Feet without a body: `examples/Foot_Tracking`.

## Which avatars work

- Shipped in `TrackedAvatars`: `RocketBox_Female1.osgb`, `RocketBox_Female2.osgb`,
  `RocketBox_Male1.osgb`, `RocketBox_Male2.osgb`, `RocketBox_Male3.osgb`, `WV_Mark.osgb`
  (Complete Characters, `Bip01` bones) and `z_ReadyPlayerMe_Female.osgb` (ReadyPlayerMe).
- The rig is recognised by bone name: `Bip01 Pelvis` Complete Characters; `Hips` Mixamo or
  ReadyPlayerMe (`custom_skeletons.Mixamo`); `Hip` or `CC_Base_Waist` Reallusion. Anything else
  falls back to the Complete Characters skeleton. SightLab turns lighting off on Complete
  Characters avatars.
- Docs: Mixamo, ReadyPlayerMe and Reallusion work with head-and-controller IK and Meta body
  tracking; lower-body trackers are tested with Complete Characters only, and
  `Optitrack Full Body` always builds the Complete Characters skeleton.
- A custom rigged avatar placed in `TrackedAvatars` appears in the GUI list; code takes any path.

## Seated, head-only, calibration

- **Seated** in the GUI or `sightlab.setSeatedMode(True)`: the legs are locked in a sitting pose
  every frame while head and hands move; with Complete Characters it also lowers the view 0.35 m.
- `sightlab.setSeatedModeHeadOnly(True, mode='default')` locks everything below the neck (arms at
  the sides, `mode='coaster'` raises them) and turns seated on; pass `transport_euler=[180, 0, 0]`
  when the transport is turned so the arms face the right way.
- No T-pose or height calibration in 2.9.3 (the multi-user one is disabled in the code): the
  avatar keeps its own proportions. A body that floats or sinks means the headset's floor height
  is wrong; redo its room setup (docs).

## Multi-user

- Each client ticks Full Body or passes `fullbody`/`fullbodyavatar` to `sl.SightLabClient(...)`;
  clients without it still see the others' bodies. The rest is in `guides/multi-user.md`.
- The server and other clients load a client's body from the file path that client sends: a
  custom avatar must exist at the same path on every PC.

## Data

The usual files are written (`rules/gaze-objects-and-data.md`); body joints are not.
`sightlab_utils.body_tracking_metrics` adds tracker and hand poses and movement metrics:

```python
import sightlab_utils.body_tracking_metrics as btm
bodyTracking = btm.BodyTracking(sightlab, noTrackerConfigs=['Desktop', 'Desktop Full Body'])

def sightLabExperiment():
    yield viztask.waitEvent(EXPERIMENT_START)
    for trial in range(sightlab.getTrialCount()):
        yield viztask.waitKeyDown(' ')
        bodyTracking.addTrialDataColumns()   # before startTrial: registers tracker columns
        yield sightlab.startTrial()
        bodyTracking.start()                 # after startTrial and the hand models
        yield viztask.waitKeyDown(' ')
        bodyTracking.stop()                  # before endTrial: closes the metrics file
        yield sightlab.endTrial()
```

- `trial_data` gains `Tracker1 x` ... `Tracker1 roll` (x, y, z, yaw, pitch, roll) for the first
  `trackerCount` (3) SteamVR trackers, and `RHand X`, `RHand Y`, `RHand Z`, `RHand Yaw`,
  `RHand Pitch`, `RHand Roll` and the same for `LHand`.
- `body_metrics/<date>_<pid>_body_metrics_<trial>.csv` (`..._combined.csv` when COMBINED):
  `p_id`, `date/time`, `trial number`, `timestamp (secs)`, then per body (`Tracker1`..., `Head`,
  `RHand`, `LHand`) `<body> speed (m/s)`, `accel (m/s^2)`, `ang speed (deg/s)`,
  `ang accel (deg/s^2)`, `path length (m)`, `state` (`Active` from `idleThreshold` 0.05 m/s or
  `angularIdleThreshold` 5 deg/s, else `Idle`).
- SteamVR trackers are read on every configuration not in `noTrackerConfigs` (default
  `('Desktop',)`). `saveTrialData=False` or `bodyMetrics=False` turns a half off.

## Replay, playback, mirror

- The replay does not show the body: a stand-in head and controllers replace the empty models.
  `examples/Avatar_Playback` plays back head, hands and voice only. The docs' motion-capture
  section is about making animations for agents with outside tools.
- Mirror, after `startTrial()`: `from sightlab_utils.mirror import placeMirror`, then
  `placeMirror(env, 'mirror', fallback_pos=[0, 1.8, 1])` fits it to the environment node `mirror`,
  else a 1 m quad at `fallback_pos`. It adds a 2048 x 1024 render pass per eye.

## Gotchas

- Keys taken: `Mocopi Full Body` turns on debug keys (1 to 8, m, n, b, j, k, l and capitals, p,
  0; off in the Quest 3 variant). Multi-user: F9 and F10 everywhere, and on the server F11, 1 to
  6, `;` `,` `.` `-` `=` `/` `[` `]`. Meta body tracking binds `j`.
- Mixamo, ReadyPlayerMe and Reallusion wrists stay at rest (`LOCK_WRISTS = True` in
  `custom_skeletons.py`): hands follow controller position, not wrist twist.
- `Pimax Full Body` shares the file of `Meta Quest Pro Full Body` (whose own avatar is a hidden
  placeholder), but SightLab starts body tracking only for the two Meta names: confirm a body
  appears before relying on it.
- The autopilot runs `Desktop` (`guides/hardware.md`); the body, its tracking and the frame rate
  (mirror, several bodies, per-frame metrics) are checked by a person on the hardware.

## Shipped examples

`examples/ViveTrackers` (`ViveTrackers_FullBody.py`: code mode, metrics, mirror; and a GUI
version), `examples/HandPath_Tracking` (metrics for hands), `examples/Hand_Tracking_Grabbing_Physics`
(`Hand_Grabbing_Physics_Full_Body_Meta.py` reads finger joints from Meta body tracking),
`examples/Foot_Tracking`, `examples/Mirror_Demo`, `examples/Avatar_Playback`. Older approaches:
`examples/Meta_Pro_Full_Body` (imports `sightlab_utils.body_tracking`, which asks for a model from
`avatar/full_body`) and `examples/Seated_or_Standing_Avatar_Body` (bones locked by hand).
