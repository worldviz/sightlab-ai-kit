# Source: ExampleScripts/Gaze_Based_Interactions/Gaze_Based_Interaction_Simple.py
# SightLab 2 shipped example, copied unchanged below this header by the AI Kit on 2026-10-30.
import sightlab_utils.sightlab as sl
from sightlab_utils.settings import *
import vizshape

# Initialize SightLab without GUI
sightlab = sl.SightLab(gui=False)

# Set environment
env = vizfx.addChild('sightlab_resources/environments/complete_scene.osgb')
sightlab.setEnvironment(env)
sightlab.setStartText(' ')

# Add a gazeable object (a red cube)
cube = vizshape.addCube(size=0.2, color=viz.RED)
cube.setPosition([0, 1.6, 2])
sightlab.addSceneObject('CubeObject', cube, gaze=True)

# Define callback functions for gaze events
def gazeActionStart(e):
	if e.object == sightlab.sceneObjects[GAZE_OBJECTS]['CubeObject']:
		print("👁️ Gaze started on CubeObject!")
		cube.color(viz.BLUE)

def gazeActionEnd(e):
	if e.object == sightlab.sceneObjects[GAZE_OBJECTS]['CubeObject']:
		print("❌ Gaze ended on CubeObject.")
		cube.color(viz.RED)

# Register gaze event callbacks
vizact.addCallback(sightlab.GAZE_TIME_EVENT, gazeActionStart)
vizact.addCallback(sightlab.GAZE_END_EVENT, gazeActionEnd)

# Define the experiment logic
def sightLabExperiment():
	yield viztask.waitEvent(EXPERIMENT_START)
	for i in range(sightlab.getTrialCount()):
		yield sightlab.startTrial(startTrialText="Look at the red cube to begin tracking gaze.")

		# Let the participant gaze around for 10 seconds
		yield viztask.waitTime(10)

		yield sightlab.endTrial(endTrialText="Trial ended. Good job!")

# Schedule experiment
viztask.schedule(sightlab.runExperiment)
viztask.schedule(sightLabExperiment)
viz.callback(viz.getEventID('ResetPosition'), sightlab.resetViewPoint)
