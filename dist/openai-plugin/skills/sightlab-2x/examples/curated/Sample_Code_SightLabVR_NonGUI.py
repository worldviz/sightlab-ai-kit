# Source: ExampleScripts/Sample Code/SightLabVR_NonGUI.py
# SightLab 2.x shipped example, copied unchanged below this header by the AI Kit on 2026-10-30.
import sightlab_utils.sightlab as sl
from sightlab_utils.settings import *

# Initialize SightLab without GUI
sightlab = sl.SightLab(gui = False)

# Load and set the environment (must be defined before scene objects)
env = vizfx.addChild("sightlab_resources/environments/dojo.osgb")
sightlab.setEnvironment(env)

#set number of trials
sightlab.setTrialCount(3)

#add objects of interest
soccerball = env.getChild('soccerball')
basketball = env.getChild('basketball')
sightlab.addSceneObject('soccerball', soccerball,gaze = True, grab = True)
sightlab.addSceneObject('basketball', basketball,gaze = True, grab = True)

#run sightlab experiment
def sightLabExperiment():
	yield viztask.waitEvent(EXPERIMENT_START)
	for i in range(0, sightlab.getTrialCount()):
		yield viztask.waitKeyDown(' ')
		yield sightlab.startTrial()

		yield viztask.waitKeyDown(' ')
		yield sightlab.endTrial()

viztask.schedule(sightlab.runExperiment)
viztask.schedule(sightLabExperiment)
viz.callback(viz.getEventID('ResetPosition'), sightlab.resetViewPoint)