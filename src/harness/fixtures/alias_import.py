from sightlab_utils import sightlab as S
from sightlab_utils.settings import *
import vizshape

lab = S.SightLab(gui=False)
env = vizfx.addChild('sightlab_resources/environments/complete_scene.osgb')
lab.setEnvironment(env)

cube = vizshape.addCube(size=0.2)
cube.setPosition([0, 1.6, 2])
lab.addSceneObject('cube', cube, gaze=True)
lab.setTrialCount(3)


def sightLabExperiment():
    yield viztask.waitEvent(EXPERIMENT_START)
    for i in range(lab.getTrialCount()):
        yield lab.startTrial(startTrialText='Look at the cube.')
        yield viztask.waitTime(5)
        yield lab.endTrial()


viztask.schedule(lab.runExperiment)
viztask.schedule(sightLabExperiment)
viz.callback(viz.getEventID('ResetPosition'), lab.resetViewPoint)
