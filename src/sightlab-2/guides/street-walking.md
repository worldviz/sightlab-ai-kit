# The Street Walking example

Sources: help.worldviz.com/sightlab street-walking-example; the demo's scripts and `modules/` (code wins).

When to read: the study is a pedestrian, street-crossing or walking-in-traffic task, or the
researcher names the Street Walking example or wants traffic around a participant on foot.

## What it is

A separate demo, not in the shipped ExampleScripts or the examples index: the researcher
downloads it from the Street Walking Example page of the SightLab documentation
(help.worldviz.com/sightlab). It is a `Street-Walking-Sample` project folder. Vehicles follow
recorded lanes, keep their gap, stop at traffic lights (each pole carries walk / hand signals)
and brake for the participant; optional avatars walk the sidewalks, pause when the participant
is in their path and wait at red lights. City ambience loops, a hit plays a crash sound, the
participant follows the ground, and on the desktop `b` cycles first- and third-person views.
Environments: `street_day.osgb`, its night copy street__night (two underscores), both with a
signalised mid-block crossing in front of the start point, and a large city_rtx2 model; day or
night is a choice of environment file. `modules/traffic/` is the package `examples/Driving`
uses (`driving.md`), plus the pedestrian signals.

| File | Use |
|---|---|
| `Street-Walking-Sample.py` | GUI version: environment, trial count and end condition from the GUI; row N of `Resources/stim_file.csv` sets trial N's traffic |
| `Street-Walking-Sample-NonGUI-STIM.py` | `SightLab(gui=False)`: one trial per row of `Resources/stim_file-non-GUI.csv`, which adds `environment`, `start_position` (`"x,y,z"`), `start_euler` (`"yaw,pitch,roll"`), `condition` (trial label); space ends a trial |
| `Street-Walking-Sample_Server.py` / `_Client.py` | multi-user: the server moves vehicles and avatars and broadcasts them; clients build the same pools with `simulate=False` |
| `Street-Walking-Sample_Replay.py` | Session Replay, re-spinning the vehicles' wheels |
| `traffic_config.py` | every tunable; all scripts import it |

## Configuring and adapting

STIM columns (case-insensitive; blank uses `traffic_config.py`): `number of vehicles`,
`traffic speed` (m/s; blank keeps each lane's own), `traffic lights` and `yield to pedestrian`
(`on`/`off`), `number of pedestrians`, `pedestrian speed`. Other condition columns are read
with `StimReader` as usual. The same in code:

```python
traffic.load_routes_for_current_environment()   # Resources/traffic/<environment>.json
traffic.configure({'number of vehicles': 4, 'traffic lights': 'off'})
traffic.start()
```

- `traffic_config.py`: `ADD_TRAFFIC`, `ADD_PEDESTRIANS`; pools `MAX_VEHICLES` (15),
  `MAX_PEDESTRIANS` (5); `GREEN_TIME`, `YELLOW_TIME`, `ALL_RED_TIME` (a route file can override
  them); `HIT_RADIUS` (0.3 m), `CLOSE_PASS_RADIUS` (1.2 m), `HIT_SOUND`, `BLOCK_AT_CONTACT`;
  `PED_SIGNALS_ON_POLES`; `WALKING_SPEED_MODE` (`'distance'`, `'head'` for the older method,
  `'feet'` untested with foot trackers); `VEHICLE_MODEL_OVERRIDES` (`yaw`, `scale`) for models
  dropped into `Resources/vehicles/`; `PEDESTRIAN_ANIMATIONS` for avatars in `Resources/pedestrians/`.
- A new environment needs `Resources/traffic/<environment>.json`: record it in the app
  (`RECORD_ROUTES = True`, start a trial, F5 recorder, F6 waypoint, F8 / F9 finish a loop / open
  lane, F10 stop line and light, F12 save) or write it: `lanes` (`waypoints`, `speed`, `loop`,
  `stop_lines`) and `intersections` (`id`, `position`, `green`, `yellow`, `all_red`, `lights`).
  Sidewalks come from `<environment>_pedestrians.json`, else are derived from the lanes.
- Trial end: the GUI's end condition or `viz.sendEvent(INITIATE_TRIAL_END)` (GUI version); in
  the non-GUI script replace `yield viztask.waitKeyDown(' ')`. A hit sends `TRAFFIC_HIT_EVENT`
  (`viz.getEventID('TRAFFIC_HIT')`) with the vehicle's name.

## Data beyond the standard files

No extra files; it all goes into SightLab's own (`rules/gaze-objects-and-data.md`):

- Trial data per frame: `Walking Speed MPH`, `Nearest Vehicle Distance` (m to the nearest
  vehicle body). Flag column: `hit by traffic_car_NN`, `close pass by traffic_car_NN`, and
  `lights <intersection>: <group> <state>` at trial start and each change (`off` without
  lights; at the mid-block crossing `lights crossing: A red` is the walk phase).
- Experiment summary: `Traffic Count`, `Min Vehicle Distance`, `Vehicle Hits`, `Close Passes`,
  `Average Walking Speed MPH`, `Average Moving Speed MPH` (moving time only).
- Gaze objects, rebuilt in replay: `traffic_car_00`…`traffic_car_14`,
  `traffic_light_<intersection>_<group>_<n>`, `pedestrian_signal_<intersection>_<light>_<n>`,
  `pedestrian_00` onward. With BIOPAC on, the GUI script also marks each hit.

## Gotchas

- Routes are matched by environment file name; with none, that trial has no traffic (a
  console message says so), and avatars without a sidewalk file need it too.
- GUI version: STIM rows match trials by position (later trials use defaults); row 1 has 0 avatars.
- Pools are built at load: counts above `MAX_VEHICLES` / `MAX_PEDESTRIANS` are cut with a
  warning; 5 avatars means the first five files alphabetically.
- `yield to pedestrian` `off` only stops vehicles braking for the participant, who has no body:
  cars pass through and hits are recorded (`BLOCK_AT_CONTACT = True` stops them short). Only
  moving vehicles count, each once per `HIT_COOLDOWN` (2 s).
- The avatar files are proxies pointing at `C:\Program Files\WorldViz\Sightlab2\sightlab_resources\avatar\`;
  another install path leaves them unloaded. In multi-user they are not gaze objects.
- Multi-user: same models, `traffic_config.py` and STIM file on every machine; vehicles yield
  to the clients' heads, not the server's camera.
- Keep `sl.WINDOW_FOV = traffic_config.DESKTOP_FOV`: otherwise desktop configs get a forced 79° FOV.
- Create `GroundFollower`, `TrialGC` and callbacks once, outside the trial loop (handlers
  stack). `TrialGC` stops frame freezes as replay data grows in long trials.
- Summary columns keep the last trial's value until rewritten; reset your own at trial start.
