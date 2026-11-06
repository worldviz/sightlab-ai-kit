# A first project, step by step (the GUI workflow)

Sources: help.worldviz.com/sightlab creating-a-new-scene, quick-start, gui-overview; the shipped
`BlankProject` and `SampleProject`; `reference/sightlab.py` (2.9.3); the Dashboard's code.

When to read: a new user asks how to make a first experiment and takes the GUI (or GUI plus
code) route of `rules/gui-vs-code.md`, or the agent builds one in SightLab's windows with
computer use. Bold words are the GUI's own labels; give the steps one at a time.

## 1. Create the project

- Dashboard, **Projects** tab, **New Project +**, a name. The Dashboard copies `BlankProject`
  into the projects folder (`Documents\Sightlab2\Projects`, or **Settings > Projects Folder**)
  and renames the scripts after the project: `SightLab_VR.py` becomes `<Name>.py` (the GUI
  script), with `<Name>_NonGUI.py`, `<Name>_Replay.py`, `<Name>_Server.py`, `<Name>_Client.py`.
- The project opens with the **Assets** panel and, by default, runs its script once, embedded,
  so the SightLab editor appears; if not, click **Edit and Run**.
- Without the Dashboard (or before 2.8.0): copy `BlankProject` under `Projects` and rename the
  copy; `SightLab_VR.py` keeps its name and opens the editor. Never edit `BlankProject` itself.

## 2. Add assets

- Drag an environment or a 360 image or video onto the editor (or the Dashboard preview):
  SightLab copies it into `Resources/environments` (`.osgb`, `.gltf`, `.glb`, `.fbx`, `.obj`) or
  `Resources/media`, switches the trial's mode and selects it. Copying by hand works too.
- **Built-In** lists the shipped `sightlab_resources`; **Change** picks another folder inside
  the project. Single objects go into the scene in Inspector, not onto the preview.
- Adding an asset is not tagging it: data comes only from ticked objects and ROIs.

## 3a. A 3D scene

- **Mode** 3D Models, pick the file under **Environment**. **Edit** opens it in Inspector
  (`guides/inspector.md`) for uniquely named group nodes, regions of interest
  (`RegionOfInterest.osgb`) and the start point. After **File > Save**, a model opened with
  **Edit** is re-read automatically (2.8.5 and later); otherwise click the refresh icon.
- The object list (**Target, Visible, Grabbable**) shows the model's group nodes, leaving out
  transforms, lights, the start point and names ending in `_env`.

## 3b. 360 media

- **Mode** 360 Media, pick the file; **Type** Video or Image; **Format** Mono, Stereo T/B or
  Stereo L/R (180°). New 360 trials start as Video and Stereo T/B: a mono file needs **Mono**
  or is split as top/bottom (code: `mediaFormat`, `rules/environments-and-resources.md`).
- Static ROIs: **Add** (or Left Shift) enters ROI mode; aim the virtual gaze point with the mouse
  and press `1`. Each region (`region_1`, ...; at most 50 per trial) gets a row for name, scale,
  opacity (lower it to hide the region) and colour; gaze data uses the name. `i` `j` `k` `l` `u`
  `o` move the last region; `f` `g` `h` grow it along x, y, z, Shift+`F` `G` `H` shrink it.
- Something that moves through the video: trace it with the 360 ROI Path Tracer in
  `examples/360 Moving Regions of Interest` (Dashboard, **Tools/Features**).

## 4. Objects, trials and options

- Each object has **Target** (gaze data: dwell, fixations, view counts), **Visible** and
  **Grabbable**, per trial. New objects start with Target and Visible on: untick Target on walls
  and floors the study does not need.
- **Count** and **Generate** make the trials; + and − add or remove one; **Current Trial** picks
  the one being edited (each has its own environment, objects, ROIs, label and conditions).
  **Label** (default `A`) becomes the data's `Trial Label` column.
- **Condition**: **Start** or **End**, a type, a value. **Key Press** (SPACEBAR, the default for
  both), **Timer** (seconds), **Custom Event** (an event name such as `triggerPress`), **Media
  End** (end only, 360), **Gaze Item** (end only, an object name), **None** (the script decides).
- **Experiment Setup**: **Randomize** the order (anything subtler is code); **Data Files** **Per
  Trial** (default) or **Combined**; **Start Text** and **End Text**.
- **Thresholds**: **Dwell Time** 0.5 s, **Fixation Duration** 0.1 s, **Dispersion Angle** 1
  degree, **Noise Reduction** 0 frames (fine for a first study). **Options**: **Screen Record**
  (video into `recordings/`), **Barchart**, **BIOPAC Markers** (`patterns/biopac-markers.md`).
- Save: a name in **Project File Name**, **Save Project**. It is written as JSON to
  `sightlab_configs/<name>.stlb` and listed in **Load Project File** (`[NEW]` starts afresh).

## 5. Choose hardware and run

**Continue** saves the settings and leaves the editor. Pick the hardware (`guides/hardware.md`;
`Desktop` for a dry run), calibrate the eye tracker for real data, enter the participant ID,
press the spacebar to start and end each trial. Data goes to `data/<date>_<ID>_experiment_data/`;
the Dashboard's **Replay** or `<Name>_Replay.py` plays it back (`guides/replay.md`).

## When to switch to Python

For what the GUI lacks: reactions to gaze or responses, ratings, adaptive trial orders, custom
data columns, other devices. **Edit <Name>.py** in the editor (or **Edit Code** in the
Dashboard) opens the GUI script; add code in its trial loop under the GUI-mode rules of
`rules/gui-vs-code.md`. Code only starts from `<Name>_NonGUI.py`.

## Editor shortcuts

Left Shift toggles navigation (3D) or ROI mode (360); `.` hides the panel; `;` locks the mouse;
`W` `A` `S` `D` move, `X`/`Z` up and down, `Q`/`E` turn; Space plays or pauses 360 video; `1`
adds an ROI; `/` saves a screenshot to `recordings/`. `R` resets the view once the session runs.

## Troubleshooting

- **Project missing from the Dashboard:** **Refresh**; check **Settings > Projects Folder**; the
  folder needs a top-level `.py` script; check write permission.
- **File missing from the list:** it must sit under the **Directory** shown, with a lowercase
  extension (`.JPG`, `.MP4`, `.GLB` are not listed; `.OSGB` is).
- **Inspector edits not showing:** save in Inspector; a model not opened with **Edit** is not
  watched, so click the refresh icon; check the group node's name is unique.
- **Script opens in another Python editor:** right-click, **Open With**, Vizard 8.
- **Stale GUI settings:** delete `sightlab_configs/recent_config.stlb` (named `.stlb` files stay).

## Gotchas

- **Continue** also writes the settings into the file selected in **Load Project File** and into
  `recent_config.stlb`, which the editor reloads next time.
- `sl.SightLab(configpath='sightlab_configs/<name>.stlb')` skips the windows but loads nothing
  unless `sightlab_configs/recent_config.stlb` exists and is not empty: **Continue** once first.
- **Built-In** files live under `Program Files`; copy one into `Resources/environments` before
  editing it. A Dashboard thumbnail drop's **Replace** deletes the project's existing files.

Shipped examples: `BlankProject`, `SampleProject`, `examples/360 Moving Regions of Interest`.
