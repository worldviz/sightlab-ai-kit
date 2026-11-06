# Avatar agents (scripted NPCs)

Sources: `sightlab_utils/sightlab.py`, `replay.py`, `avatarPlacer.py`, `avatar_playback.py` (2.9.3);
`reference/viz.py` (`VizAvatar`, `VizBone`) and Vizard 8 `vizact.py` (`walkTo`); examples `Adding_NPC`,
`Scripted Avatar Agent`, `Driving`, `Avatar_Playback`; help.worldviz.com/sightlab adding-avatar-agents,
scripted-avatar-agent, adding-your-own-custom-avatars, avatar-playback. Animation and morph ids below were
read by loading the shipped avatars in Vizard 8 on 2026-11-06.

When to read: the scene has a person or animal the participant does not converse with (a bystander, an
audience, a confederate who walks, gestures or reads fixed lines, a recorded demonstrator), or gaze on a
person must be measured. A character that talks back: `guides/ai-agents.md`; the participant's own body:
`guides/full-body-avatars.md`; finding and preparing model files: `guides/models-and-assets.md`.

## Adding an avatar

- **Inspector** (the docs' recommended route): the researcher adds the avatar file with **File > Add**,
  places it and saves (`guides/inspector.md`). The node is named after the file unless renamed; code reaches
  it with `env.getChild('<node name>')`, which returns an avatar with all the calls below.
  `examples/Adding_NPC` ships its own copy of `Business_Office.OSGB` holding two avatars; the shipped
  environment has none.
- **GUI mode**: SightLab 2.9.3 treats an environment node as an avatar when its name ends in `.cfg`, or when
  it has a child named `Skeleton` and its name does not end in a model extension (`.osgb`, `.fbx`, `.glb`...).
  A node added as `RocketBox_Male1.osgb` is therefore skipped until the researcher renames it to end in
  `.cfg`, as the docs say. Detected avatars are registered for replay automatically, the GUI's state field
  (default 1) sets their loop at trial start, and gaze is the usual checkbox. In the script, after
  `TRIAL_START`: `sightlab.sceneObjects[AVATAR_OBJECTS]['<node name>']`.
- **In code** (`vizfx.addAvatar` is `viz.addAvatar` plus Vizard's generated effects):

```python
avatar = vizfx.addAvatar('sightlab_resources/avatar/full_body/RocketBox_Male1.osgb',
                         pos=[0, 0, 2], euler=[180, 0, 0])
avatar.state(1)   # idle; until a state is set the avatar holds its bind pose
sightlab.addSceneObject('npc', avatar, gaze=True, avatar=True)
```

- **Stand-in** (legacy in the docs; `examples/Scripted Avatar Agent` uses it): a `standInAvatar.osgb` node
  named `avatarStandin` placed in Inspector; `avatarPlacer.place(env, avatar, 'avatarStandin')` (from
  `sightlab_utils import avatarPlacer`) copies its global pose to the avatar and sets its alpha to 0. The
  replay still shows the stand-in unless the replay script hides it.

## Shipped avatars (`sightlab_resources/avatar/`)

| Files | Animation ids (loops) | Morph ids | Neck bone |
|---|---|---|---|
| `full_body/RocketBox_Male1.osgb`, `RocketBox_Female1.osgb`; `TrackedAvatars/RocketBox_Male2.osgb`, `RocketBox_Male3.osgb`, `RocketBox_Female2.osgb` | 1 idle, 2 run, 3 seated on chair, 4 seated at table, 5 walk, 6 dance, 7 talking gestures (walk and run in place) | 0 angry, 1 disgust, 2 sad, 3 smile, 4 surprise | `Bip01 Neck` |
| `full_body/vcc_male.cfg`, `vcc_female.cfg` | 1 idle, 2 walk, 3 cheer, 4 clap, 5 dance, 6 fight, 7 jump, 8 lie down, 9 look around, 10 pick up, 11 run, 12–13 strafe left/right, 14 talk, 15 use item | 0 blink, 1 eyebrow, 2 talk | `Bip01 Neck` |
| `full_body/vcc_male2.cfg` | 1 idle, 2 walk, 3 run, 4 talk, 5 dance, 6 seated | none | `Bip01 Neck` |
| `Complete Character/CC2_m001_hipoly_A1.cfg` | 75: 1–7 as RocketBox, then sit down and stand up, listen, talk, idles, turns, stairs | none | `Bip01 Neck` |
| `TrackedAvatars/WV_Mark.osgb` | 1 idle, 2 walk, 3 run | none | `Bip01 Neck` |
| `full_body/Reallusion_ActorCore_Male.osgb` (a seated model) | 3 seated clips | 121, e.g. 0 `V_Open`, 16 `Eyes_Blink`, 33 `Mouth_Smile` | `NeckTwist02` |
| `full_body/ReadyPlayerMe.osgb`, `ReadyPlayerMe_Female.osgb`, `ReadyPlayerMe_Male2.osgb` | none: they stand in bind pose | about 70: 0 `mouthOpen`, visemes, 16 `mouthSmile` | `Neck` |
| `full_body/Sado_Avaturn.osgb`, `Woman_Avaturn.osgb`, `x_MixamoBot.osgb` | one clip each | Sado 72 (8 `eyesClosed`); others none | `Neck` |

`TrackedAvatars/` holds participant body models; they work as NPCs too. Animals: `chick.osgb` and
`Creature.osgb` in `sightlab_resources/objects/` load with `vizfx.addAvatar`. For any other avatar, print
the ids instead of guessing:

```python
print(list(enumerate(avatar.getAnimationList(), 1)))   # animation ids start at 1
print(list(enumerate(avatar.getMorphList())))          # morph ids start at 0
print([b.getName() for b in avatar.getBoneList()])
```

## Animation and facial morphs

```python
avatar.state(5)                      # loop 5 (fades in over 0.2 s); a name from getAnimationList() works too
avatar.execute(6)                    # play once over the loop; freeze=True holds the last frame
yield viztask.waitTime(avatar.getDuration(6))   # inside the trial task: wait for the one-shot
avatar.blend(1, 0.5); avatar.blend(5, 0.5)      # mix two loops by weight; stopCycle(5) removes one
avatar.speed(1.5)                    # every animation; setAnimationSpeed(5, 1.5) for one
avatar.setMorph(3, 1.0)              # morph id (or name), weight 0-1
avatar.addAction(vizact.morphTo(3, 0.0, time=0.5))   # ease it back
```

Trigger changes from the trial task, a key (`vizact.onkeydown('v', avatar.state, 2)`) or gaze events
(`patterns/gaze-contingent-events.md`). Mouth movement during speech is not automatic: the Scripted
Avatar Agent repeats a `morphTo` open/close sequence on the mouth morph while the audio plays.

## Walking along a path

```python
route = vizact.sequence(vizact.walkTo([0, 0, 4], walkSpeed=1.2, walkAnim=5),
                        vizact.walkTo([2, 0, 6], walkSpeed=1.2, walkAnim=5))
yield viztask.addAction(avatar, route)   # returns at the last point
```

- `walkTo` turns toward the point (90°/s, `turnSpeed`), plays the walk loop and slides the avatar in a
  straight line: no obstacle avoidance, no floor following. Give points at floor height.
- Without `walkAnim` it plays the cfg's walk animation or id 2, which is the run on RocketBox avatars;
  without `walkSpeed`, the cfg's speed or 1.7 m/s. Pass both; the Driving example walks RocketBox at
  1.2 m/s with id 5.
- When the actions finish, Vizard sets the idle pose: `state(1)` unless the cfg names another or
  `avatar.idlepose(n)` sets one (a seated NPC). Loop a route with `vizact.sequence(..., viz.FOREVER)`
  (`examples/PigeonHunt`); stop with `avatar.clearActions()`.

## Looking at the participant

```python
neck = avatar.getBone('Bip01 Neck')     # 'Neck' on Mixamo, ReadyPlayerMe, Avaturn rigs
neck.lock()                              # the animation stops driving the bone
avatar.getBone('Bip01 Head').lock()      # the examples also lock the head and Bip01 Spine1
def faceView():
    neck.lookAt(viz.MainView.getPosition(), mode=viz.AVATAR_WORLD)
faceTimer = vizact.ontimer(0, faceView)  # vizact.removeEvent(faceTimer) and neck.unlock() to stop
```

Rigs with different bone axes need a correction after `lookAt`: the examples apply
`neck.setEuler(NECK_TWIST_VALUES, viz.REL_LOCAL)` when `TURN_NECK` is set (the AI agent's Reallusion
config uses `NeckTwist02` and `[190, -165, 0]`). Check the result on the actual avatar in a desktop run.

## Gaze data on an avatar

- `addSceneObject(name, avatar, gaze=True, avatar=True)`: `gaze=True` gives dwell, fixations and views
  on the avatar as one object; `avatar=True` puts it in the replay. Use both. It works for code-loaded
  avatars and for Inspector ones fetched with `env.getChild` (the gaze ray returns that node).
- SightLab compares the gaze ray's first hit with the registered nodes, so there is no per-bone or
  per-mesh gaze. For face versus body, link an invisible region to a bone and register it:

```python
import vizshape
face = vizshape.addSphere(radius=0.15)
viz.link(avatar.getBone('Bip01 Head'), face)
sightlab.addSceneObject('npc_face', face, gaze=True, visible=False)
```

  `visible=False` sets alpha 0, which still takes the gaze ray; `face.visible(viz.OFF)` would not. The
  region is hit first, so face time is not also counted for `npc`. The head bone sits at the base of the
  head (1.59 m on `RocketBox_Male1.osgb`); show the region during a desktop run to place it.

## Avatars in the replay

With `avatar=True`, each frame stores the avatar's position, orientation, scale and the id of one running
loop (the highest-numbered). The replay reloads it with `vizfx.addAvatar` from its original path
(Inspector avatars from the environment by node name) and sets that loop. Not recorded: `execute()`
one-shots, blend weights, `speed()`, morphs, locked or turned bones (the head turned toward the participant),
and visibility (an avatar the script hides still shows). Scale is stored but not applied. Record such
changes with `sightlab.setCustomReplayFlag` (`guides/replay.md`). Without `avatar=True` the replay does
not load the object as an avatar and plays no animation on it.

## Recorded and video avatars

- `examples/Avatar_Playback` (2.9.0+): a recorded participant's head and hands (and voice) replay in a
  later live session as a confederate or demonstrator; not a full body. During setup,
  `playback = AvatarPlayback(rplyPath, sightlab=sightlab, gaze=True)` (`sightlab_utils.avatar_playback`);
  in the trial `playback.start()`, wait for `AVATAR_PLAYBACK_END`, `playback.stop()`. Gaze is recorded on
  `PlaybackAvatar_Head`; `getRoot()` moves the whole playback.
- `examples/Rotoscoped_Avatars`: a filmed person as an alpha-channel video on a quad at the stand-in; the
  sample video is not in the example folder. `examples/Avatar_Viewpoint`: an NPC's view in a second window.

## Custom avatars: what to tell the researcher

- Vizard loads avatars from `.cfg` (Cal3D: the vcc and Complete Character ones), `.osgb`, `.fbx` and
  `.gltf`/`.glb`. Check the file in Inspector first (height about 1.6–1.8 m, else insert a transform
  above the root to scale; animations and morphs listed) and keep it in the project's `Resources/`. Do
  not convert a rigged avatar by loading and saving it in a script: that strips the skeleton
  (`guides/models-and-assets.md`).
- Mixamo: rigged characters and an animation library, `Hips`/`Neck`/`Head` bones; add `.cfg` to the node
  name in Inspector for the GUI to list it. Reallusion (Character Creator, ActorCore): `Hip`,
  `NeckTwist02`, `Head`, many face morphs; the docs load these in code. RocketBox: Microsoft's free
  research library, `Bip01` rig.
- ReadyPlayerMe closed to new avatars in January 2026; earlier exports still load. Avaturn, MetaPerson,
  Daz 3D and RenderPeople also work; the Dashboard generates avatars with Meshy (2.8.9+) using the
  researcher's own key.
- Ids and bone names differ per source: print them (above) and keep them as constants in the script.

## Gotchas

- Animation ids start at 1 (`state(0)` plays nothing); morph ids start at 0.
- `blend()` adds to the loops already running: an earlier loop stays until `state()` or `stopCycle()`.
  The docs' `blend(1, 2, 0.5)` means animation 1 at weight 2 with a 0.5 s fade, not a 50% mix.
- Too dark or washed out: `avatar.disable(viz.LIGHTING)`, as the Driving and Scripted Avatar Agent do.
- Two NPCs from one file moving in lockstep: the Driving example loads repeats with `flags=viz.CACHE_NONE`.
- SightLab records every avatar registered with `avatar=True` every frame, checking each of its
  animations, used or not; the Driving example sizes its pedestrian pool to the trials' need for this. It
  also skips gaze registration of avatars in multi-user sessions, reporting that it breaks client set-up.
- The Scripted Avatar Agent has no language model, but its voice comes from OpenAI or ElevenLabs at run
  time: network, API keys and packages are the researcher's or WorldViz support's set-up.

## Shipped examples

`examples/Adding_NPC`, `examples/Scripted Avatar Agent` (fixed lines, mouth morph, head toward the
participant, ratings, avatar per trial from a STIM file), `examples/Gaze_Based_Interactions` (loops change
on gaze), `examples/PigeonHunt` (random walk loop), `examples/Driving` (pedestrian routes),
`examples/MixedReality` (`MixedReality_avatar.py`), `examples/Avatar_Playback`, `examples/Avatar_Viewpoint`,
`examples/Rotoscoped_Avatars`; conversation: `examples/AI_Intelligent_Agent` (`guides/ai-agents.md`).
