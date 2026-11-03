# Undocumented public methods (69)

Public methods in `sightlab.py` with no docstring, grouped by class. Generated; regenerate after adding docstrings.

## GUI (4)

- `GUI.loadTempAvatar(e=None)`
- `GUI.loadTempEnvironment(path=None, default=False, mode=MODEL_3D)`
- `GUI.updateGazeObject()`
- `GUI.findNodes(environment, reldirectory)`

## HUD (10)

- `HUD.getCurrentTime()`
- `HUD.writeToClientList(clientDict)`
- `HUD.writeToClient(message, color=viz.GREEN, clientsOnline=None, clientsReady=None)`
- `HUD.updateGazePointObject()`
- `HUD.updateScene(sessionRecorder)`
- `HUD.onGrab(e)`
- `HUD.onRelease(e)`
- `HUD.setTrialState()`
- `HUD.preTrial(dateTime, participantData, isGUI, trialMode, trialNumber, trialLabel, sceneObjects, trackingDataLogging, replayDataLogging, experimentDataLogging, timeLineLogging, fixationLogging, customExperimentData=None, scriptDirectory=None, trialConfigFile=None, dataFileSaving=PER_TRIAL, clientDict=None, individualEyeIntersect=True, customTrackingObjects={}, oldHeaders=False, updateRate=0)`
- `HUD.consoleON()`

## SightLab (40)

- `SightLab.compressRecording(input_path, output_path, bitrate=BIT_RATE)`
- `SightLab.setupHighlighter()`
- `SightLab.togglePoint()`
- `SightLab.toggleHUD()`
- `SightLab.toggleGazePoint()`
- `SightLab.identifyStartPoint()`
- `SightLab.resetViewPoint(event=None, pos=[0.0, 1.8, 0.25], ori=[0.0, 0.0, 0.0])`
- `SightLab.resetTrial()`
- `SightLab.setStartPoint(POSITION=None, ORIENTATION=None)`
- `SightLab.runExperiment()`
- `SightLab.resetExperiment()`
- `SightLab.showGazePath(scanPathType=GAZE, waitKey=CONTINUE_EVENT_KEY)`
- `SightLab.hideRatings(endFade)`
- `SightLab.setGazePointObject(gazePointObject)`
- `SightLab.setAvatarHead(head)`
- `SightLab.setAvatarLeftHand(leftHand)`
- `SightLab.setAvatarRightHand(rightHand)`
- `SightLab.addTrackingTrialDataColumn(columnName, trackedObject, dataType=SIXDOF, mode=viz.ABS_GLOBAL)`
- `SightLab.setExperimentSummaryData(columnName, data)`
- `SightLab.setCustomTrialData(data, columnName=SIGHTLAB_FLAG)`
- `SightLab.getPlotData()`
- `SightLab.getGazeTimeObject()`
- `SightLab.setConsoleState(state)`
- `SightLab.setTransportState(state=viz.TOGGLE)`
- `SightLab.setTransportPosition(pos, euler=None)`
- `SightLab.addRegionOfInterest(regionObject)`
- `SightLab.getRegionOfInterest(name)`
- `SightLab.setConfigDirectory(directoryName)`
- `SightLab.setEnvironmentDirectory(directoryName, mode=MODEL_3D)`
- `SightLab.setDataDirectory(directoryName)`
- `SightLab.setConditionName(conditionName)`
- `SightLab.getConditionName()`
- `SightLab.setRecordingsDirectory(directoryName)`
- `SightLab.screenCapture()`
- `SightLab.experimentSetupCompleteStatus()`
- `SightLab.setHeadlight(state, intensity=None, color=None)`
- `SightLab.setHighlighter(mode=None, setItems=None, enable=None, client=None)`
- `SightLab.setCustomReplayFlag(flagName, data)`
- `SightLab.removeGazePointWindow()`
- `SightLab.addGazePointWindow()`

## SightLabServer (6)

- `SightLabServer.startTrialServer(e)`
- `SightLabServer.endTrialServer(e)`
- `SightLabServer.startConfirmFlag(e)`
- `SightLabServer.clientAvatarsVisible(state)`
- `SightLabServer.runServer()`
- `SightLabServer.updateSharedServerData(data)`

## SightLabClient (9)

- `SightLabClient.receiveSharedServerData()`
- `SightLabClient.startTrialClient(e)`
- `SightLabClient.endTrialClient(e)`
- `SightLabClient.getClientName()`
- `SightLabClient.setStartPointSuffix(suffix)`
- `SightLabClient.clientAvatarsON()`
- `SightLabClient.clientAvatarsOFF()`
- `SightLabClient.clientAvatarsVisible(state)`
- `SightLabClient.runClient()`
