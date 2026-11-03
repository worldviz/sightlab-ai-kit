# Source: ExampleScripts/RatingScale_GUI/RatingScale_Sample.py
# SightLab 2 shipped example, copied unchanged below this header by the AI Kit on 2026-10-30.
import sightlab_utils.sightlab as sl
from sightlab_utils.settings import *

# Initialize SightLab without GUI
sightlab = sl.SightLab(gui = False)
sightlab.setStartText(' ')

# Load and set the environment (must be defined before scene objects)
env = vizfx.addChild("sightlab_resources/environments/Business_Office.osgb")
sightlab.setEnvironment(env)

#set number of trials
sightlab.setTrialCount(1)

#add objects of interest
Plant = env.getChild('Plant')
sightlab.addSceneObject('Plant', Plant,gaze = True)

#run sightlab experiment
def sightLabExperiment():
	yield viztask.waitEvent(EXPERIMENT_START)
	for i in range(0, sightlab.getTrialCount()):
		yield sightlab.startTrial(startTrialText="Press Trigger to Start")
		yield viztask.waitTime(5)
		
		yield sightlab.showRatings("What is Your Rating?", ratingScale=["Low", "Med", "High"],endFade = False)
		sightlab.setExperimentSummaryData('rating choice',sightlab.ratingChoice)
		yield viztask.waitTime(0.1)
		yield sightlab.endTrial()

viztask.schedule(sightlab.runExperiment)
viztask.schedule(sightLabExperiment)
viz.callback(viz.getEventID('ResetPosition'), sightlab.resetViewPoint)