import sightlab_utils.sightlab as sl
from sightlab_utils.settings import *
import vizshape


class Study:
    def __init__(self):
        self.sightlab = sl.SightLab(gui=False, headlight=True)
        env = vizfx.addChild('sightlab_resources/environments/complete_scene.osgb')
        self.sightlab.setEnvironment(env)
        self.cube = vizshape.addCube(size=0.2)
        self.sightlab.addSceneObject('cube', self.cube, gaze=True)
        self.sightlab.setTrialCount(2)
        self.sightlab.fooBar()
        viztask.schedule(self.sightlab.runExperiment)
        viztask.schedule(self.run)

    def run(self):
        yield viztask.waitEvent(EXPERIMENT_START)
        for i in range(self.sightlab.getTrialCount()):
            yield self.sightlab.startTrial()
            yield viztask.waitTime(5)
            yield self.sightlab.endTrial()


study = Study()
