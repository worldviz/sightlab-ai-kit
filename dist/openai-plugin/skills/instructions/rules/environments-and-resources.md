# Environments and resources

## Loading an environment (code mode)

```python
env = vizfx.addChild('sightlab_resources/environments/complete_scene.osgb')
sightlab.setEnvironment(env)
```

- Use `vizfx.addChild`, not `viz.addChild`, so the environment gets SightLab's lighting.
- `setEnvironment` has per-trial and media forms: `setEnvironment(env, trial=2)` for a
  different scene in trial 2; `setEnvironment(media, mode=MEDIA_360, mediaType='video')` for
  360 photos and videos (`examples/360 non GUI`, `patterns/360-media.md` when present).
- In GUI mode do not call `setEnvironment` at all; the researcher picks it in the GUI.

## Shipped environments and objects

The full list of shipped files, by folder, is `api/resources.md` (generated from the resource
folder; `api/resources.json` is the same for tools). Look a name up there before using it;
`harness/check.py` warns on names that do not ship or differ in case.

`sightlab_resources/environments/` ships with SightLab 2 (the names are case-sensitive on the
resource list; `.OSGB` is a real spelling for one of them):

`Business_Office.OSGB`, `Interior_Empty.osgb`, `Lecture.osgb`, `Lecture_Hall_Dark_Template.osgb`,
`Piazza_empty.osgb`, `RockyCavern.osgb`, `RockyCavern_Night.osgb`, `ShowRoom_empty.osgb`,
`ShowRoom_standin_avatar.osgb`, `Stimulus.osgb`, `complete_scene.osgb`, `dojo.osgb`,
`dojo2.osgb`, `dojo2_empty.osgb`, `empty.osgb`, `gallery_paintings.osgb`, `homeOffice.osgb`,
`jeepmodel.osgb`, `lab_empty.osgb`, `maze.osgb`, `medical_examination_room.osgb`,
`modern_office_skyline.osgb`, `pit2.osgb`, `pit_raised.osgb`, `street_day.osgb`,
`van_gogh_room.osgb`, `waiting_room.osgb`, `whiteroom.osgb`, `whiteroom_clear.osgb`.

- Good neutral choices: `complete_scene.osgb` (a furnished room with named objects such as
  `soccerball` and `basketball` reachable with `env.getChild('soccerball')`), `whiteroom.osgb`
  (empty, bright), `lab_empty.osgb`.
- Other shipped folders under `sightlab_resources/`: `objects/` (for example `Plant.osgb`,
  `basketball.osgb`, `chair.osgb`, `crate.osgb`, `guitar.osgb`, `flashlight.osgb`), `scene_objects/`,
  `avatar/`, `audio/`, `media/` (360 media), `media_2D/`. `examples/index.md` shows which
  examples use what. Showing a different subset of objects each trial:
  `patterns/show-hide-objects-per-trial.md`.
- Before naming any file, confirm it exists in the installed `sightlab_resources` folder
  (`harness/check.py` warns when a path is not on the resources list).
- A researcher's own models: any `.osgb`, `.gltf`/`.glb`, `.fbx` or `.obj` Vizard can load,
  placed in the project folder or a `Resources/` subfolder and referenced by relative path.

## Sizes: pick by class, place by bottom

`api/resources.md` lists each shipped object's bounding box in metres, a class, and its `bottom`
(lowest point relative to the model's origin), measured in Vizard. Use them:

- **Choose by class.** Things a participant holds, grabs, or studies on a table are **hand-held**
  (longest side ≤ 0.35 m); **table-top** goes up to 0.8 m; **large** is furniture, vehicles,
  rooms. A brief that says "objects on a table" wants hand-held models, not `chair.osgb` at
  scale 1. Several shipped models are larger than life (`Baseball.osgb` is 0.2 m across): read
  the table, do not assume.
- **Scale deliberately.** When the brief needs a size the model does not have, `setScale` once
  with one factor, say so in the brief as an assumption, and keep registered gaze objects big
  enough to dwell on from where the participant stands (about 0.1 m at 1.5 m is the floor).
- **Place by bottom and centre.** To stand a model on a surface at height `h`, set its y to
  `h - bottom`. Some models' centres sit well off their origin (`Table.osgb`'s centre is 0.88 m
  forward of its origin); line things up on the listed centre.
- A model is `unmeasured` in the table when it was not in the measured set; treat its size as
  unknown and check it on the first run.

## Primitives and colours

- `vizshape` primitives (`vizshape.addCube(size=0.2)`, `vizshape.addSphere(radius=0.1)`,
  `vizshape.addBox(size=(0.25, 0.25, 0.25))`) need `import vizshape` and a lit scene:
  construct with `sl.SightLab(..., headlight=True)`.
- Colour a node with `node.color(viz.BLUE)`; position it with `node.setPosition([x, y, z])`.
