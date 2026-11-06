# Hardware configurations

Sources: `sightlab_utils/settings.py` (`VIZCONNECT_DICT`, `DEFAULT_VIZCONNECT_CONFIG_LIST`) and
`reference/sightlab.py` (2.9.3); help.worldviz.com/sightlab vizconnect-events, openxr,
mixed-reality.

When to read: the study names a headset, eye tracker, controller or tracker; a script picks
the hardware in code; a response comes from a controller button; or the data must contain
pupil size.

## Choosing the configuration

A configuration is a vizconnect file in `sightlab_utils/vizconnect_configs/`, looked up by
name in `VIZCONNECT_DICT`. In GUI mode the researcher picks it in the GUI. In code mode:

- `sl.SightLab(gui=False)` without `hardwareconfig` opens a chooser at start, listing
  `VIZCONNECT_CONFIG_LIST` (by default `DEFAULT_VIZCONNECT_CONFIG_LIST` in `settings.py`).
- `hardwareconfig='Meta Quest Pro'` skips the chooser. The name must be a key of
  `VIZCONNECT_DICT` exactly, spaces and case included; otherwise SightLab shows "Hardware
  config not found" and Vizard quits. Some documentation uses short names ("Quest Pro",
  "Omnicept", "OpenXR Generic") that are not keys. Read the installed `settings.py` for the
  list (about 90 names in 2.9.3: `Meta Quest Pro`, `HP Omnicept`, `Omnicept OpenXR`,
  `OpenXR EyeTR`, `OpenXR NoEyeTR`, `Vive Focus Vision`, `Varjo`, `Pimax Dream Air`, ...).
- `vizconnectconfiglist=['Desktop', 'Meta Quest Pro']` limits the chooser to those names.
- `vizconnectconfig={'My Rig': 'D:/rigs/my_rig.py'}` replaces the table for this script (the
  chooser lists its names); `vizconnectconfig=['My Rig', 'D:/rigs/my_rig.py']` loads that file
  with no chooser.
- `sightlab.getConfig()` returns the name in use; branch on it for headset-specific
  behaviour.
- `'Desktop'` is mouse and keyboard, for development. The autopilot forces it
  (`hardwareconfig='Desktop'`) for its run only; the script keeps its own setting.

## Eye tracking and pupil data depend on the name

- Configurations for headsets without an eye tracker (`Desktop`, `Meta Quest 3`,
  `Meta No Eyetracker`, `OpenXR NoEyeTR`, ...) record the view direction as the gaze. Label
  such data head-direction, never eye tracking.
- The trial data gets `pupil diameter`, `pupil diameter L` and `pupil diameter R` only when
  the configuration name is one of `Vive Pro Eye`, `Pupil Labs Neon Quest 3`, `HP Omnicept`,
  `StarVROne`, `Vive Tobii`, `Vive Focus 3`, `Vive Focus Vision`, or `Steamlink` with eye data
  (`writeTrialData` in `reference/sightlab.py`). The same list, minus `Vive Tobii` and
  `StarVROne`, also gets `eye open`, `eye open L` and `eye open R`.
- So `Meta Quest Pro`, `Varjo`, `Pimax Dream Air` and the OpenXR configurations write no pupil
  columns, and a custom configuration name loses them even on a headset that has them. A
  brief that needs pupil size must name a configuration on that list.

## Controller buttons are events

Each vizconnect file names its own events (`_name = 'triggerPress'` in the file); which
physical button raises which, per headset, is in `guides/controls.md`. A tracked full body
is `guides/full-body-avatars.md`. Wait for one, or call back on it:

```python
yield viztask.waitEvent(viz.getEventID('triggerPress'))
viz.callback(viz.getEventID('pressRight'), onRight)
```

How many of the 66 configuration files that `VIZCONNECT_DICT` names define each event in
2.9.3: `triggerPress` 59, `ResetPosition` 56, `pressLeft` and `pressRight` 55,
`secondTrigger` 49, `toggleMenu` 48, `triggerPressLeft` 33, `triggerDown` and `triggerUp` 28,
`actionButton2` 15. On `Desktop`, `triggerPress` is the left mouse button and
`secondTrigger` the right. Before relying on anything but `triggerPress`, read the
configuration file the study will use and confirm the event is there.

## A custom vizconnect file

SightLab reaches the hardware by name. A custom file must keep `main_display`,
`main_avatar`, `main_transport`, and the trackers `head_tracker`, `eye_tracker`,
`r_hand_tracker`, `l_hand_tracker` and `merged`; copying the closest shipped configuration
and changing only the devices keeps them. Load it with `vizconnectconfig=[name, path]`.

## Mixed reality

`sightlab.setPassthrough(True)` turns on OpenXR colour passthrough on a headset that has it;
`enableMixedReality(...)` adds a chroma key; `examples/MixedReality` is the shipped example.
Neither can be checked by the autopilot.

## Gotchas

- A study built and tested on `Desktop` still needs a run on the named headset: the event
  names, tracking and eye data are only known there.
- Steamlink's gaze depends on the headset it streams from (Quest 3 has no eye tracker, so it
  is head direction).
- Do not edit `settings.py` to add a configuration; pass `vizconnectconfig` from the script
  (`rules/imports-and-frame.md`).
