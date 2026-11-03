# Source: ExampleScripts/Instructions/instructions_example.py
# SightLab 2.x shipped example, copied unchanged below this header by the AI Kit on 2026-10-30.
import sightlab_utils.sightlab as sl
from sightlab_utils.settings import *

sightlab = sl.SightLab(gui = False, pid = False)

env = vizfx.addChild("sightlab_resources/environments/dojo.osgb")
sightlab.setEnvironment(env)

basketball = env.getChild('basketball')
sightlab.addSceneObject("basketball", basketball, gaze = True, grab = True)

#set number of trials
sightlab.setTrialCount(3)

import viztask
def sightLabExperiment():
	yield viztask.waitEvent(EXPERIMENT_START)
	for i in range(0, sightlab.getTrialCount()):
		if not i == 0:
			yield viztask.waitKeyDown(' ')	
			
		yield sightlab.startTrial(startExperimentText = "Press trigger to start", textContinueEvent = "triggerPress")	
		
		yield viztask.waitKeyDown(' ')		
		yield sightlab.endTrial(endExperimentText = 'Done')
		

viztask.schedule(sightlab.runExperiment)
viztask.schedule(sightLabExperiment)