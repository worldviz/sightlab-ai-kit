# Source: ExampleScripts/Proximity Sensors/proximitySensors_example.py
# SightLab 2.x shipped example, copied unchanged below this header by the AI Kit on 2026-10-30.
"""Proximity sensors around an object and on the floor, with hand and head targets.

- Touch the blue ball with either hand: a beep plays, and Space then ends the trial.
  (Space before the touch does nothing.)
- Walk onto the 1 x 1 m square on the floor, ahead and to the left of the start: a
  beep plays.

Each trial writes every entry into and exit from the square, and every touch, to the
trial data's flag column, and the time to the first touch and the hand that made it
to the experiment summary. 'm' shows or hides the sensors' outlines.

To use your own object as a sensor, replace the ball: addBoundingSphereSensor(node)
and addBoundingBoxSensor(node) fit a sensor around any object.
"""
import vizshape
import vizproximity
import sightlab_utils.sightlab as sl
from sightlab_utils.settings import *

TRIAL_COUNT = 3
BALL_RADIUS = 0.1
BEEP = 'sightlab_resources/audio/beep.wav'
START_TEXT = 'Touch the blue ball with either hand.\n\nPress Space to start.'
END_TEXT = 'Done. Thank you!'

sightlab = sl.SightLab(gui = False)
sightlab.setTrialCount(TRIAL_COUNT)

env = vizfx.addChild('sightlab_resources/environments/Business_Office.OSGB')
sightlab.setEnvironment(env)

# Create objects
ball = vizshape.addSphere(radius = BALL_RADIUS)
ball.color(viz.BLUE)
ball.setPosition(0, 1.5, 2)
# Registered with SightLab, so the ball is in the gaze data and the replay
sightlab.addSceneObject('ball', ball, gaze = True)

# Load the beep now, so the first one plays without a delay
viz.playSound(BEEP, viz.SOUND_PRELOAD)

# The ball detects the hands
avatar = vizconnect.getAvatar()
rhand_target = vizproximity.Target(avatar.getAttachmentPoint('r_hand').getNode3d())
lhand_target = vizproximity.Target(avatar.getAttachmentPoint('l_hand').getNode3d())
HAND_NAMES = {rhand_target: 'right hand', lhand_target: 'left hand'}

handManager = vizproximity.Manager()
handManager.addTarget(rhand_target)
handManager.addTarget(lhand_target)

# A sensor the size of the ball. addBoundingSphereSensor(ball) would be 0.17 m: a
# sphere's bounding sphere is the one around its bounding box
BallSensor = handManager.addSensor(vizproximity.Sensor(vizproximity.Sphere(BALL_RADIUS), source = ball))

# The floor square detects the participant's viewpoint
target = vizproximity.Target(viz.MainView)
areaManager = vizproximity.Manager()
areaManager.addTarget(target)

# A 1 x 1 m square on the floor, ahead and to the left of the start, clear of the
# walk to the ball
FloorArea = areaManager.addSensor(vizproximity.Sensor(vizproximity.RectangleArea([1, 1], center = [-0.9, 1.0]), None))

# Proximity events are recorded only while a trial runs. Between trials SightLab
# has no trial data to write them to
trialRunning = False

def onTrialStart():
	global trialRunning
	trialRunning = True
	# Standing on the square already: there is no entry to record
	if FloorArea in areaManager.getActiveSensors(target):
		recordFlag('on floor area at trial start')

def onTrialEnd():
	global trialRunning
	trialRunning = False

vizact.addCallback(TRIAL_START, onTrialStart)
vizact.addCallback(TRIAL_END, onTrialEnd)

def recordFlag(text):
	"""Write text to the trial data's flag column, on this frame."""
	if trialRunning:
		sightlab.setCustomTrialData(text)

# Register callbacks for proximity sensors
def EnterFloorArea(e):
	viz.playSound(BEEP)
	print('Entered floor area')
	recordFlag('entered floor area')

def ExitFloorArea(e):
	print('Exited floor area')
	recordFlag('exited floor area')
areaManager.onEnter(FloorArea, EnterFloorArea)
areaManager.onExit(FloorArea, ExitFloorArea)

def TouchBall(e):
	viz.playSound(BEEP)
	print('Ball touched with the', HAND_NAMES[e.target])
	recordFlag('ball touched with the ' + HAND_NAMES[e.target])
handManager.onEnter(BallSensor, TouchBall)

# Press "m" to show or hide the sensors' outlines ("d" would also strafe right on Desktop)
handManager.setDebug(True)
areaManager.setDebug(True)
vizact.onkeydown('m', handManager.setDebug, viz.TOGGLE)
vizact.onkeydown('m', areaManager.setDebug, viz.TOGGLE)

def sightLabExperiment():
	yield viztask.waitEvent(EXPERIMENT_START)
	for trial in range(1, TRIAL_COUNT + 1):
		yield sightlab.startTrial(trialLabel = 'Trial_{}'.format(trial), startTrialText = START_TEXT, textContinueKey = ' ')
		startTime = viz.tick()

		e = yield vizproximity.waitEnter(BallSensor, [rhand_target, lhand_target])
		print('hand sensor activated')
		# SightLab keeps these columns from trial to trial, so set them every trial
		sightlab.setExperimentSummaryData('Time to Touch Ball (secs)', round(viz.tick() - startTime, 3))
		sightlab.setExperimentSummaryData('Touched With', HAND_NAMES[e.target])

		yield viztask.waitKeyDown(' ')
		yield sightlab.endTrial(endExperimentText = END_TEXT)

viztask.schedule(sightlab.runExperiment)
viztask.schedule(sightLabExperiment)
viz.callback(viz.getEventID('ResetPosition'), sightlab.resetViewPoint)
