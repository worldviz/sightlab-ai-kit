# Models and assets: getting and preparing 3D models

Sources: help.worldviz.com/sightlab getting-3d-models-and-assets, model-converter,
sightlab-dashboard (Asset Browser), playing-animations; Vizard 8.3.1 help (3D Models Introduction,
Performance, Texture Compression); `reference/sightlab.py` (2.9.3); the Dashboard's code;
`osg-converter --help` in `examples/Model_Converter`.

When to read: the researcher wants a model the resource list lacks, brings their own model or
scan, asks where to get or how to convert one, or a model loads too big, turned, dark,
untextured or slow.

Shipped files, `vizfx.addChild`, sizes and placement: `rules/environments-and-resources.md`.
Editing a model (group nodes for gaze objects, lights, textures): `guides/inspector.md`.

## Formats

- Vizard 8 names glTF 2.0 (`.gltf`, `.glb`) and FBX "(up to 2019)" its industry-standard formats;
  `.obj`, `.dae`, `.wrl`, `.flt`, `.ac`, `.lwo` are legacy, "partially supported" (Vizard help).
  `.osgb` is Vizard's native format: it loads fast and can embed textures; every shipped model is
  one except four Cal3D `.cfg` avatars. Point clouds: `.dp`, `.ply`, `.3dc`, `.asc` (docs). There
  is no USD loader.
- The GUI lists, and accepts by drag-and-drop, only `osgb`, `OSGB`, `gltf`, `fbx`, `glb` and
  `obj`, case-sensitively (`reference/sightlab.py`; `.GLB` is not listed). Others: code only.
- Recommend `.glb` whenever the researcher can choose (docs): one file with its textures inside,
  PBR materials kept, always in metres. It also survives the GUI's drag-and-drop, which copies
  only the dropped file: a `.gltf` loses its separate `.bin` and textures, an `.obj` its `.mtl`,
  an `.fbx` any external textures. Copy those folders by hand.
- `.osgb` is just as good inside SightLab, and the Dashboard produces it: Sketchfab downloads and
  AI-generated objects are converted from GLB to OSGB, and its 3D Environments and Scene Objects
  bins list only `.osgb`. Rigged avatars stay `.glb` (Animated models and avatars).

## Units, orientation, origin

Vizard works in metres with Y up; `setPosition([0, 1, 0])` is one metre above the origin, and a
model sits where its own origin is placed. Measure a new model once:

```python
model = vizfx.addChild('Resources/<model>.glb')
bb = model.getBoundingBox()
print('size', bb.size, 'centre', bb.center, 'bottom', bb.center[1] - bb.size[1] / 2)
```

- **About 100 times too big:** an FBX exported in centimetres (docs). `setScale([0.01] * 3)`
  once, or re-export in metres; in GUI mode fix the file, not the script. Then place by bottom
  and centre (`rules/environments-and-resources.md`).
- **Lying on its back or face:** authored Z-up. Re-export Y-up, or pitch it 90 degrees
  (`model.setEuler([0, -90, 0])`, or `90` if it tips the other way). **Facing away:**
  `setEuler([180, 0, 0])`. **Turns about an odd point:** transforms act about the origin;
  re-centre it in Blender, or place by the measured centre.
- Some environment boxes dwarf the room (`ShowRoom_empty.osgb` and `Business_Office.OSGB`
  measure 500 m a side in `api/resources.md`): measure the part you place things against.

## Too dark, or no textures

- Loaded with `viz.addChild`: no SightLab lighting; use `vizfx.addChild`.
- No lights of its own: shipped environments carry lights, but `setEnvironment` turns the
  headlight off for a 3D environment unless asked. `sl.SightLab(headlight=True)` (any mode), or
  in code mode `sightlab.setEnvironment(env, headlightIntensity=0.5)` (0 to 1); better, add
  lights in Inspector.
- A model whose texture already contains its lighting looks too dark or doubly shaded: show it unlit with
  `model.disable(viz.LIGHTING)`, as `examples/AI_3D_Model_Spawner` does by default (`b`
  toggles). A material that ignores lights: Inspector, **Modes > Lighting**.
- White or grey where textures should be: they did not travel with the file (Formats).

## Converting

- **Anything to `.glb`:** Blender imports FBX, OBJ, glTF, USD, STL, PLY and more; **File > Export
  > glTF 2.0**, format **glTF Binary (.glb)**. Use the Principled BSDF shader (it maps to glTF
  PBR) and bake procedural textures to images first (docs).
- **`.osgb` to `.glb`** (a shipped or Inspector-saved model into Blender or another glTF tool):
  `examples/Model_Converter` ships the converter and a sample.
  `osg-converter <model>.osgb -o <model>.glb`; a folder, or no input, converts every `.osgb` in
  it; without `-o` the `.glb` lands beside the input. `--z-up` turns Z-up data Y-up, `--compress` writes KTX2 (Basis
  Universal UASTC) textures, `--dump` prints the scene graph as JSON.
- **Anything Vizard loads to `.osgb`:** load and save in a one-off Vizard script, as the
  Dashboard does after a download. Not for rigged avatars: the Dashboard skips it for them
  because it strips the skeleton and animations.

```python
model = vizfx.addChild('Resources/<model>.glb')
model.save('Resources/<model>.osgb')
```

- Unity, Unreal, 3ds Max, Maya, Modo, Substance Painter, ZBrush, Revit, SketchUp, Rhino,
  SOLIDWORKS: the docs' getting-3d-models-and-assets page gives each one's suggested export
  (glTF for most; FBX for Unity and ZBrush, which Blender can turn into `.glb`).

## Performance: polygons and textures

- Neither the docs nor Vizard's help give a triangle or texture budget; do not quote one.
  Measure on the study PC: **F4** in Vizard shows the frame rate, pressed again all render stats
  (Inspector: F4). Update + cull + draw must fit in one frame (16 ms at 60 fps, 8 ms at 120 fps;
  the display's refresh rate sets it), GPU time too; several thousand drawables (separate
  meshes) is high (Vizard help, Performance).
- AI-generated models are often 100,000+ triangles (docs); the `FAST_MODE` of
  `examples/AI_3D_Model_Spawner` asks Meshy for a polycount of 5,000.
- Reduce (docs): Blender's Decimate modifier, less detail far away, no hidden geometry, combine
  objects that share a material, baked lighting, few real-time lights and shadows. Combining
  fights gaze tagging (each target needs its own group node): keep targets separate.
- Textures: a JPG or PNG is small on disk but uncompressed on the GPU. Inspector compresses to
  Basis Universal (High Quality, BC7, recommended) or DXT, about 4:1 (6:1 for RGB with DXT or
  High Compression);
  sides must be divisible by 4; lossy, so for heavy scenes only (Vizard help). Inspector's
  textures pane shows each texture's size, memory and compression.
- Load models before the participant waits for them, not mid-trial (Vizard help, Performance).

## Where models come from (what to tell the researcher)

- Shipped: `api/resources.md`. Online: the WorldViz Asset Browser; the docs' Environment Gallery
  links an extra environments and avatars pack.
- Dashboard **Assets** tab (or a project's Assets panel): bins for 3D Environments, Objects,
  Scene Objects, 360 Media and Avatars (built-in assets plus the user's `Assets` folder). Drag
  one onto the preview, or right-click **Add to Project**, to copy it into the project.
  **Sketchfab** search needs the researcher's Sketchfab API token; **Generate with AI** (Meshy
  or Tripo, 2.8.8 and later) needs their API key.
- Libraries (docs; pick the `.glb` download): Sketchfab (free downloadable models; its store moved
  to Fab), Fab, TurboSquid, CGTrader, RenderHub, 3DExport, 3D Models.org, Poly Haven (CC0),
  Poly Pizza (low-poly), NIH 3D (biomedical), Smithsonian 3D, NASA 3D Resources. The same page
  lists more AI generators (Rodin, Hunyuan3D, TRELLIS.2, ...).
- Own models: Blender (also embedded in the E-Learning Lab, `guides/e-learning-lab.md`). Scans:
  Polycam or Widar on a phone; ReCap Pro, RealityCapture or Metashape on a desktop. Check a scan
  like an AI model: size, triangles, lit or unlit.

## Animated models and avatars

- Keyframe animations in `.osgb`, `.fbx` or `.glb` play in Vizard. For the GUI, name the
  object's group node `<name>_animate` (loops) or `<name>_animate_1` (plays once); the object
  list then shows an Animation state, a 0-based clip index per trial. Nodes with frames are also
  detected without the suffix, less reliably.
- Code: `node.setAnimationState(0)`, `node.setAnimationLoopMode(viz.ON)` (`viz.OFF` plays once),
  `node.setAnimationSpeed(1.0)` (0 pauses), `node.getAnimationNames()`.
- A node ending `.cfg`, or with a `Skeleton` child, is an avatar, animated with `.state(n)`.
  Avatars come as `.fbx`, `.glb`/`.gltf` or Cal3D `.cfg` (docs); register one with
  `addSceneObject(..., avatar=True)` (`examples/Adding_NPC`). Sources (docs): Mixamo,
  Reallusion, Avaturn/MetaPerson, RocketBox, Daz 3D, RenderPeople, Meshy/Tripo. Ready Player Me
  shut down in January 2026; existing exports still work. Talking agents: `guides/ai-agents.md`.

## Licensing

- Free to download is not free to use: each third-party model has its own licence (Poly Haven's
  is CC0; stores and AI generators have their own terms), and its terms on credit, commercial use
  and changes cover the study, paper figures and any shared or published build. Leave the choice
  to the researcher; keep source, author and licence beside the model in `Resources/`.
- The Dashboard's Sketchfab download writes `<name>_attribution.txt` (model, author, source URL),
  but its licence line only says "Creative Commons (check Sketchfab for specific license)": the
  exact licence is on the model's page.

## Gotchas

- Re-exporting a model can rename its nodes, which breaks `env.getChild` and saved GUI configs.
- A downloaded scene may be one merged mesh: nothing to tag until it is split (Blender) or
  grouped (Inspector).
- FBX newer than 2019 may not load: re-export as FBX 2019 or `.glb`.
- 360 photos and video: `rules/environments-and-resources.md` and the docs' 360 Media page; 2D
  video on a screen: `guides/virtual-screen.md`.

## Shipped examples

`examples/Model_Converter` (`.osgb` to `.glb`); `examples/Scene_Builder` (drop `.osgb`, `.glb` or
`.gltf` into a running scene; `k`/`m` scale, `g` `h` `j` move, `t` `y` `u` rotate, Shift
reverses; `1` saves placements to `saved_models/`, `Model_Loader.py` reloads them);
`examples/AI_3D_Model_Spawner` (the same plus Meshy and other generators; needs API keys);
`examples/Model and Media Viewer` (shows each `.osgb`, `.glb`, `.fbx`, `.gltf` in
`collections/<name>/` in turn; `_tag` nodes become gaze and grab objects); `examples/Adding_NPC`.
