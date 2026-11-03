# Source: ExampleScripts/Memory_Experiment/Memory_Task.py
# SightLab 2 shipped example, copied unchanged below this header by the AI Kit on 2026-10-30.
import sightlab_utils.sightlab as sl
from sightlab_utils.settings import *
import vizinfo
import vizproximity
import vizshape

#Set up the environment and proximity sensors
sightlab = sl.SightLab(gui= False, headlight = True)
sightlab.setStartText(' ')
dojo = viz.addChild('dojo.osgb')
sightlab.setEnvironment(dojo)

sightlab.setTrialCount(6)

#Create proximity manager and set debug on. Toggle debug with m key
manager = vizproximity.Manager()
manager.setDebug(viz.OFF)
debugEventHandle = vizact.onkeydown('m',manager.setDebug,viz.TOGGLE)

#Add main viewpoint as proximity target
target = vizproximity.Target(viz.MainView)
manager.addTarget(target)

#fade to true color when viewpoint moves near
def EnterSphere(e, sphere, color):
	sphere.runAction(vizact.fadeTo(color,time=1))

#fade to white when viewpoint moves away
def ExitSphere(e, sphere):
	sphere.runAction(vizact.fadeTo(viz.WHITE,time=1))

#add spheres and create a proximity sensor around each one
sphereSensors = []
def AddSphere(name, color, position):

	sphere = vizshape.addSphere(radius=0.2)
	sphere.setPosition(position)
#	sightlab.addSceneObject(name,sphere, gaze = True)

	sensor = vizproximity.addBoundingSphereSensor(sphere,scale=5)
	sensor.name = name
	sphereSensors.append(sensor)
	manager.addSensor(sensor)

	manager.onEnter(sensor, EnterSphere, sphere, color)
	manager.onExit(sensor, ExitSphere, sphere)

AddSphere('red', viz.RED, [0,1.8,4])
AddSphere('blue', viz.BLUE, [3.5,1.8,2])
AddSphere('yellow', viz.YELLOW, [3.5,1.8,-2])
AddSphere('green', viz.GREEN, [0,1.8,-4])
AddSphere('purple', viz.PURPLE, [-3.5,1.8,-2])
AddSphere('gray', viz.GRAY, [-3.5,1.8,2])

#Add a sensor in the center of the room for the participant to return to after each trial
centerSensor = vizproximity.Sensor(vizproximity.CircleArea(1.5,center=(0.0,0.0)),None)
manager.addSensor(centerSensor)

def learnPhase():
	yield viztask.waitTime(0)
	yield sightlab.startTrial(trialLabel = 'Learning', trackingDataLogging= False,experimentSummaryLogging = False,replayDataLogging= False, timeLineLogging = False, fixationLogging = False)
	
	#let participant know learning phase has ended
	yield viztask.waitTime(30)
	yield sightlab.showInstructions("Please return to the center of the room to begin the testing phase", pauseTimer = True)
	yield viztask.waitEvent('triggerPress')
	yield sightlab.hideInstructions()
	
	#Start testing phase after 5 seconds
	yield viztask.waitTime(5)
	yield sightlab.endTrial()

def testPhase():

	results = []
	trials = [3,2,0,4,1]
	labels = ['Green','Yellow','Red','Purple','Blue']

	for i, label in zip(trials, labels):
		yield sightlab.startTrial(trialLabel=label, trackingDataLogging= True,experimentSummaryLogging = True,replayDataLogging= True, timeLineLogging = True, fixationLogging = True)
		yield sightlab.setDataLoggingState(0)
		#Check to see if participant is already in room center. If not
		#wait until the centerSensor is activated
		if centerSensor not in manager.getActiveSensors():
			yield vizproximity.waitEnter(centerSensor)

		#Get sensor for this trial
		sensor = sphereSensors[i]
		#Instruct participant where to go
		instruction = 'Walk to the {} sphere'.format(sensor.name)
		yield sightlab.showInstructions(instruction, pauseTimer = True)
		yield viztask.waitEvent('triggerPress')
		yield sightlab.hideInstructions()
		yield sightlab.setDataLoggingState(1)

		#store the time at which this trial started
		startTime = viz.tick()

		#The yielded command returns a viz.Data object with information
		#about the proximity event such as the sensor, target involved
		yield vizproximity.waitEnter(sensor)

		#calculate the time it took for the subject to find the correct object,
		#when they reach it (not after they dismiss "You Found It!")
		elapsedTime = viz.tick() - startTime

		# Round elapsedTime to 4 decimal places
		elapsedTime = round(elapsedTime, 4)

		yield sightlab.showInstructions('You Found It! \n\nPlease return to the center of the room', pauseTimer = True)
		yield viztask.waitEvent('triggerPress')
		yield sightlab.hideInstructions()

		#save results
		results.append((sensor.name, elapsedTime))
		sightlab.setExperimentSummaryData('Trial Length',elapsedTime)
		yield sightlab.endTrial(endExperimentText = 'Thank You. You have completed the experiment')

	#return results
	viztask.returnValue(results)

def experiment():
	yield viztask.waitEvent(EXPERIMENT_START)
	#Wait for spacebar to begin experiment
	yield sightlab.showInstructions("Explore the environment\nPress 'm' to toggle the visibility of the sensors\nPress trigger to begin the experiment")
	yield viztask.waitEvent('triggerPress')
	yield sightlab.showInstructions("You'll have 30 seconds to walk around and learn the true color of each sphere", pauseTimer = True)
	yield viztask.waitEvent('triggerPress')
	yield sightlab.hideInstructions()
	
	#Proceed through experiment phases
	yield learnPhase()
	results = yield testPhase()
	yield sightlab.endTrial(endExperimentText = 'Thank You. You have completed the experiment')

viztask.schedule(experiment)
viztask.schedule(sightlab.runExperiment)
viz.callback(viz.getEventID('ResetPosition'), sightlab.resetViewPoint)
