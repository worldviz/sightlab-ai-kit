# Source: ExampleScripts/Biopac Saving to Data Files/Biopac Saving to Data Files.py
# SightLab 2 shipped example, copied unchanged below this header by the AI Kit on 2026-10-30.
import sightlab_utils.sightlab as sl
from sightlab_utils.settings import *
from sightlab_utils import biopacndt
import viztask

# Initialize SightLab with Biopac enabled
sightlab = sl.SightLab(biopac=True)

# Callback function to handle incoming Biopac data
def outputToScreen(index, frame, channelsInSlice):
	for i, value in enumerate(frame):
		# Round and log to custom trial data
		sightlab.setCustomTrialData(str(round(value, 4)), f"Channel_{i}")

# Set up Biopac data server
enabledChannels = sightlab.acqServer.DeliverAllEnabledChannels()
dataServer = biopacndt.AcqNdtDataServer(sightlab.acqServer.getSingleConnectionModePort(), enabledChannels)
dataServer.RegisterCallback("OutputToScreen", outputToScreen)

# Declare dataServer as a global variable
dataServer = None

# Experiment function
def sightLabExperiment():
	global dataServer
	yield viztask.waitEvent(EXPERIMENT_START)
	
	for i in range(0, sightlab.getTrialCount()):
		if i != 0:
			yield viztask.waitKeyDown(' ')
		
		# — start trial once, with instructions only on trial 1 —
		if i == 0:
			yield sightlab.startTrial(
				startExperimentText = "Press Spacebar to Start",
				textContinueKey    = ' '
			)
		else:
			yield sightlab.startTrial()

		# Stop the dataServer if it exists
		if dataServer:
			print("Stopping previous Biopac data server...")
			dataServer.Stop()
	
		# Reinitialize Biopac data server for each trial
		print("Initializing Biopac data server...")
		dataServer = biopacndt.AcqNdtDataServer(
			sightlab.acqServer.getSingleConnectionModePort(),
			enabledChannels
		)
		dataServer.RegisterCallback("OutputToScreen", outputToScreen)
		dataServer.Start()
		
		yield viztask.waitKeyDown(' ')
		yield sightlab.endTrial()
		
		#Stop the BIOPAC data server
		dataServer.Stop()

# Schedule experiment
viztask.schedule(sightlab.runExperiment)
viztask.schedule(sightLabExperiment)
