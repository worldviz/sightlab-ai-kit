# Source: ExampleScripts/Randomize/SightLab_VR_Randomize_Blocks.py
# SightLab 2 shipped example, copied unchanged below this header by the AI Kit on 2026-10-30.
import sightlab_utils.sightlab as sl
from sightlab_utils.settings import *

#Setup SightLab Options
sightlab = sl.SightLab(gui = False, configpath = "sightlab_configs/Randomize Blocks.stlb", repetitions = 2)

def sightLabExperiment():
	yield viztask.waitEvent(EXPERIMENT_START)

	for trial in range(sightlab.getTrialCount()):
		if sightlab.getTrialNumber() == 1 and sightlab.getCurrentRepetition() == 1:
			yield sightlab.startTrial(condition = [NO_CONDITION, ""], startExperimentText = 
			"Press trigger When Ready")
		elif sightlab.getTrialNumber() > 1:
			yield viztask.waitEvent(TRIAL_START)
		
		yield viztask.waitEvent(TRIAL_END)
	
viztask.schedule(sightlab.runExperiment)
viztask.schedule(sightLabExperiment)
viz.callback(viz.getEventID('ResetPosition'), sightlab.resetViewPoint)