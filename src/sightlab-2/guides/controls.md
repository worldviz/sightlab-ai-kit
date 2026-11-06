# Controls during a session

Sources: `reference/sightlab.py` and the installed `sightlab_utils` (2.9.3): `settings.py` and the
vizconnect files for `Desktop`, `Meta Quest Pro`, `Meta Quest 3`, `Vive Focus Vision`,
`Vive Pro Eye` and `SteamVR`; help.worldviz.com/sightlab controls, vizconnect-events, gui-overview.

When to read: someone asks what a key or button does while an experiment runs; a study adds
its own key or button; instructions or a protocol must tell the participant what to press.
Editor keys are in `guides/first-project.md`, replay keys in `guides/replay.md`, button events
as code in `guides/hardware.md`.

## Who presses what

The researcher, at the PC, starts and ends trials, recentres, toggles overlays and quits. The
participant's trigger (left mouse on `Desktop`) dismisses prompt text, confirms ratings and
grabs; the right thumbstick teleports and turns. The GUI's **Start Text** stays up until the
trial's start condition fires (Space by default), so the researcher moves past it; prompts
passed in code (`startTrialText=...`) wait for `triggerPress` (`guides/instructions.md`).

## Researcher keys (any configuration)

| Key | Does |
|---|---|
| Space | GUI mode: starts, then ends, each trial (the default **Key Press** condition). Code mode: only if the script waits for it |
| `r` | raises `ResetPosition` (keyboard R in every configuration); it recentres only because the script frame wires it to `sightlab.resetViewPoint` (`rules/imports-and-frame.md`) |
| `p` | the gaze point in the participant's own view, on or off (off at start; the mirror shows it) |
| `,` | the gaze-point overlay on the desktop mirror, on or off (`gazepointvisible=False` starts it off) |
| `.` | the HUD (status line, timer, dwell console), on or off |
| `/` | a screenshot of the window into the project's `recordings/` folder |
| `;` | mouse lock: keeps the cursor inside the window |
| Shift+`P` | pauses or resumes the trial's 360 or 180 video |
| Left Shift | GUI mode only: navigation on or off (on `Desktop`, freezes mouse look and, in 3D trials, movement) |
| Tab (hold) | the list of connected clients (multi-user server) |
| `c` | eye-tracker calibration on `Vive Pro Eye`, `Vive Focus 3`, `Vive Tobii`, `Pupil Labs`, `StarVROne`, `PPT HMD` |
| Escape | quits. SightLab registers the running trial's data write to run at exit, but end the trial first when possible |
| F2, F3, F4 | full screen, render mode, frame-rate statistics (Vizard's own keys, per the docs) |

Multi-user server (`Desktop Server`): `u`/`j` forward and back, `h`/`k` left and right, `n`/`b`
up and down, `y`/`i` turn, `o`/`l` look up and down. With Mumble voice chat the server's `m`
mutes and `n` deafens; a client's `m` mutes and `d` deafens (`guides/multi-user.md`).

## The Desktop configuration

Mouse and keyboard stand in for the headset and controllers; the gaze is the view centre.

| Input | Does |
|---|---|
| Mouse movement | looks around |
| `W` `A` `S` `D`, or the arrow keys | move; `X`/`Z` (or Page Up/Page Down) up and down; `Q`/`E` turn |
| Left mouse | `triggerPress` (prompt text, rating confirm, menu buttons) and grab |
| Right mouse | `secondTrigger` (the highlighter, when the script enables it) |
| Scroll wheel | pushes the virtual hand out or pulls it back |
| Left/right arrow | also `pressLeft`/`pressRight`: move the rating-scale choice |
| `m` | `toggleMenu` (VR menu, tablet and flashlight features) |
| `t`, `c`, `g`, `2`, Enter | `t`: `confirmHighlight` and `buttonA`; `c`: `measuringToolStart`, and `triggerDown` while held (`triggerUp` on release); `g`: `measuringToolEnd`; `2`: `triggerDown2`/`triggerUp2`; Enter: `actionButton2` |

## VR controllers

| Action (event) | Quest Pro, Quest 3, Focus Vision | Vive Pro Eye | SteamVR |
|---|---|---|---|
| Prompt text, rating confirm, menu buttons (`triggerPress`) | right trigger | right trigger | right trigger |
| Grab; the left trigger alone also raises `triggerPressLeft` | either trigger | either trigger | either trigger |
| Teleport: hold to aim the arc, release to jump | right stick up | right trackpad click | right trackpad top |
| Snap turn (`SNAP_LEFT`, `SNAP_RIGHT`) | right stick left/right | left grip, right grip | right trackpad left/right |
| Rating choice (`pressLeft`, `pressRight`) | right stick left/right | right trackpad left/right | right trackpad left/right |
| Highlighter (`secondTrigger`, `secondTriggerLeft`) | right, left grip | right, left menu button | right, left grip |
| Push to talk (`triggerDown` held, `triggerUp`) | right grip | right grip | right grip |
| Menu or tablet (`toggleMenu`) | right stick click | left trackpad click | right trackpad click |
| Smooth movement | hold right B + left stick; hold right A + left stick up/down for height | hold left trigger + left trackpad | hold right B + left trackpad; right A + left trackpad up/down for height |
| Recentre (`ResetPosition`) | keyboard `r` | keyboard `r` | keyboard `r` |

Quest Pro, Quest 3 and Focus Vision also map: left stick click `toggleMedia`; left Y/X
`nextModel`/`prevModel`; right B `triggerDown2`; right A `buttonA` (and `actionButton2` on
Quest Pro and Quest 3); right grip + A `ResetPositionHMD`, which nothing in SightLab listens
to. `Meta Quest Pro` only: left grip + right B (`setOpenXRHead`) raises the view 0.7 m for a
seated participant; press again to lower it.

## Adding or changing keys

```python
def markMoment():
    sightlab.setCustomTrialData('marked', 'Researcher Mark')

vizact.onkeydown('k', markMoment)   # a researcher key, live for the whole run

# in the experiment generator: a key for desktop tests or the trigger in the headset
yield viztask.waitAny([viztask.waitKeyDown('k'), viztask.waitEvent(viz.getEventID('triggerPress'))])
```

- Prompt text: `textContinueEvent` (default `'triggerPress'`) chooses the event;
  `textContinueKey` replaces it with a key (`rules/trials-and-instructions.md`).
- Trial start and end key: in GUI mode the condition's **Key Press** value, one character or
  `SPACEBAR`; in code mode the script's own `viztask.waitKeyDown(...)` before `startTrial`
  and `endTrial`.
- `CONTINUE_EVENT_KEY` (`settings.py`, a space) is not the GUI condition key. SightLab uses it
  for `continuekey=True` (GUI mode only: the key also starts and ends every trial whatever the
  condition, for example to end a timed trial early; ignored while prompt text is up) and for
  the wait after each trial with `gazepathvisible=True` (the scan path stays until pressed).
  Do not edit `settings.py`.
- 360 and 180 helpers bind keys on request (the arguments are the keys):
  `sightlab.enableTransportToggleKey('y')`, `sightlab.enableEnvironmentNudgeKeys(']', '[')`,
  `sightlab.enableEnvironmentVerticalKeys('0', '9')`, `sightlab.enableEnvironmentPitchKeys('7', '8')`,
  `sightlab.enableMediaSkipKeys('v', 'c')`.
- Controller buttons are mapped in the vizconnect file: change a copy loaded from the script
  (`guides/hardware.md`), never the installed file.

## Keys already taken

- Always: the researcher keys above; Left Shift in GUI mode. `Desktop` adds every key and
  mouse input in its table; the eye-tracker configurations listed above add `c`.
- Multi-user scripts: the server navigation and Mumble keys. Any `enable...Keys` helper the
  script calls, and any key the example the study was copied from binds (read its script).
- GUI mode: once regions of interest were edited in the editor, `i j k l u o f g h` (and
  Shift+`F` `G` `H`) stay bound to the region nudge functions for the rest of that run.
- Keys are case-sensitive: `'p'` and `'P'` (Shift+P) are separate bindings.

## Gotchas

- `r` does nothing in a script that leaves out the `ResetPosition` callback line.
- One input, two events: on Quest Pro, Quest 3 and Focus Vision the right stick left/right is
  both snap turn and `pressLeft`/`pressRight`; on Vive Pro Eye the right grip is both snap
  turn and `triggerDown`; on `Desktop` the left/right arrows both move the view and raise
  `pressLeft`/`pressRight`. A script using those for its own responses also moves the view.
- SightLab's rating scale sets and then clears `viz.callback` on `triggerPress`, `pressLeft`
  and `pressRight`; the docs advise `triggerPress2` or `triggerPress3` for a second listener.
  For a study's own responses prefer `viztask.waitEvent` or `vizact.addCallback`.
- Text that names a control must match the hardware ("press the trigger", "click", the key).

Shipped examples: `examples/ToggleMenu`, `examples/3D Tablet Menu`, `examples/Selector Tool`,
`examples/MeasuringTape`, `examples/Instructions`.
