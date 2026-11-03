# Source: ExampleScripts/Sample Code/SightLab_VR_GUI.py
# SightLab 2.x shipped example, copied unchanged below this header by the AI Kit on 2026-10-30.
import sightlab_utils.sightlab as sl
from sightlab_utils.settings import *

sightlab = sl.SightLab()

def sightLabExperiment(): 
	yield viztask.waitEvent(EXPERIMENT_START)
	viz.callback(viz.getEventID('ResetPosition'), sightlab.resetViewPoint)
	
	for trial in range(sightlab.getTrialCount()):
		yield viztask.waitEvent(TRIAL_START)
		
		yield viztask.waitEvent(TRIAL_END)

viztask.schedule(sightlab.runExperiment)
viztask.schedule(sightLabExperiment)