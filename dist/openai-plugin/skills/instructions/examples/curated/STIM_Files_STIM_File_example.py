# Source: ExampleScripts/STIM Files/STIM_File_example.py
# SightLab 2.x shipped example, copied unchanged below this header by the AI Kit on 2026-10-30.
"""
Focus on the ball to proceed to the next trial. Will run 3 trials. 
"""

from STIM_File_Config import *

from sightlab_utils import stim_reader
import sightlab_utils.sightlab as sl
from sightlab_utils.settings import * 

sightlab = sl.SightLab(gui = False)

# Initialize StimReader with the STIM file
SR = stim_reader.StimReader(STIM_FILE_LOCATION)
SR.fillStimFileEntryList()

env = vizfx.addChild('dojo.osgb')
sightlab.setEnvironment(env)

# Add an object
basketball = vizfx.addChild('sightlab_resources/objects/basketball.osgb')
sightlab.addSceneObject("basketball", basketball, gaze = True, grab = True)	

import viztask
def findItem(e):
    global time_to_find_target, start_time
    if e.object == basketball:
        found_target = True
        time_to_find_target = round(sightlab.hud.getCurrentTime() - start_time, 4)
        print(f'Time to find target: {time_to_find_target}')
        sightlab.setExperimentSummaryData('Time to Find Target', time_to_find_target)
        viztask.schedule(sightlab.endTrial(endExperimentText = 'You Are Done'))
    else:
        print('target_object not found in GAZE_OBJECTS:', target_object)


def sightLabExperiment():
    global time_to_find_target, start_time
    # Get the entries list
    entries = SR.getStimFileEntryList()
    sightlab.setTrialCount(len(entries))

#     Iterate over the entries
    for i in range(len(entries)):
        yield viztask.waitKeyDown(' ')
        print('experiment start')
        start_time = sightlab.hud.getCurrentTime()
        currentEntry = entries[i]
        # get the label for the current trial
        if 'label' in currentEntry:
            label = currentEntry['label']
        else:
            label = ''
        yield sightlab.startTrial(trialLabel = label)
        sightlab.setDwellTimeThreshold(1)

        # Create the file name with relevant details
        fileName = '{d}_{p}_experiment_data_trial_{t}.json'.format(
            d=sightlab.dateTime, 
            p=sightlab.participantData, 
            t=sightlab.trialNumber - 1
        )

        print(f'Trial {i+1} - current entry: {currentEntry}')

        if 'object size' in currentEntry:
            ballSizeString = currentEntry['object size']
            ballSize = target_object_size[ballSizeString]
            basketball.setScale(ballSize)
            sightlab.setExperimentSummaryData('Object Size',ballSizeString)
            CONDITION = ballSizeString  # Set global CONDITION

        if 'object position' in currentEntry:
            positionString = currentEntry['object position']
            positionTuple = target_object_position[positionString]
            basketball.setPosition(positionTuple)
            
        sightlab.setExperimentSummaryData('Object Size',CONDITION)
        sightlab.setExperimentSummaryData('Position', positionTuple)

        yield viztask.waitEvent(TRIAL_END)
        yield sightlab.endTrial()
    print('experiment end')

vizact.addCallback(sightlab.GAZE_TIME_EVENT, findItem)	
viztask.schedule(sightlab.runExperiment())
viztask.schedule(sightLabExperiment)