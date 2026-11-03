# The driving simulation

Sources: help.worldviz.com/sightlab driving-example; the earlier assistant's `driving-example.md`.

When to read: the study is a driving task, or wants a vehicle the participant controls.

## What ships

`examples/Driving` (the documentation calls the folder `ExampleScripts-Driving`) is a
complete driving study: a car with gas, brake and steering, Drive and Reverse, animated
gauges and wheels, traffic and pedestrians, collisions, and session replay with the car's
movement.

| Script | Use |
|---|---|
| `Driving_GUI_Main.py` | start here; hardware and environment from the GUI, per-trial traffic from `traffic_config.py` |
| `Driving_Main_noGUI.py` | the same without the GUI; each row of `Resources/stim_file-nonGUI.csv` is one trial and sets its environment |
| `Driving_Server.py` / `Driving_Client.py` | multi-user: one server, one client per driver |
| `Driving_Config.py` | car, viewpoint, collision, driving feel, vibration, hardware mapping (`HARDWARE_CONFIGS`), the `ADD_TRAFFIC` / `ADD_PEDESTRIANS` switches |
| `traffic_config.py` | traffic and pedestrian counts and behaviour |
| `generate_pedestrian_routes.py`, `generate_traffic_network.py` | build routes and a road network for a new environment |
| `modules/driver_data.py` | pedal positions and what the driver looks at, every frame |
| `SightLabVR_Replay.py` | replay, with Follow Mode for the driver's view |

Hardware: keyboard and mouse, Xbox controller, VR controllers, SteamVR wands, and Logitech
or Thrustmaster wheels, each a named hardware configuration chosen in the GUI.

## Data

Per frame: car velocity (`Car Velocity X/Y/Z`, m/s, `Y` up), pedal positions, gaze on the
car's `InstrumentPanel`, `Radio`, `RearViewMirror`, `LeftMirror` and any other registered
object. Per trial: `Average Speed MPH`, crashes, hits and close passes (flagged in the trial
data and counted in the summary), nearest-vehicle distance. BIOPAC markers on collisions when
BIOPAC is on. Per-frame marks in the trial data the usual way, `sightlab.setCustomTrialData(value, 'Column')`; per-trial values with `setExperimentSummaryData`.

## Gotchas

- Write custom data while the trial runs: SightLab saves the trial's files just before it
  sends `TRIAL_END`, so a value set after `yield viztask.waitEvent(TRIAL_END)` never reaches
  that trial.
- Stop the car before toggling Drive and Reverse; each trial starts stationary in Drive.
- `i` recentres the view rotation on the desktop.
- Building a new driving environment means generating a traffic network and pedestrian
  routes for it; budget real time, and say so in the brief's hardware section.

## Shipped examples

`examples/Driving` is the folder described above; further driving demos exist in the
WorldViz demos folder.
