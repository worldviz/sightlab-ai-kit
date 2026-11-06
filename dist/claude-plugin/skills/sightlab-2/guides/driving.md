# The driving simulation

Sources: the Driving example's code (`Driving_GUI_Main.py`, `Driving_Main_noGUI.py`,
`Driving_Server.py`, `Driving_Client.py`, `Driving_Config.py`, `traffic_config.py`, `modules/`,
`vizconnect_configs/`, `SightLabVR_Replay.py`, `Resources/traffic/README.txt`);
`sightlab_utils/settings.py` and `sightlab.py` (2.9.3); help.worldviz.com/sightlab driving-example.

When to read: the study is a driving task, wants a vehicle the participant controls, or starts
from the driving example.

## What ships

`examples/Driving` (the documentation calls the folder `ExampleScripts-Driving`): a car with gas,
brake, steering, Drive and Reverse, gauges, working mirrors and headlights; traffic and
pedestrians; collisions; gaze on the cockpit; replay of the drive. The examples index names
`Driving_Client.py` as its main script, but that is the multi-user client: start from
`Driving_GUI_Main.py`.

| Script | Use |
|---|---|
| `Driving_GUI_Main.py` | start here: environment, trial count and start/end conditions in the GUI; row N of `Resources/stim_file.csv` sets trial N's traffic, pedestrians and headlights |
| `Driving_GUI_Traffic.py` | identical copy under an older name |
| `Driving_Main_noGUI.py` | `gui=False`; each row of `Resources/stim_file-nonGUI.csv` is a trial and its `environment` column picks the scene; spacebar starts and ends each trial |
| `Driving_Server.py` / `Driving_Client.py` | multi-user: one server, one client per driver |
| `Driving_Config.py` / `traffic_config.py` | car, seat, feel, collision, data, `HARDWARE_CONFIGS` / traffic, lights, pedestrians, route recorder |
| `SightLabVR_Replay.py` | the example's own replay (below) |
| `generate_traffic_network.py`, `probe_environment.py`, `test_traffic_network.py`, `generate_pedestrian_routes.py` | build and test turning traffic from `traffic_layouts/<layout>.py`; sidewalk routes |
| `modules/wheel_inspector.py`, `Preview-Brake_Lights.py` | print a wheel's axis and button IDs; preview vehicle lamps |

`modules/` holds the reusable parts: `car_module.py` (`Car`), `driver_data.py`,
`vehicle_collision.py` (bumper rays, `CrashLog`), `collision.py` (ground), `seat_recenter.py`,
`car_mirrors.py`, `haptics.py`, `body_motion.py`, `multiuser_cars.py`, `traffic/`. Environments:
the day and night street, `city_rtx2` and the highway (chicago2's route file ships; its model is
in the expanded download).

## Configuration

`Driving_Config.py`, defaults as shipped:

| Key | Default | Effect |
|---|---|---|
| `CAR_MODEL` | `'Resources/jeepmodel.osgb'` | the car; cockpit gaze parts and mirrors are added for this model only |
| `CAR_STARTING_POSITIONS`, `CAR_STARTING_POSITION` | per environment file name; `[0.25, 0, 0.35]` | where the car starts each trial |
| `PASSENGER_POSITION_TRUCK`, `PASSENGER_POSITION` | measured seats | desktop seat for the jeep (the scripts set `CAR_TYPE = 'Truck'` for it), for other cars |
| `SEAT_RECENTER`, `DRIVER_EYE_POINTS` | `True`; jeep and `car.osgb` | headsets: each trial moves the seat so the eyes sit at the car's eye point |
| `DESKTOP_FOV` | `70` | vertical field of view on desktop configurations |
| `MAX_SPEED`, `ACCELERATION_MPS2`, `BRAKING_MPS2`, `COAST_RATE` | `27.5` m/s, `6.0`, `8.3`, `1.2` m/s² | driving feel |
| `REAR_AXLE_OFFSET` | `[0.46, 0, -0.78]` | steering pivot; re-measure for a new car |
| `USE_COLLISION`, `USE_BUILDING_COLLISION` | `True`, `True` | ground following; bumper rays that stop the car at walls and vehicles |
| `ADD_TRAFFIC`, `ADD_PEDESTRIANS` | `True`, `True` | master switches |
| `LOG_PEDALS`, `LOG_GAZE_CATEGORIES` | `True`, `True` | the driver-data columns |
| `USE_MIRRORS`, `USE_HAPTICS`, `USE_BODY_MOTION` | `True` each | mirrors (jeep), controller vibration, visual body lean |
| `FREEZE_GC_DURING_TRIALS`, `PROFILE_FRAMES` | `True`, `False` | no garbage-collector freezes; frame report to `data/frame_profiles` (GUI script) |
| `ADD_CLIENT_CARS`, `CLIENT_CAR_COLORS`, `CLIENT_CAR_SPACING` | `True`, `True`, `8.0` | multi-user cars |

`traffic_config.py`: `MAX_VEHICLES` 30 and `MAX_PEDESTRIANS` 5 (pools; they cap the STIM counts),
`DEFAULT_VEHICLES` 6, `DEFAULT_PEDESTRIANS` 4, `PEDESTRIAN_SPEED_MPS` 1.2, `HIT_RADIUS` 0.25,
`PEDESTRIAN_HIT_RADIUS` 0.3, `PEDESTRIAN_CLOSE_PASS_RADIUS` 1.0, `LIGHTS_AS_GAZE_OBJECTS` False,
`PEDESTRIAN_GAZE_OBJECTS` True, `RANDOM_SEED` 42, `REPEATABLE_TURNS` False (True: each vehicle
makes the same turns every run), `RECORD_ROUTES` False.

STIM columns; a missing or blank value falls back:

| Column | Sets | Fallback |
|---|---|---|
| `environment` | scene file (no-GUI script only) | `ENVIRONMENT_MODEL` (the day street) |
| `number of vehicles`, `number of pedestrians` | active count, capped at the pool | `DEFAULT_VEHICLES`, `DEFAULT_PEDESTRIANS` |
| `traffic speed`, `pedestrian speed` | m/s | each lane's speed, `PEDESTRIAN_SPEED_MPS` |
| `traffic lights`, `yield to user car` | `on`/`off`; whether traffic brakes early for the car | `LIGHTS_ENABLED`, `YIELD_TO_USER_CAR` (both on) |
| `traffic seed` | the trial's seed: start layout, speeds, turns | `RANDOM_SEED` |
| `headlights` | `on`/`off`, also written to the summary | off |

## Hardware

Every script but the server passes `vizconnectconfig=HARDWARE_CONFIGS`, so SightLab's chooser lists
only these names and loads the example's own files from `vizconnect_configs/`:

| Kind | Names |
|---|---|
| Desktop | `Driving Desktop` (keyboard, mouse), `Desktop Driving Controller` |
| Wheel | `Driving G923 Wheel`, `Driving Thrustmaster Wheel`, `Driving Wheel` (Thrustmaster file), `Driving Vive Focus Vision G923 Wheel` (headset) |
| OpenXR | `Driving OpenXR`, `Driving Quest Pro`, `Driving Varjo` (one file), `Driving OpenXR No EyeTR`, `Driving Vive Focus Vision`, `Driving Pimax Controller` |
| Meta | `Driving Meta`, `Driving Meta Game Controller` |
| SteamVR, HP | `Driving SteamVR`, `Driving SteamVR Controller`, `Driving Vive`, `Driving Omnicept` |

- Names ending in "Controller" drive with an Xbox controller. Wheels are read through pygame by
  `modules/g923_input.py` or `thrustmaster_input.py` (pedal axes at the top); a person sets up the
  wheel's driver and Python support from the documentation. Another wheel: read its IDs with
  `modules/wheel_inspector.py`, copy an input module and a wheel vizconnect file, add an entry.
- Ten names are also `VIZCONNECT_DICT` keys (`Driving Desktop`, `Desktop Driving Controller`,
  `Driving Vive`, `Driving Omnicept`, `Driving SteamVR`, `Driving Meta`, `Driving OpenXR No EyeTR`,
  `Driving Quest Pro`, `Driving Varjo`, `Driving OpenXR`), but there they load older copies in
  `sightlab_utils/vizconnect_configs` (the desktop one has no `SHIFT_GEAR`, so no Reverse). To skip
  the chooser use the list form, `vizconnectconfig=['Driving Desktop',
  'vizconnect_configs/vizconnect_config_desktop_driving.py']`; `hardwareconfig=` beside the dict
  looks the relative path up inside `sightlab_utils/vizconnect_configs`, where it does not exist.
- Desktop and wheel-on-desktop configurations fix a simulated eye tracker to the view, so gaze is
  head direction (`J L I K` nudge it on `Driving Desktop` and `Desktop Driving Controller`). No
  driving name is on SightLab's pupil list: no pupil columns on any of them (`guides/hardware.md`).

## Controls

| Action | `Driving Desktop` | Xbox controller | Headset controllers | Wheel |
|---|---|---|---|---|
| Gas / brake | `=` / `-` | right / left trigger | right / left trigger | pedals |
| Steer | `A` / `D` (`W`/`S` also move) | left stick | left stick | wheel |
| Drive / Reverse | `Y` | X | Y | button 2 |
| Cycle viewpoint | `b` | Back | `b` | button 1 |

Any hardware: spacebar starts the trial (the GUI's start condition); `b` cycles in-car,
third-person, closer-in and hood views; `r` stops the car and puts car and seat back at the
trial's start; `v` prints the seat position and the eye point; `i` levels the view (not in the
no-GUI script). Seat: `T F G H Z X` on desktop, `W A S D Z X` in a headset; `0` re-centres a
headset seat after a 2 s countdown, right grip + A at once on the OpenXR configurations. Each
vizconnect file maps its own events (`Accelerate`, `Decelerate`, `turnWheelLeft`,
`turnWheelRight`, `SHIFT_GEAR`, `toggleViews`); read it for SteamVR wands.

## Data

Standard layout under the script's `data/` (`rules/gaze-objects-and-data.md`). Trial data, every
frame, after SightLab's columns:

- `my_car x`, `y`, `z`, `yaw`, `pitch`, `roll` (`addTrackingTrialDataColumn("my_car", car)`);
  `Car Velocity X`, `Car Velocity Y`, `Car Velocity Z` (m/s, world axes, Y up); `Average Speed MPH`
  (running average of the HUD speed; the last row holds the trial's).
- `Throttle Pedal`, `Brake Pedal` (0–1 from the event magnitude; keys give 0 or 1).
- `Gaze Target` (registered name, else `-`) and `Gaze Category`: `vehicle`, `pedestrian`,
  `traffic light`, `mirror`, `dashboard` by name prefix (`GAZE_CATEGORIES`), `other` for another
  gaze object, `environment` for the scene, `none` when the ray hits nothing.
- `Nearest Vehicle Distance` (m, car outline to the closest traffic body, while traffic runs).
- In `flag`: `crash: <what> at <speed> m/s`, `hit by traffic_car_NN`, `hit pedestrian <name>`,
  `close pass pedestrian <name>`.

Experiment summary, per trial: `Headlights`, `Average Speed MPH`, `Crashes`, `Traffic Count`,
`Vehicle Hits`, `Min Vehicle Distance` (blank if no vehicle came near), `Pedestrian Hits`,
`Pedestrian Close Passes`, and gaze seconds per category: `Gaze Vehicles (s)`,
`Gaze Pedestrians (s)`, `Gaze Traffic Lights (s)`, `Gaze Mirrors (s)`, `Gaze Dashboard (s)`.

Gaze objects: the jeep's `InstrumentPanel`, `Radio`, `RearViewMirror`, `LeftMirror`; every pool
vehicle (`traffic_car_00`…); pedestrians (`pedestrian_00`…, single-user); traffic lights
(`traffic_light_<intersection>_<group>_<n>`) only with `LIGHTS_AS_GAZE_OBJECTS`. The car itself is
not intersectable. `TRAFFIC_HIT_EVENT` and `PEDESTRIAN_HIT_EVENT` (in `modules.traffic`) carry the
name; with BIOPAC on, hits and crashes insert `vehicle hit: <name>`, `pedestrian hit: <name>` and
`crash: <what>` markers.

## Session replay

Use the example's `SightLabVR_Replay.py` (`guides/replay.md` for the rest). It shows `my_car` (or
each `car_<computer name>`), traffic and pedestrians; sets the third-person camera behind the car;
spins every vehicle's wheels from its movement (wheels are not recorded); re-tints multi-user cars
from the `car colors` replay flag; keeps pedestrians unlit as live; and in a multi-user session
takes traffic, pedestrians and cockpit from one client (the one picked in Client ID, else the
lowest-numbered), since each client runs its own. Follow Mode gives the driver's view.

## Multi-user driving

- `Driving_Server.py` (`sl.SightLabServer()`) sets environment, trials and start/end in its GUI,
  simulates traffic and pedestrians and broadcasts them; its own car is hidden and does not
  drive. Each `Driving_Client.py` picks its hardware and drives; one client per computer.
- With `ADD_CLIENT_CARS` the server registers each client's car as `car_<computer name>`, painted
  in that client's SightLab colour (nodes matching `CAR_PAINT_NAME_MATCH`) and lined up
  `CLIENT_CAR_SPACING` m behind the previous joiner; traffic yields to every car.
- Data is saved on the server, client files with `_client_<n>`. Not recorded in multi-user: pedal
  and gaze-category columns, `my_car` as a scene object, pedestrian gaze objects, looks at other
  drivers' cars. Client summaries carry the server's values: per-driver crashes are the `crash:`
  flags.
- The server writes client trial data under its own header, which lacks the client's `my_car`
  columns, so the names after `flag` do not line up with the values (noted in `Driving_Server.py`).

## Customising

- Environment: pick it in the GUI (or the `environment` column) and add its file name to
  `CAR_STARTING_POSITIONS`. Traffic loads `Resources/traffic/<environment name>.json` (none: no
  traffic); pedestrians `<name>_pedestrians.json`, else sidewalks derived from the vehicle lanes.
- Routes: `RECORD_ROUTES = True`, start a trial, F5 opens the recorder (F4 auto-drop, F6 drop, F9
  open lane, F8 loop, F10 stop line and light, INSERT intersection, PAGE DOWN signal group, F12
  save; `RECORDER_KEYS`). Turning traffic over a street grid: a layout in `traffic_layouts/`, then
  `generate_traffic_network.py <layout>` and `test_traffic_network.py <environment>` run with Vizard
  (`Resources/traffic/ROAD_NETWORKS.md`); never hand-edit their output. Sidewalks: add the
  environment to `ENVIRONMENTS` in `generate_pedestrian_routes.py`.
- Traffic: any model in `Resources/vehicles` joins the pool (`VEHICLE_MODEL_OVERRIDES` for yaw and
  scale, `VEHICLE_WHEEL_NODES`); avatars go in `Resources/pedestrians` (`PEDESTRIAN_ANIMATIONS`).
  In code: `traffic.configure({...})` with STIM-style keys before `traffic.start()`;
  `traffic.pause()`, `traffic.resume()`.
- Car: `CAR_MODEL` with its part names (`STEERING_WHEEL_NAME`, wheel nodes, `MPH_GAUGE`,
  `RPM_GAUGE`), `REAR_AXLE_OFFSET`, a `DRIVER_EYE_POINTS` entry, `COLLISION_LOOKAHEAD` and
  `CAR_HALF_WIDTH`. Cockpit gaze on another car: parent the parts to it and register each with
  `sightlab.addSceneObject(name, node, gaze=True)`.

```python
from modules.traffic import TRAFFIC_HIT_EVENT

def onTrafficHit(name):            # once, at load: e.g. end the trial or show a rating
    print('hit by', name)
vizact.addCallback(TRAFFIC_HIT_EVENT, onTrafficHit)

# in the trial loop, right after TRIAL_START: give a new column a value first
sightlab.setCustomTrialData('-', 'Lane Change')
```

## Gotchas

- Use `vizact.addCallback`, never `viz.callback`, on the hit events and the car's events
  (`Accelerate`, `SHIFT_GEAR`, ...): `viz.callback` replaces the scripts' handler.
- Write custom data while the trial runs (SightLab saves the trial before it sends `TRIAL_END`),
  and give a new column a value at trial start, or earlier rows leave it out (`primeTrialColumns`).
- Drive/Reverse switches only at a standstill; each trial starts stopped, in Drive.
- GUI scripts: STIM rows past the GUI trial count are unused; trials past the rows use defaults.
- Every pool vehicle and pedestrian is recorded every frame, used or not: keep `MAX_VEHICLES` and
  `MAX_PEDESTRIANS` near the largest STIM counts.
- After moving the car in code, call `building_collision.reset()` in the same frame. The scripts
  also patch `sightlab.resetTrial` (car-parented parts) and `sl.WINDOW_FOV`; keep both when copying.
- A renamed environment file loses its traffic and pedestrian routes.
- The `Driving Thrustmaster Wheel` and `Driving Wheel` paths lack `.py`, and three OpenXR file
  names contain a space: check they load before relying on them.
- The autopilot forces `Desktop`, which has no `driving` transport: a person runs these scripts,
  on `Driving Desktop` for a quick check.

## Shipped examples

`examples/Driving` is the folder above. The documentation's expanded download adds a
`Longer_Road` highway and `Driving_Simulator_360`.
