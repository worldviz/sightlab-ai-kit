# Source: ExampleScripts/Custom Data Saving/SavingCustomData.py
# SightLab 2.x shipped example, copied unchanged below this header by the AI Kit on 2026-10-30.
import sightlab_utils.sightlab as sl
from sightlab_utils.settings import *

sightlab = sl.SightLab(gui=False, pid=False)

# Set up environment
env = vizfx.addChild("sightlab_resources/environments/dojo.osgb")
sightlab.setEnvironment(env)

# Configure trials
sightlab.setTrialCount(3)

basketball = env.getChild('basketball')
sightlab.addSceneObject('basketball', basketball, gaze=True, grab=True)
sightlab.addTrackingTrialDataColumn("basketball", basketball)

def sightLabExperiment():
    for i in range(sightlab.getTrialCount()):
        yield viztask.waitKeyDown(' ')

       # Start recording right hand position
        def update_right_hand():
            R_HAND_VALUE = True
            if R_HAND_VALUE:
                rHandValue = 'rhandvalue'
                rHandPos = sightlab.getAvatarRHand().getPosition()
                rHandPos = [round(x, 3) for x in rHandPos]
                sightlab.setCustomTrialData(str(rHandPos[0]), 'Rhand X')
                sightlab.setCustomTrialData(str(rHandPos[1]), 'Rhand Y')
                sightlab.setCustomTrialData(str(rHandPos[2]), 'Rhand Z')
            else:
                lHandValue = 'lhandvalue'
            

        update_action = vizact.onupdate(0, update_right_hand)

        # Start trial
        yield sightlab.startTrial()

        # Define a button trigger event
        def buttonTrigger():
            sightlab.setCustomTrialData('T key pressed', 'custom flag')
            sightlab.addToTimeline("t pressed")
            print("T key pressed")
        vizact.onkeydown('t', buttonTrigger)
        
        # Set condition
        condition = 'condition1'
        sightlab.setCustomTrialData(condition, 'Condition')
        sightlab.setExperimentSummaryData('condition', condition)

        yield viztask.waitKeyDown(' ')
        yield sightlab.endTrial(endExperimentText='Done')

viztask.schedule(sightlab.runExperiment)
viztask.schedule(sightLabExperiment)
