# 360 media: photos and videos

Sources: `reference/sightlab.py` (2.9.3) and `sightlab_utils/panorama_utils.py`, `extract_audio.py`,
`replay.py`; `examples/360 non GUI`, `examples/360_with_3D_Model`, `examples/RatingScale Multiple Paths`;
help.worldviz.com/sightlab 360-media, data-collection-with-360-media-for-eye-tracking,
360-with-3d-models, converting-360-spherical-to-equirectangular.

When to read: a trial's environment is a 360° or 180° photo or video, above all when a script plays,
pauses, seeks, loops, turns or swaps it; the media is 8K; the study needs gaze data on 360 media; 3D
objects sit over a 360 backdrop.

Covered elsewhere: `setEnvironment(..., mode=MEDIA_360, mediaFormat=...)` and the three formats
(`rules/environments-and-resources.md`); 360 trials and static ROIs in the GUI
(`guides/first-project.md`); moving ROIs (`guides/360-moving-regions.md`); replays and heatmaps
(`guides/replay.md`). A flat video on a screen in a 3D scene is `guides/virtual-screen.md`.

## Media, formats and sizes

- Shipped in `sightlab_resources/media/` (measured): `01_Warehouse.avi` 2560×2560 (top/bottom);
  `football_pass.avi` 1920×960 and the `skybox_*`/skyline images 6144×3072 (mono); `02_parking_lot.jpg`,
  `03_DRI.jpg`, `04_warehouse.jpg` 7680×7680 (top/bottom). Mono is 2:1, top/bottom usually square.
- The GUI lists only lowercase `jpg jpeg png tiff pdf raw gif bmp webp heif heic` and
  `mp4 mov avi wmv hevc flv mkv ogg m4v` files (not the documentation's `.mpg`, `.mpeg`, `.tif`). In
  code, anything `viz.addVideo` opens works; a video that will not play needs a codec pack that a
  person sets up following the documentation.
- 8K: the GUI path loads media with `panorama_utils.make_video`, which sends a video wider than 4096
  pixels to a PyAV player (`ExternalVideo`, decoding on a thread, NVDEC hardware when it can) if a
  person has set up SightLab's 8K video support; otherwise `viz.addVideo` plays it, perhaps poorly,
  after a one-time message. Images never use PyAV.
- The 4K test halves the width only for frames over three times as wide as tall: a 180° side-by-side at
  7680×3840 counts as 7680 and needs PyAV (the documentation says up to 4K per eye is fine).
- Weak GPU: `panorama_utils.DOWNSCALE_TARGET = (3840, 1920)` before the media loads (PyAV only).
- Each PyAV player reserves 14 frame buffers, about 1.2 GB at 7680×3840. GUI mode loads every trial's
  media at setup by default; with several 8K trials construct with `loadenvironmentmode=LOAD_BY_TRIAL`
  (SightLab removes each trial's player after the trial, so only one is held).

## A 360 study in code

One medium per trial, each ending when its video ends:

```python complete
import sightlab_utils.sightlab as sl
from sightlab_utils.settings import *

sightlab = sl.SightLab(gui=False)

# One trial per entry: file, mediaType, mediaFormat
MEDIA = [
	('sightlab_resources/media/01_Warehouse.avi', 'video', 'Stereoscopic T/B'),
	('sightlab_resources/media/football_pass.avi', 'video', 'Monoscopic'),
	('sightlab_resources/media/skybox_room1.jpg', 'image', 'Monoscopic'),
]
IMAGE_SECONDS = 10
sightlab.setTrialCount(len(MEDIA))

def loadMedia(path, mediaType, mediaFormat):
	media = viz.addVideo(path)   # images too: SightLab calls play() and pause() on it
	sightlab.setEnvironment(media, mode=MEDIA_360, mediaType=mediaType, mediaFormat=mediaFormat)
	return media

media = loadMedia(*MEDIA[0])

def sightLabExperiment():
	global media
	yield viztask.waitEvent(EXPERIMENT_START)
	for i, (path, mediaType, mediaFormat) in enumerate(MEDIA):
		if i > 0:
			media.pause()
			sightlab.getEnvironment().visible(viz.OFF)   # setEnvironment leaves the old sphere
			media = loadMedia(path, mediaType, mediaFormat)
		yield viztask.waitKeyDown(' ')
		yield sightlab.startTrial(trialLabel=path.split('/')[-1])
		yield viztask.waitEvent(TRIAL_START)   # after the fade, as SightLab plays and loops the media
		yield viztask.waitTime(media.getDuration() if mediaType == 'video' else IMAGE_SECONDS)
		yield sightlab.endTrial()

viztask.schedule(sightlab.runExperiment)
viztask.schedule(sightLabExperiment)
viz.callback(viz.getEventID('ResetPosition'), sightlab.resetViewPoint)
```

- A 360 `setEnvironment` builds a new sphere on every call and never removes the last; both draw at
  `drawOrder(-100)` without depth test, so hide the old one. `trial=` does not defer the swap: swap
  between trials, before `startTrial` (`examples/RatingScale Multiple Paths` does), and that trial's
  data and replay name the right file, type and format.
- Images go through `viz.addVideo` too (as in SightLab, `make_video` and the examples): every 360 trial
  calls `play()`, `loop()`, `pause()`, `getTime()` and `getState()` on the media, which a
  `viz.addTexture` texture lacks. `mediaType` only labels the trial; it changes no playback. An image
  never ends: end its trial on time or a response.
- 8K in code: `setEnvironment` uses the object as given, so route it through PyAV yourself (assembled
  from `extract_audio.py`'s usage note; no shipped example, so check it on the first run). `remove()`
  a PyAV player when done with it, as GUI mode does.

```python
from sightlab_utils import panorama_utils, extract_audio
video, isExternal = panorama_utils.make_video(path)    # PyAV above 4K, else viz.addVideo
video = extract_audio.attach(path, video, isExternal)  # sound for the PyAV player
sightlab.setEnvironment(video, mode=MEDIA_360, mediaType='video', mediaFormat='Monoscopic')
```

## Controlling playback

- `sightlab.getMediaObject()` is the video or image, `sightlab.getEnvironment()` its sphere. In GUI
  mode the media object is `None` between trials.
- SightLab itself: GUI mode rewinds and pauses each trial's media as the trial loads; both modes call
  `play()` and `loop()` right after sending `TRIAL_START`, and `pause()` as the trial ends. Code mode
  never rewinds: reusing a media object, call `media.setTime(0)` before `startTrial`. A `play()` of
  your own after `startTrial` (as in `examples/360 non GUI`) is harmless.
- On the media: `play()`, `pause()`, `setTime(seconds)`, `getTime()`, `getDuration()`, `loop(viz.OFF)`,
  `getState()` (`viz.MEDIA_RUNNING`, `viz.MEDIA_PAUSED`, `viz.MEDIA_STOPPED`); the 8K player has them too.
- A task waiting on `TRIAL_START` resumes inside the event, before SightLab's `play()` and `loop()`.
  To play once or start paused, `yield viztask.waitFrame(1)` after it, then
  `sightlab.getMediaObject().loop(viz.OFF)` or `.pause()`.
- Ending at the media's end: the GUI's Media End is a trial timer of the length it shows ("Length
  (secs)"), not a watch for the end. In code, wait `getDuration()` after `TRIAL_START` (script above)
  or pass `startTrial(trialLength=...)`. `viztask.waitMediaEnd` never fires for the 8K player.
- Keys: `sightlab.toggleMediaPause()` is always on Shift+P; `sightlab.enableMediaSkipKeys()` adds V
  and C (5 s forward and back). Pausing the media stops neither the trial timer nor the data.
- The replay follows recorded pauses, but while playing it re-seeks only on a jump of nearly the
  whole video (a loop): after a seek in the experiment, drag the replay's slider to resync.

## Turning the sphere (starting orientation)

- Unturned, straight ahead (+Z) is the frame's left/right edge and azimuth grows to the right, so the
  frame's centre is behind the participant (vizshape's inside-out sphere; the 360 ROI documentation
  says the same). Yaw 180 brings the centre forward, as the `360_with_3D_Model` spheres do. The real
  heading also depends on the headset's forward; `ResetPosition` (R) recentres.
- Code mode, after `setEnvironment`: `sightlab.getEnvironment().setEuler([180, 0, 0])`, or
  `sightlab.setEnvironmentOffset(euler=(180, 0, 0))`, the same underneath; its `scale=` sizes the
  sphere and `pos=` adds to earlier offsets.
- GUI mode builds the spheres itself, so the documentation patches the class before SightLab is
  created (`StereoSphere` likewise for top/bottom):

```python
import sightlab_utils.panorama_utils as panorama_utils
_orig_init = panorama_utils.MonoSphere.__init__
def _turned_init(self, *args, **kwargs):
	_orig_init(self, *args, **kwargs)
	self.setEuler([180, 0, 0])
panorama_utils.MonoSphere.__init__ = _turned_init
```

- The turn is not recorded (360 replay data keeps the media's time and state, not the sphere): the
  replay script turns its sphere too, `replay.sceneObjects[MEDIA_OBJECT].setEuler(180, 0, 0)` at start
  and on `TRIAL_LOADED_EVENT` (documentation). In the replay `MEDIA_OBJECT` is the sphere and
  `replay.mediaFile` the video; in the experiment `MEDIA_OBJECT` is the video.
- The L/R sphere already has yaw −90: add to it. GUI ROIs are fixed in the world, so turn before
  drawing them; moving ROIs turn with the sphere.
- `sightlab.enableEnvironmentPitchKeys()` (7, 8) changes the sphere's roll: a tilt on the 180° sphere,
  a roll on a 360 sphere.

## Audio

- Up to 4K (`viz.addVideo`) the video's own sound plays; `media.volume(0)` mutes it.
- 8K through PyAV: the sound is a WAV beside the video, named after it plus _audio, made on first use
  with ffmpeg (imageio-ffmpeg's or one on the PATH) as 48 kHz stereo; 4-channel ambisonic sound is
  mixed down, so it does not follow head turns. Without ffmpeg the video is silent (console lines
  start `[extract_audio]`). Delete the WAV after replacing the video.
- The WAV is re-synced only on `play()` and `setTime()`; the 8K player and its sound wrapper have no
  `volume()`. Replays of 8K videos are silent (the replay loads them without the WAV).

## Gaze data on 360 media

- The media is not a gaze object: without ROIs no dwell or fixation rows exist for parts of it and
  `view status` stays `None`. Add ROIs (GUI, or the moving-ROI tracer).
- Each `trial_data` row still has where gaze met the sphere, `combined eye intersect x/y/z` (and per
  eye), in world coordinates. The sphere has a 1 m radius and follows the head position (`head x/y/z`),
  so there is no parallax. `combined eye yaw/pitch/roll` are eye-in-head angles; fixation and
  gaze-angle columns work without ROIs. A model or ROI in front of the sphere takes the hit instead.
- Into the frame (360 spheres): d = intersect − head; azimuth = atan2(dx, dz), elevation =
  atan2(dy, hypot(dx, dz)) (`moving_rois.py`'s `angles`), minus any yaw given to the sphere; column =
  (azimuth mod 360) / 360 × width from the left edge, row = (90 − elevation) / 180 × height (top/bottom
  stereo: the top half).
- `examples/convert_to_pixels` predates these files: it reads tab-separated rows with x, y, z in
  columns 2–4, takes z as up (Vizard's up is y) and ignores the head position. Compute as above.
- Video time is not a `trial_data` column; the replay file stores it each frame. In GUI mode trial
  time is about video time until the first loop.

## 3D models over 360 media

- `examples/360_with_3D_Model` is a 3D trial (`empty.osgb`, default `MODEL_3D`) with its own
  `vizshape.addSphere(flipFaces=True)` scaled 10, yaw 180, `disable(viz.DEPTH_TEST)` and
  `drawOrder(-100)` so models draw over it, and `crate.osgb` registered with `gaze=True, grab=True`.
  SightLab does not know that sphere: the script plays it (V toggles, B restarts), the replay has no
  video time, and it stays put as the participant walks. `examples/Biofeedback` (its
  `360_with_3D_Model` folder) does the same with its own `high_res_video.py` for 8K.
- Or a `MEDIA_360` trial plus models registered with `addSceneObject`: the sphere draws behind
  everything, but gaze takes the first hit and the sphere is 1 m away, so gaze on a model farther out
  lands on the sphere; enlarge it past the models (`setEnvironmentOffset(scale=...)`). GUI-mode 360
  trials also hide the hands and stop the transport (not for L/R). No shipped example: check on a run.

## Gotchas

- Media End on an 8K PyAV video fails in 2.9.3: SightLab calls `stoptime()` on the media, which the
  PyAV player and its sound wrapper lack. Use a Timer of the video's length (the same trial timer).
- L/R in code mode: SightLab shows its 180° backdrop (`sightlab.dome180`) only in GUI or config mode,
  so the back half of the sphere is uncovered; `sightlab.dome180.visible(viz.ON)` does what the GUI does.
- `getRegionOfInterest` returns `None` for GUI and tracer ROIs in 2.9.3 (`guides/360-moving-regions.md`).

## Shipped examples

`examples/360 non GUI` (code-only basics), `examples/RatingScale Multiple Paths` (media chosen by a
rating, swapped with `setEnvironment`), `examples/360_with_3D_Model`, `examples/Biofeedback`,
`examples/360 Moving Regions of Interest`, `examples/convert_to_pixels`, `examples/Group_Heatmap_Replay`
(360 heatmaps across participants), `examples/Virtual 2D Screen` (contrast: a flat screen in 3D).
