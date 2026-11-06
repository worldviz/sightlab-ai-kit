# AI object detection

Sources: help.worldviz.com/sightlab ai-object-detection and ai-ar-object-detection;
`sightlab_utils/yolox_object_detection.py` and `volume_manager.py` (2.9.3). The older
`ai_objectdetection_v2` page is superseded.

When to read: the study needs gaze on things that are not registered scene objects (a scene
too large to tag by hand, or another application's window in AR mode), found automatically
while the participant looks around.

## What it is

`YOLOXObjectDetection` runs a YOLOX detector on the rendered view while a trial runs. Each
tracked detection becomes a gaze volume named `yolo_<class>_<tracker id>` (for example
`yolo_person_3`), so it collects gaze data like a registered object. Bounding boxes and
labels are drawn on the desktop mirror window only, never in the headset.

It needs an NVIDIA GPU and the object-detection packages, which a person installs with
WorldViz's installer; the module imports `torch` as it loads, so the import fails on a PC
without them. On a headset without an eye tracker the "gaze" on a detection is the view
direction; label it so (`guides/hardware.md`).

## Using it

Build the detector once, start it after each `startTrial`, and end it, with `yield`, before
each `endTrial`:

```python
from sightlab_utils.yolox_object_detection import YOLOXObjectDetection

detector = YOLOXObjectDetection(viz, sightlab, confidence=0.6)

def sightLabExperiment():
    yield viztask.waitEvent(EXPERIMENT_START)
    for trial in range(sightlab.getTrialCount()):
        yield viztask.waitKeyDown(' ')
        yield sightlab.startTrial()
        detector.startDetection()
        yield viztask.waitKeyDown(' ')
        yield detector.endDetection()
        yield sightlab.endTrial()
```

Constructor keywords (2.9.3 defaults): `confidence=0.6`, `interval=0.1` (seconds between
frames sent to the detector), `nms=0.45`, `useBoundingBoxOverlay=True`,
`useVolumeManager=True`, `maxTrackedVolumes=15`, `showVolumesInHMD=True`,
`showVolumesInMirror=True`, `volumeAlpha=0.25`, `showLabels=True`, `enableGazeTracking=True`,
`showBoundingBoxes=True`, `boundingBoxThickness=2`, `boundingBoxColor=[0,1,0]`, `AR=False`.
The upper-case names in the documentation (`USE_BOUNDING_BOXES`, ...) belong to the
example's config file, not to the constructor.

While it runs, `m` toggles the volumes in the mirror, `i` in the headset, `b` the boxes.

## Gotchas

- `useVolumeManager=False` crashes `startDetection()` in 2.9.3 (it calls the volume manager
  unconditionally); keep it `True` and hide volumes with `showVolumesInHMD=False` and
  `showVolumesInMirror=False` instead.
- `AR=True` asks for the window to capture inside the constructor, which is why the
  detector is built once, before the loop.
- `startDetection()` binds `m`, `i` and `b` again each time, so after several trials one key
  press can toggle more than once.
- Make the Vizard window full screen before the first trial: resizing it while detection
  runs misplaces the boxes.
- The same real object can get several tracker ids when tracking loses it; group by class
  when analysing.
- The desktop autopilot cannot check detection quality or timing; a person checks it on the
  GPU machine.

## Shipped examples

`examples/AI_ObjectDetection`, `examples/AI_AR_Object_Detection`. Detection on a recording
after the fact, outside SightLab, is the External Data Recorder's (`guides/data-recorder.md`).
