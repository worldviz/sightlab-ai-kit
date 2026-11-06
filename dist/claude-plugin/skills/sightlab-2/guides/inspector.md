# Inspector (the scene editor)

Sources: help.worldviz.com/sightlab scene-editor-inspector; `reference/sightlab.py` (2.9.3)
for the start-point and node lookups.

When to read: the researcher wants to prepare or change a 3D environment (name or group
objects so they record gaze data, add a region of interest, set where the participant
starts, adjust lighting or textures, add 3D text), or asks how to open or use Inspector.

## What it is

Inspector is Vizard's visual browser and editor for 3D models. SightLab uses it as its
scene editor. The researcher opens it with **Edit** next to the environment in the GUI's
Experiment Options, from **Tools** in the Vizard IDE, or with the Inspector shortcut in
`Documents\Sightlab2`. Dragging a model onto the window, or **File > Open**, opens another
model.

With computer use (control of the screen, mouse and keyboard), the agent can make the edits
itself. Without it, give the researcher the steps, then write the code against the node
names they chose. Either way, `check.py` and the autopilot see only the script and the saved
model.

## What the script depends on

- **Node names.** A node's name in the scene graph is what code reaches with
  `env.getChild('name')`, and what the GUI lists as a possible scene object. Names are
  case-sensitive. Ask the researcher for the exact name, or print `env.getNodeNames()` once.
- **Group nodes.** An object needs its own group node to be registered as a gaze object;
  transform nodes position things. To wrap a node, right-click it in the scene graph, choose
  **Insert Above** (or **Insert Below**), and give the new node a unique name.
- **The saved file.** Edits exist only after **File > Save**, and only in that file. Save a
  copy into the project's `Resources/` folder rather than editing a shipped environment in
  `sightlab_resources`, and load it by relative path (`rules/environments-and-resources.md`).

## Make an object or region record gaze data

Researcher, in Inspector:

1. For an object: insert a group node above it and name it (for example `Dashboard`).
2. For a region of interest: **File > Add**, choose `RegionOfInterest.osgb` (or
   `RegionOfInterestSphere.osgb`) from `scene_objects` (the project's `Resources/scene_objects`
   or `sightlab_resources/scene_objects`; **File > Open Containing Folder** helps find it),
   move and scale it over the area, and give it a unique name.
3. **File > Save**.

GUI mode: the researcher picks the new node in the GUI's scene-object list. Code mode, with
an edited copy of `complete_scene.osgb` saved into the project's `Resources/`:

```python
env = vizfx.addChild('Resources/complete_scene.osgb')
sightlab.setEnvironment(env)
dashboard = env.getChild('Dashboard')
sightlab.addSceneObject('Dashboard', dashboard, gaze=True)
```

A region of interest is registered the same way, with `addSceneObject(..., gaze=True)`. In
2.9.3 `addRegionOfInterest()` has an empty body (`reference/sightlab.py`); do not use it for
3D scenes. Regions of interest on 360 media are drawn in the SightLab GUI, not in Inspector.

## Set where the participant starts

Researcher, in Inspector: **File > Add** `SIGHTLAB_START_POINT.osgb` from `scene_objects`,
move and rotate it, save.

What SightLab does with it: when a trial starts without an explicit `startPoint` or
`startEuler`, it looks for a node named exactly `SIGHTLAB_START_POINT` in the environment,
takes the position and orientation of its `SIGHTLAB_START_POINT_TRANSFORM` child, and hides
the marker. Multi-user clients look for `SIGHTLAB_START_POINT_<suffix>` instead
(`setStartPointSuffix`; `SIGHTLAB_START_POINT_CLIENT.osgb` ships for this). Some
documentation spells it `SIGHTLAB_STARTING_POINT`; the code checks `SIGHTLAB_START_POINT`.

## Lighting

- Add a light: **Create > Light**, pick a type (a directional light's position does not
  change its output; only its rotation does), set colour and **Shadows** in Properties, and
  rename it (for example `Sun`) so a script can reach it with `env.getChild('Sun')`.
- A model that ignores lighting: select its material node and set **Modes > Lighting** to On.
- Ambient light, environment map and fog: select the **Scene** root node, edit them in
  Properties, turn on **Effects** (bottom right) to preview, and tick **Save Scene Settings**
  so they are stored in the file.

## Textures, performance and other items

- The textures pane (lower left) lists every texture with its dimensions, memory size and
  compression: the first place to look when a scene runs below the headset's frame rate.
- Select a material node to edit its properties (PBR attributes, diffuse, colour, alpha) or
  swap a texture (click the texture, then the folder icon).
- **Create** also adds 3D text (**Create > Text 3D**, for labels above objects), other
  primitives, and **External Reference**, which reuses a model kept in a folder beside the
  file instead of copying it into each scene.
- Animations on nodes and avatars can be previewed with the playback controls.

## Navigation, for telling the researcher

Left drag orbits; Shift + left click moves the view to the clicked surface; right drag pans;
the wheel zooms; `Z` zooms to the selected node; hold the right button and use `WASD` and
`QE` to fly (Vizard 8.3.1 or later); `F2` is full screen; `Alt+D` searches nodes and
textures; Peek Mode isolates the selected object.

## Gotchas

- A node renamed in Inspector after the script was written breaks `env.getChild` in code
  mode and drops out of a saved GUI config; change both together.
- An object without its own group node cannot be told apart from its neighbours in the data.
- Desktop autopilot runs use the head direction as the gaze, so they show that a region is
  registered and reachable, not how real eye tracking lands on it.

More detail: Vizard's Inspector documentation (docs.worldviz.com/vizard, "Inspector").
