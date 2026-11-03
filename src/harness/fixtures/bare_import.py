import sightlab_utils.sightlab
from sightlab_utils.settings import *
import vizshape

sightlab = sightlab_utils.sightlab.SightLab(gui=False)
env = vizfx.addChild('sightlab_resources/environments/complete_scene.osgb')
sightlab.setEnvironment(env)

cube = vizshape.addCube(size=0.2)
cube.setPosition([0, 1.6, 2])
sightlab.addSceneObject('cube', cube, gaze=True)
sightlab.setTrialCount(3)
sightlab.fooBar()


def sightLabExperiment():
    yield viztask.waitEvent(EXPERIMENT_START)
    for i in range(sightlab.getTrialCount()):
        yield sightlab.startTrial(startTrialText='Look at the cube.')
        yield viztask.waitTime(5)
        yield sightlab.endTrial()


viztask.schedule(sightlab.runExperiment)
viztask.schedule(sightLabExperiment)
viz.callback(viz.getEventID('ResetPosition'), sightlab.resetViewPoint)
