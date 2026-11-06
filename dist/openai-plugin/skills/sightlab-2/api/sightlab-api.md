# SightLab 2 API map (sightlab_utils 2.9.3)

Generated 2026-11-05T23:53Z by `tools/gen_api_map.py`. Do not edit; regenerate.
Signatures are what the installed package exposes; docstrings are the first paragraph only.

## class SightLab

Constructor keyword arguments: `gui=True`, `pid=True`, `biopac=None`, `timer=True`, `fadequad=True`, `headlight=False`, `mouselock=False`, `gazepointvisible=True`, `gazepathvisible=ADDITIONAL_SETTINGS['Gaze Path Visible']`, `console=ADDITIONAL_SETTINGS['Console']`, `screenrecord=False`, `trackingdatalogging=True`, `replaydatalogging=True`, `experimentdatalogging=True`, `timelinelogging=True`, `fixationlogging=True`, `continuekey=False`, `trialcount=None`, `configpath=None`, `loadenvironmentmode=LOAD_ALL`, `directory=None`, `repetitions=1`, `datafilesaving=PER_TRIAL`, `loglevel=viz.OFF`, `hardwareconfig=None`, `vizconnectconfig=None`, `vizconnectconfiglist=None`, `serverMode=False`, `clientMode=False`, `highlighttool=False`, `title=SIGHTLAB_VERSION`, `individual_eye_intersect=True`, `oldHeaders=False`, `updateRate=0`, `selectconfig=None`, `optimizeintersect=True`, `fastload=False`, `barchart=False`, `fullbody=False`, `fullbodyavatar=None`

### `compressRecording(input_path, output_path, bitrate=BIT_RATE)`

_No docstring._

### `setupHighlighter()`

_No docstring._

### `togglePoint()`

_No docstring._

### `toggleHUD()`

_No docstring._

### `toggleGazePoint()`

_No docstring._

### `identifyStartPoint()`

_No docstring._

### `resetViewPoint(event=None, pos=[0.0, 1.8, 0.25], ori=[0.0, 0.0, 0.0])`

_No docstring._

### `resetTrial()`

_No docstring._

### `setStartPoint(POSITION=None, ORIENTATION=None)`

_No docstring._

### `runExperiment()` *(generator: use with `yield`)*

_No docstring._

### `resetExperiment()`

_No docstring._

### `showGazePath(scanPathType=GAZE, waitKey=CONTINUE_EVENT_KEY)`

_No docstring._

### `sceneToggle(state)`

Toggle visibility of scene objects.

### `showInstructions(message='', image=None, pauseTimer=False)` *(generator: use with `yield`)*

Display an instruction screen with optional image.

### `hideInstructions(pauseTimer=False, endFade=True)` *(generator: use with `yield`)*

Hide the instruction screen and resume scene.

### `showRatings(message, ratingScale=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'], color=viz.WHITE, characterLimit=8, pauseTimer=True, endFade=True, uiScale=1.0)` *(generator: use with `yield`)*

Display a rating scale interface for participant responses.

### `hideRatings(endFade)` *(generator: use with `yield`)*

_No docstring._

### `setEnvironment(environmentObject, trial=DEFAULT, mode=MODEL_3D, mediaType='video', mediaFormat='Stereoscopic T/B', headlightIntensity=0)`

Set the experiment environment or 360° media.

### `setEnvironmentOffset(pos=(0.0, 0.0, 0.0), euler=None, scale=None)`

Shift the 360/180 environment sphere relative to the viewer.

### `getEnvironment()`

Get the current environment object.

### `getCurrentEnvironmentName()`

Get the filename of the current environment.

### `getCurrentTrialDirectory()`

Get the directory path for the current trial's environment.

### `getMediaObject()`

Get the 360° media object (video or image texture).

### `setGazePointObject(gazePointObject)`

_No docstring._

### `getGazePointObject(clientNumber=1)`

Get the gaze point visualization object.

### `getAvatarHead()`

Get the avatar head object.

### `getAvatarRHand()`

Get the avatar right hand object.

### `getAvatarLHand()`

Get the avatar left hand object.

### `getEyeTracker()`

Get the eye tracker object.

### `addSceneObject(objectName, sceneObject, gaze=False, grab=False, visible=True, avatar=False, customChildOf=None)`

Add an object to the scene with optional gaze tracking and grab interaction.

### `removeGazeObject(objectName)`

Remove an object from gaze tracking.

### `removeGrabObject(objectName)`

Remove an object from grab interaction.

### `removeInvisibleObject(objectName)`

Make an invisible object visible again.

### `removeSceneObject(objectName)`

Remove a scene object and clean up all associated tracking.

### `getCurrentRepetition()`

Get the current repetition number.

### `getTrialCount()`

Get the total number of trials in the experiment.

### `setTrialCount(trialCount)`

Set the number of trials and initialize their settings.

### `setTrialLength(length)`

Set the trial duration in seconds.

### `startTrial(condition=None, trialLength=-1, trialLabel=None, startTrialText=None, startExperimentText=None, startRatings=None, textContinueEvent='triggerPress', textContinueKey=None, trackingDataLogging=None, replayDataLogging=None, experimentSummaryLogging=None, timeLineLogging=None, fixationLogging=None, startPoint=None, startEuler=None)` *(generator: use with `yield`)*

Start a trial with optional configuration.

### `endTrial(condition=NO_CONDITION, endTrialText=None, endExperimentText=None, textContinueEvent='triggerPress', textContinueKey=None, textContinueTimer=None, endRatings=None)` *(generator: use with `yield`)*

End the current trial and save data.

### `setAvatarHead(head)`

_No docstring._

### `setAvatarLeftHand(leftHand)`

_No docstring._

### `setAvatarRightHand(rightHand)`

_No docstring._

### `setSeatedMode(state=True)`

Enable or disable seated mode for avatar leg positioning.

### `setSeatedModeHeadOnly(state=True, mode='default', transport_euler=None)`

Enable or disable seated head-only mode for avatar positioning.

### `addTrackingTrialDataColumn(columnName, trackedObject, dataType=SIXDOF, mode=viz.ABS_GLOBAL)`

_No docstring._

### `setExperimentSummaryData(columnName, data)`

_No docstring._

### `setCustomTrialData(data, columnName=SIGHTLAB_FLAG)`

_No docstring._

### `getPlotData()`

_No docstring._

### `getGazeTimeObject()`

_No docstring._

### `setConsoleState(state)`

_No docstring._

### `setTransportState(state=viz.TOGGLE)`

_No docstring._

### `enableTransportToggleKey(key='y')`

Bind a keyboard key to toggle the main transport on/off.

### `enableEnvironmentNudgeKeys(forwardKey=']', backKey='[', step=0.1)`

Bind keys to nudge the 360/180 environment sphere along Z.

### `enableEnvironmentVerticalKeys(upKey='0', downKey='9', step=0.1)`

Bind keys to nudge the 360/180 environment sphere along Y.

### `enableEnvironmentPitchKeys(upKey='7', downKey='8', step=5.0)`

Bind keys to pitch-rotate the 360/180 environment sphere.

### `enableMediaSkipKeys(forwardKey='v', backKey='c', step=5.0)`

Bind keys to skip forward/back in the current 360 or SBS 180 video.

### `toggleMediaPause()`

Toggle play/pause on the current 360 or SBS 180 video.

### `setTransportPosition(pos, euler=None)`

_No docstring._

### `setDataLoggingState(state, buffer=True)`

Enable or disable data logging and timer tracking.

### `resetTimer()`

Reset the trial timer to zero.

### `getConfig()`

Get the current vizconnect configuration name.

### `setPassthrough(state=True, clearColor=viz.BLACK)`

Enable or disable OpenXR video passthrough (mixed reality).

### `enableMixedReality(keyColor=(0.2, 0.23, 0.28), threshold=0.02, softness=0.02, spill=0.2)`

Enable OpenXR passthrough and chroma-key the current 180 SBS video.

### `disableMixedReality()`

Disable passthrough and remove the chroma-key shader.

### `getTrialNumber()`

Get the current trial number.

### `setfadeQuadState(state: bool)`

Control the fade quad visibility.

### `setDwellTimeThreshold(dwellTime=DWELL_THRESHOLD_VALUE)`

Set the dwell time threshold for gaze events.

### `setFixationSaccadeThresholds(dispersionThreshold=1, durationThreshold=0.1)`

Set thresholds for fixation/saccade detection algorithm.

### `setEnvironmentFolder(path, mode=MODEL_3D)`

Set the resource folder for environments or media files.

### `setStartText(startText)`

Set the text displayed on the start trial button.

### `setMaxDistance(distance)`

Set the maximum distance for gaze intersection checks.

### `getCurrentGazeEventData()`

Get the current gaze event data.

### `addRegionOfInterest(regionObject)`

_No docstring._

### `getRegionOfInterest(name)`

_No docstring._

### `setConfigDirectory(directoryName)`

_No docstring._

### `setEnvironmentDirectory(directoryName, mode=MODEL_3D)`

_No docstring._

### `setDataDirectory(directoryName)`

_No docstring._

### `setConditionName(conditionName)`

_No docstring._

### `getConditionName()`

_No docstring._

### `setRecordingsDirectory(directoryName)`

_No docstring._

### `screenCapture()`

_No docstring._

### `experimentSetupCompleteStatus()`

_No docstring._

### `setHeadlight(state, intensity=None, color=None)`

_No docstring._

### `getExperimentDataFolderPath()`

Get the absolute path to the experiment data folder.

### `storeReplayExecCode(method)`

Store Python source code for replay execution.

### `addToTimeline(flag=None, objectName=None, dwellTime=None)`

Add an event to the timeline log.

### `getTimeLineData(client=None)`

Get timeline event data.

### `setHighlighter(mode=None, setItems=None, enable=None, client=None)`

_No docstring._

### `setCustomReplayFlag(flagName, data)`

_No docstring._

### `removeGazePointWindow()`

_No docstring._

### `addGazePointWindow()`

_No docstring._

### `regenerateDataFiles(folderPath, dispersionThreshold=DISPERSION_THRESHOLD_VALUE, durationThreshold=DURATION_THRESHOLD_VALUE, dwellThreshold=DWELL_THRESHOLD_VALUE, fileType=PER_TRIAL, noiseReductionThreshold=0, flipEyePitch=False)`

folderPath,  dispersionThreshold = DISPERSION_THRESHOLD_VALUE,  durationThreshold = DURATION_THRESHOLD_VALUE,  dwellThreshold = DWELL_THRESHOLD_VALUE,  fileType = PER_TRIAL, noiseReductionThreshold = 0, flipEyePitch = False):

## class SightLabServer(SightLab)

Constructor keyword arguments: `gui=True`, `biopac=None`, `timer=True`, `fadequad=True`, `hardwareconfig='Desktop Server'`, `headlight=False`, `mouselock=False`, `gazepointvisible=True`, `gazepathvisible=ADDITIONAL_SETTINGS['Gaze Path Visible']`, `gazerayvisible=True`, `console=ADDITIONAL_SETTINGS['Console']`, `screenrecord=False`, `trackingdatalogging=True`, `replaydatalogging=True`, `experimentdatalogging=True`, `timelinelogging=True`, `fixationlogging=True`, `continuekey=False`, `trialcount=None`, `configpath=None`, `loadenvironmentmode=LOAD_ALL`, `directory=None`, `repetitions=1`, `avatarintersect=True`, `individualeyeintersect=True`, `datafilesaving=PER_TRIAL`, `loglevel=viz.OFF`, `vizconnectconfig=None`, `vizconnectconfiglist=None`, `title=SIGHTLAB_VERSION`, `mumble_server=None`, `mumble_port=64738`, `mumble_password=''`, `mumble_channel='SightLab'`, `optimizeintersect=True`, `fastload=False`

### `startTrialServer(e)`

_No docstring._

### `endTrialServer(e)`

_No docstring._

### `startConfirmFlag(e)`

_No docstring._

### `clientAvatarsVisible(state)`

_No docstring._

### `runServer()` *(generator: use with `yield`)*

_No docstring._

### `updateSharedServerData(data)`

_No docstring._

### `toggleMute()`

Toggle microphone mute

### `toggleDeafen()`

Toggle audio deafen

### `disconnectVoice()`

Disconnect from voice server

## class SightLabClient(SightLab)

Constructor keyword arguments: `biopac=None`, `gui=True`, `timer=True`, `mouselock=False`, `headlight=False`, `fadequad=True`, `gazepointvisible=True`, `console=ADDITIONAL_SETTINGS['Console']`, `screenrecord=False`, `loadenvironmentmode=LOAD_ALL`, `configpath=None`, `hardwareconfig=None`, `highlighttool=False`, `avatarintersect=True`, `vizconnectconfig=None`, `vizconnectconfiglist=None`, `server=None`, `title=SIGHTLAB_VERSION`, `individual_eye_intersect=True`, `mumble_server=None`, `mumble_port=64738`, `mumble_password=''`, `mumble_channel='SightLab'`, `optimizeintersect=True`, `fastload=False`, `fullbody=False`, `fullbodyavatar=None`

### `receiveSharedServerData()`

_No docstring._

### `startTrialClient(e)`

_No docstring._

### `endTrialClient(e)`

_No docstring._

### `getClientName()`

_No docstring._

### `setStartPointSuffix(suffix)`

_No docstring._

### `clientAvatarsON()`

_No docstring._

### `clientAvatarsOFF()`

_No docstring._

### `clientAvatarsVisible(state)`

_No docstring._

### `runClient()` *(generator: use with `yield`)*

_No docstring._

### `toggleMute()`

Toggle microphone mute

### `toggleDeafen()`

Toggle audio deafen

### `disconnectVoice()`

Disconnect from voice server

## eye_tracker_utils


Constants: `GAZE_BEGIN_EVENT`, `GAZE_TIME_EVENT`, `GAZE_END_EVENT`

## gaze_events

- `id(name)` — Generate unique ID for use over viznet

Constants: `UPDATE_GAZE_EVENT`, `GAZE_START_EVENT`, `GAZE_FIXATION_EVENT`, `GAZE_END_EVENT`, `SET_GAZE_POINT_EVENT`

## settings constants

Available after `from sightlab_utils.settings import *`:

`LANGUAGE`, `WINDOW_SIZE`, `WINDOW_FOV`, `WINDOW_X_SIZE`, `WINDOW_Y_SIZE`, `SCALE_FACTOR`, `VIZCONNECT_DICT`, `DEFAULT_VIZCONNECT_CONFIG_LIST`, `FULL_BODY_VIZCONNECT_CONFIG_LIST`, `VIZCONNECT_CONFIG_LIST`, `VIZCONNECT_CONFIG`, `OPENXR_VIZCONNECTS`, `CONTINUE_EVENT_KEY`, `CONTINUE_ON_LEFT`, `COMPRESS_VIDEOS`, `VIDEO_FILE_TYPE`, `BIT_RATE`, `VIDEO_RECORDING_WINDOW_HEIGHT`, `VIDEO_RECORDING_WINDOW_WIDTH`, `START_TEXT`, `BIOPAC_TOGGLE`, `DISPERSION_THRESHOLD_VALUE`, `DURATION_THRESHOLD_VALUE`, `DWELL_THRESHOLD_VALUE`, `SERVER_CONNECT_RETRY_INTERVAL`, `AUTO_SERVER_FROM_SIGHTLAB_SYNC`, `ROUND_VALUES`, `FADE_IN_TIME`, `FADE_OUT_TIME`, `TRIAL_OR_SCENE`, `SHIFT_LOCK_TOGGLE`, `ADDITIONAL_SETTINGS`, `PARTICIPANT_INFO1`, `PARTICIPANT_INFO2`
