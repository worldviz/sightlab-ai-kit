# Source: ExampleScripts/Reaction Time/reactionTime.py
# SightLab 2.x shipped example, copied unchanged below this header by the AI Kit on 2026-10-30.
import sightlab_utils.sightlab as sl
from sightlab_utils.settings import *
import vizshape
import vizact
import vizmat

# Initialize SightLab
sightlab = sl.SightLab(gui=False, headlight=True)
sightlab.setTrialCount(1)

FADE_IN_SPHERE = 0.1  # seconds the sphere takes to fade out

# Load Environment
env = vizfx.addChild('dojo.osgb')
sightlab.setEnvironment(env)

# Create Sphere
sphere = vizshape.addSphere(radius=0.2, color=viz.RED)
sightlab.addSceneObject("target_sphere", sphere, gaze=True)  # Enable gaze tracking

# While hidden, the sphere waits here, under the floor
PARKED_POSITION = [0, -10, 0]

def hideSphere():
    """Hides the sphere. visible() rather than alpha() so the replay records it,
    and no intersection so gaze can't land on it. SightLab's instruction screens
    turn every scene object back on, so it also waits under the floor."""
    sphere.visible(viz.OFF)
    sphere.disable(viz.INTERSECTION)
    sphere.setPosition(PARKED_POSITION)

def showSphere(position):
    sphere.alpha(1)  # undo the last fade-out
    sphere.setPosition(position)
    sphere.enable(viz.INTERSECTION)
    sphere.visible(viz.ON)

hideSphere()  # Initially hidden

sphereFade = vizact.fadeTo(0, time=FADE_IN_SPHERE)
textFade = vizact.sequence(
    vizact.fadeTo(1, time=0.8, interpolate=vizact.easeOut),
    vizact.waittime(2),
    vizact.fadeTo(0, time=0.8, interpolate=vizact.easeOut)
)

# Display Reaction Time
timeDisplay = viz.addText("Time:", viz.SCREEN, pos=(0.05, 0.05, 0))
timeDisplay.alpha(0)

positions = [[1, 2, 3], [-2, 1, 3], [1.5, 1.5, 3], [0, 0.5, 3]]

# The sphere's current showing: when it was drawn, when the latest look at it
# began, and the reaction time once it has been found
showing = {'onset': None, 'gazeStart': None, 'reactionTime': None}


def gazeBegin(e):
    """Gaze landed on the sphere: note when, in case this look reaches the dwell time"""
    if e.object == sphere:
        showing['gazeStart'] = viz.tick()


def gazeActionStart(e):
    """Triggered when user has looked at the sphere for the dwell time"""
    if (e.object == sightlab.sceneObjects[GAZE_OBJECTS]['target_sphere']
            and showing['onset'] is not None and showing['reactionTime'] is None):
        # The reaction time ends where this look began. GAZE_TIME_EVENT comes only
        # once the look has lasted the dwell time (0.5 s by default).
        start = showing['gazeStart'] if showing['gazeStart'] is not None else viz.tick()
        reactionTime = max(0.0, start - showing['onset'])
        showing['reactionTime'] = reactionTime
        print('Reaction time:', reactionTime)
        timeDisplay.message(f'Time: {reactionTime:.2f}')
        sightlab.setCustomTrialData(round(reactionTime, 4), 'Reaction Time')

# vizact.addCallback adds to SightLab's own handlers of these events; viz.callback would replace them
vizact.addCallback(sightlab.GAZE_BEGIN_EVENT, gazeBegin)
vizact.addCallback(sightlab.GAZE_TIME_EVENT, gazeActionStart)

def TestReactionTime():
    """Runs the reaction time test"""
    for position in positions:
        yield viztask.waitTime(vizmat.GetRandom(1.5, 2.5))  # Wait randomly
        showing.update(onset=None, gazeStart=None, reactionTime=None)
        showSphere(position)  # Show sphere

        d = yield viztask.waitDraw()  # Wait for next frame
        showing['onset'] = d.time  # Save display time

        # Until the sphere is found, or a 3 s timeout before moving to next position
        yield viztask.waitAny([viztask.waitTrue(lambda: showing['reactionTime'] is not None), viztask.waitTime(3)])
        found = showing['reactionTime'] is not None
        yield viztask.runAction(sphere, sphereFade)  # Fade out
        hideSphere()
        showing['onset'] = None
        if found:
            yield viztask.runAction(timeDisplay, textFade)  # Show the time

def sightLabExperiment():
    """Main experiment loop"""
    yield viztask.waitEvent(EXPERIMENT_START)
    viz.callback(viz.getEventID('ResetPosition'), sightlab.resetViewPoint)
    sightlab.resetViewPoint()
    sightlab.setFixationSaccadeThresholds(dispersionThreshold = 1, durationThreshold = 0.1)
    for i in range(sightlab.getTrialCount()):
        yield sightlab.startTrial(
            startExperimentText="Look at the red ball as quickly as you can when it appears \n\n Press Trigger or Left Mouse Button to Continue",
            textContinueEvent="triggerPress"
        )
        yield TestReactionTime()  # Run reaction time test
        # Let SightLab see the gaze leave the hidden sphere before the trial ends;
        # otherwise its dwell timer fires a 'dwell onset' in the next trial
        yield viztask.waitFrame(2)
        yield sightlab.endTrial()
        
viztask.schedule(sightlab.runExperiment)
viztask.schedule(sightLabExperiment)