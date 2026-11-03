#import sys
#import os
#import threading
#import re
#
#def create_filtered_output():
#    """Redirect native stdout/stderr through a filtering pipe"""
#    
#    # Patterns to filter out
#    filter_patterns = re.compile(
#        r'\[.*?\] \[info\] (Received|Client Sent).*socket'
#    )
#    
#    # Save original file descriptors
#    original_stdout_fd = os.dup(1)
#    original_stderr_fd = os.dup(2)
#    
#    # Create pipes
#    stdout_read, stdout_write = os.pipe()
#    stderr_read, stderr_write = os.pipe()
#    
#    # Redirect stdout/stderr to write end of pipes
#    os.dup2(stdout_write, 1)
#    os.dup2(stderr_write, 2)
#    os.close(stdout_write)
#    os.close(stderr_write)
#    
#
#    def filter_output(read_fd, original_fd):
#        """Thread function to read, filter, and output"""
#        read_file = os.fdopen(read_fd, 'r', buffering=1, encoding='utf-8', errors='replace')
#        write_file = os.fdopen(original_fd, 'w', buffering=1, encoding='utf-8', errors='replace')
#        try:
#            for line in read_file:
#                if not filter_patterns.search(line):
#                    write_file.write(line)
#                    write_file.flush()
#        except (OSError, ValueError):
#            pass  # Handle closed console gracefully
#    
#    # Start filter threads
#    stdout_thread = threading.Thread(target=filter_output, args=(stdout_read, original_stdout_fd), daemon=True)
#    stderr_thread = threading.Thread(target=filter_output, args=(stderr_read, original_stderr_fd), daemon=True)
#    stdout_thread.start()
#    stderr_thread.start()
#
## Call this FIRST, before any imports
#create_filtered_output()

import viz
import vizact
import vizconnect
import vizfx
import vizinfo
import vizshape
import viztask
import time
import vizinput
import vizmat
import os
from os import path

import shutil
from pathlib import Path

import subprocess
import json

import vizdlg
import csv
import vizshape
import glob
import random
import statistics
import webbrowser
import viznet
import sys
import gc
import inspect
import re
try:
    import vizmic
except Exception:
    vizmic = None
import vizdragdrop
import shutil
import urllib

import socket
import time
import atexit

from queue import Queue
from collections import deque
from collections import Counter
from collections import defaultdict
from typing import Dict, Optional, List, Any

import numpy as np
import pandas as pd

from sightlab_utils import biopacndt
from sightlab_utils import common_utils
from sightlab_utils import eye_tracker_utils
from sightlab_utils import panorama_utils
from sightlab_utils import extract_audio
from sightlab_utils import viznet_ip_patch  # lets clients connect to the server by IP address
from sightlab_utils import long_paths
from datetime import datetime


def _startSightLabSync():
    """Multi-user sessions: tell SightLab Sync which SightLab folder this script lives in
    and make sure its background agent runs. It changes nothing until a PC on the
    network is made the primary. Never raises."""
    try:
        from sightlab_utils import sightlab_sync
        sightlab_sync.register_script_location(os.getcwd())
        sightlab_sync.ensure_agent_running()
    except Exception:
        pass

from copy import deepcopy
from tools import highlighter
from tools import grabber
from sightlab_utils.settings import *
from sightlab_utils.sightlab_config import *

from inspect import getsourcefile
from os.path import abspath
import inspect
from deepdiff import DeepDiff

viz.res.addPath(r"C:\Program Files\WorldViz\Sightlab2")

# Set by the SightLab Dashboard (detail_page.py's run_embedded) when this
# module is running inside its embedded Vizard session AND the user has
# "Inspector embedded" checked in Settings. When present, the Edit button
# routes through it instead of os.startfile so Inspector opens docked in the
# Dashboard's panel rather than as a separate top-level window. Left as None
# for standalone Vizard.exe runs (and whenever the setting is unchecked), in
# which case Edit keeps the original os.startfile behavior.
DASHBOARD_EMBEDDED_INSPECTOR_HOOK = None

# Set alongside DASHBOARD_EMBEDDED_INSPECTOR_HOOK by the same run_embedded()
# call. Called with no arguments right after self.currTrial actually changes
# (see setTrialSettings, the single chokepoint all trial-switch paths --
# nextTrial/previousTrial/addTrial/deleteTrial/the trial-list dropdown --
# funnel through) so an already-embedded Inspector can follow the newly
# selected trial's environment. Event-driven on purpose: the Dashboard's own
# poll-based auto-follow was disabled after causing an unresponsiveness
# report, so this avoids a timer entirely rather than reusing that path.
DASHBOARD_TRIAL_CHANGED_HOOK = None

class SessionRecorder:
    """
    Records experiment session data including eye tracking, gaze events, object interactions, and trial metrics.
    
    Manages data logging for SightLab experiments, handling replay data, trial data, experiment summaries,
    timelines, and fixation/saccade analysis. Supports both single-user and multi-user (server/client) modes.
    """
    
    def __init__(self, 
                 dateTime = datetime.now().strftime("%m-%d-%Y-%H-%M-%S"), 
                 participant = None, 
                 isGUI = None, 
                 trialMode = MODEL_3D, 
                 trialNumber = 1, 
                 trialLabel = "A",
                 maxDistance = 1000,
                 sceneObjects = None, 
                 customExperimentData = None,
                 trackingDataLogging = True,
                 replayDataLogging = True,
                 experimentSummary = True,
                 trialTimeLine = True,
                 fixationTimeLine = True,
                 scriptDirectory = None,
                 trialConfigFile = None,
                 dataFileSaving = PER_TRIAL,
                 serverMode = False,
                 clientMode = False,
                 clientDict = None,
                 individualEyeIntersect = True,
                 customTrackingObjects = {},
                 dispersionThreshold = DISPERSION_THRESHOLD_VALUE,
                 durationThreshold = DURATION_THRESHOLD_VALUE,
                 dwellThreshold = DWELL_THRESHOLD_VALUE,
                 noiseReductionThreshold = 0,
                 regenerateMode = False,
                 oldHeaders = False,
                 overlayWindow = None):
        """
        Initialize the session recorder with experiment configuration and data logging settings.
        
        Args:
            dateTime (str): Timestamp for the session (default: current time)
            participant (dict): Participant information dictionary
            isGUI (bool): Whether GUI mode is enabled
            trialMode (str): Trial mode (MODEL_3D, MEDIA_360, etc.)
            trialNumber (int): Current trial number
            trialLabel (str): Label for the trial
            maxDistance (float): Maximum ray-cast distance for gaze intersection
            sceneObjects (dict): Dictionary of scene objects by category
            customExperimentData (dict): Custom experiment metadata
            trackingDataLogging (bool): Enable detailed tracking data logging
            replayDataLogging (bool): Enable replay data logging
            experimentSummary (bool): Enable experiment summary generation
            trialTimeLine (bool): Enable trial timeline logging
            fixationTimeLine (bool): Enable fixation timeline logging
            scriptDirectory (str): Path to the experiment script directory
            trialConfigFile (dict): Trial configuration settings
            dataFileSaving (str): Data file saving mode (PER_TRIAL or COMBINED)
            serverMode (bool): Whether running as server in multi-user mode
            clientMode (bool): Whether running as client in multi-user mode
            clientDict (dict): Dictionary mapping client connections to IDs
            individualEyeIntersect (bool): Calculate separate intersections for each eye
            customTrackingObjects (dict): Custom objects to track
            dispersionThreshold (float): Dispersion threshold for fixation detection (degrees)
            durationThreshold (float): Duration threshold for fixation detection (seconds)
            dwellThreshold (float): Dwell time threshold for gaze events (seconds)
            noiseReductionThreshold (int): Window size for noise reduction filtering
            regenerateMode (bool): Whether regenerating data from existing replay files
            oldHeaders (bool): Use old header format for compatibility
        """
        
        self.serverMode = serverMode
        self.clientMode = clientMode
        
        self.sceneObjects = sceneObjects
        self.gazePoints = {}
        self.avatarHeadPoints = {}

        self.trialState = viz.OFF
        
        self.clientDict = clientDict
     
        self.timeLine = {}
        
        self.grabStatus = {}
        
        self.timeToFirstFixation = -1
        
        self.trackingDataFlag = trackingDataLogging
        self.replayDataFlag = replayDataLogging
        self.experimentSummaryFlag = experimentSummary
        self.trialTimeLineFlag = trialTimeLine
        self.fixationTimeLineFlag = fixationTimeLine
                                    
        self.scriptDirectory = scriptDirectory
                                    
        self.trialConfigFile = trialConfigFile
    
        self.customObjects = deepcopy(customTrackingObjects)
        
        tempCustomObjects =  deepcopy(customTrackingObjects)
        for column in tempCustomObjects:
            for item in tempCustomObjects[column]:
                item.pop(1)
                                        
        self.customExperimentData = customExperimentData
        
        self.dataFileSaving = dataFileSaving
        
        self.individualEyeIntersect = individualEyeIntersect
        
        self.currentTime = 0.0
        
        self.trialData = None
        self.timelineData = None
        self.summaryData   = None
        self.plotData = []
        
        self.changedObjects = {}
        
        self.overlayWindow = overlayWindow
            
        self.flag = "-"
        self.customFlags = {}
        self.customReplayFlags = {}
                
        self.gazeTracker = {RAW_INTERSECT: None}
        
        if self.sceneObjects is not None:
            for gazeItem in self.sceneObjects[GAZE_OBJECTS]:
                self.gazeTracker[gazeItem] = {}
                self.gazeTracker[gazeItem][GAZE_STATE] = None
                self.gazeTracker[gazeItem][GAZE_BOOL] = False
                self.gazeTracker[gazeItem][DWELL_SPHERE_COUNT] = 1
                self.gazeTracker[gazeItem][DWELL_TIME] = DWELL_THRESHOLD_VALUE
                self.gazeTracker[gazeItem][VIEW_STATUS] = False
                
            for roiItem in self.sceneObjects[REGIONS_OF_INTEREST]:
                gazeItem = roiItem[4] if isinstance(roiItem, tuple) else roiItem
                self.gazeTracker[gazeItem] = {}
                self.gazeTracker[gazeItem][GAZE_STATE] = None
                self.gazeTracker[gazeItem][GAZE_BOOL] = False
                self.gazeTracker[gazeItem][DWELL_SPHERE_COUNT] = 1
                self.gazeTracker[gazeItem][DWELL_TIME] = DWELL_THRESHOLD_VALUE
                self.gazeTracker[gazeItem][VIEW_STATUS] = False
                
            for grabItem in self.sceneObjects[GRAB_OBJECTS]:
                self.grabStatus[grabItem] = False
                        
        self.participant = participant
        self.dateTime = dateTime
        self.trialNumber = trialNumber
        self.trialLabel = trialLabel
        self.fixationCount = 0
        
        self.oldHeadersBool = oldHeaders
        
        self.noiseReductionWindowSize = noiseReductionThreshold
        
        self.regenerateMode = regenerateMode
        
        if self.scriptDirectory is not None:
            if not self.clientMode and (self.trackingDataFlag or self.replayDataFlag or self.experimentSummaryFlag or self.trialTimeLineFlag or self.fixationTimeLineFlag):
                if viz.res.isPublished():
                    base_path = viz.res.getPublishedPath(DEFAULT_DATA_DIRECTORY)
                else:
                    base_path = os.path.join(self.scriptDirectory, DEFAULT_DATA_DIRECTORY)
                # A data folder too deep for Windows' path limit takes the extended-length
                # form, which every writer below inherits through os.path.join (SL-Q27)
                exp_dir_name = DEFAULT_EXPERIMENT_DIRECTORY.format(date=self.dateTime, p=self.participant[ID])
                base_path = long_paths.long_path(base_path, reserve=len(exp_dir_name) + 1 + long_paths.session_reserve(self.participant[ID]))
                try:
                    os.makedirs(base_path, exist_ok=True)
                except PermissionError:
                    # Fall back to LocalAppData when script directory is read-only
                    local_appdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
                    self.scriptDirectory = os.path.join(local_appdata, 'WorldViz', 'SightLab')
                    base_path = os.path.join(self.scriptDirectory, DEFAULT_DATA_DIRECTORY)
                    os.makedirs(base_path, exist_ok=True)
                    self.basePath = base_path
                self.basePath = base_path
                    
                if not regenerateMode:
                    exp_dir = DEFAULT_EXPERIMENT_DIRECTORY.format(date=self.dateTime, p=self.participant[ID])
                    try:
                        os.makedirs(os.path.join(base_path, exp_dir), exist_ok=True)
                    except PermissionError:
                        # Fall back to LocalAppData when script directory is read-only
                        local_appdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
                        self.scriptDirectory = os.path.join(local_appdata, 'WorldViz', 'SightLab')
                        base_path = os.path.join(self.scriptDirectory, DEFAULT_DATA_DIRECTORY)
                        os.makedirs(os.path.join(base_path, exp_dir), exist_ok=True)
                        self.basePath = base_path
                    
                    self.expDir = exp_dir
                else:
                    base_exp_dir = DEFAULT_EXPERIMENT_DIRECTORY.format(date=self.dateTime, p=self.participant[ID])
                    
                    # determine the replay directory and file paths
                    replay_dir = os.path.join(base_path, base_exp_dir, DEFAULT_REPLAY_DATA_DIRECTORY)
                    replay_file = os.path.join(
                        replay_dir,
                        REPLAY_DATA_FILE.format(date=self.dateTime, p=self.participant[ID], t=self.trialNumber)
                    )

                    # only bump the version if that exact replay file already exists
                    if os.path.isfile(replay_file):
                        version = 1
                        while True:
                            candidate_dir = f"{base_exp_dir}_v{version}"
                            candidate_replay_dir = os.path.join(base_path, candidate_dir, DEFAULT_REPLAY_DATA_DIRECTORY)
                            candidate_file = os.path.join(
                                candidate_replay_dir,
                                REPLAY_DATA_FILE.format(date=self.dateTime, p=self.participant[ID], t=self.trialNumber)
                            )
                            if not os.path.isfile(candidate_file):
                                base_exp_dir = candidate_dir
                                replay_dir = candidate_replay_dir
                                break
                            version += 1
                    
                    
                    # define the high-level experiment directory
                    experiment_dir = os.path.join(base_path, base_exp_dir)

                    # define and create the ReplayData subfolder
                    replay_dir = os.path.join(experiment_dir, DEFAULT_REPLAY_DATA_DIRECTORY)
                    os.makedirs(replay_dir, exist_ok=True)

                    # expDir should now be the high-level folder, not the ReplayData folder
                    self.expDir = experiment_dir
                    
#                    # make sure the (possibly versioned) directory exists
#                    os.makedirs(replay_dir, exist_ok=True)
#                    self.expDir = replay_dir

            else:
                self.basePath = None
                self.expDir = None
                    
        self.customTrialDataColumns = {}
        
        self.dispersionThreshold = dispersionThreshold
        self.durationThreshold = durationThreshold
        self.dwellThreshold = dwellThreshold
        
        self.maxDistance = maxDistance
        
        customObjects = {}
        avatarObjects = {}
        if self.sceneObjects is not None:
            for obj in self.sceneObjects[CUSTOM_OBJECTS]:
                if not isinstance(self.sceneObjects[CUSTOM_OBJECTS][obj], list):
                    customObjects[obj] = self.sceneObjects[CUSTOM_OBJECTS][obj].getFilename()
                else:
                    customObjects[obj] = [self.sceneObjects[CUSTOM_OBJECTS][obj][1], self.sceneObjects[CUSTOM_OBJECTS][obj][2].getFilename()]
                
            for obj in self.sceneObjects[AVATAR_OBJECTS]:
                avatar_obj = self.sceneObjects[AVATAR_OBJECTS][obj]
                if hasattr(avatar_obj, '_childNodeName'):
                    avatarObjects[obj] = "__CHILD__:" + avatar_obj._childNodeName
                else:
                    avatarObjects[obj] = avatar_obj.getFilename()

        self.replayData = {
            RPLY_VERSION: VERSION_NUMBER,
            CONFIGURATION: VIZCONNECT_CONFIG,
            MODE: trialMode,
            ISGUI: isGUI,
            DATE_TIME: dateTime,
            PARTICIPANT: participant,
            TRIAL_NUMBER: trialNumber,
            TRIAL_LABEL: trialLabel,

            THRESHOLDS: {
                DISPERSION_THRESHOLD: self.dispersionThreshold,
                DURATION_THRESHOLD: self.durationThreshold,
                DWELL_THRESHOLD: self.dwellThreshold
            },
            
            CUSTOM_OBJECTS: customObjects,
            AVATAR_OBJECTS: avatarObjects,
            
            TRIAL_FLAGS: {
                SIXDOF: tempCustomObjects,
                CUSTOM_FLAGS: self.customFlags,
                EXPERIMENT_FLAGS: self.customExperimentData
            },
            
            OBJECT_TRACKER: {}
        }
            
        if isGUI is not None:
            if isGUI:
                if trialMode == MODEL_3D:
                    environmentObject = ENVIRONMENT_OBJECT
                    self.trialMode = trialMode
                else:
                    environmentObject = MEDIA_OBJECT
                    self.trialMode = trialMode[0]
                   
                try:
                    environmentPath = os.path.relpath(self.sceneObjects[environmentObject].getFilename(), self.scriptDirectory)
                except Exception as e:
                    print("no relative path found from: ", self.scriptDirectory)
                    environmentPath = self.sceneObjects[environmentObject].getFilename()
                            
                self.replayData.update({
                    ENVIRONMENT_FILE: environmentPath,

                    GAZE_OBJECTS: list(self.sceneObjects[GAZE_OBJECTS].keys()),
                    GRAB_OBJECTS: list(self.sceneObjects[GRAB_OBJECTS].keys()),
                    INVISIBLE_OBJECTS: list(self.sceneObjects[INVISIBLE_OBJECTS].keys()),
                    REGIONS_OF_INTEREST: list(self.sceneObjects[REGIONS_OF_INTEREST].keys())
                })
                
                if not self.serverMode:# or not self.clientMode:
                    self.replayData.update(
                    {AVATAR_HEAD_FILE: self.sceneObjects[AVATAR_HEAD_OBJECT].getFilename().split('\\')[-1],
                    AVATAR_RIGHT_HAND_FILE: self.sceneObjects[AVATAR_RIGHT_HAND_OBJECT].getFilename().split('\\')[-1],
                    AVATAR_LEFT_HAND_FILE: self.sceneObjects[AVATAR_LEFT_HAND_OBJECT].getFilename().split('\\')[-1],
                    GAZE_POINT_FILE: self.sceneObjects[GAZE_POINT_OBJECT].getFilename().split('\\')[-1],
                    })
                else:
                    self.replayData.update(
                    {AVATAR_HEAD_FILE: {},
                    AVATAR_RIGHT_HAND_FILE: {},
                    AVATAR_LEFT_HAND_FILE: {},
                    GAZE_POINT_FILE: {},
                    })
                    
                    keyDict = {
                    AVATAR_HEAD_OBJECT: AVATAR_HEAD_FILE,
                    AVATAR_RIGHT_HAND_OBJECT: AVATAR_RIGHT_HAND_FILE, 
                    AVATAR_LEFT_HAND_OBJECT: AVATAR_LEFT_HAND_FILE, 
                    GAZE_POINT_OBJECT: GAZE_POINT_FILE
                    }
                    
                    for item in [AVATAR_HEAD_OBJECT, AVATAR_RIGHT_HAND_OBJECT, AVATAR_LEFT_HAND_OBJECT, GAZE_POINT_OBJECT]:
                        for client in self.sceneObjects[item]:
                            if not item == GAZE_POINT_OBJECT:
                                self.replayData[keyDict[item]][client] = self.sceneObjects[item][client].getFilename().split('\\')[-1]
                            else:
                                self.replayData[keyDict[item]][client] = [self.sceneObjects[item][client].getFilename().split('\\')[-1], self.sceneObjects[item][client].getColor()]
                    
                    self.clientCount = len(self.sceneObjects[AVATAR_HEAD_OBJECT])
            else:
                if trialMode == MODEL_3D:
                    environmentObject = ENVIRONMENT_OBJECT
                    self.trialMode = trialMode
                else:
                    environmentObject = MEDIA_OBJECT
                    self.trialMode = trialMode[0]
                            
                self.replayData.update({
                    ENVIRONMENT_FILE: self.sceneObjects[environmentObject].getFilename(),
                    AVATAR_HEAD_FILE: self.sceneObjects[AVATAR_HEAD_OBJECT].getFilename(),
                    AVATAR_RIGHT_HAND_FILE: self.sceneObjects[AVATAR_RIGHT_HAND_OBJECT].getFilename(),
                    AVATAR_LEFT_HAND_FILE: self.sceneObjects[AVATAR_LEFT_HAND_OBJECT].getFilename(),
                    GAZE_POINT_FILE: self.sceneObjects[GAZE_POINT_OBJECT].getFilename(),
                    
                    GAZE_OBJECTS: list(self.sceneObjects[GAZE_OBJECTS].keys()),
                    GRAB_OBJECTS: list(self.sceneObjects[GRAB_OBJECTS].keys()),
                    INVISIBLE_OBJECTS: list(self.sceneObjects[INVISIBLE_OBJECTS].keys()),
                })
            
        self.initDataCount = 14
            
        self.saccadeFixationDict = {}
        self.fixationSphereDict = {}
        self.fixationSphereDataList = []
        
        if VIZCONNECT_CONFIG == "Screen Based EyeTracker":
            import tobii_research as tr
            
            self.SCREEN_WIDTH, self.SCREEN_HEIGHT = viz.window.getSize()	
            print(f"Window width: {self.SCREEN_WIDTH}, Window height: {self.SCREEN_HEIGHT}")

            # Connect to the Tobii eye tracker
            eye_trackers = tr.find_all_eyetrackers()
            if len(eye_trackers) == 0:
                raise Exception("No Tobii eye trackers found!")
            eye_tracker = eye_trackers[0]
            print(f"Connected to Tobii Eye Tracker: {eye_tracker.model}, Serial: {eye_tracker.serial_number}")
            
            # Global variables for gaze positions
            self.screen_eyetracker_gaze_position = [0.5, 0.5]  # Start at center

            self.screen_eyetracker_smoothed_position = [0.5, 0.5]

            def gaze_data_callback(gaze_data):
                left_gaze = gaze_data['left_gaze_point_on_display_area']
                right_gaze = gaze_data['right_gaze_point_on_display_area']

                # Validate and average gaze data if possible
                if (
                    left_gaze and left_gaze[0] > 0 and left_gaze[1] > 0 and
                    right_gaze and right_gaze[0] > 0 and right_gaze[1] > 0
                ):
                    self.screen_eyetracker_gaze_position = [
                        (left_gaze[0] + right_gaze[0]) / 2,
                        (left_gaze[1] + right_gaze[1]) / 2
                    ]
                elif left_gaze and left_gaze[0] > 0 and left_gaze[1] > 0:
                    self.screen_eyetracker_gaze_position = left_gaze
                elif right_gaze and right_gaze[0] > 0 and right_gaze[1] > 0:
                    self.screen_eyetracker_gaze_position = right_gaze
                else:
                    # If no valid gaze, center
                    pass

            # Subscribe to Tobii gaze data
            eye_tracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, gaze_data_callback, as_dictionary=True)
                
            
    def updateReplayData(self, currentTime, eyeTracker, intersectPoint):
        """
        Update replay data with current frame's tracking information.
        
        Records positions, orientations, colors, and states of all tracked objects including
        environment, avatars, gaze objects, grab objects, custom objects, eye tracking data,
        pupil diameter, and custom flags for the current timestamp.
        
        Args:
            currentTime (float): Current timestamp in seconds
            eyeTracker: Eye tracker object for gaze data
            intersectPoint (list): 3D coordinates of gaze intersection point [x, y, z]
        """
        trackedObjects = [ENVIRONMENT_OBJECT, AVATAR_HEAD_OBJECT, AVATAR_RIGHT_HAND_OBJECT, GAZE_POINT_OBJECT]

        if "Desktop" not in VIZCONNECT_CONFIG:
            trackedObjects.append(AVATAR_LEFT_HAND_OBJECT)
                
        self.replayData[OBJECT_TRACKER][str(currentTime)] = {}
        
        if self.trialMode == MEDIA_360:
            trackedObjects.remove(ENVIRONMENT_OBJECT)
            
            media = self.sceneObjects[MEDIA_OBJECT]
            self.replayData[OBJECT_TRACKER][str(currentTime)][MEDIA_OBJECT] = [media.getTime(), media.getState()]
        
        for item in trackedObjects:
            position = self.sceneObjects[item].getPosition(mode = viz.ABS_GLOBAL)
            orientation = self.sceneObjects[item].getEuler(mode = viz.ABS_GLOBAL)
            color = self.sceneObjects[item].getColor()
            
            #This is getting the scale and putting in json
            scale = self.sceneObjects[item].getScale(mode = viz.ABS_GLOBAL)
            
            visible = self.sceneObjects[item].getVisible()
                         
            self.replayData[OBJECT_TRACKER][str(currentTime)][item] = {}
            
            self.replayData[OBJECT_TRACKER][str(currentTime)][item][POSITION] = position
            self.replayData[OBJECT_TRACKER][str(currentTime)][item][ORIENTATION] = orientation
            self.replayData[OBJECT_TRACKER][str(currentTime)][item][COLOR] = color
            
            #This is also getting the scale and putting in json
            self.replayData[OBJECT_TRACKER][str(currentTime)][item][SCALE] = scale
            
            if item == ENVIRONMENT_OBJECT:
                self.replayData[OBJECT_TRACKER][str(currentTime)][item][VISIBLE] = visible
        
        self.replayData[OBJECT_TRACKER][str(currentTime)][GAZE_OBJECTS] = {}
        
        for item in self.sceneObjects[GAZE_OBJECTS]:
            gazeObject = self.sceneObjects[GAZE_OBJECTS][item]
            
            position = gazeObject.getPosition(mode = viz.ABS_GLOBAL)
            orientation = gazeObject.getEuler(mode = viz.ABS_GLOBAL)
            color = gazeObject.getColor()
                    
            scale = gazeObject.getScale(mode = viz.ABS_GLOBAL)
            visible = gazeObject.getVisible()
            
            self.replayData[OBJECT_TRACKER][str(currentTime)][GAZE_OBJECTS][item] = {}
            self.replayData[OBJECT_TRACKER][str(currentTime)][GAZE_OBJECTS][item][POSITION] = position
            self.replayData[OBJECT_TRACKER][str(currentTime)][GAZE_OBJECTS][item][ORIENTATION] = orientation
            self.replayData[OBJECT_TRACKER][str(currentTime)][GAZE_OBJECTS][item][SCALE] = scale
            self.replayData[OBJECT_TRACKER][str(currentTime)][GAZE_OBJECTS][item][COLOR] = color
            self.replayData[OBJECT_TRACKER][str(currentTime)][GAZE_OBJECTS][item][VISIBLE] = visible
            
        self.replayData[OBJECT_TRACKER][str(currentTime)][GRAB_OBJECTS] = {}
        
        for item in self.sceneObjects[GRAB_OBJECTS]:
            grabObject = self.sceneObjects[GRAB_OBJECTS][item]
            
            position = grabObject.getPosition(mode = viz.ABS_GLOBAL)
            orientation = grabObject.getEuler(mode = viz.ABS_GLOBAL)
                    
            scale = grabObject.getScale(mode = viz.ABS_GLOBAL)
            color = grabObject.getColor()
            
            visible = grabObject.getVisible()
            
            self.replayData[OBJECT_TRACKER][str(currentTime)][GRAB_OBJECTS][item] = {}
            self.replayData[OBJECT_TRACKER][str(currentTime)][GRAB_OBJECTS][item][POSITION] = position
            self.replayData[OBJECT_TRACKER][str(currentTime)][GRAB_OBJECTS][item][ORIENTATION] = orientation
            self.replayData[OBJECT_TRACKER][str(currentTime)][GRAB_OBJECTS][item][SCALE] = scale
            self.replayData[OBJECT_TRACKER][str(currentTime)][GRAB_OBJECTS][item][COLOR] = color
            self.replayData[OBJECT_TRACKER][str(currentTime)][GRAB_OBJECTS][item][VISIBLE] = visible
            
        self.replayData[OBJECT_TRACKER][str(currentTime)][CUSTOM_OBJECTS] = {}
        
        for item in self.sceneObjects[CUSTOM_OBJECTS]:
            if not isinstance(self.sceneObjects[CUSTOM_OBJECTS][item], list):
                customObject = self.sceneObjects[CUSTOM_OBJECTS][item]
                # Register newly added custom objects in the replay header
                if item not in self.replayData[CUSTOM_OBJECTS]:
                    self.replayData[CUSTOM_OBJECTS][item] = customObject.getFilename()
            else:
                customObject = self.sceneObjects[CUSTOM_OBJECTS][item][0]
                # Register newly added custom child objects in the replay header
                if item not in self.replayData[CUSTOM_OBJECTS]:
                    self.replayData[CUSTOM_OBJECTS][item] = [self.sceneObjects[CUSTOM_OBJECTS][item][1], self.sceneObjects[CUSTOM_OBJECTS][item][2].getFilename()]
            
            position = customObject.getPosition(mode=viz.ABS_GLOBAL)
            orientation = customObject.getEuler(mode = viz.ABS_GLOBAL)
            scale = customObject.getScale(mode = viz.ABS_GLOBAL)
            color = customObject.getColor()
            visible = customObject.getVisible()
            
            self.replayData[OBJECT_TRACKER][str(currentTime)][CUSTOM_OBJECTS][item] = {}
            self.replayData[OBJECT_TRACKER][str(currentTime)][CUSTOM_OBJECTS][item][POSITION] = position
            self.replayData[OBJECT_TRACKER][str(currentTime)][CUSTOM_OBJECTS][item][ORIENTATION] = orientation
            self.replayData[OBJECT_TRACKER][str(currentTime)][CUSTOM_OBJECTS][item][SCALE] = scale
            
            self.replayData[OBJECT_TRACKER][str(currentTime)][CUSTOM_OBJECTS][item][VISIBLE] = visible
            
        self.replayData[OBJECT_TRACKER][str(currentTime)][AVATAR_OBJECTS] = {}
        
        for item in self.sceneObjects[AVATAR_OBJECTS]:
            avatarObject = self.sceneObjects[AVATAR_OBJECTS][item]
            
            # Register newly added avatars in the replay header so replay can load them
            if item not in self.replayData[AVATAR_OBJECTS]:
                if hasattr(avatarObject, '_childNodeName'):
                    self.replayData[AVATAR_OBJECTS][item] = "__CHILD__:" + avatarObject._childNodeName
                else:
                    self.replayData[AVATAR_OBJECTS][item] = avatarObject.getFilename()
            
            isChild = hasattr(avatarObject, '_childNodeName')
            
            if isChild:
                position = avatarObject.getPosition()
                orientation = avatarObject.getEuler()
                scale = avatarObject.getScale()
            else:
                position = avatarObject.getPosition(mode=viz.ABS_GLOBAL)
                orientation = avatarObject.getEuler(mode = viz.ABS_GLOBAL)
                scale = avatarObject.getScale(mode = viz.ABS_GLOBAL)
            
            state = 0
                    
            for animationItem in avatarObject.getAnimationList():
                animID = avatarObject.getAnimationID(animationItem)
                if avatarObject.getCycleRunning(animID):
                    state = animID
            
            self.replayData[OBJECT_TRACKER][str(currentTime)][AVATAR_OBJECTS][item] = {}
            self.replayData[OBJECT_TRACKER][str(currentTime)][AVATAR_OBJECTS][item][POSITION] = position
            self.replayData[OBJECT_TRACKER][str(currentTime)][AVATAR_OBJECTS][item][ORIENTATION] = orientation
            self.replayData[OBJECT_TRACKER][str(currentTime)][AVATAR_OBJECTS][item][SCALE] = scale
            self.replayData[OBJECT_TRACKER][str(currentTime)][AVATAR_OBJECTS][item][AVATAR_STATE] = state
            self.replayData[OBJECT_TRACKER][str(currentTime)][AVATAR_OBJECTS][item]['isChild'] = isChild
            
        self.replayData[OBJECT_TRACKER][str(currentTime)][REGIONS_OF_INTEREST] = {}
        
        for item in self.sceneObjects[REGIONS_OF_INTEREST]:
            name = item[4] if isinstance(item, tuple) else item
            self.replayData[OBJECT_TRACKER][str(currentTime)][REGIONS_OF_INTEREST][name] = {}
            self.replayData[OBJECT_TRACKER][str(currentTime)][REGIONS_OF_INTEREST][name][POSITION] = self.sceneObjects[REGIONS_OF_INTEREST][item].getPosition(mode=viz.ABS_GLOBAL)
            self.replayData[OBJECT_TRACKER][str(currentTime)][REGIONS_OF_INTEREST][name][ORIENTATION] = self.sceneObjects[REGIONS_OF_INTEREST][item].getEuler(mode=viz.ABS_GLOBAL)
            self.replayData[OBJECT_TRACKER][str(currentTime)][REGIONS_OF_INTEREST][name][SCALE] = list(self.sceneObjects[REGIONS_OF_INTEREST][item].getScale())
            
        self.replayData[OBJECT_TRACKER][str(currentTime)][GAZE_TRACKER] = {}
        self.replayData[OBJECT_TRACKER][str(currentTime)][FIXATION_TRACKER] = {DELTA_ANGLE: 0.0, DELTA_VELOCITY: 0.0}
        
        gazeObjects = {**self.sceneObjects[GAZE_OBJECTS], **self.sceneObjects[REGIONS_OF_INTEREST]}
        
        for gazeItem in gazeObjects:
            if isinstance(gazeItem, tuple):
                item = gazeItem[4]
            else:
                item = gazeItem
                
            if item in self.gazeTracker:
                gazeState = self.gazeTracker[item]
                if gazeState[GAZE_STATE] == GAZE_FIXATED:
                    gazeState[GAZE_BOOL] = True
                    
                elif gazeState[GAZE_STATE] == GAZE_ENDED:
                    gazeState[GAZE_BOOL] = False
                else:
                    gazeState[GAZE_BOOL] = False
                    
                if gazeState[GAZE_BOOL]:
                    gazeState[DWELL_SPHERE_COUNT] += 1
                                    
                self.replayData[OBJECT_TRACKER][str(currentTime)][GAZE_TRACKER][item] = {}
                
                self.replayData[OBJECT_TRACKER][str(currentTime)][GAZE_TRACKER][item][GAZE_STATE] = gazeState[GAZE_STATE]
                self.replayData[OBJECT_TRACKER][str(currentTime)][GAZE_TRACKER][item][GAZE_BOOL] = gazeState[GAZE_BOOL]
                self.replayData[OBJECT_TRACKER][str(currentTime)][GAZE_TRACKER][item][DWELL_SPHERE_COUNT] = gazeState[DWELL_SPHERE_COUNT]
                self.replayData[OBJECT_TRACKER][str(currentTime)][GAZE_TRACKER][item][DWELL_TIME] = gazeState[DWELL_TIME]
                self.replayData[OBJECT_TRACKER][str(currentTime)][GAZE_TRACKER][item][VIEW_STATUS] = gazeState[VIEW_STATUS]
                
                self.gazeTracker[item][VIEW_STATUS] = False

        pupilDiameter = None
        pupilDiameterL = None
        pupilDiameterR = None
        eyeOpen = None
        eyeOpenL = None
        eyeOpenR = None

        if VIZCONNECT_CONFIG == 'Vive Focus Vision':
            pupilDiameter = eyeTracker.getEyeDataHTC(viz.BOTH_EYE).pupilDiameter

            pupilDiameterL = eyeTracker.getEyeDataHTC(viz.LEFT_EYE).pupilDiameter
            pupilDiameterR = eyeTracker.getEyeDataHTC(viz.RIGHT_EYE).pupilDiameter

            eyeOpen = eyeTracker.getEyeDataHTC(viz.BOTH_EYE).eyeOpenness
            eyeOpenL = eyeTracker.getEyeDataHTC(viz.LEFT_EYE).eyeOpenness
            eyeOpenR = eyeTracker.getEyeDataHTC(viz.RIGHT_EYE).eyeOpenness

        elif VIZCONNECT_CONFIG in ['Vive Pro Eye','Pupil Labs Neon Quest 3','HP Omnicept','Vive Tobii','StarVROne','Vive Focus 3']:
            pupilDiameter = eyeTracker.getPupilDiameter()
            pupilDiameterL = eyeTracker.getPupilDiameter(viz.LEFT_EYE)
            pupilDiameterR = eyeTracker.getPupilDiameter(viz.RIGHT_EYE)

            if not VIZCONNECT_CONFIG in ['Vive Tobii','StarVROne' ]:
                eyeOpen = eyeTracker.getEyeOpen()
                eyeOpenL = eyeTracker.getEyeOpen(viz.LEFT_EYE)
                eyeOpenR = eyeTracker.getEyeOpen(viz.RIGHT_EYE)

        # gazeSource is only set by steamlink_gaze.setupEyeTracker(). The External Data Recorder
        # also has a 'Steamlink' config, but on a desktop vizconnect whose eye_tracker is a plain group.
        elif VIZCONNECT_CONFIG == 'Steamlink' and hasattr(eyeTracker, 'gazeSource'):
            pupilDiameter = eyeTracker.getPupilDiameter()
            pupilDiameterL = eyeTracker.getPupilDiameter(viz.LEFT_EYE)
            pupilDiameterR = eyeTracker.getPupilDiameter(viz.RIGHT_EYE)

            eyeOpen = eyeTracker.getEyeOpen()
            eyeOpenL = eyeTracker.getEyeOpen(viz.LEFT_EYE)
            eyeOpenR = eyeTracker.getEyeOpen(viz.RIGHT_EYE)

        self.replayData[OBJECT_TRACKER][str(currentTime)][PUPIL_DIAMETER] = {
            'pupilDiameter' : pupilDiameter,
            'pupilDiameterL' : pupilDiameterL,
            'pupilDiameterR' : pupilDiameterR,
            'eyeOpen' : eyeOpen,
            'eyeOpenL' : eyeOpenL,
            'eyeOpenR' : eyeOpenR
        }

        # Which source the Steamlink config's gaze came from; the trial data writer also uses it
        # to tell this config's eye data apart from the External Data Recorder's 'Steamlink'.
        if hasattr(eyeTracker, 'gazeSource'):
            self.replayData[OBJECT_TRACKER][str(currentTime)][PUPIL_DIAMETER]['gazeSource'] = eyeTracker.gazeSource

        left_eye_pos = None
        right_eye_pos = None
        leftEuler = None
        rightEuler = None
        leftEyeMat = None
        rightEyeMat = None

        both_eyes_pos = intersectPoint
        both_eyes_mat = eyeTracker.getMatrix()
        both_eyes_euler = both_eyes_mat.getEuler()

        if VIZCONNECT_CONFIG == "Screen Based EyeTracker":
            line = vizmat.VectorToPoint(viz.MainView.getPosition(), eyeTracker.getMatrix().getPosition())
            endPos = vizmat.MoveAlongVector(viz.MainView.getPosition(), line, 1000)
            info = viz.intersect(viz.MainView.getPosition(), endPos)
            leftInfo = rightInfo = info
            
            import math 
            
            dx, dy, dz = line
            yaw = math.degrees(math.atan2(dy, dx))
            
            distance = math.sqrt(dx**2 + dy**2)
            pitch = math.degrees(math.atan2(-dz, distance))
            
            roll = 0
            
            leftEuler = rightEuler = [yaw, pitch, roll]
            
            if info.valid:
                left_eye_pos = right_eye_pos = info.point
            else:
                left_eye_pos = right_eye_pos = endPos

        else: 
            leftGazeMat = eyeTracker.getMatrix(viz.LEFT_EYE)
            leftEuler = leftGazeMat.getEuler()
            
            rightGazeMat = eyeTracker.getMatrix(viz.RIGHT_EYE)
            rightEuler = rightGazeMat.getEuler()

            left_eye_pos = None
            right_eye_pos = None

            if self.individualEyeIntersect:
                leftGazeMat.setTrans([-0.0325, 0, 0])
                leftGazeMat.postMult(viz.MainView.getMatrix())
                line = leftGazeMat.getLineForward(self.maxDistance)
                leftInfo = viz.intersect(line.begin, line.end)
                
                if leftInfo.valid:
                    left_eye_pos = leftInfo.point
                else:
                    left_eye_pos = vizmat.MoveAlongVector(line.begin, line, self.maxDistance)

                rightGazeMat.setTrans([0.0325, 0, 0])
                rightGazeMat.postMult(viz.MainView.getMatrix())
                line = rightGazeMat.getLineForward(self.maxDistance)
                            
                rightInfo = viz.intersect(line.begin, line.end)
                if rightInfo.valid:
                    right_eye_pos = rightInfo.point
                else:
                    right_eye_pos = vizmat.MoveAlongVector(line.begin, line, self.maxDistance)

        self.replayData[OBJECT_TRACKER][str(currentTime)][EYE_TRACKER] = {
            LEFT_EYE: {
                POSITION: left_eye_pos,
                ORIENTATION: leftEuler,
                #MATRIX: leftEyeMat
            },
            RIGHT_EYE: {
                POSITION: right_eye_pos,
                ORIENTATION: rightEuler,
                #MATRIX: rightEyeMat
            },
            BOTH_EYES: {
                POSITION: both_eyes_pos,
                ORIENTATION: both_eyes_euler,
                #MATRIX: both_eyes_mat
            }
        }
        
        sixdofTracker = []
        
        for columnName in self.customObjects:
            for item in self.customObjects[columnName]:
#                print(item)
                dataType = item[0]
                trackedObject = item[1]
                mode = item[2]
                
                if dataType == POSITION:
                    sixdofTracker.append(trackedObject.getPosition(mode)[0])
                    sixdofTracker.append(trackedObject.getPosition(mode)[1])
                    sixdofTracker.append(trackedObject.getPosition(mode)[2])
                elif dataType == ORIENTATION:
                    sixdofTracker.append(trackedObject.getEuler(mode)[0])
                    sixdofTracker.append(trackedObject.getEuler(mode)[1])
                    sixdofTracker.append(trackedObject.getEuler(mode)[2])
                elif dataType == SCALE:
                    sixdofTracker.append(trackedObject.getScale(mode)[0])
                    sixdofTracker.append(trackedObject.getScale(mode)[1])
                    sixdofTracker.append(trackedObject.getScale(mode)[2])
                    
        self.replayData[OBJECT_TRACKER][str(currentTime)][CUSTOM_FLAGS] = {
            REPLAY_FLAG: deepcopy(self.customReplayFlags),
            SIGHTLAB_FLAG: self.flag,
            TRIAL_FLAGS: deepcopy(self.customFlags),
            SIXDOF: sixdofTracker
        }
        
        self.customReplayFlags = {}

        for item in self.customFlags:
            self.customFlags[item] = "-"
            
        self.setFlag()

        self.replayData[OBJECT_TRACKER][str(currentTime)][UNIX_TIMESTAMP] = time.time()
              
        if self.clientMode:
            changedObjects = {}
            compare_keys = [GRAB_OBJECTS, AVATAR_OBJECTS, CUSTOM_OBJECTS, REGIONS_OF_INTEREST]

            if len(self.replayData[OBJECT_TRACKER]) >= 2:
                prevObjectTracker = self.replayData[OBJECT_TRACKER][list(self.replayData[OBJECT_TRACKER].keys())[-2]]
                currObjectTracker = self.replayData[OBJECT_TRACKER][str(currentTime)]
                
                filtered_prevObjectTracker = {k: prevObjectTracker[k] for k in compare_keys if k in prevObjectTracker}
                filtered_currObjectTracker = {k: currObjectTracker[k] for k in compare_keys if k in currObjectTracker}
                            
                difference = DeepDiff(filtered_prevObjectTracker, filtered_currObjectTracker)
                
                try:
                    if 'values_changed' in difference:
                        for path in difference['values_changed'].keys():
                            matches = re.findall(r"\['(.*?)'\]|\[(\d+)\]", path)

                            path_items = [match[0] or match[1] for match in matches]
                            
                            if path_items[-4] in compare_keys:
                                objectType = path_items[-4]
                                objectName = path_items[-3]
                                
                                if objectType not in changedObjects:
                                    changedObjects[objectType] = []
                                    
                                if not objectName in changedObjects[objectType]:
                                    changedObjects[objectType].append(objectName)
                                
                        if not self.changedObjects == {}:
                            filtered_dict1 = {k: self.changedObjects[k] for k in compare_keys if k in self.changedObjects}
                            filtered_dict2 = {k: changedObjects[k] for k in compare_keys if k in changedObjects}
                                    
                            diff = DeepDiff(filtered_dict1, filtered_dict2)
                            
                            # Get the items that have not changed (i.e., items that are the same in both dictionaries)
                            unchanged_items = {k: v for k, v in filtered_dict2.items() if k not in diff.get('values_changed', {})}

                            # Remove these items from changedObjects
                            for key in unchanged_items.keys():
                                if key in changedObjects:
                                    for item in self.changedObjects[key]:
                                        if item in changedObjects[key]:
                                            changedObjects[key].remove(item)
                            
                            if GRAB_OBJECTS in changedObjects:
                                for grabItem in changedObjects[GRAB_OBJECTS]:
                                    if grabItem in self.grabStatus and not self.grabStatus[grabItem]:
                                        changedObjects[GRAB_OBJECTS].remove(grabItem)
                                        
#                            print("changed objects: ", changedObjects)
#                            print("grab status: ", self.grabStatus)
                                            
                        self.changedObjects = {}
                except:
                    print("diff check failed")
            
            viznet.client.sendAll(CLIENT_AVATAR_UPDATE, client = viz.net.getName(), objectTracker = self.replayData[OBJECT_TRACKER][str(currentTime)], changedObjects = changedObjects)
            
    def writeReplayData(self):
        """
        Write accumulated replay data to a binary file using orjson for efficient serialization.
        
        Saves the complete replay data dictionary including all tracked object states,
        eye tracking data, and custom flags to a timestamped JSON file in the replay
        data directory.
        """
        import orjson
#        if self.serverMode:
#            lastValidData = None
#            missingInitData = []
#            for timestamp in self.replayData[OBJECT_TRACKER]:
#                if len(self.replayData[OBJECT_TRACKER][timestamp]) == len(self.clientDict) and len(self.clientDict)>0:
#                    lastValidData = self.replayData[OBJECT_TRACKER][timestamp]
#                    
#                else:
#                    if lastValidData is not None:
#                        for client in lastValidData:
#                            if client not in self.replayData[OBJECT_TRACKER][timestamp]:
#                                self.replayData[OBJECT_TRACKER][timestamp][client] = lastValidData[client]
#                    else:
#                        for client in self.clientDict:
#                            if self.clientDict[client] not in self.replayData[OBJECT_TRACKER][timestamp]:
#                                self.replayData[OBJECT_TRACKER][timestamp][self.clientDict[client]] = None
            # Precompute expected client IDs once (pick keys OR values depending on your schema)
            
#            expected_clients = set(self.clientDict.keys())  # If timestamp dicts use clientDict KEYS as IDs
#            # expected_clients = set(self.clientDict.values())  # If they use clientDict VALUES as IDs
#
#            lastValidData = None
#
#            for timestamp, data in self.replayData[OBJECT_TRACKER].items():
#                # Fast path complete row
#                if len(data) == len(expected_clients) and expected_clients:
#                    lastValidData = data
#                    continue
#
#                # Compute exactly what's missing (avoid looping all clients)
#                present = set(data.keys())
#                missing = expected_clients - present
#                if not missing:
#                    if len(data) == len(expected_clients) and expected_clients:
#                        lastValidData = data
#                    continue
#
#                if lastValidData is not None:
#                    # Carry forward only the missing ones
#                    for cid in missing:
#                        if cid in lastValidData:
#                            data[cid] = lastValidData[cid]
#                    # Update lastValidData if we've now completed this timestamp
#                    if len(data) == len(expected_clients):
#                        lastValidData = data
#                else:
#                    # No prior full row initialize only the missing ones to None
#                    for cid in missing:
#                        data[cid] = None
                
        path = os.path.join(self.basePath, self.expDir, DEFAULT_REPLAY_DATA_DIRECTORY)
        os.makedirs(path, exist_ok=True)
        self.replayDataFileName = os.path.join(path, REPLAY_DATA_FILE.format(date = self.dateTime, p=self.participant[ID], t=self.trialNumber))
#        self.replayDataFile = open(self.replayDataFileName, "w")
        
#        json.dump(self.replayData, self.replayDataFile)
        with open(self.replayDataFileName, "wb", buffering=1<<20) as f:
#            f.write(orjson.dumps(self.replayData))
            f.write(orjson.dumps(self.replayData,
                     option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY))
        
#        self.replayDataFile.close()
        
#    def writeReplayData(self):
#        if self.serverMode:
#            lastValidData = None
#            missingInitData = []
#            for timestamp in self.replayData[OBJECT_TRACKER]:
#                currData = {}
#                if len(self.replayData[OBJECT_TRACKER][timestamp]) == len(self.clientDict) and len(self.clientDict)>0:
#                    lastValidData = self.replayData[OBJECT_TRACKER][timestamp]
#                else:
#                    if lastValidData is not None:
#                        for client in lastValidData:
#                            if client not in self.replayData[OBJECT_TRACKER][timestamp]:
#                                self.replayData[OBJECT_TRACKER][timestamp][client] = lastValidData[client]
#                    else:
#                        for client in self.clientDict:
#                            if self.clientDict[client] not in self.replayData[OBJECT_TRACKER][timestamp]:
#                                self.replayData[OBJECT_TRACKER][timestamp][self.clientDict[client]] = None
#
#                for client in self.clientDict:
#                    if client in self.replayData[OBJECT_TRACKER][timestamp]:
#                        currData[client] = self.replayData[OBJECT_TRACKER][timestamp][client]
#
#        path = os.path.join(self.basePath, self.expDir, DEFAULT_REPLAY_DATA_DIRECTORY)
#        os.makedirs(path, exist_ok=True)
#        self.replayDataFileName = os.path.join(
#            path,
#            REPLAY_DATA_FILE.format(date=self.dateTime, p=self.participant[ID], t=self.trialNumber)
#        )
#
#        # ? write atomically with a local handle; no stray close + dump on closed file
#        with open(self.replayDataFileName, "w") as f:
#            json.dump(self.replayData, f, separators=(',', ':'))

    def writeTrialData(self, replayData, clientID = None):
        """
        Write frame-by-frame trial tracking data to CSV file.
        
        Exports detailed tracking data including eye positions, head positions, fixation status,
        gaze events, custom flags, and pupil diameter measurements to a CSV file with headers.
        
        Args:
            replayData (dict): Complete replay data dictionary with tracking information
            clientID (str, optional): Client ID for multi-user sessions. If None, writes server data
        """
        objectTracker = replayData[OBJECT_TRACKER]
        print(self.clientMode, self.serverMode, self.basePath, self.expDir)
        path = os.path.join(self.basePath, self.expDir, DEFAULT_TRIAL_DATA_DIRECTORY)
        os.makedirs(path, exist_ok=True)
        
        if RPLY_VERSION not in replayData:
            if self.trialData is None:
                return
                
            currTrialData = self.trialData[self.trialNumber]
            firstKey = next(iter(currTrialData))
            
            firstFrameData = currTrialData[firstKey]
            
            headers = list(firstFrameData.keys())
            headers.pop(0)
            print("first frame headers: ", headers)
            
            headers.insert(headers.index('flag'), 'view status')
            headers.insert(headers.index('label') + 1, 'timestamp')
            print("header insert: ", headers)
            
            objectTracker = {float(k): v for k, v in objectTracker.items()}
            
        else:
            customObjects = replayData[TRIAL_FLAGS][SIXDOF]
            customFlags = replayData[TRIAL_FLAGS][CUSTOM_FLAGS]
            
#            headers = [
#            'p_id', 'date/time', 'unix timestamp', 'frame rate', 'trial number', 'label', 'timestamp (secs)', 
#            'combined eye intersect x', 'combined eye intersect y','combined eye intersect z',
#            'combined eye yaw', 'combined eye pitch', 'combined eye roll',
#            'left eye intersect x', 'left eye intersect y','left eye intersect z', 
#            'right eye intersect x', 'right eye intersect y','right eye intersect z', 
#            'left eye yaw', 'left eye pitch', 'left eye roll',
#            'right eye yaw', 'right eye pitch', 'right eye roll',
#            'head x', 'head y', 'head z', 
#            'head yaw', 'head pitch', 'head roll', 
#            'fixation status', 'delta gaze angle (deg)', 'delta gaze velocity (deg/sec)', 
#            'view status', 'flag'
#            ]

            headers = trial_data_headers.copy() if not self.oldHeadersBool else trial_data_headers_old.copy()
        
            if not self.individualEyeIntersect:
                del headers[headers.index('left eye intersect x'):headers.index('right eye intersect z')+1]

            # Steamlink eye data is only written when it came from steamlink_gaze.setupEyeTracker
            # (tagged with gazeSource). The External Data Recorder's 'Steamlink' writes its own columns.
            steamlinkEyeColumns = False
            if replayData[CONFIGURATION] == 'Steamlink':
                frames = (f if clientID is None else f.get(clientID) for f in objectTracker.values())
                eyeData = next((f for f in frames if f), {}).get(PUPIL_DIAMETER)
                steamlinkEyeColumns = isinstance(eyeData, dict) and 'gazeSource' in eyeData

            if replayData[CONFIGURATION] in ['Vive Pro Eye' , 'Pupil Labs Neon Quest 3', 'HP Omnicept','StarVROne','Vive Tobii', 'Vive Focus 3','Vive Focus Vision'] or steamlinkEyeColumns:
                headers.insert(-1, 'pupil diameter')
                headers.insert(-1, 'pupil diameter L')
                headers.insert(-1, 'pupil diameter R')
                
                if not replayData[CONFIGURATION] in ['Vive Tobii','StarVROne']:
                    headers.insert(-1, 'eye open')
                    headers.insert(-1, 'eye open L')
                    headers.insert(-1, 'eye open R')

            for columnName in customObjects:
                for item in customObjects[columnName]:
                    dataType = item[0]
                    
                    if dataType == POSITION:
                        headers.append(columnName + " x")
                        headers.append(columnName + " y")
                        headers.append(columnName + " z")
                    elif dataType == ORIENTATION:
                        headers.append(columnName + " yaw")
                        headers.append(columnName + " pitch")
                        headers.append(columnName + " roll")
                    elif dataType == SCALE:
                        headers.append(columnName + " x")
                        headers.append(columnName + " y")
                        headers.append(columnName + " z")
                    
            for columnName in customFlags:
                headers.append(columnName)
                    
        if clientID is None:
            if self.dataFileSaving == PER_TRIAL:
                self.trialDataFileName = os.path.join(path, TRIAL_DATA_FILE.format(date = self.dateTime, p=self.participant[ID], t=self.trialNumber))
                self.trialDataFile = open(self.trialDataFileName, mode = "w",  newline='')

            elif self.dataFileSaving == COMBINED:
                self.trialDataFileName = os.path.join(path, TRIAL_DATA_FILE.format(date = self.dateTime, p=self.participant[ID], t=ALL_TRIALS))
                self.trialDataFile = open(self.trialDataFileName, mode = "a+",  newline='')
        else:
            if self.dataFileSaving == PER_TRIAL:
                self.trialDataFileName = os.path.join(path, CLIENT_TRIAL_DATA_FILE.format(date = self.dateTime, p=self.participant[ID], t=self.trialNumber, c=clientID))
                self.trialDataFile = open(self.trialDataFileName, mode = "w",  newline='')

            elif self.dataFileSaving == COMBINED:
                self.trialDataFileName = os.path.join(path, CLIENT_TRIAL_DATA_FILE.format(date = self.dateTime, p=self.participant[ID], t=ALL_TRIALS, c=clientID))
                self.trialDataFile = open(self.trialDataFileName, mode = "a+",  newline='')
            
        self.trialDataFileWriter = csv.writer(self.trialDataFile)
        
        if self.dataFileSaving == PER_TRIAL or (self.dataFileSaving == COMBINED and self.trialNumber == 1):
            self.trialDataFileWriter.writerow(headers)
            
        fixationState = "None"
        saccadeAngle = "None"
        viewStatus = "None"
        prevTimestamp = 0.0
        
        if RPLY_VERSION in replayData:
            for timestamp in objectTracker:
                pid = replayData[PARTICIPANT][ID]
                dateTime = replayData[DATE_TIME]
                
                if clientID is None:
                    currData = objectTracker[timestamp] 
                else:
                    if clientID in objectTracker[timestamp]:
                        currData = objectTracker[timestamp][clientID]
                    else: 
                        continue
                
                unixTime = currData[UNIX_TIMESTAMP]
                tick = timestamp
                
                # Guard against division by zero when timestamps are identical
                time_delta = float(timestamp) - float(prevTimestamp)
                if time_delta > 0:
                    fps = 1 / time_delta
                else:
                    fps = 0  # or use previous fps value, or a default like 90
                prevTimestamp = timestamp
                
#                fps = 1/(float(timestamp) - float(prevTimestamp))
#                prevTimestamp = timestamp
                
                point = currData[EYE_TRACKER][BOTH_EYES][POSITION]
                eye_euler = currData[EYE_TRACKER][BOTH_EYES][ORIENTATION]
                left_eye = currData[EYE_TRACKER][LEFT_EYE][POSITION]
                right_eye = currData[EYE_TRACKER][RIGHT_EYE][POSITION]
                
                if left_eye is None:
                    left_eye = [-1, -1, -1]
                if right_eye is None:
                    right_eye = [-1, -1, -1]
                    
                left_euler = currData[EYE_TRACKER][LEFT_EYE][ORIENTATION]
                right_euler = currData[EYE_TRACKER][RIGHT_EYE][ORIENTATION]

                position = currData[AVATAR_HEAD_OBJECT][POSITION]
                euler = currData[AVATAR_HEAD_OBJECT][ORIENTATION]

                flag = currData[CUSTOM_FLAGS][SIGHTLAB_FLAG]
                customFlags = currData[CUSTOM_FLAGS][TRIAL_FLAGS]
                
                customData = currData[CUSTOM_FLAGS][SIXDOF]
                
                row = None
                saccadeVelocity = "-"
                
                fixationState = currData[FIXATION_TRACKER][FIXATION_STATUS]
                saccadeAngle = currData[FIXATION_TRACKER][DELTA_ANGLE]
                saccadeVelocity = currData[FIXATION_TRACKER][DELTA_VELOCITY]
                
                viewStatus = "None"
                gazeTracker = currData[GAZE_TRACKER]
                for gazeObject in gazeTracker:
                    if gazeTracker[gazeObject][VIEW_STATUS] and gazeObject is not RAW_INTERSECT:
                        viewStatus = gazeObject
                        break
                    
                row = [pid, dateTime, unixTime, fps, self.trialNumber, self.trialLabel, tick, 
                       point[0], point[1], point[2], 
                       eye_euler[0], eye_euler[1] * (-1 if not self.regenerateMode else 1), eye_euler[2],
                       left_eye[0], left_eye[1], left_eye[2],
                       right_eye[0], right_eye[1], right_eye[2], 
                       left_euler[0], left_euler[1] * (-1 if not self.regenerateMode else 1), left_euler[2], 
                       right_euler[0], right_euler[1] * (-1 if not self.regenerateMode else 1), right_euler[2], 
                       position[0], position[1], position[2], 
                       euler[0], euler[1], euler[2], 
                       fixationState, saccadeAngle, saccadeVelocity, 
                       viewStatus, flag]
                
                if not self.individualEyeIntersect:
                    del row[trial_data_headers.index('left eye intersect x'):trial_data_headers.index('right eye intersect z')+1]
                    
                if replayData[CONFIGURATION] in ['Vive Pro Eye' , 'Pupil Labs Neon Quest 3','StarVROne' ,'HP Omnicept','Vive Tobii', 'Vive Focus 3','Vive Focus Vision'] or steamlinkEyeColumns:
                    pupilDiameter = currData[PUPIL_DIAMETER]['pupilDiameter']
                    pupilDiameterL = currData[PUPIL_DIAMETER]['pupilDiameterL']
                    pupilDiameterR = currData[PUPIL_DIAMETER]['pupilDiameterR']

                    row = row[:-1] + [pupilDiameter, pupilDiameterL, pupilDiameterR] + row[-1:]

                    if not replayData[CONFIGURATION] in ['Vive Tobii','StarVROne']:
                        eyeOpen = currData[PUPIL_DIAMETER]['eyeOpen']
                        eyeOpenL = currData[PUPIL_DIAMETER]['eyeOpenL']
                        eyeOpenR = currData[PUPIL_DIAMETER]['eyeOpenR']
                        row = row[:-1] + [eyeOpen, eyeOpenL, eyeOpenR] + row[-1:]
                    
                for data in customData:
                    row.append(data)
                    
                for data in customFlags:
                    row.append(customFlags[data])
                        
                for index in range(0, len(row)):
                    try:
                        float(row[index])
                        row[index] = round(row[index], ROUND_VALUES)
                    except:
                        continue
                        
                self.trialDataFileWriter.writerow(row)
        else:
            currTrialData = self.trialData[self.trialNumber]
            
            for timestamp in currTrialData:                
                row = []
                otTimestamp = timestamp
                
                if not timestamp in objectTracker:
                    for item in objectTracker:
                        if abs(float(item) - timestamp) < 0.1:
                            otTimestamp = item
                            break
                
                if not timestamp in objectTracker:
                    continue
                    
                currData = objectTracker[otTimestamp] if clientID is None else objectTracker[otTimestamp][clientID]
                
                for column in currTrialData[timestamp]:
                    if not column in ['fixation status', 'timestamp']:
                        if column == 'flag':
                            viewStatus = "None"
                            gazeTracker = currData[GAZE_OBJECTS]
                            for gazeObject in gazeTracker:
                                if gazeTracker[gazeObject][GAZE_BOOL]:
                                    viewStatus = gazeObject
                                    break
                                    
                            row.append(viewStatus)
                            
                        row.append(currTrialData[timestamp][column])
                        
                        if column == 'label':
                            row.append(currTrialData[timestamp]['timestamp'])
                        
                    elif column == 'fixation status':
                        fixationState = currData[FIXATION_TRACKER][FIXATION_STATUS]
                        row.append(fixationState)
                    
                self.trialDataFileWriter.writerow(row)
            
        self.trialDataFile.close()

    def appendTrialSummary(self, replayData, viewAnalysis, fixationMetrics, clientID = None):
        """
        Append summary statistics for the trial to the experiment summary CSV file.
        
        Calculates and writes aggregated metrics including dwell times, fixation counts,
        saccadic movements, and time to first fixation for each region of interest and
        the entire scene.
        
        Args:
            replayData (dict): Complete replay data with tracking information
            viewAnalysis (dict): Analyzed view data with dwell times and visit counts
            fixationMetrics (dict): Fixation and saccade event data
            clientID (str, optional): Client ID for multi-user sessions
        """
        def calculateSaccadeMetrics(saccadeAngleValues, saccadeVelocityValues):
            if saccadeAngleValues:
                amplitudeAverage = round(statistics.mean(saccadeAngleValues), ROUND_VALUES)
            else:
                amplitudeAverage = 0
                
            non_list_values = [value for value in saccadeVelocityValues if not isinstance(value, list)]
            if non_list_values:
                velocityAverage = round(statistics.mean(non_list_values), ROUND_VALUES)
                velocityPeak = round(max(non_list_values), ROUND_VALUES)
            else:
                velocityAverage = 0
                velocityPeak = 0
                
            return amplitudeAverage, velocityAverage, velocityPeak
            
        path = os.path.join(self.basePath, self.expDir)
        os.makedirs(path, exist_ok=True)
        
        self.plotData = []
        
        if clientID is not None:
            self.experimentSummaryFileName = os.path.join(path, CLIENT_EXPERIMENT_SUMMARY_FILE.format(date = self.dateTime, p=self.participant[ID], c = clientID))
        else:
            self.experimentSummaryFileName = os.path.join(path, EXPERIMENT_SUMMARY_FILE.format(date = self.dateTime, p=self.participant[ID]))
        
        self.experimentSummaryFile = open(self.experimentSummaryFileName, mode = "a+",  newline='')
        self.experimentSummaryFile.seek(0, os.SEEK_END)
        file_is_empty = self.experimentSummaryFile.tell() == 0
        self.experimentSummaryFileWriter = csv.writer(self.experimentSummaryFile)
        
        self.experimentSummaryData = []
            
        self.experimentSummaryFile.seek(0)
        
        objectTracker = replayData[OBJECT_TRACKER]
        
        reader = csv.reader(self.experimentSummaryFile)
        first_line = next(reader, None)
        
        if RPLY_VERSION not in replayData:
            customObjects = {}
            
            customFlags = {}
            
            currTrialData = self.summaryData[self.trialNumber]
            firstKey = next(iter(currTrialData))
            
            firstFrameData = currTrialData[firstKey]
            
            headers = list(firstFrameData.keys())
            
            headers.insert(headers.index('Label'), 'Trial Length')
            
            headers.extend(['Total Fixation Duration (sec)', 'Average Fixation Duration (sec)'])
        else:
#            headers = ['Participant ID', 'Experiment Date/Time', PARTICIPANT_INFO1, PARTICIPANT_INFO2, 
#                       'Trial Number', 'Trial Length (secs)', 'Label', 
#                       'ROI/Object', 'Dwell Visits', 'Fixation Count', 
#                       'Total Dwell Time (secs)', 'Avg Dwell Time (secs)', 
#                       'Avg Saccadic Amplitude (deg)', 'Avg Saccadic Velocity (deg/sec)', 'Saccadic Velocity Peak (deg/sec)', 
#                       'Time to First Fixation (secs)', 'Total Fixation Duration (sec)', 'Average Fixation Duration (sec)']
            
            headers = trial_summary_headers if not self.oldHeadersBool else trial_summary_headers_old
            
            headers[headers.index('First Name')] = PARTICIPANT_INFO1
            headers[headers.index('Last Name')] = PARTICIPANT_INFO2
            
            self.customExperimentData = replayData[TRIAL_FLAGS][EXPERIMENT_FLAGS]
        
            for i in self.customExperimentData:
                headers.append(i)
        
        if file_is_empty:
            self.experimentSummaryFileWriter.writerow(headers)
        
        self.experimentSummaryFile.seek(0, 2)
                
#        if RPLY_VERSION in replayData:
        for objectKey in viewAnalysis['views_per_object']:
            if isinstance(objectKey, tuple):
                objectName = objectKey[4]
            else:
                objectName = objectKey
            
            views = viewAnalysis['views_per_object'][objectKey]
            totalTime = round(viewAnalysis['total_time_per_object'].get(objectKey, 0), ROUND_VALUES)
            avgTime = round(viewAnalysis['average_time_per_view_per_object'].get(objectKey, 0), ROUND_VALUES)

            row = [self.participant[ID], self.dateTime, self.participant[PARTICIPANT_INFO2], self.participant[PARTICIPANT_INFO1], 
                   self.trialNumber, self.timeStampList[-1], self.trialLabel, objectName, views]
            
            totalFixationTime = 0
            avgFixationTime = 0
            fixationCount = 0
            timeToFirstFixation = -1
            
            saccadeAngleValues = []
            saccadeVelocityValues = []
            
            for event in fixationMetrics:
                eventData = fixationMetrics[event]
                if eventData['eventType'] == SACCADE and objectKey == eventData['object']:
                    if eventData["interFixationAmplitude"] is not None:
                        saccadeAngleValues.append(eventData["interFixationAmplitude"])
                        
                    if eventData["interFixationVelocity"] is not None:
                        saccadeVelocityValues.append(eventData["interFixationVelocity"])
                    
                if eventData['eventType'] == FIXATION and objectKey == eventData['object']:
                    totalFixationTime += eventData['eventDuration']
                    fixationCount += 1
                    
                    if fixationCount == 1:
                        timeToFirstFixation = float(eventData['startTime'])
                  
            if fixationCount > 0:
                avgFixationTime = totalFixationTime/fixationCount
                    
            row.append(fixationCount)
            
            row.append(round(totalTime, ROUND_VALUES))
            row.append(round(avgTime,ROUND_VALUES))
            
            for i in objectTracker:
                if clientID is None:
                    currData = objectTracker[i] 
                else:
                    if clientID in objectTracker[i]:
                        currData = objectTracker[i][clientID]
                    else:
                        currData = None
                        continue
                        
                if GAZE_OBJECTS in currData:
                    gazeTracker = currData[GAZE_OBJECTS]
                elif GAZE_TRACKER in currData:
                    gazeTracker = currData[GAZE_TRACKER]
                
                fixationTracker =  currData[FIXATION_TRACKER]
            
#                if gazeTracker[objectName][GAZE_BOOL]:
#                    saccadeAngleValues.append(fixationTracker[DELTA_ANGLE])
#                    saccadeVelocityValues.append(fixationTracker[DELTA_VELOCITY])
            
            amplitudeAverage, velocityAverage, velocityPeak = calculateSaccadeMetrics(saccadeAngleValues, saccadeVelocityValues)
            
            row.extend([amplitudeAverage, velocityAverage, velocityPeak])
            
            row.append(round(timeToFirstFixation, ROUND_VALUES))
                
            row.extend([round(totalFixationTime, ROUND_VALUES), round(avgFixationTime, ROUND_VALUES)])
                
            self.experimentSummaryFileWriter.writerow(row)
            self.plotData.append([objectName, views, totalTime, avgTime])
            
        saccadeAngleValues = []
        saccadeVelocityValues = []
        
        for i in objectTracker:
            if clientID is None:
                    currData = objectTracker[i] 
            else:
                if clientID in objectTracker[i]:
                    currData = objectTracker[i][clientID]
                else: 
                    continue
                    
#            saccadeAngleValues.append(currData[FIXATION_TRACKER][DELTA_ANGLE])
#            saccadeVelocityValues.append(currData[FIXATION_TRACKER][DELTA_VELOCITY])
                    
        timeToFirstFixation = -1
            
        totalFixationTime = 0
        avgFixationTime = 0
        fixationCount = 0
        
        for event in fixationMetrics:
            eventData = fixationMetrics[event]
            if eventData['eventType'] == SACCADE:
                if eventData["interFixationAmplitude"] is not None:
                    saccadeAngleValues.append(eventData["interFixationAmplitude"])
                
                if eventData["interFixationVelocity"] is not None:
                    saccadeVelocityValues.append(eventData["interFixationVelocity"])
                    
            if eventData['eventType'] == FIXATION:
                totalFixationTime += eventData['eventDuration']
                fixationCount += 1
                if fixationCount == 1:
                    timeToFirstFixation = float(eventData['startTime'])
                                    
        amplitudeAverage, velocityAverage, velocityPeak = calculateSaccadeMetrics(saccadeAngleValues, saccadeVelocityValues)
                
        avgFixationTime = totalFixationTime/fixationCount if not fixationCount == 0 else 0
        
        row = [self.participant[ID], self.dateTime, self.participant[PARTICIPANT_INFO2], self.participant[PARTICIPANT_INFO1], self.trialNumber, 
               self.timeStampList[-1], self.trialLabel, "ENTIRE_SCENE", viewAnalysis['total_views'], 
               fixationCount, round(viewAnalysis['total_time_overall'], ROUND_VALUES), 
               round(viewAnalysis['average_time_per_view_overall'], ROUND_VALUES), 
               amplitudeAverage, velocityAverage, velocityPeak, round(timeToFirstFixation, ROUND_VALUES), round(totalFixationTime, ROUND_VALUES), round(avgFixationTime, ROUND_VALUES)]
            
        if RPLY_VERSION in replayData:
            for i in self.customExperimentData:
                row.append(self.customExperimentData[i])
        else:
            currTrialData = self.summaryData[self.trialNumber]
            
            if len(currTrialData["ENTIRE_SCENE"]) > 16:
                row.extend(currTrialData["ENTIRE_SCENE"][16:])
            
        self.experimentSummaryFileWriter.writerow(row)
          
        self.experimentSummaryFile.close()
                
    def appendConfigData(self):
        """
        Append trial configuration data to JSON file.
        
        Saves trial-specific configuration settings to a JSON file for the current experiment.
        Merges new config data with existing data if file already exists.
        Used to maintain a complete record of all trial configurations in an experiment session.
        
        Returns:
            None. Writes/updates JSON config file in experiment directory
        """
        folder = os.path.join(self.scriptDirectory, DEFAULT_DATA_DIRECTORY, DEFAULT_EXPERIMENT_DIRECTORY.format(date = self.dateTime, p=self.participant[ID]))
        file_path = os.path.join(long_paths.long_path(folder, reserve=long_paths.session_reserve(self.participant[ID])), TRIAL_CONFIG_PATH)

        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {}
        
        data.update(self.trialConfigFile)
        
        # Get the directory from the file path
        directory = os.path.dirname(file_path)

        # Check if the directory exists
        if os.path.exists(directory):
            # Directory exists, open the file for writing
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=4)

    def writeTimeLineData(self, viewAnalysis, fixationMetrics, clientID = None):
        """
        Write timeline data showing gaze events over time to CSV file.
        
        Creates a chronological log of all gaze events including start/end times,
        dwell durations, fixation counts, and associated flags for each region of interest.
        
        Args:
            viewAnalysis (dict): Analyzed view data with temporal information
            fixationMetrics (dict): Fixation event data for counting
            clientID (str, optional): Client ID for multi-user sessions
        """
        path = os.path.join(self.basePath, self.expDir, DEFAULT_TRIAL_TIMELINE_DIRECTORY)
        os.makedirs(path, exist_ok=True)
        
        if clientID is None:
            if self.dataFileSaving == PER_TRIAL:
                self.trialTimeLineFileName = os.path.join(path, TRIAL_TIMELINE_DATA_FILE.format(date = self.dateTime, p=self.participant[ID], t=self.trialNumber))
                self.trialTimeLineFile = open(self.trialTimeLineFileName, mode = "w",  newline='')

            elif self.dataFileSaving == COMBINED:
                self.trialTimeLineFileName = os.path.join(path, TRIAL_TIMELINE_DATA_FILE.format(date = self.dateTime, p=self.participant[ID], t=ALL_TRIALS))
                self.trialTimeLineFile = open(self.trialTimeLineFileName, mode = "a+",  newline='')
        else:
            if self.dataFileSaving == PER_TRIAL:
                self.trialTimeLineFileName = os.path.join(path, CLIENT_TRIAL_TIMELINE_DATA_FILE.format(date = self.dateTime, p=self.participant[ID], t=self.trialNumber, c = clientID))
                self.trialTimeLineFile = open(self.trialTimeLineFileName, mode = "w",  newline='')

            elif self.dataFileSaving == COMBINED:
                self.trialTimeLineFileName = os.path.join(path, CLIENT_TRIAL_TIMELINE_DATA_FILE.format(date = self.dateTime, p=self.participant[ID], t=ALL_TRIALS, c = clientID))
                self.trialTimeLineFile = open(self.trialTimeLineFileName, mode = "a+",  newline='')
                
        self.trialTimeLineFileWriter = csv.writer(self.trialTimeLineFile)
        
        headers = ['Participant ID', 'Trial Date/Time', PARTICIPANT_INFO1, PARTICIPANT_INFO2, 'Trial Number', 'Start Time (secs)', 'End Time (secs)',
                        'ROI/Object', 'Dwell Time (secs)', 'Fixation Count', 'Flag']
                        
        if RPLY_VERSION not in self.replayData:
            customObjects = {}
            customFlags = {}
            
            currTrialData = self.timelineData[self.trialNumber]
            
            if not len(currTrialData) > 0:
                print("Timeline Read Failed")
                vizinput.message("Timeline Data Empty")
                return
                
            firstKey = next(iter(currTrialData))
            
            firstFrameData = currTrialData[firstKey]
                        
            if len(list(firstFrameData.keys())) > 9:
                headers.extend(list(firstFrameData.keys())[8:])
            
        if self.dataFileSaving == PER_TRIAL or (self.dataFileSaving == COMBINED and self.trialNumber == 1):
            self.trialTimeLineFileWriter.writerow(headers)
        
        dateTime = self.dateTime #datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
        
        timelineIndexDict = {}
               
        for viewKey in viewAnalysis['views']:
            view = viewAnalysis['views'][viewKey]
            name = view['object']
            start = viewAnalysis['views_without_threshold'][viewKey]['start']
            end = viewAnalysis['views_without_threshold'][viewKey]['end']
            
            if not name in timelineIndexDict:
                timelineIndexDict[name] = 0
            else:
                timelineIndexDict[name] += 1
            
            fixationCount = 0
                    
            for event in fixationMetrics:
                eventData = fixationMetrics[event]
                if eventData['eventType'] == FIXATION and name == eventData['object'] and start <= float(eventData['startTime']) <= end:
                    fixationCount += 1

            if isinstance(view['object'], tuple):
                objectName = view['object'][-1]
            else: 
                objectName = view['object']
            
            row = [self.participant[ID] ,dateTime, self.participant[PARTICIPANT_INFO2], self.participant[PARTICIPANT_INFO1], self.trialNumber, 
                   round(start, ROUND_VALUES), round(end, ROUND_VALUES),objectName, round(view['duration'], ROUND_VALUES), fixationCount]

            self.trialTimeLineFileWriter.writerow(row)
                
        self.trialTimeLineFile.close()

    def writeFixationTimelineData(self, fixationSaccadeMetrics, clientID = None):
        """
        Write detailed fixation and saccade event timeline to CSV file.
        
        Creates a chronological record of individual fixation and saccade events with
        detailed metrics including duration, dispersion, velocity, amplitude, and angular distance.
        Separate files for each client in multi-user mode.
        
        Args:
            fixationSaccadeMetrics (dict): Event data keyed by timestamp with metrics
            clientID (str, optional): Client ID for multi-user sessions
            
        Returns:
            None. Writes fixation timeline CSV file
        """
        path = os.path.join(self.basePath, self.expDir, DEFAULT_FIXATION_TIMELINE_DIRECTORY)
        os.makedirs(path, exist_ok=True)
        
        if clientID is None:
            if self.dataFileSaving == PER_TRIAL:
                self.fixationTimeLineFileName = os.path.join(path, FIXATION_TIMELINE_DATA_FILE.format(date = self.dateTime, p=self.participant[ID], t=self.trialNumber))
                self.fixationTimeLineFile = open(self.fixationTimeLineFileName, mode = "w",  newline='')

            elif self.dataFileSaving == COMBINED:
                self.fixationTimeLineFileName = os.path.join(path, FIXATION_TIMELINE_DATA_FILE.format(date = self.dateTime, p=self.participant[ID], t=ALL_TRIALS))
                self.fixationTimeLineFile = open(self.fixationTimeLineFileName, mode = "a+",  newline='')
        else:
            if self.dataFileSaving == PER_TRIAL:
                self.fixationTimeLineFileName = os.path.join(path, CLIENT_FIXATION_TIMELINE_DATA_FILE.format(date = self.dateTime, p=self.participant[ID], t=self.trialNumber, c = clientID))
                self.fixationTimeLineFile = open(self.fixationTimeLineFileName, mode = "w",  newline='')

            elif self.dataFileSaving == COMBINED:
                self.fixationTimeLineFileName = os.path.join(path, CLIENT_FIXATION_TIMELINE_DATA_FILE.format(date = self.dateTime, p=self.participant[ID], t=ALL_TRIALS, c = clientID))
                self.fixationTimeLineFile = open(self.fixationTimeLineFileName, mode = "a+",  newline='')
                
        self.fixationTimeLineFileWriter = csv.writer(self.fixationTimeLineFile)
        
        headers = ['Participant ID', 'Trial Date/Time', PARTICIPANT_INFO1, PARTICIPANT_INFO2, 'Trial Number', 'Trial Label', 
        'Start Time (secs)','End Time (secs)', 'Type', 'ROI/Object', 'Duration (secs)', 'Dispersion (deg)', 
        'Average Delta Velocity (deg/sec)', 'Peak Delta Amplitude (deg)', 'Total Angular Distance (deg)', 'Peak Delta Velocity (deg/sec)', 
        'Saccadic Amplitude (deg)', 'Saccadic Velocity (deg/sec)']
        
        if self.dataFileSaving == PER_TRIAL or (self.dataFileSaving == COMBINED and self.trialNumber == 1):
            self.fixationTimeLineFileWriter.writerow(headers)
        
        dateTime = datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
        
        timelineIndexDict = {}
        
        fixationSaccadeMetrics = dict(sorted(fixationSaccadeMetrics.items(), key = lambda x:float(x[0])))
        
        for timestamp in fixationSaccadeMetrics:
            eventData = fixationSaccadeMetrics[timestamp]
            
            eventType = eventData['eventType']
            eventDuration = round(eventData['eventDuration'], ROUND_VALUES)
            eventDispersion = round(eventData['dispersion'], ROUND_VALUES)
            
            eventPeakAmplitude = round(eventData['peakAmplitude'], ROUND_VALUES)
            eventPeakVelocity = round(eventData['peakVelocity'], ROUND_VALUES)
            eventAngularDistance = round(eventData['angularDistance'], ROUND_VALUES)
            
            if eventData['averageVelocity'] is not None:
                eventVelocity = round(eventData['averageVelocity'], ROUND_VALUES)
            else:
                eventVelocity = "None"
            
            currObj = "None"
            saccadicAmplitude = "-"
            saccadicVelocity = "-"
            value = None

            if eventData['object'] is not None:
                currObj = eventData['object']
                        
            if eventType == SACCADE:
                if eventData["interFixationAmplitude"] is not None:
                    saccadicAmplitude = round(eventData["interFixationAmplitude"], ROUND_VALUES)
                    
                if eventData["interFixationVelocity"] is not None:
                    saccadicVelocity = round(eventData["interFixationVelocity"], ROUND_VALUES)
            
            row = [self.participant[ID], self.dateTime, self.participant[PARTICIPANT_INFO2], self.participant[PARTICIPANT_INFO1], 
                   self.trialNumber, self.trialLabel,
                   eventData['startTime'], eventData['endTime'], eventType, currObj, 
                   eventDuration, eventDispersion, eventVelocity, eventPeakAmplitude, 
                   eventAngularDistance, eventPeakVelocity, saccadicAmplitude, saccadicVelocity]
            
            self.fixationTimeLineFileWriter.writerow(row)
            
        self.fixationTimeLineFile.close()
    
    def updateData(self, currentTime, intersectPoint, eyeTracker):
        """
        Update per-frame data recording during active trial.
        
        Called each frame to update gaze point visualization and record tracking data.
        Handles both VR head-mounted displays and screen-based eye trackers with
        appropriate coordinate transformations. In client mode, sends data to server.
        
        Args:
            currentTime (float): Current timestamp in seconds
            intersectPoint (list): 3D world coordinates [x, y, z] of gaze intersection
            eyeTracker: Eye tracker data object with gaze information
            
        Returns:
            None. Updates replay data and sends to server if in client mode
        """
#        intersectPoint = [self.maxDistance, self.maxDistance, self.maxDistance]
        if not VIZCONNECT_CONFIG == "Screen Based EyeTracker":
            self.sceneObjects[GAZE_POINT_OBJECT].setPosition(intersectPoint)
        else:
            SMOOTHING_FACTOR = 0.2
            DEFAULT_Z_DISTANCE = 0.3  # Default gaze_z_world
            PIXEL_SCALE = 0.0005  # Meters per pixel at default distance
            
            # Smooth the gaze position
            self.screen_eyetracker_smoothed_position[0] += (self.screen_eyetracker_gaze_position[0] - self.screen_eyetracker_smoothed_position[0]) * SMOOTHING_FACTOR
            self.screen_eyetracker_smoothed_position[1] += (self.screen_eyetracker_gaze_position[1] - self.screen_eyetracker_smoothed_position[1]) * SMOOTHING_FACTOR

            # Set dynamic Z distance
            gaze_z_world = 0.8 

            # Adjust pixel scale based on Z-distance
            scaling_factor = gaze_z_world / DEFAULT_Z_DISTANCE
            dynamic_pixel_scale = PIXEL_SCALE * scaling_factor

            # Convert normalized coordinates (0-1) to pixel coordinates
            gaze_x_pixels = self.screen_eyetracker_smoothed_position[0] * self.SCREEN_WIDTH
            gaze_y_pixels = self.screen_eyetracker_smoothed_position[1] * self.SCREEN_HEIGHT

            # Convert pixel coordinates to world coordinates
            gaze_x_world = (gaze_x_pixels - self.SCREEN_WIDTH / 2) * dynamic_pixel_scale
            gaze_y_world = -(gaze_y_pixels - self.SCREEN_HEIGHT / 2) * dynamic_pixel_scale

            # Update eyeTracker position
            self.sceneObjects[GAZE_POINT_OBJECT].setReferenceFrame(viz.RF_VIEW)
            self.sceneObjects[GAZE_POINT_OBJECT].setPosition([gaze_x_world, gaze_y_world, gaze_z_world])
            #eyeTrackerNode.setPosition([gaze_x_world, gaze_y_world, gaze_z_world])
  
        self.updateReplayData(currentTime, eyeTracker, intersectPoint)

        #if self.trackingDataFlag:
            #self.updateTrialData(currentTime, point, eyeTracker, maxDistance, label)
            
        if self.clientMode:
            send_success = False
            retry_count = 0
            max_retries = 5  # or whatever seems appropriate

            while not send_success and retry_count < max_retries:
                try:
                    viznet.client.send(CLIENT_TRIAL_DATA_UPDATE, 
                                       client=viz.net.getName(), 
                                       replayData=self.replayData[OBJECT_TRACKER][str(currentTime)], 
                                       timestamp=str(currentTime), 
                                       customFlags=self.customFlags, 
                                       customObjects=self.customObjects)
                    send_success = True  # Sent successfully, exit loop

                except socket.error as e:
                    print('SOCKET ERROR FIX INITIATED')
                    if e.errno == 10035:  # WSAEWOULDBLOCK
                        retry_count += 1
                        print('Network temporarily blocked, retrying...')
                        viz.logNotice('Network temporarily blocked, retrying...')
                        #time.sleep(0.01)  # sleep briefly (10ms) before retrying
                    else:
                        raise  # Re-raise if another error occurs

#            if not send_success:
#                viz.logWarn('Failed to send data after multiple retries.')

    def saccadeFixationCalculate(self, objectTracker, dispersionThreshold, durationThreshold, dwellThreshold, noiseFilter = 50, client=None):
        """
        Calculate fixations and saccades using dispersion-threshold identification algorithm.
        
        Analyzes eye movement data to identify fixation periods (stable gaze) and saccadic
        movements (rapid eye movements). Computes view durations, fixation counts, and
        saccadic metrics for each region of interest.
        
        Args:
            objectTracker (dict): Frame-by-frame tracking data
            dispersionThreshold (float): Maximum dispersion in degrees for fixation (typically 1-2°)
            durationThreshold (float): Minimum duration in seconds for fixation (typically 0.1s)
            dwellThreshold (float): Minimum dwell time in seconds for gaze events
            noiseFilter (int, optional): Window size for noise reduction filtering. Default 50
            client (str, optional): Client ID for multi-user session analysis
            
        Returns:
            None. Updates internal state with fixation/saccade metrics
        """
        # ------------- submethod definitions -------------
        def initBuffers():
            self.gazePoints = {}
            self.avatarHeadPoints = {}
            self.fixationCount = 0
            self.timeToFirstFixation = -1
            
        def analyzeViews(data: Dict[str, Optional[str]], buffer: int = 0):
            """
            Args:
            data: dict mapping timestamp-strings (e.g. "1.435") → object name or None
            buffer: max number of consecutive None-frames to treat as noise
            
            Returns a dict with:
            - views_per_object: {obj: count}
            - total_views: int
            - total_time_per_object: {obj: seconds}
            - average_time_per_view_per_object: {obj: seconds}
            - total_time_overall: seconds
            - average_time_per_view_overall: seconds
            - time_to_first_view_per_object: {obj: seconds}
            - time_to_first_view_overall: seconds
            - views: List of {'object', 'start', 'end', 'duration'}
            """

            # 1) sort
            items = sorted(((float(ts), obj) for ts,obj in data.items()), key=lambda x: x[0])
            times = [t for t,_ in items]
            objs  = [o for _,o in items]
            n = len(objs)
            
            # 2) smooth short None-gaps
            if buffer > 0:
                i = 0
                while i < n:
                    if objs[i] is not None:
                        cur = objs[i]
                        j = i+1
                        if j < n and objs[j] is None:
                            gap_start = j
                            while j < n and objs[j] is None:
                                j += 1
                            if j < n and objs[j] == cur and (j-gap_start) <= buffer:
                                for k in range(gap_start, j):
                                    objs[k] = cur
                                # stay at i, now extended
                                continue
                    i += 1
            
            # 3) segment into views
            views = {}
            i = 0
            viewIndex = 1
            while i < n:
                if objs[i] is not None:
                    obj = objs[i]
                    start = times[i]
                    j = i+1
                    while j < n and objs[j] == obj:
                        j += 1
                    end = times[j-1]
                    views[viewIndex] = {
                        'object':   obj,
                        'start':    start,
                        'end':      end,
                        'duration': end - start
                    }
                    viewIndex += 1
                    i = j
                else:
                    i += 1

            # 3.5) drop short views
            views_without_threshold = deepcopy(views)
            if dwellThreshold > 0:
                views = {v: views[v] for v in views if views[v]['duration'] >= dwellThreshold}

            # 4) compute metrics
            vp = defaultdict(int)
            tt = defaultdict(float)
            for v in views:
                vp[views[v]['object']] += 1
                tt[views[v]['object']] += views[v]['duration']

            vp_no_threshold = defaultdict(int)
            for v in views_without_threshold:
                vp_no_threshold[views_without_threshold[v]['object']] += 1
            
            total_views = len(views)
            total_time  = sum(views[v]['duration'] for v in views)
            
            avg_per_obj = {o: tt[o]/vp[o] for o in vp}
            avg_overall = (total_time/total_views) if total_views else 0

            first_obj = {o: next(views_without_threshold[v]['start'] for v in views if views[v]['object']==o) for o in vp}

            first_any = {}
        
            if len(views) > 0:
                first_key = next(iter(views))
                first_any = [views[first_key]['object'], views_without_threshold[first_key]['start']]
                for v in views:
                    if views_without_threshold[v]['start'] < first_any[1]:
                        first_any = [views[v]['object'], views_without_threshold[v]['start']]
            
            currData = None
            if client is None:
                for key in objectTracker:
                    currData = objectTracker[key]
                    
                    if currData is None:
                        continue
                            
                    break
            else:
                for key in objectTracker:
                    if client in objectTracker[key]:
                        currData = objectTracker[key][client]
                        
                        if currData is None:
                            continue
                            
                        break
            
            if currData is not None:
                if GAZE_TRACKER in currData:
                    all_objs = set(currData[GAZE_TRACKER].keys())
                elif GAZE_OBJECTS in currData:
                    all_objs = set(currData[GAZE_OBJECTS].keys())
                
            for o in all_objs:
                vp.setdefault(o, 0)
                tt.setdefault(o, 0.0)
                avg_per_obj.setdefault(o, 0.0)
                first_obj.setdefault(o, None)
                
            return {
                'views_per_object':               dict(vp),
                'views_per_object_no_threshold':  dict(vp_no_threshold),
                'total_views':                    total_views,
                'total_time_per_object':          dict(tt),
                'average_time_per_view_per_object': avg_per_obj,
                'total_time_overall':             total_time,
                'average_time_per_view_overall':  avg_overall,
                'time_to_first_view_per_object':  first_obj,
                'time_to_first_view_overall':     first_any,
                'views':                          views,
                'views_without_threshold':        views_without_threshold
            }

        def extractTimestampsAndPoints(viewAnalysis):
            if self.serverMode:
                filteredTracker = {
                    timestamp: data
                    for timestamp, data in objectTracker.items()
                    if client in data
                }
                self.timeStampList = list(filteredTracker.keys())
            else:
                self.timeStampList = list(objectTracker.keys())

            if client is not None:
                for timestamp, data in objectTracker.items():
                    if client in data:
                        self.gazePoints[timestamp] = data[client][GAZE_POINT_OBJECT][POSITION]
                        self.avatarHeadPoints[timestamp] = data[client][AVATAR_HEAD_OBJECT][POSITION]
            else:
                for timestamp, data in objectTracker.items():
                    if data is None:
                        continue
                        
                    self.gazePoints[timestamp] = data[GAZE_POINT_OBJECT][POSITION]
                    self.avatarHeadPoints[timestamp] = data[AVATAR_HEAD_OBJECT][POSITION]

        def applyNoiseReductionFilter():
            from collections import deque
            windowSize = self.noiseReductionWindowSize
            smoothedGazePoints = {}
            xQueue = deque(maxlen=windowSize)
            yQueue = deque(maxlen=windowSize)
            zQueue = deque(maxlen=windowSize)
            for timestamp in self.gazePoints:
                x, y, z = self.gazePoints[timestamp]
                xQueue.append(x)
                yQueue.append(y)
                zQueue.append(z)
                if len(xQueue) == windowSize:
                    smoothedGazePoints[timestamp] = [
                        sum(xQueue) / windowSize,
                        sum(yQueue) / windowSize,
                        sum(zQueue) / windowSize
                    ]
                else:
                    smoothedGazePoints[timestamp] = [x, y, z]
            self.gazePoints = smoothedGazePoints

        def computeDirectionVectors():
            directionVectorMap = {}
            for timestamp in self.timeStampList:
                if not timestamp in self.gazePoints:
                    continue
                    
                gazePoint = np.array(self.gazePoints[timestamp])
                headPoint = np.array(self.avatarHeadPoints[timestamp])
                direction = gazePoint - headPoint
                unitDirection = direction / np.linalg.norm(direction)
                directionVectorMap[timestamp] = unitDirection
            return directionVectorMap

        def computeFrameToFrameAngles(directionVectorMap):
            prevVec = None
            
            for ts in self.timeStampList:
                if not ts in directionVectorMap:
                    continue
                    
                currVec = directionVectorMap[ts]
                
                currObjectTracker = objectTracker[ts] if client is None else objectTracker[ts][client]
                
                if FIXATION_TRACKER not in currObjectTracker:
                    currObjectTracker[FIXATION_TRACKER] = {DELTA_ANGLE: 0.0, DELTA_VELOCITY: 0.0}
                        
                if prevVec is None:
                    currObjectTracker[FIXATION_TRACKER][DELTA_ANGLE] = 0.0
                else:
                    dp = np.clip(np.dot(prevVec, currVec), -1.0, 1.0)
                        
                    currObjectTracker[FIXATION_TRACKER][DELTA_ANGLE] = np.degrees(np.arccos(dp))
                    
                prevVec = currVec

        def identifyFixationIntervals(directionVectorMap):
            def angular_deviation(u, v):
                # guard against small numerical overshoot
                dp = np.dot(u, v)
                dp_clamped = np.clip(dp, -1.0, 1.0)
                return np.degrees(np.arccos(dp_clamped))
                
            # guard against empty or 1-length lists
            totalFrames = len(self.timeStampList)
            if totalFrames < 2:
                return []


            # minimum number of frames for a valid fixation
            fixationSpans = []
            totalFrames   = len(self.timeStampList)
            
            i = 0

            while i < totalFrames:
                j = i
#                print("i: ", i)
                currObjectTracker = None
                
                # grow the window until dispersion exceeds threshold
                while j < totalFrames:
                    windowTimestamps = self.timeStampList[i:j+1]
                    ts = self.timeStampList[j]
                    currObjectTracker = objectTracker[ts] if client is None else objectTracker[ts][client]
#                    print("test: ", currObjectTracker)
                    if currObjectTracker is None:
                        j += 1
                        break
                        
                    if currObjectTracker[FIXATION_TRACKER][DELTA_ANGLE] < 0.25*dispersionThreshold and len(windowTimestamps) > 10:
                        j += 1
#                        print("shortcut")
                        if j < totalFrames:
                            continue
                    
                    windowVectors = [directionVectorMap[t] for t in windowTimestamps]

                    # centroid of the unit vectors
                    centroidVector    = np.mean(windowVectors, axis=0)
                    centroidUnitVec   = centroidVector / np.linalg.norm(centroidVector)

                    maxDispersion = max(
                                    angular_deviation(vec, centroidUnitVec)
                                    for vec in windowVectors
                                )
                                
#                    print("centroid")
                    
                    if maxDispersion <= dispersionThreshold:
                        j += 1
#                        print("add on")
                    else:
#                        print("break")
                        break
                    
#                print("j: ", j)
#                print(currObjectTracker)
                if currObjectTracker is None:
                    i += 1
#                    print("empty 2")
                    if i < totalFrames:
                            continue
                
#                print("final before", totalFrames, j, i)
#                j = totalFrames - 1 if j >= totalFrames else j
#                spanLength = j - i
              
                j = totalFrames - 1 if j >= totalFrames else j
                i = 0 if i < 0 else i
                if i >= totalFrames or j >= totalFrames:
                    break  # or return fixationSpans
                spanLength = j - i
                spanDuration = float(self.timeStampList[j]) - float(self.timeStampList[i])

                
                spanDuration = float(self.timeStampList[j]) - float(self.timeStampList[i])
                # if we hit the duration threshold, record as fixation
                if spanDuration >= durationThreshold:
                    fixationSpans.append((i, j))
                # advance to the next unchecked frame
                i = j if spanLength > 0 else i+1
                
#                print("final", totalFrames, j, i, spanDuration, spanLength)

            return fixationSpans

        def assignLabelsToTimestamps(fixationSpanList):
            for timestamp in self.timeStampList:
                currData = objectTracker[timestamp] if client is None else objectTracker[timestamp][client]
                #self.saccadeFixationDict[timestamp] = SACCADE
                
                if currData is None:
                    continue
                    
                if FIXATION_TRACKER not in currData:
                    currData[FIXATION_TRACKER] = {DELTA_ANGLE: 0.0, DELTA_VELOCITY: 0.0}
                    
                currData[FIXATION_TRACKER][FIXATION_STATUS] = SACCADE
                
            for startIndex, endIndex in fixationSpanList:
                for index in range(startIndex, endIndex):
                    timestamp = self.timeStampList[index]
                    
                    currData = objectTracker[timestamp] if client is None else objectTracker[timestamp][client]
                    
                    if FIXATION_TRACKER not in currData:
                        currData[FIXATION_TRACKER] = {DELTA_ANGLE:0.0, DELTA_VELOCITY: 0.0}
                    
                    currData[FIXATION_TRACKER][FIXATION_STATUS] = FIXATION

        def computeSaccadeKinematics():
            previousLabel = None
            saccadeStartTime = None
            accumulatedAngle = 0.0
            peakVelocity = 0.0
            
            for iterationIndex, timestamp in enumerate(self.timeStampList):
                currData = objectTracker[timestamp] if client is None else objectTracker[timestamp][client]
                
                if currData is None:
                    continue
                    
                if FIXATION_TRACKER not in currData:
                    currData[FIXATION_TRACKER] = {DELTA_ANGLE: 0.0, DELTA_VELOCITY: 0.0}
                        
                currentLabel = currData[FIXATION_TRACKER][FIXATION_STATUS]
                if currentLabel == SACCADE:
                    if previousLabel == FIXATION:
                        saccadeStartTime = float(timestamp)
                        accumulatedAngle = 0.0
                        peakVelocity = 0.0
                    if iterationIndex > 0:
                        timeDelta = float(timestamp) - float(self.timeStampList[iterationIndex - 1])
                        angleChange = currData[FIXATION_TRACKER][DELTA_ANGLE]
                        velocity = angleChange / timeDelta
                        peakVelocity = max(peakVelocity, velocity)
                        currData[FIXATION_TRACKER][DELTA_VELOCITY] = velocity
                        accumulatedAngle += angleChange
                else:  # FIXATION
                    if previousLabel == SACCADE:
                        accumulatedAngle = 0.0
                        peakVelocity = 0.0
                        self.fixationCount += 1
                    if iterationIndex > 0:
                        timeDelta = float(timestamp) - float(self.timeStampList[iterationIndex - 1])
                        angleChange = currData[FIXATION_TRACKER][DELTA_ANGLE]
                        velocity = angleChange / timeDelta
                        peakVelocity = max(peakVelocity, velocity)
                        currData[FIXATION_TRACKER][DELTA_VELOCITY] = velocity
                        accumulatedAngle += angleChange
                previousLabel = currentLabel

        def updateDwellTimes(viewAnalysis, client):
            from collections import defaultdict
            
            # 1) Build a map: objectId -> list of its views (in chronological order)
            viewsByObject = defaultdict(list)
            for index in viewAnalysis.get('views_without_threshold', []):
                view = viewAnalysis['views_without_threshold'][index]
                viewsByObject[view['object']].append(view)
                        
            # ----------- new submethod -----------
        def compileFixationSaccadeMetrics(fixationIntervals, viewAnalysis):
            timestamps               = self.timeStampList
            self.fixationSaccadeMetrics = {}
            
#              #  1) MERGE ADJACENT/OVERLAPPING FIXATIONS 
#            mergedFixations = []
#            for start, end in fixationIntervals:
#                if mergedFixations and start <= mergedFixations[-1][1] + 1:
#                    # extend the previous block
#                    mergedFixations[-1] = (
#                        mergedFixations[-1][0],
#                        max(mergedFixations[-1][1], end)
#                    )
#                else:
#                    mergedFixations.append((start, end))
#            fixationIntervals = mergedFixations

            # Build saccade intervals as the gaps between fixation spans
            saccadeIntervals = []
            previousEndIndex = 0
            for fixStart, fixEnd in fixationIntervals:
                #if previousEndIndex <= fixStart:
                saccadeIntervals.append((previousEndIndex, fixStart))
                previousEndIndex = fixEnd
            # tail end
            if previousEndIndex < len(timestamps):
                saccadeIntervals.append((previousEndIndex, len(timestamps)-1))

            # helper to compute dispersion over any span
            def computeDispersionForSpan(startIdx, endIdx):
                windowVectors = []
                for i in range(startIdx, endIdx):
                    if timestamps[i] in directionVectors:
                        windowVectors.append(directionVectors[timestamps[i]])
                
                if len(windowVectors) == 0:
                    return 0.0
                    
                centroidVec = np.mean(windowVectors, axis=0)
                centroidUnit = centroidVec / np.linalg.norm(centroidVec)
                dispersions = [
                    np.arccos(np.dot(vec, centroidUnit))
                    for vec in windowVectors
                ]
                return max(dispersions) if len(dispersions) > 0 else 0.0
                
            def computeCentroidUnit(startIdx, endIdx):
                vecs = [ directionVectors[timestamps[i]] for i in range(startIdx, endIdx) ]
                c = np.mean(vecs, axis=0)
                return c / np.linalg.norm(c)
            

            # record FIXATION metrics
            for startIdx, endIdx in fixationIntervals:
                endIdx = len(timestamps) -1 if endIdx >= len(timestamps) else endIdx
                spanStartTime = float(timestamps[startIdx])
                spanEndTime   = float(timestamps[endIdx])
                intervalDuration = spanEndTime - spanStartTime
                intervalDispersion = computeDispersionForSpan(startIdx, endIdx)
                
                position = self.gazePoints[timestamps[startIdx]]
                
                totalAmp = 0
                for i in range(startIdx, endIdx):
                    currData = objectTracker[timestamps[i]] if client is None else objectTracker[timestamps[i]][client]
                    totalAmp += currData[FIXATION_TRACKER][DELTA_ANGLE]
                    
                #  average velocity like saccades 
                avgVel = totalAmp / intervalDuration if intervalDuration > 0 else 0.0
                
                amps = []
                for i in range(startIdx, endIdx):
                    currData = objectTracker[timestamps[i]] if client is None else objectTracker[timestamps[i]][client]
                    amps.append(currData[FIXATION_TRACKER][DELTA_ANGLE])
                    
                peakAmp = max(amps) if amps else 0.0

                #  peak instantaneous velocity (amp / dt) 
                instVels = []
                for idx in range(startIdx + 1, endIdx):
                    dt = float(timestamps[idx]) - float(timestamps[idx - 1])
                    if dt > 0:
                        currData = objectTracker[timestamps[idx]] if client is None else objectTracker[timestamps[idx]][client]
                        instVels.append(
                            currData[FIXATION_TRACKER][DELTA_VELOCITY]
                        )
                peakVel = max(instVels) if instVels else 0.0

                #  pull the first non-None ROI in the merged span
                roi = None

                for index in viewAnalysis['views_without_threshold']:
                    view = viewAnalysis['views_without_threshold'][index]
                    if view['start'] <= float(timestamps[startIdx]) <= view['end']:
                        roi = view['object']
                        break

                self.fixationSaccadeMetrics[spanStartTime] = {
                    "eventType":       "FIXATION",
                    "object":          roi,
                    "eventDuration":   intervalDuration,
                    "dispersion":      intervalDispersion,
                    "angularDistance":  totalAmp,
                    "averageVelocity": avgVel,
                    "peakAmplitude":   peakAmp,
                    "peakVelocity":    peakVel,
                    "position":        position,
                    "startTime":       timestamps[startIdx],
                    "endTime":         timestamps[endIdx]
                }                    

            # record SACCADE metrics
            for startIdx, endIdx in saccadeIntervals:
                if startIdx == endIdx:
                    continue
                    
                currData = objectTracker[timestamps[startIdx]]
                if currData is None:
                    continue
                    
                endIdx = len(timestamps) -1 if endIdx >= len(timestamps) else endIdx
                spanStartTime = float(timestamps[startIdx])
                spanEndTime   = float(timestamps[endIdx])
                intervalDuration = spanEndTime - spanStartTime
                intervalDispersion = computeDispersionForSpan(startIdx, endIdx)

                totalAmp = 0
                for i in range(startIdx, endIdx):
                    currData = objectTracker[timestamps[i]] if client is None else objectTracker[timestamps[i]][client]
                    if currData is not None:
                        totalAmp += currData[FIXATION_TRACKER][DELTA_ANGLE]
                    
                #  average velocity like saccades 
                avgVel = totalAmp / intervalDuration if intervalDuration > 0 else 0.0
                
                amps = []
                for i in range(startIdx, endIdx):
                    currData = objectTracker[timestamps[i]] if client is None else objectTracker[timestamps[i]][client]
                    if currData is not None:
                        amps.append(currData[FIXATION_TRACKER][DELTA_ANGLE])
                    
                peakAmp = max(amps) if amps else 0.0

                #  peak instantaneous velocity (amp / dt) 
                instVels = []
                for idx in range(startIdx + 1, endIdx):
                    dt = float(timestamps[idx]) - float(timestamps[idx - 1])
                    if dt > 0:
                        currData = objectTracker[timestamps[idx]] if client is None else objectTracker[timestamps[idx]][client]
                        if currData is not None:
                            instVels.append(
                            currData[FIXATION_TRACKER][DELTA_VELOCITY]
                            )
                peakVel = max(instVels) if instVels else 0.0
                
                #  find the flanking fixations 
                prevFix = nextFix = None
                for fStart, fEnd in fixationIntervals:
                    if fEnd <= startIdx:
                        prevFix = (fStart, fEnd)
                    elif fStart >= endIdx and nextFix is None:
                        nextFix = (fStart, fEnd)

                #  compute centroid-to-centroid amplitude (in degrees) if both exist 
                interFixAmp = None
                if prevFix and nextFix:
                    v1 = computeCentroidUnit(prevFix[0], prevFix[1])
                    v2 = computeCentroidUnit(nextFix[0], nextFix[1])
                    interFixAmp = np.arccos(np.dot(v1, v2)) * 180.0/np.pi
                    
                interFixVel = interFixAmp/intervalDuration if interFixAmp is not None else None
                
                roi = []

                for index in viewAnalysis['views_without_threshold']:
                    view = viewAnalysis['views_without_threshold'][index]
                    if view['start'] <= float(timestamps[startIdx]) <= view['end']:
                        roi.append(view['object'])
                        
                if len(roi) > 1 or len(roi) == 0:
                    roi = None
                else:
                    roi = roi[0]

                self.fixationSaccadeMetrics[spanStartTime] = {
                    "eventType":       "SACCADE",
                    "object":          roi, 
                    "eventDuration":   intervalDuration,
                    "dispersion":      intervalDispersion,
                    "angularDistance":  totalAmp,
                    "averageVelocity": avgVel,
                    "peakAmplitude":   peakAmp,
                    "peakVelocity":    peakVel,
                    "interFixationAmplitude": interFixAmp,
                    "interFixationVelocity": interFixVel,
                    "startTime":       timestamps[startIdx],
                    "endTime":         timestamps[endIdx]
                }

        # ------------- main execution flow -------------
        initBuffers()
        viewStatusDict = {}
        for timestamp in objectTracker:
            viewStatusDict[timestamp] = None
            if client is not None:
                if client not in objectTracker[timestamp]:
                    continue
                    
                currData = objectTracker[timestamp][client]
            else:
                currData = objectTracker[timestamp]
                
            if currData is None:
                continue
                
            if GAZE_TRACKER in currData:
                for objectName in currData[GAZE_TRACKER]:
                    if VIEW_STATUS in currData[GAZE_TRACKER][objectName]:
                        viewBool = currData[GAZE_TRACKER][objectName][VIEW_STATUS]
                    else:
                        viewBool = currData[GAZE_TRACKER][objectName][GAZE_BOOL]
                        
                    if viewBool and objectName is not RAW_INTERSECT:
                        viewStatusDict[timestamp] = objectName
                        break
            elif GAZE_OBJECTS in currData:
                for objectName in currData[GAZE_OBJECTS]:
                    if VIEW_STATUS in currData[GAZE_OBJECTS][objectName]:
                        viewBool = currData[GAZE_OBJECTS][objectName][VIEW_STATUS]
                    else:
                        viewBool = currData[GAZE_OBJECTS][objectName][GAZE_BOOL]
                        
                    if viewBool and objectName is not RAW_INTERSECT:
                        viewStatusDict[timestamp] = objectName
                        break
        
        viewAnalysis = analyzeViews(viewStatusDict, buffer = 1)
        
        extractTimestampsAndPoints(viewAnalysis)
        
        if self.noiseReductionWindowSize > 0:
            applyNoiseReductionFilter()
            
        if not self.timeStampList:
            return
    
#        print(client)
        if client is not None:
            for ts in objectTracker:
                if client in objectTracker[ts]:
                    if objectTracker[ts][client] == {}:
                        objectTracker[ts].remove(client)

        self.replayData[OBJECT_TRACKER] = {k: v for k, v in self.replayData[OBJECT_TRACKER].items() if v != {}}
        
#        print("1")
        directionVectors = computeDirectionVectors()
#        print("1")
        computeFrameToFrameAngles(directionVectors)
        
        # Create a list of timestamps that have complete data
        valid_ts = [
            ts for ts in self.timeStampList
            if (ts in self.gazePoints) and (ts in self.avatarHeadPoints)
               and (ts in objectTracker) and (
                    (client is None and objectTracker[ts] is not None) or
                    (client is not None and client in objectTracker[ts])
               )
        ]

        # If your timestamps are numeric strings, sort them numerically to avoid order issues
        # (optional but recommended for replays)
        valid_ts.sort(key=float)

        # Replace timeStampList used by identifyFixationIntervals
        self.timeStampList = valid_ts

#        print("1")
        fixationIntervals = identifyFixationIntervals(directionVectors)
#        print("1")
        assignLabelsToTimestamps(fixationIntervals)
#        print("1")
        computeSaccadeKinematics()
#        print("1")
        updateDwellTimes(viewAnalysis, client)
#        print("1")
        compileFixationSaccadeMetrics(fixationIntervals, viewAnalysis)
#        print("1")
        self.replayData[OBJECT_TRACKER] = objectTracker
#        print("1")
        return viewAnalysis, self.fixationSaccadeMetrics
        
    def setFlag(self, flagText = '-', columnName = SIGHTLAB_FLAG):
        """
        Set a flag for the current frame of data.
        
        Flags are used to mark specific events or conditions during experiment recording.
        Multiple flags can be accumulated in the default SIGHTLAB_FLAG column.
        
        Args:
            flagText (str, optional): Text content of the flag. Default '-'
            columnName (str, optional): Column name for the flag. Default SIGHTLAB_FLAG
            
        Returns:
            None. Updates self.flag or self.customFlags dictionary
        """
        if columnName == SIGHTLAB_FLAG:
            if not self.flag == "-" and not flagText == "-":
                self.flag += ", " + str(flagText)
            else:
                self.flag = str(flagText)
        else:
            self.customFlags[columnName] = str(flagText)
        
    def setGazeState(self, sceneObject, state, fixationPeriod = 0):
        """
        Update the gaze state for a tracked scene object.
        
        Sets whether an object is currently being gazed at and tracks fixation duration.
        Used to maintain real-time gaze interaction state for AOI (Area of Interest) analysis.
        
        Args:
            sceneObject: The scene object being tracked
            state: Gaze state (True if object is being fixated on, False otherwise)
            fixationPeriod (float, optional): Duration of fixation in seconds. Default 0
            
        Returns:
            None. Updates self.gazeTracker dictionary
        """
        if sceneObject in self.gazeTracker:
            self.gazeTracker[sceneObject][GAZE_STATE] = state
            self.gazeTracker[sceneObject][FIXATION_PERIOD] = fixationPeriod
            
    def updateClientData(self, e):
        """
        Receive and store client data in multi-user server mode.
        
        In server mode, receives replay data from connected clients and stores it with
        timestamp synchronization. Uses binary search for efficient timestamp matching.
        Aggregates custom objects and flags from all clients.
        
        Args:
            e: Event object containing client data with attributes:
               - e.client: Client network object
               - e.timestamp: Client's local timestamp (string)
               - e.replayData: Client's frame data
               - e.customObjects: Client's custom tracked objects
               - e.customFlags: Client's custom flag data
               
        Returns:
            None. Updates self.replayData, self.customObjects, self.customFlags dictionaries
        """
        def calculateClosestTimestamp(timestamp):
            keys = self.replayData[OBJECT_TRACKER].keys()

            if keys:  
                closest_key = min(keys, key=lambda x: abs(float(x) - float(timestamp)))
            else:
                closest_key = timestamp
                
            return closest_key
            
        def closest_last_n(ts):
            # keys is a dict_keys or list of key strings
            keys = self.replayData[OBJECT_TRACKER].keys()
            
            if len(keys) > 1:
                lastTS = float(list(keys)[-1])
                
                n = int(abs(lastTS - float(ts))*120 + 200)
                
                tail = list(keys)[-n:]                    # last N by insertion order
                tsf  = float(ts)
                return min(tail, key=lambda k: abs(float(k) - tsf)) if tail else ts
            else:
                return ts
                
        def calculateClosestTimestampNew(ts):
            from bisect import bisect_left
            d = self.replayData[OBJECT_TRACKER]
            if not d:
                return ts

            # Lazy-build/refresh a sorted cache of (float_ts -> original_key)
            # Refresh when the dict size changes (cheap & safe heuristic).
            if not hasattr(self, "_ts_cache_size") or self._ts_cache_size != len(d):
                pairs = sorted((float(k), k) for k in d.keys())
                self._ts_vals = [p[0] for p in pairs]   # sorted float timestamps
                self._ts_keys = [p[1] for p in pairs]   # corresponding original keys (likely strings)
                self._ts_cache_size = len(d)

            vals = self._ts_vals
            keys = self._ts_keys
            tsf  = float(ts)

            i = bisect_left(vals, tsf)
            if i == 0:
                return keys[0]
            if i == len(vals):
                return keys[-1]

            # choose closer neighbor
            before, after = vals[i-1], vals[i]
            return keys[i-1] if (tsf - before) <= (after - tsf) else keys[i]


        clientID = self.clientDict[e.client]
            
        if not clientID in self.customObjects:
            self.customObjects[clientID] = e.customObjects
            
        if not clientID in self.customFlags:
            self.customFlags[clientID] = e.customFlags
        
#        timestamp = calculateClosestTimestamp(e.timestamp)
#        timestamp = closest_last_n(e.timestamp)
        timestamp = calculateClosestTimestampNew(e.timestamp)
        
#        timestamp = e.timestamp
        
        if not timestamp in self.replayData[OBJECT_TRACKER]:
            self.replayData[OBJECT_TRACKER][timestamp] = {}
            
        if not isinstance(self.replayData[OBJECT_TRACKER][timestamp], dict):
            self.replayData[OBJECT_TRACKER][timestamp] = {clientID: {}}
            
        self.replayData[OBJECT_TRACKER][timestamp][clientID] = e.replayData
        
        # Inject server-side AVATAR_OBJECTS and CUSTOM_OBJECTS into client frame data
        # so they appear in the replay (server doesn't call updateReplayData)
        if self.serverMode:
            clientData = self.replayData[OBJECT_TRACKER][timestamp][clientID]
            if isinstance(clientData, dict):
                # Inject AVATAR_OBJECTS
                for item in self.sceneObjects.get(AVATAR_OBJECTS, {}):
                    avatarObject = self.sceneObjects[AVATAR_OBJECTS][item]
                    
                    # Dynamic header registration
                    if item not in self.replayData.get(AVATAR_OBJECTS, {}):
                        if hasattr(avatarObject, '_childNodeName'):
                            self.replayData[AVATAR_OBJECTS][item] = "__CHILD__:" + avatarObject._childNodeName
                        else:
                            self.replayData[AVATAR_OBJECTS][item] = avatarObject.getFilename()
                    
                    if AVATAR_OBJECTS not in clientData:
                        clientData[AVATAR_OBJECTS] = {}
                    
                    if item not in clientData[AVATAR_OBJECTS]:
                        isChild = hasattr(avatarObject, '_childNodeName')
                        if isChild:
                            position = avatarObject.getPosition()
                            orientation = avatarObject.getEuler()
                            scale = avatarObject.getScale()
                        else:
                            position = avatarObject.getPosition(mode=viz.ABS_GLOBAL)
                            orientation = avatarObject.getEuler(mode=viz.ABS_GLOBAL)
                            scale = avatarObject.getScale(mode=viz.ABS_GLOBAL)
                        
                        state = 0
                        try:
                            for animationItem in avatarObject.getAnimationList():
                                animID = avatarObject.getAnimationID(animationItem)
                                if avatarObject.getCycleRunning(animID):
                                    state = animID
                        except:
                            pass
                        
                        clientData[AVATAR_OBJECTS][item] = {
                            POSITION: position,
                            ORIENTATION: orientation,
                            SCALE: scale,
                            AVATAR_STATE: state,
                            'isChild': isChild
                        }
                
                # Inject CUSTOM_OBJECTS
                for item in self.sceneObjects.get(CUSTOM_OBJECTS, {}):
                    if not isinstance(self.sceneObjects[CUSTOM_OBJECTS][item], list):
                        customObject = self.sceneObjects[CUSTOM_OBJECTS][item]
                        if item not in self.replayData.get(CUSTOM_OBJECTS, {}):
                            self.replayData[CUSTOM_OBJECTS][item] = customObject.getFilename()
                    else:
                        customObject = self.sceneObjects[CUSTOM_OBJECTS][item][0]
                        if item not in self.replayData.get(CUSTOM_OBJECTS, {}):
                            self.replayData[CUSTOM_OBJECTS][item] = [self.sceneObjects[CUSTOM_OBJECTS][item][1], self.sceneObjects[CUSTOM_OBJECTS][item][2].getFilename()]
                    
                    if CUSTOM_OBJECTS not in clientData:
                        clientData[CUSTOM_OBJECTS] = {}
                    
                    if item not in clientData[CUSTOM_OBJECTS]:
                        position = customObject.getPosition(mode=viz.ABS_GLOBAL)
                        orientation = customObject.getEuler(mode=viz.ABS_GLOBAL)
                        scale = customObject.getScale(mode=viz.ABS_GLOBAL)
                        visible = customObject.getVisible()
                        
                        clientData[CUSTOM_OBJECTS][item] = {
                            POSITION: position,
                            ORIENTATION: orientation,
                            SCALE: scale,
                            VISIBLE: visible
                        }
                    
    def writeSessionData(self):
        """
        Process and write all session data to output files.
        
        Coordinates the complete data export pipeline when a trial ends:
        1. Cleans empty replay data frames
        2. Runs fixation/saccade analysis for each client
        3. Writes various output files based on enabled flags:
           - Trial tracking data (raw frame-by-frame)
           - Experiment summary (aggregated metrics)
           - Timeline data (temporal analysis)
           - Fixation timeline (fixation-specific analysis)
           - Replay data (for playback in replay mode)
           - Trial configuration data
        
        Returns:
            None. Writes data to CSV/JSON files and updates internal state
        """
        if not self.trialState or self.clientMode:
            return
        # Temporarily bypass all data writing to test performance
#        print("writeSessionData() bypassed for testing")
#        return
            
        self.replayData[OBJECT_TRACKER] = {k: v for k, v in self.replayData[OBJECT_TRACKER].items() if v != {}}
        
        for client in (self.clientDict if self.serverMode else [None]):
            clientName = client if client is None else self.clientDict[client]
            viewAnalysis, fixationMetrics = self.saccadeFixationCalculate(self.replayData[OBJECT_TRACKER], self.dispersionThreshold, self.durationThreshold, self.dwellThreshold, self.noiseReductionWindowSize, clientName)

            if self.trackingDataFlag:
                self.writeTrialData(self.replayData, clientName)
                
            if self.experimentSummaryFlag:
                self.appendTrialSummary(self.replayData, viewAnalysis, fixationMetrics, clientName)
                
            if self.trialTimeLineFlag:
                self.writeTimeLineData(viewAnalysis, fixationMetrics, clientName)
            
            if self.fixationTimeLineFlag:
                self.writeFixationTimelineData(fixationMetrics, clientName)
            
        if self.replayDataFlag:
            self.writeReplayData()
                
        if self.trialConfigFile is not None:
            self.appendConfigData()        
    
    def __del__(self):
        pass
        
class GUI:
    """
    Graphical User Interface for experiment configuration and management.
    
    Provides an interactive GUI window for configuring experiment parameters including:
    - Participant information
    - Trial settings and conditions
    - Environment and object selection
    - Regions of interest (ROI) definition
    - Media setup for 360° videos/images
    - Multi-user server/client configuration
    - Data recording options
    
    Handles loading/saving configurations and provides real-time preview of experimental setups.
    """
    def __init__(self, guiWindow, isGUI, biopacToggle, gazePointWindow, configPath = None, configSelect = None, directory = None, serverMode = False, clientMode = False, demoMode = False):
        """
        Initialize the GUI configuration interface.
        
        Args:
            guiWindow: Vizard GUI window object for displaying interface
            isGUI (bool): Whether GUI mode is enabled
            biopacToggle: BIOPAC device toggle state or None
            gazePointWindow: Window for gaze point visualization
            configPath (str, optional): Path to configuration file to load
            configSelect (str, optional): Specific config selection from file
            directory (str, optional): Working directory path, defaults to script location
            serverMode (bool, optional): Whether running as multi-user server. Default False
            clientMode (bool, optional): Whether running as multi-user client. Default False
            demoMode (bool, optional): Whether running in demo mode. Default False
        """
        self.demoMode = demoMode
        
        if directory is None:
#            stack = inspect.stack()
#            # The first entry in the stack is the current function frame, so get the second
#            caller_frame = stack[2]
#            if clientMode or serverMode:
#                caller_frame = stack[3]
#                
#            # Get the path of the file in the caller frame
#            module_path = caller_frame.filename
#            # Convert to absolute path, if necessary
#            self.path =  os.path.abspath(module_path)
            self.path = sys.argv[0]
            self.scriptDirectory = os.path.abspath(os.path.dirname(self.path))
        else:
            self.path = directory
            self.scriptDirectory = os.path.dirname(directory)
        
        self.biopacToggle = biopacToggle
        
        self.serverMode = serverMode
        self.clientMode = clientMode
        
        if self.clientMode:
            viz.MainView.getHeadLight().enable()
            
        self.clientColor = viz.WHITE
        
        self.trialSettings = {}
        
        self.trialSettings[DEFAULT] = {
            SCREEN_RECORD: viz.OFF,
            BARCHART: viz.OFF,
            NUMBER_OF_TRIALS: 1,
            RANDOM_TRIALS: False,
            DATA_SAVING: PER_TRIAL,
            START_EXPERIMENT_TEXT: "",
            END_EXPERIMENT_TEXT: "",
            TRACKING: viz.ON,
            TRIAL_LABEL: "A",
            BIOPAC: viz.OFF if biopacToggle is None else biopacToggle,
            DWELL_TIME: DWELL_THRESHOLD_VALUE,
            DISPERSION_THRESHOLD: 1,
            DURATION_THRESHOLD: 0.1,
            NOISE_REDUCTION: 0,
            
            AVATAR_HEAD: None,
            AVATAR_RIGHT_HAND: None,
            AVATAR_LEFT_HAND: None,
            
            FULL_BODY_TOGGLE: viz.OFF,
            FULL_BODY_AVATARS: None,
            SEATED_MODE: viz.OFF,
            SHOW_AVATAR: viz.OFF,
            
            RECENT_CONFIG: RECENT_CONFIG_FILE,
            
            GAZE_POINT: None,
            
            MODE: MODEL_3D,
            ENVIRONMENT: None,
            ENVIRONMENT_DIRECTORY: DEFAULT_ENVIRONMENT_DIRECTORY,
            
            START_CONDITION: [KEY_PRESS, "SPACEBAR"] if isGUI else [NO_CONDITION, ""],
            END_CONDITION: [KEY_PRESS, "SPACEBAR"] if isGUI else [NO_CONDITION, ""],
            
            TRIAL_SETUP: {},
            MEDIA_SETUP:{},
            CLIENT_INFO: {SERVER_LIST: [], SERVER_NAME: "", FIRST_NAME: "", SHOW_NAME: False, SSP_SUFFIX: ""},
            REGIONS_OF_INTEREST:{},
            SCENE_SETUP: ADDITIONAL_SETTINGS
        }
        
        if self.clientMode:
            self.trialSettings[DEFAULT][AUTO_ASSIGN] = viz.OFF
            
        vizdragdrop.disable()
        
        #self.trialSettings['1'] = deepcopy(self.trialSettings[DEFAULT])
        
        self.trialSchema = None
        
        self.isGUI = isGUI
        self.configPath = configPath
        self.configSelect = configSelect
        
        self.defaultTrialSettings = deepcopy(self.trialSettings[DEFAULT])
        self.newTrialSettings = deepcopy(self.defaultTrialSettings)
        
        self.serverConnected = False
        self.serverAttempted = False
        
        self.buttonLabels = {}
        self.trialButtonLabels = {}
        self.environmentButtonLabels = {}
        self.environmentNodes = None
        self.modifyFlag = False
        self.resourceLists = None
        
        self.configDirectory = DEFAULT_CONFIG_DIRECTORY
        self.avatarHeadDirectory = AVATAR_HEAD_RESOURCE_PATH
        self.avatarHandsDirectory = AVATAR_HANDS_RESOURCE_PATH
        self.gazePointDirectory = GAZE_POINT_RESOURCE_PATH
        self.environmentDirectory = DEFAULT_ENVIRONMENT_DIRECTORY
        self.mediaDirectory = DEFAULT_MEDIA_DIRECTORY
        self.recordingsDirectory = DEFAULT_RECORDINGS_DIRECTORY
        self.dataDirectory = DEFAULT_DATA_DIRECTORY
        
        self.tempEnvironment = None
        self.tempAvatar = None
        self.tempFullBodyAvatar = None
        self.tempText = None
        self.clientID = "clientID"
        self.transportState = False
        
        self.avatarGroup = viz.addGroup()
        mainViewNode = vizconnect.getDisplay().getRaw().getView()
        rootLink = viz.link(mainViewNode, self.avatarGroup, mask=viz.LINK_ALL)
        rootLink.preTrans([0,-1.8,0])
#        rootLink.preEuler([20,0,0])
        
        self.textCharLimit = 12
        self.tempAvatarBlink = None
        self.tempLHand = None
        self.tempRHand = None
        self.regionsOfInterest = {}
        
        self.mediaToggle = None
        self.conditionTextboxValue = "-"
        #self.updateGaze = vizact.onupdate(vizconnect.PRIORITY_ANIMATOR+1, self.updateGazeObject)
        self.updateGaze = vizact.onupdate(vizconnect.PRIORITY_ANIMATOR+1, self.updateGazeObject)
        #self.updateGaze.setEnabled(viz.OFF)
        
        self.recordROI = None
        
        self.tempMedia = None
        
        self.loadedConfig = False

        # Auto-refresh: poll environment file for external changes (e.g. saved in Inspector)
        self._env_poll_timer = None
        self._env_poll_path = None
        self._env_poll_mtime = 0

        self.guiWindow = guiWindow
        self.gazePointWindow = gazePointWindow
        self.gazePointObject = None
        self.sceneInfoPanel = None
        self.trialInfoPanel = None
        self.transportToggleAction = None
        
        self.customChildFlag = False
        
        if self.clientMode:
            self.loadTempEnvironment(default = True)
        
        self.pageLimit = 5
        self.currTrial = DEFAULT
        self.windowSize = viz.MainWindow.getSize(mode = viz.WINDOW_PIXELS)
        
        self.conditionToMenuDict = {
            NO_CONDITION: "None", 
            KEY_PRESS: "Key Press", 
            TIMER: "Timer", 
            CUSTOM_EVENT: "Custom Event", 
            ON_MEDIA_END: "Media End",
            ON_GAZE_TIME: "Gaze Item"
        }
        
        self.menuToConditionDict = {
            "None": NO_CONDITION,
            "Key Press": KEY_PRESS,
            "Timer": TIMER,
            "Custom Event": CUSTOM_EVENT,
            "Media End": ON_MEDIA_END,
            "Gaze Item": ON_GAZE_TIME
        }
        
        self.conditionValues = {
            NO_CONDITION: "-", 
            KEY_PRESS: "SPACEBAR", 
            TIMER: "10", 
            CUSTOM_EVENT: "triggerPress", 
            ON_MEDIA_END: "0",
            ON_GAZE_TIME: "None"
        }
        
        self.participantData = {
            ID: "",
            PARTICIPANT_INFO1: "",
            PARTICIPANT_INFO2: ""
        }
        
    def loadConfigFile(self):
        """
        Load experiment configuration from JSON file.
        
        Attempts to load configuration from:
        1. User-specified config file (if configPath provided)
        2. Most recently used config (stored in recent_config.json)
        3. Default settings (if no config found)
        
        Handles backwards compatibility by adding missing keys from new settings.
        Converts old list-based trial setup format to dictionary format.
        
        Returns:
            None. Updates self.trialSettings with loaded configuration
        """
        if viz.res.isPublished():
            base_path = viz.res.getPublishedPath('')
        else:
            base_path = self.scriptDirectory
        
        recentConfig = os.path.join(base_path, RECENT_CONFIG_PATH)
        
        if path.exists(recentConfig) and not os.path.getsize(recentConfig) == 0 and (self.isGUI or self.configPath is not None):
            configFilePath = recentConfig
            
            if self.configPath is not None:
                if viz.res.isPublished():
                    configFilePath = os.path.join(base_path, self.configPath)
                else:
                    configFilePath = self.configPath
            
            configFile = open(configFilePath, "r")
            
            self.suffix = None
            if CLIENT_INFO in self.trialSettings and SSP_SUFFIX in self.trialSettings[CLIENT_INFO]:
                suffix = self.trialSettings[DEFAULT][CLIENT_INFO][SSP_SUFFIX]
                
            self.trialSettings = json.load(configFile)
            if "DEFAULT" in self.trialSettings:
                self.trialSettings.pop("DEFAULT")
            
            if RECENT_CONFIG in self.trialSettings[DEFAULT]:
                recentConfig = os.path.join(base_path, DEFAULT_CONFIG_DIRECTORY, self.trialSettings[DEFAULT][RECENT_CONFIG])
                if path.exists(recentConfig) and not os.path.getsize(recentConfig) == 0 and self.configPath is None:
                    configFile.close()
                    
                    configName = self.trialSettings[DEFAULT][RECENT_CONFIG]
                    configFile = open(recentConfig, "r")
                    self.trialSettings = json.load(configFile)
                    self.trialSettings[DEFAULT][RECENT_CONFIG] = configName
                    
                    if "DEFAULT" in self.trialSettings:
                        self.trialSettings.pop("DEFAULT")
                    
            self.loadedConfig = True
            
            if self.biopacToggle is not None and not self.serverMode:
                self.trialSettings[DEFAULT][BIOPAC] = self.biopacToggle
                    
            for trial in self.trialSettings:
                missingKeys = set(self.newTrialSettings.keys()) - set(self.trialSettings[trial].keys())
                for key in missingKeys:
                    self.trialSettings[trial][key] = self.newTrialSettings[key]
                    
                for item in self.trialSettings[trial][TRIAL_SETUP]:
                    if isinstance(self.trialSettings[trial][TRIAL_SETUP][item], list):
                        target = self.trialSettings[trial][TRIAL_SETUP][item][0]
                        visible = self.trialSettings[trial][TRIAL_SETUP][item][1]
                        grab = self.trialSettings[trial][TRIAL_SETUP][item][2]
                        
                        self.trialSettings[trial][TRIAL_SETUP][item] = {
                        TARGET: target,
                        VISIBLE: visible,
                        GRAB: grab
                        }
                
            print("Loaded Project File\n", self.trialSettings)
                                
            configFile.close()
         
        else:
            print("No config file found")
            self.loadedConfig = False
            
#    def loadSchema(self):
#        #read the schema file
#        
#        def resolve_refs(node, defs):
#            if isinstance(node, dict):
#                if "$ref" in node:
#                    ref_path = node["$ref"].split("/")[-1]
#                    return resolve_refs(defs[ref_path], defs)
#                return {k: resolve_refs(v, defs) for k, v in node.items()}
#            elif isinstance(node, list):
#                return [resolve_refs(item, defs) for item in node]
#            else:
#                return node
#
#        # Usage:
#        schema = json.load(open("config.json"))
#        defs = schema.get("$defs", {})
#        resolved_schema = resolve_refs(schema, defs)
#        
#        #
        
    def addSyncPrimaryServer(self):
        """
        Offer the SightLab Sync primary PC as this client's multi-user server.

        It is added to the server list, and chosen when no server is chosen yet
        (a client that has never run a session has no recent_config_client.stlb, so
        none is). The list is saved with the rest of the client settings when a
        session runs. Off with AUTO_SERVER_FROM_SIGHTLAB_SYNC = False in settings.py.
        """
        if not globals().get('AUTO_SERVER_FROM_SIGHTLAB_SYNC', True):  # an older settings.py lacks it
            return
        try:
            from sightlab_utils import sightlab_sync
            serverName = sightlab_sync.primary_server_name()
            if serverName and sightlab_sync.add_server_choice(
                    self.trialSettings[DEFAULT].setdefault(CLIENT_INFO, {}), serverName, SERVER_LIST, SERVER_NAME):
                print("[SightLab Sync] Server list offers the primary PC: " + serverName)
        except Exception as e:
            print("[SightLab Sync] Could not add the primary PC as server: {}".format(e))

    def generateResourceLists(self):
        """
        Scan resource directories and build file lists for GUI dropdowns.
        
        Populates lists of available resources:
        - Avatar heads (for multi-user visualization)
        - Avatar hands (for hand tracking visualization)
        - Gaze point objects (for gaze visualization)
        - Saved configuration files
        
        Also loads the most recent or specified configuration file.
        
        Returns:
            None. Updates self.avatarHeadFileList, self.avatarHandsFileList,
            self.gazePointFileList, self.loadConfigFileList
        """
        
        self.fullBodyAvatarFileList = []
        
        try:
            for file in os.listdir(FULL_BODY_AVATAR_RESOURCE_PATH):
                self.fullBodyAvatarFileList.append(file)
        except Exception as e:
            print(f"Error loading full body avatar files: {e}") 
            
        self.avatarHeadFileList = []
        for file in os.listdir(AVATAR_HEAD_RESOURCE_PATH):
            self.avatarHeadFileList.append(file)
        
        self.avatarHandsFileList = []
        for file in os.listdir(AVATAR_HANDS_RESOURCE_PATH):
            self.avatarHandsFileList.append(file)
            
        self.gazePointFileList = []
        for file in os.listdir(GAZE_POINT_RESOURCE_PATH):
            self.gazePointFileList.append(file)
            
        self.loadConfigFileList = ["[NEW]"]
        
        if self.configPath is not None:
            self.loadConfigFileList.append(os.path.basename(self.configPath))
        
        if self.configDirectory == DEFAULT_CONFIG_DIRECTORY:
            os.makedirs(self.configDirectory, exist_ok=True)
            
        configFileList = self.findFiles(self.configDirectory, ".stlb")

        self.loadConfigFileList.extend(configFileList)
        
        self.loadConfigFile()
        if self.clientMode:
            self.addSyncPrimaryServer()

        if self.trialSettings[DEFAULT][TRIAL_SETUP] is None:
            self.trialSettings[DEFAULT][TRIAL_SETUP] = {}
        
        if self.environmentDirectory == DEFAULT_ENVIRONMENT_DIRECTORY:
            if self.loadedConfig:
                if self.trialSettings[DEFAULT][MODE] == MODEL_3D:
                    self.environmentDirectory = self.trialSettings[DEFAULT][ENVIRONMENT_DIRECTORY]
                else:
                    self.mediaDirectory = self.trialSettings[DEFAULT][ENVIRONMENT_DIRECTORY]
            
        self.environmentFileList = self.findFiles(self.environmentDirectory)
        
        modelFileTypes = ["osgb", "OSGB", "gltf", "fbx", "glb", "obj"]
        
        for fileList in [self.environmentFileList, self.avatarHeadFileList, self.avatarHandsFileList, self.gazePointFileList]:
            for file in fileList[:]:
                _, ext = os.path.splitext(file)
                # Remove the leading dot for easier comparison
                ext = ext[1:]
                if ext not in modelFileTypes:
                    fileList.remove(file)
                        
        self.mediaFileList = self.findFiles(self.mediaDirectory)
        for file in self.mediaFileList:
            imageFileTypes = ["jpg", "jpeg", "png", "tiff", "pdf", "raw", "gif", "bmp", "webp", "heif", "heic"]
            videoFileTypes = ["mp4", "mov", "avi", "wmv", "hevc", "flv", "mkv", "ogg", "m4v"]
            if file[-3:] not in imageFileTypes and file[-3:] not in videoFileTypes and file[-4:] not in imageFileTypes and file[-4:] not in videoFileTypes:
                self.mediaFileList.remove(file)
            
        self.resourceLists = {
            ENVIRONMENT: self.environmentFileList,
            MEDIA: self.mediaFileList,
            
            AVATAR_HEAD: self.avatarHeadFileList,
            AVATAR_LEFT_HAND: self.avatarHandsFileList,
            AVATAR_RIGHT_HAND: self.avatarHandsFileList,
            
            FULL_BODY_AVATARS: self.fullBodyAvatarFileList,
            
            GAZE_POINT: self.gazePointFileList,
            LOAD_CONFIG: self.loadConfigFileList
        }
        
    def sceneInfo(self):
        """
        Create and display the main experiment configuration GUI panel.
        
        Builds a comprehensive multi-page interface for configuring all experiment parameters:
        - Participant information input
        - Trial settings (number, randomization, data saving mode)
        - Environment/object/media selection
        - Regions of interest (ROI) definition
        - Start/end conditions
        - Eye tracking parameters
        - Multi-user server/client settings
        - Configuration file management (save/load)
        
        Uses nested helper functions for handling UI callbacks and configuration management.
        
        Returns:
            None. Displays GUI window and sets up event handlers
        """
        def saveConfig(textbox):
            self.setSettings()
            self.trialInfo(getSettings=True)
            if self.configDirectory == DEFAULT_CONFIG_DIRECTORY:
                os.makedirs(self.configDirectory, exist_ok=True)
                
            if not self.serverMode:
                name = str(textbox.get()) + ".stlb"
            else:
                name = str(textbox.get()) + "_server.stlb"
                
            path = None
            if name == ".stlb" or name == "_server.stlb":
                name = self.buttonLabels[LOAD_CONFIG].getItems()[self.buttonLabels[LOAD_CONFIG].getSelection()]
            else:
                if not name in self.loadConfigFileList:
                    path = os.path.join(self.scriptDirectory, self.configDirectory, name)
                    self.resourceLists[LOAD_CONFIG].append(path)
                    self.buttonLabels[LOAD_CONFIG].addItem(name)
                    self.loadConfigFileList.append(name)
                    
                self.buttonLabels[LOAD_CONFIG].select(self.buttonLabels[LOAD_CONFIG].getItems().index(name))
                
            if path is None:
                path = os.path.join(self.scriptDirectory, self.configDirectory, name)
                            
            configFile = open(path, "w")
            
            self.buttonLabels[SAVE_CONFIG].message(t("Saved!"))
            json.dump(self.trialSettings, configFile, indent = 4)
                        
            configFile.close()
            
            currentConfig = self.buttonLabels[LOAD_CONFIG].getItems()[self.buttonLabels[LOAD_CONFIG].getSelection()]
            recentConfig = deepcopy(self.trialSettings)
            recentConfig[DEFAULT][RECENT_CONFIG] = currentConfig
            
            configFile = open(RECENT_CONFIG_PATH, "w")
            json.dump(recentConfig, configFile, indent = 4)
            configFile.close()
        
        def setDefault():
            self.trialSettings = {}
            self.trialSettings[DEFAULT] = deepcopy(self.newTrialSettings)
            self.trialSettings[DEFAULT][ENVIRONMENT_DIRECTORY] = self.environmentDirectory
            #self.trialSettings['1'] = self.trialSettings[DEFAULT]
            
            self.defaultTrialSettings = deepcopy(self.newTrialSettings)
            self.modifyFlag = False
            
            if self.tempEnvironment is not None:
                self.tempEnvironment.remove()
                self.tempEnvironment = None
                
            self.loadedConfig = False

            self.buttonLabels[SAVE_CONFIG_NAME].message('')

            self.refreshGUI()
            self.refreshExperimentSetup()

        def setDefaultThreshold(threshold):
            self.buttonLabels[threshold].message(str(self.newTrialSettings[threshold]))
            
        def loadConfig(e, configSelect = None):
            configFile = e.object.getItem(e.newSel) if e is not None else configSelect
            
            if configFile == "[NEW]":
                setDefault()
                return
                
            self.loadedConfig = True
            
            configPath = None
            
            self.buttonLabels[SAVE_CONFIG].message(t("Save Project"))
            
            for i in self.resourceLists[LOAD_CONFIG]:
                if os.path.basename(i) == configFile:
                    configPath = i
                    continue
                
            if not configPath == None:
                configFile = open(configPath, "r")
            else:
                print("Project load failed")
                return
                
            self.trialSettings = json.load(configFile)
            if "DEFAULT" in self.trialSettings:
                self.trialSettings.pop("DEFAULT")
                
            configFile.close()
            
            for trial in self.trialSettings:
                missingKeys = set(self.newTrialSettings.keys()) - set(self.trialSettings[trial].keys())
                
                for key in missingKeys:
                    self.trialSettings[trial][key] = self.newTrialSettings[key]
                    
                for item in self.trialSettings[trial][TRIAL_SETUP]:
                    if isinstance(self.trialSettings[trial][TRIAL_SETUP][item], list):
                        target = self.trialSettings[trial][TRIAL_SETUP][item][0]
                        visible = self.trialSettings[trial][TRIAL_SETUP][item][1]
                        grab = self.trialSettings[trial][TRIAL_SETUP][item][2]
                        
                        self.trialSettings[trial][TRIAL_SETUP][item] = {
                        TARGET: target,
                        VISIBLE: visible,
                        GRAB: grab
                        }
            
            if self.trialSettings[DEFAULT][MODE] == MODEL_3D:
                self.environmentFileList = []
                for file in os.listdir(self.trialSettings[DEFAULT][ENVIRONMENT_DIRECTORY]):
                    self.environmentFileList.append(file)
                    
                self.resourceLists[ENVIRONMENT] = self.environmentFileList
            
            else:
                self.mediaFileList = []
                for file in os.listdir(self.trialSettings[DEFAULT][ENVIRONMENT_DIRECTORY]):
                    self.mediaFileList.append(file)
                    
                self.resourceLists[MEDIA] = self.mediaFileList
            
            self.refreshGUI()
            
            self.refreshExperimentSetup()
                
            self.environmentNodes = None
            
        def environmentList(e):
            if self.trialSettings[DEFAULT][MODE] == MEDIA_360:
                self.loadedConfig = False
            
        def openInVizard():
            #os.startfile(self.path, "Edit")
            vizardPath =  os.path.join(viz.res.getVizardPath(), r"bin\Vizard.exe")
            subprocess.run([vizardPath, self.path])
            
        def openFolder():
            os.startfile(self.scriptDirectory)
            
        def fullBodyAvatarToggle(state):
            self.trialSettings[DEFAULT][FULL_BODY_TOGGLE] = state
            global VIZCONNECT_CONFIG_LIST, FULL_BODY_VIZCONNECT_CONFIG_LIST, DEFAULT_VIZCONNECT_CONFIG_LIST
            if state:
                # Turn off auto assign if it's checked
                if AUTO_ASSIGN in self.buttonLabels and self.buttonLabels[AUTO_ASSIGN].get():
                    self.buttonLabels[AUTO_ASSIGN].set(viz.OFF)
                    self.trialSettings[DEFAULT][AUTO_ASSIGN] = viz.OFF
                
                self.buttonLabels[AVATAR_LEFT_HAND].select(self.buttonLabels[AVATAR_LEFT_HAND].getItems().index("empty.osgb"))
                self.buttonLabels[AVATAR_RIGHT_HAND].select(self.buttonLabels[AVATAR_RIGHT_HAND].getItems().index("empty.osgb"))
                
                self.buttonLabels[AVATAR_HEAD].select(self.buttonLabels[AVATAR_HEAD].getItems().index("X_Empty.osgb"))
                
                self.trialSettings[DEFAULT][AVATAR_HEAD] = self.buttonLabels[AVATAR_HEAD].getItems()[self.buttonLabels[AVATAR_HEAD].getSelection()]
                self.trialSettings[DEFAULT][AVATAR_RIGHT_HAND] = self.buttonLabels[AVATAR_RIGHT_HAND].getItems()[self.buttonLabels[AVATAR_RIGHT_HAND].getSelection()]
                self.trialSettings[DEFAULT][AVATAR_LEFT_HAND] = self.buttonLabels[AVATAR_LEFT_HAND].getItems()[self.buttonLabels[AVATAR_LEFT_HAND].getSelection()]
                
                # Turn on Show Avatar when Full Body is enabled
                if SHOW_AVATAR in self.buttonLabels and self.buttonLabels[SHOW_AVATAR] is not None:
                    self.buttonLabels[SHOW_AVATAR].set(viz.ON)
                    self.trialSettings[DEFAULT][SHOW_AVATAR] = viz.ON
                
                # Hide regular head/hands preview avatars when full body is enabled
                if self.tempAvatar is not None:
                    self.tempAvatar.visible(viz.OFF)
                if self.tempLHand is not None:
                    self.tempLHand.visible(viz.OFF)
                if self.tempRHand is not None:
                    self.tempRHand.visible(viz.OFF)
                
                self.refreshGUI()
                
                loadFullBodyAvatar()

                self.buttonLabels[FULL_BODY_AVATARS].enable()
                self.buttonLabels[SEATED_MODE].enable()

                VIZCONNECT_CONFIG_LIST = FULL_BODY_VIZCONNECT_CONFIG_LIST.copy()
                                
            else:
                if self.tempFullBodyAvatar is not None:
                    self.tempFullBodyAvatar.remove()
                    self.tempFullBodyAvatar = None
                
                # Show regular head/hands preview avatars when full body is disabled
                if self.tempAvatar is not None:
                    self.tempAvatar.visible(viz.ON)
                if self.tempLHand is not None:
                    self.tempLHand.visible(viz.ON)
                if self.tempRHand is not None:
                    self.tempRHand.visible(viz.ON)
                
                self.trialSettings[DEFAULT][AVATAR_HEAD] = None
                self.trialSettings[DEFAULT][AVATAR_RIGHT_HAND] = None
                self.trialSettings[DEFAULT][AVATAR_LEFT_HAND] = None
                
                self.refreshGUI()
                VIZCONNECT_CONFIG_LIST  = DEFAULT_VIZCONNECT_CONFIG_LIST.copy()

                # Uncheck and disable Seated mode when Full Body is disabled
                self.buttonLabels[SEATED_MODE].set(viz.OFF)
                self.trialSettings[DEFAULT][SEATED_MODE] = viz.OFF
                self.buttonLabels[SEATED_MODE].disable()
                self.buttonLabels[FULL_BODY_AVATARS].disable()
            
            self.vizconnectConfigList = VIZCONNECT_CONFIG_LIST.copy()
            self.vizconnectConfigListArg  = VIZCONNECT_CONFIG_LIST.copy()
            
        def seatedModeToggle(state):
            self.trialSettings[DEFAULT][SEATED_MODE] = state

        def loadFullBodyAvatar(e=None):
            self.loadFullBodyAvatar()
            
        def randomizeTrials(state):
            for trial in self.trialSettings:
                self.trialSettings[trial][RANDOM_TRIALS] = state
                
        def dataSaving(state):
            for trial in self.trialSettings:
                self.trialSettings[trial][DATA_SAVING] = state
                
        def zoomInfoPanel(level):
            global SCALE_FACTOR
            
            SCALE_FACTOR += level
            
            if self.sceneInfoPanel is not None:
                self.sceneInfoPanel.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)
            
            if self.trialInfoPanel is not None:
                self.trialInfoPanel.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)
                
        def checkUpdates():
            try:
                with urllib.request.urlopen("https://help.worldviz.com/sightlab/sightlab_version.json") as url:
                    data = json.loads(url.read().decode())
                    latest_version = data["latest_version"]

                    current_version = VERSION_NUMBER
                    
                    if not latest_version == current_version:
                        # Prompt user to download the update
                        choice = vizinput.ask("New version available!\nCurrent: {}\nLatest: {}\n\nWould you like to download it now?".format(current_version, latest_version))
                        if choice:
                            webbrowser.open("https://sado1.s3.us-east-1.amazonaws.com/Storage/Sightlab2_Installer.exe")
                    else:
                        vizinput.message("You are using the latest version: {}".format(current_version))
            except Exception as e:
                vizinput.message("Could not check for updates: {}".format(e))
        
        def serverRefresh(serverName = None, firstLaunch = False, buttonPress = False, listChange = False):
            if serverName is None:
                serverName = self.buttonLabels[SERVER_NAME].getItems()[self.buttonLabels[SERVER_NAME].getSelection()]
                
            self.buttonLabels[SERVER_STATUS].uppicture(os.path.join(ICONS_PATH, "red_status.png"))
            
            if self.serverConnected or listChange or self.serverAttempted:
                if self.serverAttempted and not self.serverConnected:
                    self.serverAttempted = False
                    viznet.client.disconnect()
                    viznet.client = None
                    viznet.client = viznet._ClientInterface()
                     
                if self.serverConnected or listChange:
                    if self.serverConnected:
                        viznet.client.disconnect()
                        viznet.client = None
                        viznet.client = viznet._ClientInterface()
                        
                    self.serverConnected = False
                    self.serverAttempted = False
                    
                    viz.sendEvent(SERVER_DISCONNECTED)
                    return
                        
            while not viznet.client.connect(serverName,port_in=14951,port_out=14950):
                if firstLaunch:
                    self.serverConnected = False
                    viz.sendEvent(SERVER_DISCONNECTED)
                    return
                    
                if vizinput.ask("The server '" +serverName + "' isn't on the network, would you like to try another?"):
                    serverName = vizinput.input('Enter Server Name')
                    
                    if buttonPress:
                        serverList = self.buttonLabels[SERVER_NAME]
                        serverList.addItem(serverName)
                        self.trialSettings[DEFAULT][CLIENT_INFO][SERVER_LIST].insert(0, serverName)
                        serverList.select(serverList.getItems().index(serverName))
                        
                else:
                    self.serverConnected = False
                    viz.sendEvent(SERVER_DISCONNECTED)
                    return
                    
            self.serverAttempted = True
                    
#            pingStart = viz.tick()
            
#            while not self.serverConnected:
#                if viz.tick() - pingStart > 2.0:
#                    return
                                
#            self.serverConnected = True
            
            return serverName
            
        def onServerList(e):
            serverName = e.object.getItem(e.newSel)
            
            serverRefresh(listChange = True)
            
            if serverName == "[NEW]":
                serverName = vizinput.input("Enter the server name")
                
                serverList = self.buttonLabels[SERVER_NAME]
                serverList = self.buttonLabels[SERVER_NAME]
                if serverName =="":
                    if len(serverList.getItems())<=2:
                        serverList.select(0)
                    else:
                        serverList.select(1)
                    return
                serverList.addItem(serverName)
                
                self.buttonLabels[SERVER_ROW].setMargin(0)
                
                serverList.select(serverList.getItems().index(serverName))
                
                if SERVER_LIST in self.trialSettings[DEFAULT][CLIENT_INFO]:
                    self.trialSettings[DEFAULT][CLIENT_INFO][SERVER_LIST].insert(0, serverName)
                else:
                    self.trialSettings[DEFAULT][CLIENT_INFO][SERVER_LIST] = [serverName]
                
                if "-" in serverList.getItems():
                    serverList.removeItem(serverList.getItems().index("-"))
                
            viz.sendEvent(SERVER_DISCONNECTED)
            
        def autoAssign(state):
            if state:
                # Uncheck full body checkbox and disable full body avatars list
                if self.buttonLabels[FULL_BODY_TOGGLE].get():
                    self.buttonLabels[FULL_BODY_TOGGLE].set(viz.OFF)
                    fullBodyAvatarToggle(False)
                self.buttonLabels[FULL_BODY_AVATARS].disable()
                
                # Select GlowManAuto AFTER full body toggle handling (since fullBodyAvatarToggle resets AVATAR_HEAD)
                self.buttonLabels[AVATAR_HEAD].select(self.buttonLabels[AVATAR_HEAD].getItems().index("GlowManAuto.osgb"))
            else:
                if self.trialSettings[DEFAULT][AVATAR_HEAD] is not None:
                    if self.trialSettings[DEFAULT][AVATAR_HEAD] in self.buttonLabels[AVATAR_HEAD].getItems() and "GlowManAuto" not in self.trialSettings[DEFAULT][AVATAR_HEAD]:
                        self.buttonLabels[AVATAR_HEAD].select(self.buttonLabels[AVATAR_HEAD].getItems().index(self.trialSettings[DEFAULT][AVATAR_HEAD]))
                    else:
                        self.buttonLabels[AVATAR_HEAD].select(self.buttonLabels[AVATAR_HEAD].getItems().index("GlowManBlue.osgb"))
                
            self.trialSettings[DEFAULT][AUTO_ASSIGN] = state
            
            self.loadTempAvatar()
            
        def openAvatarFolder():
            os.startfile(AVATAR_HEAD_RESOURCE_PATH)
        
        def openFullBodyAvatarFolder():
            os.startfile(FULL_BODY_AVATAR_RESOURCE_PATH)
            
        def refreshAvatarList():
            self.avatarHeadFileList = []
            for file in os.listdir(AVATAR_HEAD_RESOURCE_PATH):
                self.avatarHeadFileList.append(file)
                    
            self.resourceLists[AVATAR_HEAD] = self.avatarHeadFileList
            
            modelFileTypes = ["osgb", "OSGB", "gltf", "fbx", "glb", "obj"]
        
            for file in self.avatarHeadFileList:
                _, ext = os.path.splitext(file)
                # Remove the leading dot for easier comparison
                ext = ext[1:]
                if ext not in modelFileTypes:
                    self.avatarHeadFileList.remove(file)
                    
            self.buttonLabels[AVATAR_HEAD].clearItems()
            self.buttonLabels[AVATAR_HEAD].addItems(self.resourceLists[AVATAR_HEAD])
            
            if "GlowManBlue.osgb" in self.resourceLists[AVATAR_HEAD]:
                 self.buttonLabels[AVATAR_HEAD].select(self.resourceLists[AVATAR_HEAD].index("GlowManBlue.osgb"))
                 
            self.loadTempAvatar()
            
        def updateText(e):
            if self.tempText is not None:
                if len(e.newText) < self.textCharLimit:
                    self.tempText.message(e.newText)
                else:
                    self.tempText.message(e.newText[:10]+"...")
    
        self.generateResourceLists()
        
        self.sceneInfoPanel = vizinfo.InfoPanel(t(GUI_TEXT), title = SIGHTLAB_VERSION, window=self.guiWindow, align = viz.ALIGN_LEFT_TOP, icon = True)
        
        row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_RIGHT_CENTER, background=False,border=False)
        
        self.buttonLabels[CHECK_FOR_UPDATES] = row.addItem(viz.addButtonLabel(t("Check for Updates")))
        
        self.buttonLabels[DOCUMENTATION] = row.addItem(viz.addButtonLabel(t("Documentation")))
        
        self.buttonLabels[ZOOM_OUT] = row.addItem(viz.addButton())
        self.buttonLabels[ZOOM_OUT].uppicture(os.path.join(ICONS_PATH,'zoom_out.png'))
        
        self.buttonLabels[ZOOM_IN] = row.addItem(viz.addButton())
        self.buttonLabels[ZOOM_IN].uppicture(os.path.join(ICONS_PATH,'zoom_in.png'))
        
        self.sceneInfoPanel.addItem(row, align=viz.ALIGN_RIGHT_CENTER)
        
        self.sceneInfoPanel.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)
        
        if self.clientMode:
            self.sceneInfoPanel.addSection(t("Server"))
            row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False,border=False)
            
            serverNameList = ["[NEW]"]
            if len(self.trialSettings[DEFAULT][CLIENT_INFO][SERVER_LIST]) > 0:
                serverNameList.extend(self.trialSettings[DEFAULT][CLIENT_INFO][SERVER_LIST])
            else:
                serverNameList.insert(0, "-")
            
            self.buttonLabels[SERVER_NAME] = row.addItem(viz.addDropList())
            self.buttonLabels[SERVER_NAME].addItems(serverNameList)
            
            if self.trialSettings[DEFAULT][CLIENT_INFO][SERVER_NAME] in serverNameList:
                self.buttonLabels[SERVER_NAME].select(serverNameList.index(self.trialSettings[DEFAULT][CLIENT_INFO][SERVER_NAME]))
                
            self.buttonLabels[SERVER_NAME].setLength(1)
            self.buttonLabels[SERVER_STATUS] = row.addItem(viz.addButton())
            self.buttonLabels[SERVER_STATUS].uppicture(os.path.join(ICONS_PATH, 'red_status.png'))
            self.buttonLabels[SERVER_REFRESH] = row.addItem(viz.addButtonLabel(t("Connect")))
            #self.buttonLabels[SERVER_REFRESH].uppicture(os.path.join(ICONS_PATH, 'refresh_icon.png'))
            
            self.buttonLabels[SERVER_ROW] = self.sceneInfoPanel.addLabelItem(t("Name"), row)
            self.buttonLabels[SERVER_ROW].setMargin(0)
            
        if not self.clientMode:
            self.sceneInfoPanel.addSeparator()

            self.buttonLabels[LOAD_CONFIG] = self.sceneInfoPanel.addLabelItem(t('Load Project File'), viz.addDropList())
            
            baseNameList = []
            for config in self.resourceLists[LOAD_CONFIG]: 
                if self.clientMode and "client" not in config:
                    continue
                if self.serverMode and "server" not in config and not "[NEW]" == config:
                    continue
                if not self.clientMode and not self.serverMode and ("client" in config or "server" in config):
                    continue
                    
                baseNameList.append(os.path.basename(config))
                
            self.buttonLabels[LOAD_CONFIG].addItems(baseNameList)
            
            row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False,border=False)
            row.setMargin(0)
            
            self.buttonLabels[SAVE_CONFIG_NAME] = row.addItem(viz.addTextbox())
            self.buttonLabels[SAVE_CONFIG] = row.addItem(viz.addButtonLabel(t("Save Project")))
            
            self.sceneInfoPanel.addLabelItem(t("Project File Name"), row)
        
            row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False,border=False)
            row.setMargin(0)
            
            self.buttonLabels[OPEN_IN_VIZARD] = viz.addButtonLabel('Edit ' + os.path.basename(self.path))
            row.addItem(self.buttonLabels[OPEN_IN_VIZARD])
            
            self.buttonLabels[OPEN_FOLDER] = viz.addButton()
            self.buttonLabels[OPEN_FOLDER].uppicture(os.path.join(ICONS_PATH, 'folder_icon.png'))
            
            row.addItem(self.buttonLabels[OPEN_FOLDER])
            
            self.sceneInfoPanel.addLabelItem('', row)
            
            self.sceneInfoPanel.addSection(t(f'{TRIAL_OR_SCENE} Setup') if TRIAL_OR_SCENE == "Scene" else t("Experiment Setup"))
            
            #self.buttonLabels[NUMBER_OF_TRIALS] = self.sceneInfoPanel.addLabelItem(f"{TRIAL_OR_SCENE} Count" , viz.addText(""))
                
            #self.buttonLabels[MODE] = self.sceneInfoPanel.addLabelItem("Mode" , viz.addText(""))

            #self.buttonLabels[ENVIRONMENT] = self.sceneInfoPanel.addLabelItem("Environment" , viz.addText(""))
                
            #self.buttonLabels[ENVIRONMENT_DIRECTORY] = self.sceneInfoPanel.addLabelItem("Directory" , viz.addText(""))
            
            self.buttonLabels[RANDOM_CHECKBOX] = self.sceneInfoPanel.addLabelItem(t("Randomize"), viz.addCheckbox())
            
            row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER,background=False,border=False)
            row.setMargin(0)
            
            self.buttonLabels[PER_TRIAL] = row.addItem(viz.addRadioButton('data_save'))
            row.addItem(viz.addText(t(f"Per {TRIAL_OR_SCENE}") + "      "))

            self.buttonLabels[COMBINED] = row.addItem(viz.addRadioButton('data_save'))
            row.addItem(viz.addText(t("Combined")))
            
            self.sceneInfoPanel.addLabelItem(t("Data Files"), row)
            
            textRow = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, background=False, border=False)
            textRow.setMargin(0)
            self.buttonLabels[START_EXPERIMENT_TEXT] = textRow.addItem(viz.addButtonLabel(t("Start Text")))
            self.buttonLabels[START_EXPERIMENT_TEXT].setLength(0.5)
            self.buttonLabels[END_EXPERIMENT_TEXT] = textRow.addItem(viz.addButtonLabel(t("End Text")))
            self.buttonLabels[END_EXPERIMENT_TEXT].setLength(0.5)
            self.sceneInfoPanel.addItem(textRow)
            
            # self.buttonLabels[TRIAL_SETUP] = self.sceneInfoPanel.addLabelItem('' , viz.addButtonLabel('Modify'))
            # self.buttonLabels[TRIAL_SETUP].setLength(0.5)
            
            self.trialInfo()
            self.refreshExperimentSetup()
        
        if not self.serverMode:
            self.sceneInfoPanel.addSection(t('Avatar'))
            
            row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False,border=False)
            row.setMargin(0)
            
            self.buttonLabels[FULL_BODY_TOGGLE] = row.addItem(viz.addCheckbox())
            self.buttonLabels[FULL_BODY_AVATARS] = row.addItem(viz.addDropList())
            self.buttonLabels[FULL_BODY_AVATARS].addItems(self.resourceLists[FULL_BODY_AVATARS])
            self.buttonLabels[FULL_BODY_AVATARS].disable()
            
            if self.clientMode:
                self.buttonLabels[UPLOAD_FULL_BODY_AVATAR] = row.addItem(viz.addButton())
                self.buttonLabels[UPLOAD_FULL_BODY_AVATAR].uppicture(os.path.join(ICONS_PATH, 'folder_icon.png'))
            
            self.sceneInfoPanel.addLabelItem(t('Full Body'), row)
            
            row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False,border=False)
            row.setMargin(0)
            
            self.buttonLabels[SEATED_MODE] = row.addItem(viz.addCheckbox())
            self.buttonLabels[SEATED_MODE].disable()

            self.sceneInfoPanel.addLabelItem(t('  Seated'), row)
            
            row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False,border=False)
            row.setMargin(0)
            
            self.buttonLabels[AVATAR_HEAD] = row.addItem(viz.addDropList())
            self.buttonLabels[AVATAR_HEAD].addItems(self.resourceLists[AVATAR_HEAD])
            
            if self.clientMode:
                self.buttonLabels[UPLOAD_AVATAR] = row.addItem(viz.addButton())
                self.buttonLabels[UPLOAD_AVATAR].uppicture(os.path.join(ICONS_PATH, 'folder_icon.png'))
                
                self.buttonLabels[REFRESH_AVATARS] = row.addItem(viz.addButton())
                self.buttonLabels[REFRESH_AVATARS].uppicture(os.path.join(ICONS_PATH, 'refresh_icon.png'))
                
                row.addItem(viz.addText(t('Auto Assign')))
                self.buttonLabels[AUTO_ASSIGN] =  row.addItem(viz.addCheckbox())
                self.buttonLabels[AUTO_ASSIGN].set(0)
#                self.trialSettings[DEFAULT][AUTO_ASSIGN] = viz.OFF
                
            else:
                row.addItem(viz.addText(t('Show')))
                self.buttonLabels[SHOW_AVATAR] = row.addItem(viz.addCheckbox())
                self.buttonLabels[SHOW_AVATAR].set(0)
                
            self.sceneInfoPanel.addLabelItem(t('Head'), row)
                
            row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False,border=False)
            row.setMargin(0)
            
            self.buttonLabels[AVATAR_LEFT_HAND] = row.addItem(viz.addDropList(), align = viz.ALIGN_LEFT_CENTER)
            self.buttonLabels[AVATAR_LEFT_HAND].addItems(self.resourceLists[AVATAR_LEFT_HAND])
            
            row.addItem(viz.addText(t("L")))
            
            self.sceneInfoPanel.addLabelItem(t("Hands"), row)
            
            row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False,border=False)
            row.setMargin(0)
            
            self.buttonLabels[AVATAR_RIGHT_HAND] = row.addItem(viz.addDropList(), align = viz.ALIGN_LEFT_CENTER)
            self.buttonLabels[AVATAR_RIGHT_HAND].addItems(self.resourceLists[AVATAR_RIGHT_HAND])
            
            row.addItem(viz.addText(t("R")))
            
            self.sceneInfoPanel.addLabelItem("", row)
            

            if not self.clientMode:
                self.buttonLabels[GAZE_POINT] = self.sceneInfoPanel.addLabelItem(t('Gaze Point'), viz.addDropList())
                self.buttonLabels[GAZE_POINT].addItems(self.resourceLists[GAZE_POINT])
                
                try:
                    self.gazePointObject = vizfx.addChild(os.path.join(GAZE_POINT_RESOURCE_PATH, self.resourceLists[GAZE_POINT[0]]))
                except:
                    self.gazePointObject = vizfx.addChild(DEFAULT_GAZE_POINT_PATH)
            else:
                self.gazePointObject = vizfx.addChild(DEFAULT_GAZE_POINT_PATH)
                
            self.gazePointObject.visible(viz.OFF)
                
            self.gazePointObject.disable(viz.INTERSECTION)
            
            self.gazePointObject.renderToMain = False
            self.gazePointObject.renderOnlyToWindows([self.gazePointWindow])
            
            def loadGazePointObject(e):
                if self.gazePointObject is not None:
                    self.gazePointObject.remove()
                
                self.gazePointObject = vizfx.addChild(os.path.join(GAZE_POINT_RESOURCE_PATH, e.object.getItem(e.newSel)))
                self.gazePointObject.disable(viz.INTERSECTION)
                
            if not self.clientMode:
                vizact.onlist(self.buttonLabels[GAZE_POINT], loadGazePointObject)
        else:
            self.gazePointObject = vizfx.addChild(DEFAULT_GAZE_POINT_PATH)
            self.gazePointObject.visible(viz.OFF)
            self.gazePointObject.disable(viz.INTERSECTION)
            
        if not self.clientMode:
            self.sceneInfoPanel.addSection(t('Thresholds'))
            
            row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False,border=False)
            
            row.setMargin(0)
                    
            self.buttonLabels[DWELL_TIME] = viz.addTextbox()
            self.buttonLabels[DWELL_TIME].message(str(self.newTrialSettings[DWELL_TIME]))
            self.buttonLabels[DWELL_TIME].setLength(0.5)
            
            row.addItem(self.buttonLabels[DWELL_TIME])
            
            row.addItem(viz.addText(t("secs    ")))
            
            self.buttonLabels[DEFAULT_DWELL] = viz.addButton()
            self.buttonLabels[DEFAULT_DWELL].uppicture(os.path.join(ICONS_PATH,'revert_icon.png'))
            row.addItem(self.buttonLabels[DEFAULT_DWELL])
            
            self.sceneInfoPanel.addLabelItem(t('Dwell Time'), row)
            
            row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False,border=False)
            
            row.setMargin(0)
                    
            self.buttonLabels[DURATION_THRESHOLD] = viz.addTextbox()
            self.buttonLabels[DURATION_THRESHOLD].message(str(self.newTrialSettings[DURATION_THRESHOLD]))
            self.buttonLabels[DURATION_THRESHOLD].setLength(0.5)
            
            row.addItem(self.buttonLabels[DURATION_THRESHOLD])
            
            row.addItem(viz.addText(t("secs    ")))
            
            self.buttonLabels[DEFAULT_DURATION] = viz.addButton()
            self.buttonLabels[DEFAULT_DURATION].uppicture(os.path.join(ICONS_PATH,'revert_icon.png'))
            row.addItem(self.buttonLabels[DEFAULT_DURATION])
            
            self.sceneInfoPanel.addLabelItem(t('Fixation Duration'), row)
            
            row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False,border=False)
            
            row.setMargin(0)
                    
            self.buttonLabels[DISPERSION_THRESHOLD] = viz.addTextbox()
            self.buttonLabels[DISPERSION_THRESHOLD].message(str(self.newTrialSettings[DISPERSION_THRESHOLD]))
            self.buttonLabels[DISPERSION_THRESHOLD].setLength(0.5)
            
            row.addItem(self.buttonLabels[DISPERSION_THRESHOLD])
            
            row.addItem(viz.addText(t("degrees    ")))
            
            self.buttonLabels[DEFAULT_DISPERSION] = viz.addButton()
            self.buttonLabels[DEFAULT_DISPERSION].uppicture(os.path.join(ICONS_PATH,'revert_icon.png'))
            row.addItem(self.buttonLabels[DEFAULT_DISPERSION])
            
            self.sceneInfoPanel.addLabelItem(t('Dispersion Angle'), row)
            
            row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False,border=False)
            
            row.setMargin(0)
                    
            self.buttonLabels[NOISE_REDUCTION] = viz.addTextbox()
            self.buttonLabels[NOISE_REDUCTION].message(str(self.newTrialSettings[NOISE_REDUCTION]))
            self.buttonLabels[NOISE_REDUCTION].setLength(0.5)
            
            row.addItem(self.buttonLabels[NOISE_REDUCTION])
            
            row.addItem(viz.addText(t("frames    ")))
            
            self.buttonLabels[DEFAULT_NOISE] = viz.addButton()
            self.buttonLabels[DEFAULT_NOISE].uppicture(os.path.join(ICONS_PATH,'revert_icon.png'))
            row.addItem(self.buttonLabels[DEFAULT_NOISE])
            
            self.sceneInfoPanel.addLabelItem(t('Noise Reduction'), row)
            
            self.sceneInfoPanel.addSection(t('Options'))
            
            optionsRow = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, background=False, border=False)
            optionsRow.setMargin(0)
            self.buttonLabels[SCREEN_RECORD] = optionsRow.addItem(viz.addCheckbox())
            optionsRow.addItem(viz.addText(t('      Barchart') + '  '))
            self.buttonLabels[BARCHART] = optionsRow.addItem(viz.addCheckbox())
            self.sceneInfoPanel.addLabelItem(t('Screen Record'), optionsRow)
            
            self.buttonLabels[BIOPAC] = self.sceneInfoPanel.addLabelItem(t('BIOPAC Markers'), viz.addCheckbox())
            
        if self.serverMode:
            if self.demoMode:
                self.buttonLabels[SESSION_ID] = self.sceneInfoPanel.addLabelItem(t('Session ID'),viz.addText("SIGHTLAB_DEMO"))
            else:
                self.buttonLabels[SESSION_ID] = self.sceneInfoPanel.addLabelItem(t('Session ID'),viz.addTextbox())
                
            #self.buttonLabels[SHOW_NAME] = self.sceneInfoPanel.addLabelItem('Show Tags', viz.addCheckbox())
            
        if self.clientMode:
            self.sceneInfoPanel.addSection(t('Info'))
            self.buttonLabels[FIRST_NAME] = self.sceneInfoPanel.addLabelItem(t('Name'), viz.addTextbox())
            self.buttonLabels[FIRST_NAME].message(self.trialSettings[DEFAULT][CLIENT_INFO][FIRST_NAME])
            
            self.buttonLabels[SHOW_NAME] = self.sceneInfoPanel.addLabelItem(t('Show'), viz.addCheckbox())
            self.buttonLabels[SHOW_NAME].set(self.trialSettings[DEFAULT][CLIENT_INFO][SHOW_NAME])
            
            self.sceneInfoPanel.addSection(t('Start Point'))
            self.buttonLabels[SSP_SUFFIX] = self.sceneInfoPanel.addLabelItem(t('Suffix'), viz.addTextbox())
            
            if hasattr(self, 'suffix') and self.suffix is not None:
                self.trialSettings[DEFAULT][CLIENT_INFO][SSP_SUFFIX] = self.suffix
                
            #print("suffix: ", self.trialSettings[DEFAULT][CLIENT_INFO][SSP_SUFFIX])
            if SSP_SUFFIX in self.trialSettings[DEFAULT][CLIENT_INFO]:
                self.buttonLabels[SSP_SUFFIX].message(self.trialSettings[DEFAULT][CLIENT_INFO][SSP_SUFFIX])
            else:
                self.trialSettings[DEFAULT][CLIENT_INFO][SSP_SUFFIX] = "1"
                self.buttonLabels[SSP_SUFFIX].message(self.trialSettings[DEFAULT][CLIENT_INFO][SSP_SUFFIX])
            
            self.buttonLabels[AUTO_ASSIGN].set(self.trialSettings[DEFAULT][AUTO_ASSIGN])
            
        self.loadTempAvatar()
        
        self.sceneInfoPanel.addSeparator()
        
        # Add Mumble launcher button to bottom of panel for client/server modes
        if self.clientMode or self.serverMode:
            row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False,border=False)
            if self.clientMode:
                self.buttonLabels[MUMBLE_LAUNCHER] = row.addItem(viz.addButtonLabel(t('Mumble Client')))
            else:
                self.buttonLabels[MUMBLE_LAUNCHER] = row.addItem(viz.addButtonLabel(t('Mumble Server')))
            self.sceneInfoPanel.addItem(row, align=viz.ALIGN_LEFT_CENTER)

#        self.continuePanel = vizdlg.Panel(window = self.guiWindow, background=False,border=False, margin = 0)
#        self.buttonLabels[CONTINUE] = self.sceneInfoPanel.addItem(viz.addButtonLabel('Continue'),align=viz.ALIGN_RIGHT_CENTER)
        self.buttonLabels[CONTINUE] = viz.addButtonLabel(t('Continue'))
#        self.buttonLabels[CONTINUE].setScale()
        self.buttonLabels[CONTINUE].setLength(0.5)
        _continueAlign  = vizdlg.ALIGN_LEFT_BOTTOM  if CONTINUE_ON_LEFT else vizdlg.ALIGN_RIGHT_BOTTOM
        _continueAnchor = viz.LeftBottom             if CONTINUE_ON_LEFT else viz.RightBottom
        _continueOffset = (50, 50, 0)               if CONTINUE_ON_LEFT else (-50, 50, 0)
        self.continuePanel = vizdlg.Panel(window = self.guiWindow, layout=vizdlg.LAYOUT_HORZ_BOTTOM, align=_continueAlign, background=False,border=False, margin = 0)
        self.continuePanel.addItem(self.buttonLabels[CONTINUE])
        self._continueBaseScale = 1.25
        self.continuePanel.setScale(self._continueBaseScale * SCALE_FACTOR, self._continueBaseScale * SCALE_FACTOR)

        self._continueBaseOffset = _continueOffset
        self.continueLink = viz.link(_continueAnchor, self.continuePanel, offset=(self._continueBaseOffset[0] * SCALE_FACTOR, self._continueBaseOffset[1] * SCALE_FACTOR, 0))
        
        self.refreshGUI()
        
        if not self.serverMode:
            vizact.onlist(self.buttonLabels[AVATAR_HEAD], self.loadTempAvatar)
            vizact.onlist(self.buttonLabels[AVATAR_LEFT_HAND], self.loadTempAvatar)
            vizact.onlist(self.buttonLabels[AVATAR_RIGHT_HAND], self.loadTempAvatar)
            
            vizact.onbuttondown(self.buttonLabels[FULL_BODY_TOGGLE], fullBodyAvatarToggle, True)
            vizact.onbuttonup(self.buttonLabels[FULL_BODY_TOGGLE], fullBodyAvatarToggle, False)
            
            vizact.onbuttondown(self.buttonLabels[SEATED_MODE], seatedModeToggle, True)
            vizact.onbuttonup(self.buttonLabels[SEATED_MODE], seatedModeToggle, False)
            
            vizact.onlist(self.buttonLabels[FULL_BODY_AVATARS], loadFullBodyAvatar)
            
            if not self.clientMode:
                def showAvatar(state):
                    self.tempAvatar.visible(state)
                    self.tempLHand.visible(state)
                    self.tempRHand.visible(state)
                    if self.tempFullBodyAvatar is not None:
                        self.tempFullBodyAvatar.visible(state)
                    
                vizact.onbuttondown(self.buttonLabels[SHOW_AVATAR], showAvatar, viz.ON)
                vizact.onbuttonup(self.buttonLabels[SHOW_AVATAR], showAvatar, viz.OFF)
            
        if not self.clientMode:
            vizact.onbuttonup(self.buttonLabels[OPEN_IN_VIZARD], openInVizard)
            vizact.onbuttonup(self.buttonLabels[OPEN_FOLDER], openFolder)
            vizact.onbuttonup(self.buttonLabels[SAVE_CONFIG], saveConfig, self.buttonLabels[SAVE_CONFIG_NAME])
            #vizact.onbuttonup(self.buttonLabels[TRIAL_SETUP], self.trialInfo)
            vizact.onbuttonup(self.buttonLabels[RANDOM_CHECKBOX], randomizeTrials, False)
            vizact.onbuttondown(self.buttonLabels[RANDOM_CHECKBOX], randomizeTrials, True) 
            vizact.onbuttondown(self.buttonLabels[PER_TRIAL], dataSaving, PER_TRIAL)
            vizact.onbuttondown(self.buttonLabels[COMBINED], dataSaving, COMBINED)
            
            def onStartTextButton():
                text = vizinput.input(t('Enter Start Experiment Text'), self.trialSettings[DEFAULT].get(START_EXPERIMENT_TEXT, ''))
                if text is not None:
                    self.trialSettings[DEFAULT][START_EXPERIMENT_TEXT] = text
            
            def onEndTextButton():
                text = vizinput.input(t('Enter End Experiment Text'), self.trialSettings[DEFAULT].get(END_EXPERIMENT_TEXT, ''))
                if text is not None:
                    self.trialSettings[DEFAULT][END_EXPERIMENT_TEXT] = text
            
            vizact.onbuttonup(self.buttonLabels[START_EXPERIMENT_TEXT], onStartTextButton)
            vizact.onbuttonup(self.buttonLabels[END_EXPERIMENT_TEXT], onEndTextButton)
            vizact.onbuttonup(self.buttonLabels[DEFAULT_DWELL], setDefaultThreshold, DWELL_TIME)
            vizact.onbuttonup(self.buttonLabels[DEFAULT_DISPERSION], setDefaultThreshold, DISPERSION_THRESHOLD)
            vizact.onbuttonup(self.buttonLabels[DEFAULT_DURATION], setDefaultThreshold, DURATION_THRESHOLD)
            vizact.onbuttonup(self.buttonLabels[DEFAULT_NOISE], setDefaultThreshold, NOISE_REDUCTION)
            vizact.onlist(self.buttonLabels[LOAD_CONFIG], loadConfig)
            
        else:
            vizact.onbuttondown(self.buttonLabels[AUTO_ASSIGN], autoAssign, True)
            vizact.onbuttonup(self.buttonLabels[AUTO_ASSIGN], autoAssign, False)
            
            if self.buttonLabels[AUTO_ASSIGN].get():
                autoAssign(True)
            
            vizact.onbuttonup(self.buttonLabels[UPLOAD_AVATAR], openAvatarFolder)
            vizact.onbuttonup(self.buttonLabels[UPLOAD_FULL_BODY_AVATAR], openFullBodyAvatarFolder)
            vizact.onbuttonup(self.buttonLabels[REFRESH_AVATARS], refreshAvatarList)
            
            vizact.ontextbox(self.buttonLabels[FIRST_NAME], updateText)
            vizact.onbuttonup(self.buttonLabels[SHOW_NAME], self.tempText.visible, viz.OFF)
            vizact.onbuttondown(self.buttonLabels[SHOW_NAME], self.tempText.visible, viz.ON)
            
            vizact.onlist(self.buttonLabels[SERVER_NAME], onServerList)
            vizact.onbuttonup(self.buttonLabels[SERVER_REFRESH], serverRefresh, buttonPress = True)
            
#            if self.buttonLabels[SERVER_NAME].getItems()[self.buttonLabels[SERVER_NAME].getSelection()] not in ["[NEW]", " "]:
#                serverRefresh(self.buttonLabels[SERVER_NAME].getItems()[self.buttonLabels[SERVER_NAME].getSelection()], True)

        vizact.onbuttonup(self.buttonLabels[ZOOM_IN], zoomInfoPanel, 0.1)
        vizact.onbuttonup(self.buttonLabels[ZOOM_OUT], zoomInfoPanel, -0.1)
        vizact.onbuttondown(self.buttonLabels[DOCUMENTATION], webbrowser.open, "https://help.worldviz.com/sightlab/")
        vizact.onbuttondown(self.buttonLabels[CHECK_FOR_UPDATES], checkUpdates)
        
        # Add Mumble launcher button callbacks
        if self.clientMode:
            vizact.onbuttondown(self.buttonLabels[MUMBLE_LAUNCHER], self.launch_tool, r"C:\Program Files\Mumble\client\mumble.exe", "Mumble Client")
        elif self.serverMode:
            vizact.onbuttondown(self.buttonLabels[MUMBLE_LAUNCHER], self.launch_tool, r"C:\Program Files\Mumble\server\mumble-server.exe", "Mumble Server")
        
        if not self.clientMode:
            if self.configSelect is not None:
                self.buttonLabels[LOAD_CONFIG].select(self.buttonLabels[LOAD_CONFIG].getItems().index(self.configSelect))
                loadConfig(None, self.configSelect)
                print("config selected")
            else:
                if RECENT_CONFIG in self.trialSettings[DEFAULT] and self.trialSettings[DEFAULT][RECENT_CONFIG] in self.buttonLabels[LOAD_CONFIG].getItems():
                    self.buttonLabels[LOAD_CONFIG].select(self.buttonLabels[LOAD_CONFIG].getItems().index(self.trialSettings[DEFAULT][RECENT_CONFIG]))
                    self.trialSettings[DEFAULT].pop(RECENT_CONFIG)
    
        while True:
            yield viztask.waitButtonUp(self.buttonLabels[CONTINUE])
            
            if not self.clientMode:
#                if self.buttonLabels[ENVIRONMENT].getMessage() == "NONE":
#                    vizinput.message("No environment selected, click Modify")
#                    self.buttonLabels[TRIAL_SETUP].setFocus(viz.ON)
#                else:
                if self.serverMode and self.transportToggleAction is not None:
                    self.transportToggleAction.setEnabled(viz.ON)
                break
            else:
                if self.serverConnected:
                    break
                    
                vizinput.message("Server not connected")
        
        
        self.completeSceneInfo()
        
        viztask.returnValue(self.trialSettings[DEFAULT][MODE])
        
    def completeSceneInfo(self):
        """
        Finalize and save GUI configuration settings.
        
        Called when user clicks Continue button. Gathers all settings from GUI controls,
        saves trial information, and prepares configuration for experiment execution.
        Handles server-specific setup if in server mode.
        
        Returns:
            None. Updates self.trialSettings with final configuration
        """
        self.setSettings() 
        self.trialInfo(getSettings=True)
        
        if self.serverMode:
            if self.demoMode:
                self.participantData[ID] = "SIGHTLAB_DEMO"
            else:
                self.participantData[ID] = self.buttonLabels[SESSION_ID].get()
            
        if self.clientMode:
            self.trialSettings[DEFAULT][CLIENT_INFO] = {}
            self.trialSettings[DEFAULT][CLIENT_INFO][FIRST_NAME] = self.buttonLabels[FIRST_NAME].get()
            self.trialSettings[DEFAULT][CLIENT_INFO][SHOW_NAME] = self.buttonLabels[SHOW_NAME].get()
            self.trialSettings[DEFAULT][CLIENT_INFO][SSP_SUFFIX] = self.buttonLabels[SSP_SUFFIX].get()
            self.trialSettings[DEFAULT][CLIENT_INFO][SERVER_NAME] = self.buttonLabels[SERVER_NAME].getItems()[self.buttonLabels[SERVER_NAME].getSelection()]
            
            serverList = self.buttonLabels[SERVER_NAME].getItems()
                
            for item in ["[NEW]", "-"]:
                if item in serverList:
                    serverList.remove(item)
                
            self.trialSettings[DEFAULT][CLIENT_INFO][SERVER_LIST] = serverList
            
        global RECENT_CONFIG_PATH, RECENT_CONFIG_FILE
        RECENT_CONFIG_PATH = os.path.join(self.configDirectory, RECENT_CONFIG_FILE)
        
        if not self.clientMode:
            currentConfig = self.buttonLabels[LOAD_CONFIG].getItems()[self.buttonLabels[LOAD_CONFIG].getSelection()]
        else:
            currentConfig = RECENT_CONFIG_CLIENT_FILE
            
        recentConfig = deepcopy(self.trialSettings)
        
        if currentConfig == "[NEW]":
            currentConfig = RECENT_CONFIG_FILE
            
        recentConfig[DEFAULT][RECENT_CONFIG] = currentConfig
        
        try:
            configFile = open(RECENT_CONFIG_PATH, "w")
            json.dump(recentConfig, configFile, indent = 4)
            configFile.close()
            
            if currentConfig not in [RECENT_CONFIG_FILE] :
                currentConfigFile = open(os.path.join(self.configDirectory, currentConfig), "w")
                json.dump(self.trialSettings, currentConfigFile, indent = 4)
                currentConfigFile.close()
                
        except:
            print("Project file may be open in another application. Close the file and retry")
#            viz.quit()
        
#        if currentConfig not in [RECENT_CONFIG_FILE] :
#            currentConfigFile = open(os.path.join(self.configDirectory, currentConfig), "w")
#            json.dump(self.trialSettings, currentConfigFile, indent = 4)
#            currentConfigFile.close()
                                
        if self.tempEnvironment is not None:
            self.tempEnvironment.remove()
            self.tempEnvironment = None
            
        for roi in self.regionsOfInterest:
            self.regionsOfInterest[roi].remove()
            
        if self.gazePointObject is not None:
            self.gazePointObject.remove()
            self.gazePointObject = None
                
        self.regionsOfInterest = {}
        
        if SHIFT_LOCK_TOGGLE:
            if not self.modifyFlag:
                self.trialInfo(button = False)
        else:
            if self.transportToggleAction is not None:
                self.transportToggleAction.remove()
                self.transportToggleAction = None
        
        if not self.clientMode:
            self.trialInfoPanel.remove()
            
        self.sceneInfoPanel.remove()
        self.continuePanel.remove()
        
    def disableSceneInfo(self):
        """
        Visually disable the scene info GUI panel.
        
        Reduces panel opacity and hides all control elements to indicate disabled state.
        Used during operations where GUI interaction should be prevented.
        
        Returns:
            None. Updates GUI panel visibility
        """
        self.sceneInfoPanel.alpha(0.5)
        
        for label in self.buttonLabels:
            self.buttonLabels[label].visible(viz.OFF)
    
    def enableSceneInfo(self):
        """
        Re-enable the scene info GUI panel.
        
        Restores panel opacity and shows all control elements.
        
        Returns:
            None. Updates GUI panel visibility
        """
        self.sceneInfoPanel.alpha(0.949999988079071)
        for label in self.buttonLabels:
            self.buttonLabels[label].visible(viz.ON)
            
    def refreshExperimentSetup(self):
        """
        Update experiment setup display with current trial configuration.
        
        Refreshes the summary display showing number of trials, trial labels,
        and other high-level experiment parameters. Updates the GUI panel to
        reflect any changes made to trial settings.
        
        Returns:
            None. Updates GUI display elements
        """
        #trialCount = ""
        #self.currTrial = '1'
        
        if str(self.trialSettings[self.currTrial][NUMBER_OF_TRIALS]) == "-1":
            trialCount = "Infinite"
        else:
            trialCount = str(self.trialSettings[self.currTrial][NUMBER_OF_TRIALS])
            
#        self.buttonLabels[NUMBER_OF_TRIALS].message(trialCount)
            
        modeName = ""
        if self.trialSettings[self.currTrial][MODE] == MODEL_3D:
            modeName = "3D Models"
        else:
            modeName = "360 Media"
            
#        self.buttonLabels[MODE].message(modeName)
        
#        if self.transportToggleAction is not None:
#            self.transportToggleAction.setEnabled(viz.OFF)
        
        environmentName = "NONE"
        if self.trialSettings[self.currTrial][ENVIRONMENT] is None:
            if len(self.resourceLists[ENVIRONMENT]) > 0:
                environmentName = self.resourceLists[ENVIRONMENT][0]
                self.trialSettings[self.currTrial][ENVIRONMENT] = os.path.basename(self.resourceLists[ENVIRONMENT][0])
            else:
                environmentName = "NONE"
        else:
            environmentName = self.trialSettings[self.currTrial][ENVIRONMENT]
            
        #self.buttonLabels[ENVIRONMENT].message(os.path.basename(environmentName))
            
        full_path = self.trialSettings[self.currTrial][ENVIRONMENT_DIRECTORY]
                
        if os.path.normpath(full_path) in [SIGHTLAB_ENVIRONMENT_RESOURCES, SIGHTLAB_MEDIA_RESOURCES]:
            directoryName = "BUILT-IN"
        else:
            directoryName = self.normalizePath(full_path)
            
#        self.buttonLabels[ENVIRONMENT_DIRECTORY].message(directoryName)
        
        self.buttonLabels[RANDOM_CHECKBOX].set(self.trialSettings[self.currTrial][RANDOM_TRIALS])
        
        self.buttonLabels[SAVE_CONFIG].message(t("Save Project"))
        
        self.loadTempEnvironment(default = True)
                
        if not environmentName == "NONE" and self.trialSettings[self.currTrial][MODE] == MODEL_3D:
            self.loadTempEnvironment(path = os.path.join(self.scriptDirectory, self.trialSettings[self.currTrial][ENVIRONMENT_DIRECTORY], self.trialSettings[self.currTrial][ENVIRONMENT]))
        elif self.trialSettings[self.currTrial][MODE] == MEDIA_360:
            self.loadTempEnvironment()
            
    def generatePages(self, guiList, pageLimit = 25):
        """
        Split GUI element list into paginated pages.
        
        When the number of GUI elements (e.g., trials, objects) exceeds the page limit,
        distributes them across multiple pages for better organization and performance.
        
        Args:
            guiList (list): List of GUI elements to paginate
            pageLimit (int, optional): Maximum elements per page. Default 25
            
        Returns:
            dict: Dictionary mapping page numbers to element sublists
        """
        pageDict = {}
        pageCount = 1
        if len(guiList) > pageLimit:
            pageCount = len(guiList)//pageLimit + 1
            if len(guiList)%pageLimit == 0:
                pageCount -= 1
                
            for page in range(pageCount):
                start_index = page * pageLimit
                end_index = min(start_index + pageLimit, len(guiList))
                pageDict[page + 1] = guiList[start_index:end_index]
                
                if page + 1 == 1:
                    pageDict[page + 1].append("...")
                elif page + 1 == pageCount:
                    pageDict[page + 1].insert(0, "...")
                else:
                    pageDict[page + 1].append("...")
                    pageDict[page + 1].insert(0, "...")
        else:
            pageDict[1] = guiList
            
        return pageDict
            
    def trialInfo(self, button = True, getSettings = None):
        """
        Create trial-specific configuration interface.
        
        Generates a detailed configuration panel for individual trial settings including:
        - Environment/media file selection (drag-and-drop support)
        - Object placement and visibility
        - Regions of interest (ROI) setup
        - Trial-specific start/end conditions
        - Media player controls for 360° content
        
        Nested helper functions handle file drops, object management, and UI callbacks.
        
        Args:
            button (bool, optional): Whether to show modification button. Default True
            getSettings (bool, optional): If True, saves settings without showing UI. Default None
            
        Returns:
            None. Updates self.trialSettings for current trial
        """
        def droppedEnvironment(e):
            envPath = e.filenames[0]
            
            extension = os.path.splitext(envPath)[1][1:]
            
            modelFileTypes = ["osgb", "OSGB", "gltf", "fbx", "glb", "obj"]
            imageFileTypes = ["jpg", "jpeg", "png", "tiff", "pdf", "raw", "gif", "bmp", "webp", "heif", "heic"]
            videoFileTypes = ["mp4", "mov", "avi", "wmv", "hevc", "flv", "mkv", "ogg", "m4v"]
                    
            if not extension in modelFileTypes and not extension in imageFileTypes and not extension in videoFileTypes:
                return
                
            baseName = os.path.basename(envPath)
            
            directory = os.path.dirname(envPath)
            destination = "resources"
            
            if extension in modelFileTypes:
                destination = os.path.join(destination, "environments")
                if not self.trialSettings[self.currTrial][MODE] == MODEL_3D:
                    self.trialButtonLabels[TRIAL_SETUP][ENVIRONMENT_UI][MODEL_3D_RADIO].set(1)
                    onModel3D()
                    
            elif extension in imageFileTypes:
                destination = os.path.join(destination, "media")
                if not self.trialSettings[self.currTrial][MODE] == MEDIA_360:
                    self.trialButtonLabels[TRIAL_SETUP][ENVIRONMENT_UI][MEDIA_360_RADIO].set(1)
                    onMedia360()
                    
            elif extension in videoFileTypes:
                destination = os.path.join(destination, "media")
                if not self.trialSettings[self.currTrial][MODE] == MEDIA_360:
                    self.trialButtonLabels[TRIAL_SETUP][ENVIRONMENT_UI][MEDIA_360_RADIO].set(1)
                    destination = os.path.join(destination, "media")
                    onMedia360()
                    
            os.makedirs(os.path.join(self.scriptDirectory, destination), exist_ok = True)
            
            shutil.copy(envPath, os.path.join(self.scriptDirectory, destination, baseName))
            
            changeDirectory(os.path.join(self.scriptDirectory, destination))
            
            onEnvironmentList(None, manual = baseName)
            
        def enableTrialInfo():
            def enableWindow():
                if self.trialInfoPanel is not None:
                    self.trialInfoPanel.remove()
                    
                self.trialsWindow = viz.addWindow(size=(1,1), pos=(0,1), clearMask = 0, scene=viz.addScene())
                self.trialInfoPanel = vizinfo.InfoPanel('', title=t(f'{TRIAL_OR_SCENE} Configuration'), window = self.trialsWindow ,align=viz.ALIGN_RIGHT_TOP, icon=True)
                
                self.trialInfoPanel.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)
                
                self.trialButtonLabels[TRIAL_SETUP] = {}
                self.trialButtonLabels[TRIAL_SETUP][TRIALS_UI] = {}
                self.trialButtonLabels[TRIAL_SETUP][ENVIRONMENT_UI] = {}
                self.trialButtonLabels[TRIAL_SETUP][MODEL_3D_UI] = {}
                self.trialButtonLabels[TRIAL_SETUP][MEDIA_360_UI] = {}
                
                self.currTrial = "1"
                
                vizact.onkeydown('.', self.trialInfoPanel.setPanelVisible, viz.TOGGLE)
                
                if self.transportToggleAction is None:
                    self.transportToggleAction = vizact.onkeydown(viz.KEY_SHIFT_L, toggleTransports)
                else:
                    self.transportToggleAction.setEnabled(viz.ON)
                    
                vizdragdrop.enable()
                
                vizdragdrop.onDropFile('*.*',droppedEnvironment)
                
            def enableTrialsSection():
                self.trialInfoPanel.addSection(t(f"{TRIAL_OR_SCENE}s"))
                
                row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER,background=False,border=False)
                row.setMargin(0)
                
                trialGUI = self.trialButtonLabels[TRIAL_SETUP][TRIALS_UI]
                
                trialGUI[TRIALS_TEXTBOX] = viz.addTextbox()
                trialGUI[GENERATE_BUTTON] = viz.addButtonLabel(t("Generate"))
                
                row.addItem(trialGUI[TRIALS_TEXTBOX])
                row.addItem(trialGUI[GENERATE_BUTTON])
                
                trialGUI[TRIAL_COUNT] = self.trialInfoPanel.addLabelItem(t('Count'), row)

                trialGUI[TRIALS_TEXTBOX].message(t("Infinite") if str(self.trialSettings[DEFAULT][NUMBER_OF_TRIALS]) == "-1" else str(self.trialSettings[DEFAULT][NUMBER_OF_TRIALS]))
                
                trialItems = ["1"]
                
                trialGUI[TRIAL_LIST] = viz.addDropList()
                
                trialGUI[PREVIOUS_BUTTON] = viz.addButton()
                trialGUI[PREVIOUS_BUTTON].uppicture(os.path.join(ICONS_PATH, "up_chevron.png"))
                trialGUI[NEXT_BUTTON] = viz.addButton()
                trialGUI[NEXT_BUTTON].uppicture(os.path.join(ICONS_PATH, "down_chevron.png"))
                trialGUI[TRACKING] = viz.addCheckbox()
#                trialGUI[TRACKING].set(viz.ON)
                
                row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_BOTTOM,background=False,border=False)
                row.setMargin(0)
                row.addItem(trialGUI[TRIAL_LIST])
                row.addItem(trialGUI[PREVIOUS_BUTTON])
                row.addItem(trialGUI[NEXT_BUTTON])
                row.addItem(trialGUI[TRACKING])
                row.addItem(viz.addText(t("Tracking")))
                
                self.trialInfoPanel.addLabelItem(t(f"Current {TRIAL_OR_SCENE}"), row)
                
                if self.loadedConfig or self.modifyFlag:
                    trial_list = list(self.trialSettings.keys())
                    if "DEFAULT" in trial_list:
                        trial_list.remove("DEFAULT")
                        
                    trialGUI[TRIAL_LIST].addItems(trial_list)
                    
#                    self.defaultTrialSettings = deepcopy(self.trialSettings[DEFAULT])
                    #self.trialSettings['1'] = deepcopy(self.trialSettings[DEFAULT])
                    
                else:
#                    if not len(self.trialSettings) == int(self.trialSettings[DEFAULT][NUMBER_OF_TRIALS]):
#                        for i in range(0, int(self.trialSettings[DEFAULT][NUMBER_OF_TRIALS])):
#                            trialItems.append(str(i+1))
#                            self.trialSettings[str(i+1)] = deepcopy(self.trialSettings[DEFAULT])
#                    else:
#                        self.defaultTrialSettings = deepcopy(self.trialSettings[DEFAULT])
#                        self.trialSettings['1'] = deepcopy(self.trialSettings[DEFAULT])
#                        trialItems.append("1")
                        
                    trialGUI[TRIAL_LIST].addItems(trialItems)
                    
                trialGUI[TRIAL_LIST].select(0)
                
                self.currTrial = trialGUI[TRIAL_LIST].getItems()[trialGUI[TRIAL_LIST].getSelection()]
                
                self.prevMode = self.trialSettings[self.currTrial][MODE]
                
                vizact.onbuttonup(trialGUI[GENERATE_BUTTON], onGenerateTrials)
                vizact.onlist(trialGUI[TRIAL_LIST], onTrialList)
                
                trialGUI[ADD_BUTTON] = viz.addButton()
                trialGUI[ADD_BUTTON].uppicture(os.path.join(ICONS_PATH, "add_icon.png"))
                trialGUI[DELETE_BUTTON] = viz.addButton()
                trialGUI[DELETE_BUTTON].uppicture(os.path.join(ICONS_PATH, "subtract_icon.png"))
                
                row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_BOTTOM,background=False,border=False)
                row.setMargin(0)
                row.addItem(trialGUI[ADD_BUTTON])
                row.addItem(trialGUI[DELETE_BUTTON])
                
                self.trialInfoPanel.addLabelItem("", row)
                
                trialGUI[TRIAL_LABEL] = self.trialInfoPanel.addLabelItem(t("Label"), viz.addTextbox())
                trialGUI[TRIAL_LABEL].message(self.trialSettings[DEFAULT][TRIAL_LABEL])
                
                row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_BOTTOM,background=False,border=False)
                row.setMargin(0)
                trialGUI[CONDITION] = row.addItem(viz.addDropList())
                trialGUI[CONDITION].addItems(["Start", "End"])
                trialGUI[CONDITION].setLength(0.5)
                
                trialGUI[CONDITION_TYPE] = row.addItem(viz.addDropList())
                trialGUI[CONDITION_TYPE].addItems(list(self.menuToConditionDict.keys()))

                self.trialInfoPanel.addLabelItem(t("Condition"), row)
                trialGUI[CONDITION_TEXT] = self.trialInfoPanel.addLabelItem("", viz.addTextbox())
                trialGUI[CONDITION_TEXT].setLength(1.25)
                
                setCondition()
                trialGUI[TRACKING].set(self.trialSettings[DEFAULT][TRACKING])
                
                vizact.onlist(trialGUI[CONDITION_TYPE], onConditionList)
                vizact.ontextbox(trialGUI[CONDITION_TEXT], onConditionTextbox)
                vizact.onlist(trialGUI[CONDITION], switchCondition)
                
            def enableEnvironmentSection():
                self.trialInfoPanel.addSection(t("Environment"))
                trialGUI = self.trialButtonLabels[TRIAL_SETUP][ENVIRONMENT_UI]
            
                row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER,background=False,border=False)
                row.setMargin(0)
                
                model3DLabel = viz.addText(t("3D Models      "))
                trialGUI[MODEL_3D_RADIO] = viz.addRadioButton('env')
                media360Label = viz.addText(t("360 Media"))
                trialGUI[MEDIA_360_RADIO] = viz.addRadioButton('env')
                
                row.addItem(trialGUI[MODEL_3D_RADIO])
                row.addItem(model3DLabel)
                
                row.addItem(trialGUI[MEDIA_360_RADIO])
                row.addItem(media360Label)
                
                self.trialInfoPanel.addLabelItem(t("Mode"), row)
                
                row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER,background=False,border=False)
                row.setMargin(0)
                
                trialGUI[CHOOSE_DIRECTORY] = viz.addButtonLabel(t("Change"))
                
                trialGUI[BUILT_IN] = viz.addButtonLabel(t("Built-In"))
                
                full_path = self.trialSettings[DEFAULT][ENVIRONMENT_DIRECTORY]
                
                if os.path.normpath(full_path) in [SIGHTLAB_ENVIRONMENT_RESOURCES, SIGHTLAB_MEDIA_RESOURCES]:
                    directoryName = "BUILT-IN"
                else:
                    directoryName = self.normalizePath(full_path)
                
                trialGUI[DIRECTORY_LABEL] = viz.addText(directoryName)
                
                #row.addItem(trialGUI[DIRECTORY_LABEL])
                row.addItem(trialGUI[CHOOSE_DIRECTORY])
                row.addItem(trialGUI[BUILT_IN])
                
                self.trialInfoPanel.addLabelItem(t("Directory"), trialGUI[DIRECTORY_LABEL])
                self.trialInfoPanel.addLabelItem("", row)
                
                label = None
                resourceList = None
                
                if self.trialSettings[DEFAULT][MODE] == MODEL_3D:
                    trialGUI[MODEL_3D_RADIO].set(1)
                    label = t('Environment')
                    resourceList = self.resourceLists[ENVIRONMENT]
                    
                elif self.trialSettings[DEFAULT][MODE] == MEDIA_360:
                    trialGUI[MEDIA_360_RADIO].set(1)
                    label = t('Environment')
                    resourceList = self.resourceLists[MEDIA]
                    
                for i in range(0, len(resourceList)):
                    resourceList[i] = os.path.basename(resourceList[i])
                
                if len(resourceList) == 0:
                    resourceList = ["No items found"]
                
                row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER,background=False,border=False)
                row.setMargin(0)
                
                trialGUI[ENVIRONMENT_LIST] =  viz.addDropList()
                row.addItem(trialGUI[ENVIRONMENT_LIST])
                # trialGUI[ENVIRONMENT_LIST].setLength(1.5)
                
                trialGUI[OPEN_ENVIRONMENT] = viz.addButtonLabel(t("Edit"))
                row.addItem(trialGUI[OPEN_ENVIRONMENT])
                
                self.trialInfoPanel.addLabelItem(label, row)
                
                self.environmentPageLimit = 20
                self.environmentCurrPage = 1
                
                self.environmentPageDict = self.generatePages(resourceList, self.environmentPageLimit)
                    
                trialGUI[ENVIRONMENT_LIST].addItems(self.environmentPageDict[self.environmentCurrPage])
                                
                row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER,background=False,border=False)
                row.setMargin(0)
                
                trialGUI[REFRESH_CHILDREN] = viz.addButton()
                trialGUI[REFRESH_CHILDREN].uppicture(os.path.join(ICONS_PATH,'refresh_icon.png'))
                #trialGUI[REFRESH_CHILDREN].downpicture(os.path.join(os.path.dirname(__file__),'refresh_icon.png'))
                
                row.addItem(trialGUI[REFRESH_CHILDREN])
                
                trialGUI[ADD_NEW] = viz.addButton()
                trialGUI[ADD_NEW].uppicture(os.path.join(ICONS_PATH,'plus_icon.png'))
                
                row.addItem(trialGUI[ADD_NEW])
                
                trialGUI[OPEN_FOLDER] = viz.addButton()
                trialGUI[OPEN_FOLDER].uppicture(os.path.join(ICONS_PATH, 'folder_icon.png'))
            
                row.addItem(trialGUI[OPEN_FOLDER])
                
                trialGUI[OPEN_ASSET_BROWSER] = viz.addButton()
                trialGUI[OPEN_ASSET_BROWSER].uppicture(os.path.join(ICONS_PATH, 'globe.png'))
                
                row.addItem(trialGUI[OPEN_ASSET_BROWSER])

                self.trialInfoPanel.addLabelItem("", row)
                
                    
                if not resourceList[0] == "No items found":
                    try:
                        envName = os.path.basename(self.trialSettings[DEFAULT][ENVIRONMENT])
                        #print(envName, resourceList)
                        if envName in resourceList and resourceList.index(envName) > self.environmentPageLimit:
                            onEnvironmentList(None, manual = "...")
                            
                            trialGUI[ENVIRONMENT_LIST].select(trialGUI[ENVIRONMENT_LIST].getItems().index(envName)) 
                            #print("next page", trialGUI[ENVIRONMENT_LIST].getSelection())
                        trialGUI[ENVIRONMENT_LIST].select(trialGUI[ENVIRONMENT_LIST].getItems().index(envName)) 
                    except:
                        self.loadTempEnvironment(default = True)
                        
            enableWindow()
            enableTrialsSection()
            enableEnvironmentSection()
            
            refreshEnvironmentList()
            
            trialGUI = self.trialButtonLabels[TRIAL_SETUP][TRIALS_UI]
            environmentGUI = self.trialButtonLabels[TRIAL_SETUP][ENVIRONMENT_UI]
                
            vizact.onbuttonup(trialGUI[PREVIOUS_BUTTON], previousTrial)
            vizact.onbuttonup(trialGUI[ADD_BUTTON], addTrial)
            vizact.onbuttonup(trialGUI[DELETE_BUTTON], deleteTrial)
            vizact.onbuttonup(trialGUI[NEXT_BUTTON], nextTrial)
            
            vizact.onbuttondown(environmentGUI[MODEL_3D_RADIO], onModel3D)
            vizact.onbuttondown(environmentGUI[MEDIA_360_RADIO], onMedia360)
            
            vizact.onlist(environmentGUI[ENVIRONMENT_LIST], onEnvironmentList)
            vizact.onbuttonup(environmentGUI[OPEN_ENVIRONMENT], openEnvironment)
            vizact.onbuttonup(environmentGUI[REFRESH_CHILDREN], refreshChildren)
            vizact.onbuttonup(environmentGUI[ADD_NEW], openNewInspector)
            vizact.onbuttonup(environmentGUI[OPEN_FOLDER], openDirectory)
            vizact.onbuttonup(environmentGUI[OPEN_ASSET_BROWSER], openAssetBrowser)
        
        def enable3DModelSection():                
            model3DGUI = self.trialButtonLabels[TRIAL_SETUP][MODEL_3D_UI]
            
            self.trialButtonLabels[SEPARATORS] = []
            
            self._childSectionHeader = self.trialInfoPanel.addSection(t("Target, Visible, Grabbable"))
            self.trialButtonLabels[SEPARATORS].append(self._childSectionHeader)

            row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_BOTTOM,background=False,border=False)
            
            fixation = row.addItem(viz.addCheckbox())
            
            visible = row.addItem(viz.addCheckbox())
            
            grabbable = row.addItem(viz.addCheckbox())
            
            label = self.trialInfoPanel.addLabelItem("", row)
                
            model3DGUI[SELECT_ALL] = [fixation, visible, grabbable, label]
            
            model3DGUI[CHILD_LIST] = {}
            
            for i in range(0, self.pageLimit):
                row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_BOTTOM,background=False,border=False)
            
                fixation = row.addItem(viz.addCheckbox())
                
                visible = row.addItem(viz.addCheckbox())
                
                grabbable = row.addItem(viz.addCheckbox())
                
                stateBox = row.addItem(viz.addTextbox())
                stateBox.message('1')
                stateBox.setLength(0.3)
                stateBox.visible(viz.OFF)
                
                label = self.trialInfoPanel.addLabelItem("", row)
                node = ""
                
                model3DGUI[CHILD_LIST][str(i+1)] = [fixation, visible, grabbable, label, node, stateBox]
                vizact.ontextbox(stateBox, onStateBoxChanged, str(i+1))
            
            row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_BOTTOM,background=False,border=False)
            #row.setMargin(0)
            model3DGUI = self.trialButtonLabels[TRIAL_SETUP][MODEL_3D_UI]
            
            model3DGUI[PREVIOUS_PAGE_BUTTON] = row.addItem(viz.addButton())
            model3DGUI[PREVIOUS_PAGE_BUTTON].uppicture(os.path.join(ICONS_PATH, "left_chevron.png"))
            
            model3DGUI[NEXT_PAGE_BUTTON] = row.addItem(viz.addButton())
            model3DGUI[NEXT_PAGE_BUTTON].uppicture(os.path.join(ICONS_PATH, "right_chevron.png"))
            
            self.pageText = self.trialInfoPanel.addLabelItem(t("Page") + " 1 " + t("of") + " 1", row)
            
#            self.trialButtonLabels[SEPARATORS].append(self.trialInfoPanel.addSeparator())
            
            row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_BOTTOM,background=False,border=False)
            model3DGUI = self.trialButtonLabels[TRIAL_SETUP][MODEL_3D_UI]
            
#            self.trialButtonLabels[DONE] = self.trialInfoPanel.addItem(viz.addButtonLabel('Done'),align=viz.ALIGN_LEFT_CENTER)
            
#            self.trialButtonLabels[CLOSE] = self.trialInfoPanel.addItem(viz.addButtonLabel('Close'),align=viz.ALIGN_LEFT_CENTER)
            
            if self.modifyFlag or self.loadedConfig:
                # If TRIAL_SETUP is empty (e.g., switched from 360 mode), populate as new trial
                if not self.trialSettings[self.currTrial][TRIAL_SETUP]:
                    populateModel3D(True)
                else:
                    populateModel3D()
            else:
                populateModel3D(True)
            
            vizact.onbuttonup(model3DGUI[PREVIOUS_PAGE_BUTTON], refreshChildNodes, -1)
            vizact.onbuttonup(model3DGUI[NEXT_PAGE_BUTTON], refreshChildNodes, 1)
            
            vizact.onbuttonup(model3DGUI[SELECT_ALL][0], toggleAll, TARGET, viz.OFF)
            vizact.onbuttonup(model3DGUI[SELECT_ALL][1], toggleAll, VISIBLE, viz.OFF)
            vizact.onbuttonup(model3DGUI[SELECT_ALL][2], toggleAll, GRAB, viz.OFF)
            
            vizact.onbuttondown(model3DGUI[SELECT_ALL][0], toggleAll, TARGET, viz.ON)
            vizact.onbuttondown(model3DGUI[SELECT_ALL][1], toggleAll, VISIBLE, viz.ON)
            vizact.onbuttondown(model3DGUI[SELECT_ALL][2], toggleAll, GRAB, viz.ON)
            
#            vizact.onbuttonup(self.trialButtonLabels[DONE], trialSetup)
        
        def remove3DModelSection():
            model3DGUI = self.trialButtonLabels[TRIAL_SETUP][MODEL_3D_UI]
            
            for item in model3DGUI:
                if item in [PREVIOUS_PAGE_BUTTON, NEXT_PAGE_BUTTON, SECTION_HEADER, ADD_CHILD, ADD_CHILD_TEXTBOX, ADD_CHILD_LABEL]:
                    self.trialInfoPanel.removeItem(model3DGUI[item])
                elif item == SELECT_ALL:
                    self.trialInfoPanel.removeItem(model3DGUI[item][3])
                else:
                    for i in model3DGUI[item]:
                        self.trialInfoPanel.removeItem(model3DGUI[item][i][3])
                    
            for item in self.trialButtonLabels[SEPARATORS]:
                self.trialInfoPanel.removeItem(item)
                
#            self.trialInfoPanel.removeItem(self.trialButtonLabels[DONE])
            
            self.trialInfoPanel.removeItem(self.pageText)
                    
        def enable360MediaSection():
            media360GUI = self.trialButtonLabels[TRIAL_SETUP][MEDIA_360_UI]
            
            self.trialButtonLabels[SEPARATORS] = []
            self.trialButtonLabels[SEPARATORS].append(self.trialInfoPanel.addSection(t("Media Options")))
            
            row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER,background=False,border=False)
            row.setMargin(0)
            
            videoLabel = viz.addText(t("Video     "))
            media360GUI[VIDEO_RADIO] = viz.addRadioButton('type')
            imageLabel = viz.addText(t("Image"))
            media360GUI[IMAGE_RADIO] = viz.addRadioButton('type')
            
            row.addItem(media360GUI[VIDEO_RADIO])
            row.addItem(videoLabel)
            
            row.addItem(media360GUI[IMAGE_RADIO])
            row.addItem(imageLabel)
            
            media360GUI[MEDIA_TYPE] = self.trialInfoPanel.addLabelItem(t("Type"), row)
            
            media360GUI[VIDEO_RADIO].set(1)
            
            row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER,background=False,border=False)
            row.setMargin(0)
            
            monoLabel = viz.addText(t("Mono      "))
            media360GUI[MONO_RADIO] = viz.addRadioButton('format')
            stereoTBLabel = viz.addText(t("Stereo T/B      "))
            media360GUI[STEREO_TB_RADIO] = viz.addRadioButton('format')
            stereoLRLabel = viz.addText(t("Stereo L/R"))
            media360GUI[STEREO_LR_RADIO] = viz.addRadioButton('format')
            
            row.addItem(media360GUI[MONO_RADIO])
            row.addItem(monoLabel)
            
            row.addItem(media360GUI[STEREO_TB_RADIO])
            row.addItem(stereoTBLabel)
            
            row.addItem(media360GUI[STEREO_LR_RADIO])
            row.addItem(stereoLRLabel)
            
            media360GUI[MEDIA_FORMAT] =  self.trialInfoPanel.addLabelItem(t("Format"), row)
        
            self.trialButtonLabels[SEPARATORS].append(self.trialInfoPanel.addSection(t("Regions of Interest")))

            populateMedia360(True, False)
            
#            self.trialButtonLabels[SEPARATORS].append(self.trialInfoPanel.addSection("Regions of Interest"))
#            
            #populateROI(True)
            
            def imageRadio():
                self.trialSettings[self.currTrial][MEDIA_SETUP][MEDIA_TYPE] = "image"
                refreshEnvironmentList()
                
            def videoRadio():
                self.trialSettings[self.currTrial][MEDIA_SETUP][MEDIA_TYPE] = "video"
                refreshEnvironmentList()
                
            def monoRadio():
                self.trialSettings[self.currTrial][MEDIA_SETUP][MEDIA_FORMAT] = "Monoscopic"
                self.loadTempEnvironment()
                toggleTransports(viz.OFF)
                
            def stereoTBRadio():
                self.trialSettings[self.currTrial][MEDIA_SETUP][MEDIA_FORMAT] = "Stereoscopic T/B"
                self.loadTempEnvironment()
                toggleTransports(viz.OFF)
                
            def stereoLRRadio():
                self.trialSettings[self.currTrial][MEDIA_SETUP][MEDIA_FORMAT] = "Stereoscopic L/R"
                self.loadTempEnvironment()
                toggleTransports(viz.OFF)
                
            vizact.onbuttondown(media360GUI[IMAGE_RADIO], imageRadio)
            vizact.onbuttondown(media360GUI[VIDEO_RADIO], videoRadio)
            
            vizact.onbuttondown(media360GUI[MONO_RADIO], monoRadio)
            vizact.onbuttondown(media360GUI[STEREO_TB_RADIO], stereoTBRadio)
            vizact.onbuttondown(media360GUI[STEREO_LR_RADIO], stereoLRRadio)
            
        def remove360MediaSection():
            media360GUI = self.trialButtonLabels[TRIAL_SETUP][MEDIA_360_UI]
            
            for item in self.trialButtonLabels[SEPARATORS]:
                self.trialInfoPanel.removeItem(item)
            
            for item in media360GUI:
                if item is not REGIONS_OF_INTEREST:
                    self.trialInfoPanel.removeItem(media360GUI[item])
                    
            for item in media360GUI[REGIONS_OF_INTEREST]:
                self.trialInfoPanel.removeItem(media360GUI[REGIONS_OF_INTEREST][item][0])
            
            for roi in self.regionsOfInterest:
                self.regionsOfInterest[roi].remove()
                
            self.regionsOfInterest = {}
                
#            self.trialInfoPanel.removeItem(self.trialButtonLabels[DONE])
            
        def onGenerateTrials():
            trialGUI = self.trialButtonLabels[TRIAL_SETUP][TRIALS_UI]
            textBoxLabel = trialGUI[TRIAL_COUNT]
            trialList = trialGUI[TRIAL_LIST]
            textBox = trialGUI[TRIALS_TEXTBOX]
            
            numCount = textBox.get()
            
            if numCount == '':
                return
                
            trialKey = int(self.currTrial)-1
            
            getTrialSettings()
            
            trialList.clearItems()
            trialItems = []
            
            visualLimit = int(numCount)
            if visualLimit > 25:
                visualLimit = 25
                
            for i in range(0, visualLimit):
                trialItems.append(str(i+1))
            
            if not visualLimit == int(numCount):
                trialItems.append("...")
                
            trialList.addItems(trialItems)
            trialList.select(trialKey)
            
            self.trialSettings[DEFAULT][NUMBER_OF_TRIALS] = numCount
            
            lastKey = list(self.trialSettings.keys())[-1]
            if int(numCount) > len(self.trialSettings):
                for i in range(len(self.trialSettings), int(numCount)):
                    self.trialSettings[str(i+1)] = deepcopy(self.trialSettings[lastKey])
            elif int(numCount) < len(self.trialSettings):
                for i in range(int(numCount), len(self.trialSettings)):
                    self.trialSettings.pop(str(i+1))
                self.currTrial = numCount
                    
            for trial in self.trialSettings:
                self.trialSettings[trial][NUMBER_OF_TRIALS] = numCount
                     
        def getCondition():
            trialGUI = self.trialButtonLabels[TRIAL_SETUP][TRIALS_UI]
            
            currentCondition = trialGUI[CONDITION].getItems()[trialGUI[CONDITION].getSelection()]
            
            if currentCondition == "Start":
                currentCondition = START_CONDITION
            else:
                currentCondition = END_CONDITION
                
            conditionType = trialGUI[CONDITION_TYPE].getItems()[trialGUI[CONDITION_TYPE].getSelection()]            
            conditionType = self.menuToConditionDict[conditionType]
            
            conditionSettings = self.trialSettings[self.currTrial][currentCondition]
            
            if conditionType not in conditionSettings:
                value = self.conditionValues[conditionType]
                if conditionType == ON_MEDIA_END and self.tempMedia is not None:
                    value =  str(round(self.tempMedia.getDuration(), ROUND_VALUES))
                    
                if conditionType == ON_GAZE_TIME and self.environmentNodes is not None:
                    value = self.environmentNodes[0]
            else:
                value = trialGUI[CONDITION_TEXT].get()
            
            self.trialSettings[self.currTrial][currentCondition] = [conditionType, value]
            
        def setCondition():
            trialGUI = self.trialButtonLabels[TRIAL_SETUP][TRIALS_UI]
            
            if trialGUI[CONDITION].getSelection() == 0:
                currentCondition = START_CONDITION
            else:
                currentCondition = END_CONDITION
                
            if self.trialSettings[self.currTrial][MODE] == MODEL_3D:
                if "Media End" in trialGUI[CONDITION_TYPE].getItems():
                    trialGUI[CONDITION_TYPE].removeItem(trialGUI[CONDITION_TYPE].getItems().index("Media End"))
            else:
                if currentCondition == START_CONDITION and "Media End" in trialGUI[CONDITION_TYPE].getItems():
                    trialGUI[CONDITION_TYPE].removeItem(trialGUI[CONDITION_TYPE].getItems().index("Media End"))
                else:
                    if "Media End" not in trialGUI[CONDITION_TYPE].getItems():
                        trialGUI[CONDITION_TYPE].addItem("Media End")
                        
            if currentCondition == START_CONDITION and "Gaze Item" in trialGUI[CONDITION_TYPE].getItems():
                trialGUI[CONDITION_TYPE].removeItem(trialGUI[CONDITION_TYPE].getItems().index("Gaze Item"))
            elif currentCondition == END_CONDITION and "Gaze Item" not in trialGUI[CONDITION_TYPE].getItems():
                trialGUI[CONDITION_TYPE].addItem("Gaze Item")
                
            conditionSettings = self.trialSettings[self.currTrial][currentCondition]

            conditionType = conditionSettings[0]
            value = conditionSettings[1]
            
            if conditionType == ON_MEDIA_END:
                value = str(round(self.tempMedia.getDuration(), ROUND_VALUES))
                self.trialSettings[self.currTrial][currentCondition][1] = value
            
            selection = self.conditionToMenuDict[conditionType]
            trialGUI[CONDITION_TYPE].select(trialGUI[CONDITION_TYPE].getItems().index(selection))
            trialGUI[CONDITION_TYPE].setLength(0.5)
            trialGUI[CONDITION_TEXT].row.margin = 0
            
            if conditionType == NO_CONDITION:
                trialGUI[CONDITION_TEXT].label.message(value)

            elif conditionType == KEY_PRESS:
                trialGUI[CONDITION_TEXT].label.message("Key")
                
            elif conditionType == TIMER:
                trialGUI[CONDITION_TEXT].label.message("Seconds")
                
            elif conditionType == CUSTOM_EVENT:
                trialGUI[CONDITION_TEXT].label.message("Name")
                
            elif conditionType == ON_MEDIA_END:
                trialGUI[CONDITION_TEXT].label.message("Length (secs)")
                
            elif conditionType == ON_GAZE_TIME:
                trialGUI[CONDITION_TEXT].label.message("Object")
                
            trialGUI[CONDITION_TEXT].message(value)
            
        def onConditionTextbox(e):
            getCondition()
            
        def switchCondition(e):
            setCondition()
            
        def onConditionList(e):
            getCondition()
            setCondition()
        
        def onTrialList(e):
            trialGUI = self.trialButtonLabels[TRIAL_SETUP][TRIALS_UI]
            trialList = trialGUI[TRIAL_LIST]
            
            if e.object.getItem(e.newSel) == '...':
                if e.newSel == 0:
                    trialList.clearItems()
                    trialItems = [DEFAULT]
                    
                    visualLimit = int(self.trialSettings[DEFAULT][NUMBER_OF_TRIALS])
                    if visualLimit > 25:
                        visualLimit = 25
                        
                    for i in range(0, visualLimit):
                        trialItems.append(str(i+1))
                    
                    if not visualLimit == int(self.trialSettings[DEFAULT][NUMBER_OF_TRIALS]):
                        trialItems.append("...")
                        
                    trialList.addItems(trialItems)
                    trialList.select(0)
                else:
                    trialList.clearItems()
                    trialItems = ["..."]
                    
                    visualLimit = int(self.trialSettings[DEFAULT][NUMBER_OF_TRIALS])
                    if visualLimit > 50:
                        visualLimit = 50
                        
                    for i in range(25, visualLimit):
                        trialItems.append(str(i+1))
                    
                    if not visualLimit == int(self.trialSettings[DEFAULT][NUMBER_OF_TRIALS]):
                        trialItems.append("...")
                        
                    trialList.addItems(trialItems)
                    trialList.select(1)
                return

            getTrialSettings()
            
            trialGUI = self.trialButtonLabels[TRIAL_SETUP][TRIALS_UI]
            self.prevMode = self.trialSettings[self.currTrial][MODE]
            self.currTrial = trialGUI[TRIAL_LIST].getItems()[trialGUI[TRIAL_LIST].getSelection()]
            
            setTrialSettings()
                
        def refreshEnvironmentList(recursive = True):
            environmentList = self.trialButtonLabels[TRIAL_SETUP][ENVIRONMENT_UI][ENVIRONMENT_LIST]
            environmentList.clearItems()
            
            environmentFileList = []

            for file in self.findFiles(self.trialSettings[self.currTrial][ENVIRONMENT_DIRECTORY], recursive = recursive):
                if self.trialSettings[self.currTrial][MODE] == MEDIA_360:
                    imageFileTypes = ["jpg", "jpeg", "png", "tiff", "pdf", "raw", "gif", "bmp", "webp", "heif", "heic"]
                    videoFileTypes = ["mp4", "mov", "avi", "wmv", "hevc", "flv", "mkv", "ogg", "m4v"]
                    if file[-3:] in imageFileTypes or file[-3:] in videoFileTypes or file[-4:] in imageFileTypes or file[-4:] in videoFileTypes:
                        environmentFileList.append(file)
                else:
                    modelFileTypes = ["osgb", "OSGB", "gltf", "fbx", "glb", "obj"]
                    if file[-3:] in modelFileTypes or file[-4:] in modelFileTypes:
                        environmentFileList.append(file)
                                                
            if len(environmentFileList) == 0:
                environmentFileList.append("No items found")
                
            for i in range(0, len(environmentFileList)):
                environmentFileList[i] = os.path.basename(environmentFileList[i])
            
            self.environmentPageDict = self.generatePages(environmentFileList, self.environmentPageLimit)
            
            if not self.environmentCurrPage <= len(self.environmentPageDict):
                self.environmentCurrPage = 1
                
            if not self.trialSettings[self.currTrial][ENVIRONMENT] in self.environmentPageDict[self.environmentCurrPage] and len(self.environmentPageDict)>1:
                self.environmentCurrPage = 2
                if not self.trialSettings[self.currTrial][ENVIRONMENT] in self.environmentPageDict[self.environmentCurrPage]:
                    self.environmentCurrPage = 1
            
            environmentList.addItems(self.environmentPageDict[self.environmentCurrPage])
            
            if self.trialSettings[self.currTrial][MODE] == MODEL_3D:
                self.resourceLists[ENVIRONMENT] = environmentFileList
            elif self.trialSettings[self.currTrial][MODE] == MEDIA_360:
                self.resourceLists[MEDIA] = environmentFileList
            
            if self.trialSettings[self.currTrial][ENVIRONMENT] in environmentFileList:
                environmentList.select(environmentList.getItems().index(self.trialSettings[self.currTrial][ENVIRONMENT]))
            else:
                environmentList.select(0)
                newEnvironment = environmentList.getItems()[0]
                if newEnvironment != "No items found":
                    self.trialSettings[self.currTrial][ENVIRONMENT] = newEnvironment
                    # Auto-populate nodes for the new environment (only if GUI is fully initialized)
                    # Check for pageText (3D mode) or VIDEO_RADIO (360 mode) to ensure GUI exists
                    if self.trialSettings[self.currTrial][MODE] == MODEL_3D:
                        if hasattr(self, 'pageText') and self.pageText is not None:
                            populateModel3D(newTrial=True)
                    else:
                        if MEDIA_360_UI in self.trialButtonLabels[TRIAL_SETUP] and VIDEO_RADIO in self.trialButtonLabels[TRIAL_SETUP][MEDIA_360_UI]:
                            populateMedia360()
                else:
                    self.trialSettings[self.currTrial][ENVIRONMENT] = newEnvironment
                
#            environmentList.setLength(1.5)
        
        def getTrialSettings():
            getCondition()
            self.trialSettings[self.currTrial][TRIAL_LABEL] = self.trialButtonLabels[TRIAL_SETUP][TRIALS_UI][TRIAL_LABEL].get()
            self.trialSettings[self.currTrial][TRACKING] = self.trialButtonLabels[TRIAL_SETUP][TRIALS_UI][TRACKING].get()
            
            if self.trialSettings[self.currTrial][MODE] == MODEL_3D:
                pageLabels = self.trialButtonLabels[TRIAL_SETUP][MODEL_3D_UI][CHILD_LIST]
                
                for node in pageLabels:
                    if not pageLabels[node][4] == "No child found":
                        nodeName = pageLabels[node][4]
                        # Preserve existing AVATAR flag if present
                        existingAvatar = self.trialSettings[self.currTrial][TRIAL_SETUP].get(nodeName, {}).get("AVATAR", False)
                        existingAnimate = self.trialSettings[self.currTrial][TRIAL_SETUP].get(nodeName, {}).get("ANIMATE", False)
                        try:
                            stateVal = int(pageLabels[node][5].get()) if len(pageLabels[node]) > 5 else 1
                        except (ValueError, TypeError):
                            stateVal = 1
                        self.trialSettings[self.currTrial][TRIAL_SETUP][nodeName] = {
                        TARGET: pageLabels[node][0].get(),
                        VISIBLE: pageLabels[node][1].get(),
                        GRAB: pageLabels[node][2].get(),
                        "AVATAR": existingAvatar,
                        "ANIMATE": existingAnimate,
                        "STATE": stateVal
                        }
                
                self.trialSettings[self.currTrial][MEDIA_SETUP] = {}
                # Ensure REGIONS_OF_INTEREST is cleared for 3D mode
                self.trialSettings[self.currTrial][REGIONS_OF_INTEREST] = {}
                
#                if self.currTrial == DEFAULT:
#                    setDefaultTrials()
#                    self.environmentDirectory = self.trialSettings[DEFAULT][ENVIRONMENT_DIRECTORY]
            else:
                self.trialSettings[self.currTrial][TRIAL_SETUP] = {}
#                if self.currTrial == DEFAULT:
#                    setDefaultTrials()
#                    self.mediaDirectory = self.trialSettings[DEFAULT][ENVIRONMENT_DIRECTORY]
            
        def setTrialSettings():
            model3D = self.trialButtonLabels[TRIAL_SETUP][ENVIRONMENT_UI][MODEL_3D_RADIO]
            media360 = self.trialButtonLabels[TRIAL_SETUP][ENVIRONMENT_UI][MEDIA_360_RADIO]
        
            if self.trialSettings[self.currTrial][MODE] == MODEL_3D:
                model3D.set(1)
                if self.prevMode == MEDIA_360:
                    onModel3D()
                else:
                    onModel3D(False)
            elif self.trialSettings[self.currTrial][MODE] == MEDIA_360:
                media360.set(1)
                if self.prevMode == MODEL_3D:
                    onMedia360()
                else:
                    onMedia360(False)
                    
            trialGUI = self.trialButtonLabels[TRIAL_SETUP][TRIALS_UI]
            trialGUI[CONDITION].select(0)
            
            setCondition()
            trialGUI[TRIAL_LABEL].message(self.trialSettings[self.currTrial][TRIAL_LABEL])
            trialGUI[TRACKING].set(self.trialSettings[self.currTrial][TRACKING])

            if DASHBOARD_TRIAL_CHANGED_HOOK is not None:
                try:
                    DASHBOARD_TRIAL_CHANGED_HOOK()
                except Exception as e:
                    print(f"[Inspector] Trial-changed hook failed: {e}")

        def previousTrial():
            getTrialSettings()
            
            trialNumber = self.trialButtonLabels[TRIAL_SETUP][TRIALS_UI][TRIAL_LIST]
            if trialNumber.getSelection()-1 >= 0:
                trialNumber.select(trialNumber.getSelection()-1)
            
            trialGUI = self.trialButtonLabels[TRIAL_SETUP][TRIALS_UI]
            self.prevMode = self.trialSettings[self.currTrial][MODE]
            self.currTrial = trialGUI[TRIAL_LIST].getItems()[trialGUI[TRIAL_LIST].getSelection()]
            setTrialSettings()
            
        def addTrial():
#            if self.currTrial == DEFAULT:
#                return
                
            getTrialSettings()
            
            trialNumber = self.trialButtonLabels[TRIAL_SETUP][TRIALS_UI][TRIAL_LIST]
            
            numCount = int(self.trialSettings[DEFAULT][NUMBER_OF_TRIALS]) + 1
            
            for i in range(numCount, int(self.currTrial), -1):
                self.trialSettings[str(i)] = deepcopy(self.trialSettings[str(i-1)])
                
            self.trialSettings[str(int(self.currTrial) + 1)] = deepcopy(self.trialSettings[self.currTrial])
            
            self.prevMode = self.trialSettings[self.currTrial][MODE]
            
            trialKey = str(self.currTrial)
            
            self.currTrial = str(int(self.currTrial) + 1)
            
            for trial in self.trialSettings:
                self.trialSettings[trial][NUMBER_OF_TRIALS] = str(numCount)
            
            self.defaultTrialSettings = deepcopy(self.trialSettings[trialKey])
            
            trialNumber.addItem(str(numCount))
            
            if trialNumber.getSelection()+1 < len(trialNumber.getItems()):
                trialNumber.select(trialNumber.getSelection()+1)
                
            setTrialSettings()
            
            trialGUI = self.trialButtonLabels[TRIAL_SETUP][TRIALS_UI]
            trialCount = trialGUI[TRIALS_TEXTBOX]
            trialCount.message(str(numCount))
            
            #print(self.trialSettings)
            
        def deleteTrial():
#            if self.currTrial == DEFAULT:
#                return
                
            trialNumber = self.trialButtonLabels[TRIAL_SETUP][TRIALS_UI][TRIAL_LIST]
            
            self.prevMode = self.trialSettings[self.currTrial][MODE]
            
            for i in range(int(self.currTrial), int(self.trialSettings[DEFAULT][NUMBER_OF_TRIALS])-1):
                self.trialSettings[str(i)] = self.trialSettings[str(i+1)]
 
            self.trialSettings.pop(str(self.trialSettings[DEFAULT][NUMBER_OF_TRIALS]))
            
            numCount = int(self.trialSettings[DEFAULT][NUMBER_OF_TRIALS]) - 1
            
            if trialNumber.getSelection()-1 >= 0:
                self.currTrial = str(int(self.currTrial) - 1)
                trialNumber.select(trialNumber.getSelection()-1)
                
            trialNumber.removeItem(trialNumber.getItems().index(self.trialSettings[DEFAULT][NUMBER_OF_TRIALS]))
            
            for trial in self.trialSettings:
                self.trialSettings[trial][NUMBER_OF_TRIALS] = str(numCount)
                
            self.defaultTrialSettings = deepcopy(self.trialSettings[DEFAULT])
            
            setTrialSettings()
            
            trialGUI = self.trialButtonLabels[TRIAL_SETUP][TRIALS_UI]
            trialCount = trialGUI[TRIALS_TEXTBOX]
            trialCount.message(str(numCount))
            
        def nextTrial():
            getTrialSettings()
            
            trialNumber = self.trialButtonLabels[TRIAL_SETUP][TRIALS_UI][TRIAL_LIST]
            if trialNumber.getSelection()+1 < len(trialNumber.getItems()):
                trialNumber.select(trialNumber.getSelection()+1)
            
            trialGUI = self.trialButtonLabels[TRIAL_SETUP][TRIALS_UI]
            self.prevMode = self.trialSettings[self.currTrial][MODE]
            self.currTrial = trialGUI[TRIAL_LIST].getItems()[trialGUI[TRIAL_LIST].getSelection()]
            
            setTrialSettings()
            
        def refreshChildren():
            refreshEnvironmentList()
            if self.trialSettings[self.currTrial][MODE] == MODEL_3D:
                populateModel3D(True)
            else:
                populateMedia360()

        # Exposed on self so external tooling (e.g. the SightLab Dashboard's
        # embedded Inspector "Save Scene" button) can trigger the same
        # refresh the "Edit" button's own external-change polling does,
        # without needing its own copy of the poll-timer machinery.
        self.refreshChildren = refreshChildren

        def openNewInspector():
            def find_file_in_directory(directory, filename):
                for root, dirs, files in os.walk(directory):
                    if filename in files:
                        return os.path.join(root, filename)
                return None

            filename = "Inspector.exe"

            # First, try to find the file in a common directory
            common_dirs = [os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)")]
            for dir in common_dirs:
                if dir:
                    path = find_file_in_directory(dir, filename)
                    if path:
                        os.startfile(path)
                        return
                        
        def openDirectory():
            if not self.trialSettings[self.currTrial][ENVIRONMENT_DIRECTORY] == ".":
                directory = os.path.join(self.scriptDirectory, self.trialSettings[self.currTrial][ENVIRONMENT_DIRECTORY])
            else:
                directory = self.scriptDirectory
                
            os.startfile(directory)
            
        def openAssetBrowser():
            webbrowser.open("https://help.worldviz.com/sightlab/worldviz-asset-browser")

        def _checkEnvFileChanged():
            """Poll the environment file for external modifications (e.g. saved from Inspector)."""
            path = self._env_poll_path
            if not path or not os.path.isfile(path):
                return
            try:
                current_mtime = os.path.getmtime(path)
            except OSError:
                return
            if current_mtime <= self._env_poll_mtime:
                return
            # File was modified externally — update mtime and auto-refresh
            print(f"[AUTO-REFRESH] Environment file changed externally, refreshing: {path}")
            self._env_poll_mtime = current_mtime
            refreshChildren()

        def openEnvironment():
            if not self.trialSettings[self.currTrial][ENVIRONMENT_DIRECTORY] == ".":
                directory = os.path.join(self.scriptDirectory, self.trialSettings[self.currTrial][ENVIRONMENT_DIRECTORY])
            else:
                directory = self.scriptDirectory
                
            path = os.path.join(directory, self.trialSettings[self.currTrial][ENVIRONMENT])

            if DASHBOARD_EMBEDDED_INSPECTOR_HOOK is not None:
                try:
                    DASHBOARD_EMBEDDED_INSPECTOR_HOOK(path)
                except Exception as e:
                    print(f"[Inspector] Embedded hook failed, opening in a separate window instead: {e}")
                    os.startfile(path)
            else:
                os.startfile(path)

            # Start polling this file for external changes (e.g. saved in Inspector)
            self._env_poll_path = os.path.abspath(path)
            try:
                self._env_poll_mtime = os.path.getmtime(self._env_poll_path)
            except OSError:
                self._env_poll_mtime = 0
            if self._env_poll_timer is not None:
                self._env_poll_timer.remove()
            self._env_poll_timer = vizact.ontimer(2, _checkEnvFileChanged)
            
        def onModel3D(replace = True):
            viz.sendEvent(STOP_ADD_ROI_EVENT)
            
            self.trialSettings[self.currTrial][MEDIA_SETUP] = {}
            # Clear REGIONS_OF_INTEREST when switching to 3D mode (3D uses TRIAL_SETUP, not ROIs)
            self.trialSettings[self.currTrial][REGIONS_OF_INTEREST] = {}
            
            if not self.trialSettings[self.currTrial][MODE] == MODEL_3D:
                self.trialSettings[self.currTrial][MODE] = MODEL_3D
                
                self.trialSettings[self.currTrial][ENVIRONMENT_DIRECTORY] = self.environmentDirectory
                
            changeDirectory(self.trialSettings[self.currTrial][ENVIRONMENT_DIRECTORY])
      
            if replace:
                remove360MediaSection()
                enable3DModelSection()
            else:
                populateModel3D()
                
            if self.recordROI is not None:
                self.recordROI.setEnabled(viz.OFF)
            
        def onMedia360(replace = True, reload = True):
            self.trialSettings[self.currTrial][TRIAL_SETUP] = {}
            
            if not self.trialSettings[self.currTrial][MODE] == MEDIA_360:
                self.trialSettings[self.currTrial][MODE] = MEDIA_360

                self.trialSettings[self.currTrial][ENVIRONMENT_DIRECTORY] = self.mediaDirectory
                
            changeDirectory(self.trialSettings[self.currTrial][ENVIRONMENT_DIRECTORY])
            
            if replace:
                remove3DModelSection()
                enable360MediaSection()
            else:
                populateMedia360(reload)
                
#            if self.currTrial == DEFAULT:
#                setDefaultTrials()
                
            if self.recordROI is not None:
                self.recordROI.setEnabled(viz.OFF)
            
        def populateModel3D(newTrial = False):
            self.environmentNodes = self.findNodes(self.trialSettings[self.currTrial][ENVIRONMENT], self.trialSettings[self.currTrial][ENVIRONMENT_DIRECTORY])
            
            self.pageNodes = {}
            
            self.currPage = 1
            
            if int(len(self.environmentNodes) % self.pageLimit) == 0:
                self.totalPages = int(len(self.environmentNodes) / self.pageLimit)
            else:
                self.totalPages = int(len(self.environmentNodes) / self.pageLimit) + 1
            
            self.pageText.label.message(t("Page") + " " + str(self.currPage) + " " + t("of") + " " + str(self.totalPages))
            
            if newTrial:
                self.trialSettings[self.currTrial][TRIAL_SETUP] = {}
                # Clear REGIONS_OF_INTEREST for 3D mode (ROIs are only for 360 media)
                self.trialSettings[self.currTrial][REGIONS_OF_INTEREST] = {}
                
            for node in self.environmentNodes:
                page = str(int((self.environmentNodes.index(node)) / self.pageLimit) + 1)
                if page not in self.pageNodes:
                    self.pageNodes[page] = []
                    
                self.pageNodes[page].append(node)
                
                if newTrial:
                    is_avatar = hasattr(self, 'avatarNodes') and node in self.avatarNodes
                    is_animate = hasattr(self, 'animateNodes') and node in self.animateNodes
                    self.trialSettings[self.currTrial][TRIAL_SETUP][node] = {
                    TARGET: viz.ON,
                    VISIBLE: viz.ON,
                    GRAB: viz.OFF,
                    "AVATAR": is_avatar,
                    "ANIMATE": is_animate,
                    "STATE": 0 if is_animate else 1
                    }

                    if node[-4:] == "_env":
                        self.trialSettings[self.currTrial][TRIAL_SETUP][node] = {
                        TARGET: viz.OFF,
                        VISIBLE: viz.ON,
                        GRAB: viz.OFF,
                        "AVATAR": False,
                        "ANIMATE": False,
                        "STATE": 1
                        }
                    
            if len(self.environmentNodes) == 0:
                self.pageNodes[str(self.currPage)] = ["No child found"]

            refreshChildNodes()
            
            #ROIs
#            self.trialButtonLabels[SEPARATORS].append(self.trialInfoPanel.addSection("Regions of Interest"))
#            
#            for roi in self.regionsOfInterest:
#                self.regionsOfInterest[roi].remove()
#                
#            self.regionsOfInterest = {}
#            
#            if newTrial:
#                populateROI()
#            else:
#                populateROI(True)
                
        def populateMedia360(reload = True, start = True):
            media360GUI = self.trialButtonLabels[TRIAL_SETUP][MEDIA_360_UI]
            
            imageFileTypes = ["jpg", "jpeg", "png", "tiff", "pdf", "raw", "gif", "bmp", "webp", "heif", "heic"]
            videoFileTypes = ["mp4", "mov", "avi", "wmv", "hevc", "flv", "mkv", "ogg", "m4v"]
            
            fileFormat = self.trialSettings[self.currTrial][ENVIRONMENT].split(".")[-1].lower()
            
            if fileFormat in imageFileTypes:
                if MEDIA_TYPE not in self.trialSettings[self.currTrial][MEDIA_SETUP]:
                    media360GUI[IMAGE_RADIO].set(1)
                    self.trialSettings[self.currTrial][MEDIA_SETUP][MEDIA_TYPE] = "image"
                else:
                    if self.trialSettings[self.currTrial][MEDIA_SETUP][MEDIA_TYPE] == "image":
                        media360GUI[IMAGE_RADIO].set(1)
                    else:
                        media360GUI[VIDEO_RADIO].set(1)
                        
            if fileFormat in videoFileTypes:
                if MEDIA_TYPE not in self.trialSettings[self.currTrial][MEDIA_SETUP]:
                    media360GUI[VIDEO_RADIO].set(1)
                    self.trialSettings[self.currTrial][MEDIA_SETUP][MEDIA_TYPE] = "video"
                else:
                    if self.trialSettings[self.currTrial][MEDIA_SETUP][MEDIA_TYPE] == "video":
                        media360GUI[VIDEO_RADIO].set(1)
                    else:
                        media360GUI[IMAGE_RADIO].set(1)
                        
            if MEDIA_FORMAT in self.trialSettings[self.currTrial][MEDIA_SETUP]:
                if self.trialSettings[self.currTrial][MEDIA_SETUP][MEDIA_FORMAT] == "Stereoscopic T/B":
                    media360GUI[STEREO_TB_RADIO].set(1)
                elif self.trialSettings[self.currTrial][MEDIA_SETUP][MEDIA_FORMAT] == "Stereoscopic L/R":
                    media360GUI[STEREO_LR_RADIO].set(1)
                else:
                    media360GUI[MONO_RADIO].set(1)
            else:
                self.trialSettings[self.currTrial][MEDIA_SETUP][MEDIA_FORMAT] = "Stereoscopic T/B"
                media360GUI[STEREO_TB_RADIO].set(1)
                
            if reload:
                self.loadTempEnvironment()
                toggleTransports(viz.OFF)
                
            for roi in self.regionsOfInterest:
                self.regionsOfInterest[roi].remove()
                
            self.regionsOfInterest = {}
            
            if start:
                populateROI()
            else:
                populateROI(True)
            
        def populateROI(start = False):
            def remove360End():
                media360GUI = self.trialButtonLabels[TRIAL_SETUP][MEDIA_360_UI]
                
                if ADD_ROI in media360GUI:
                    self.trialInfoPanel.removeItem(media360GUI[ADD_ROI])
                
                item = self.trialButtonLabels[SEPARATORS][-1]
                self.trialInfoPanel.removeItem(item)
                
                if REGIONS_OF_INTEREST in media360GUI:
                    for item in media360GUI[REGIONS_OF_INTEREST]:
                        self.trialInfoPanel.removeItem(media360GUI[REGIONS_OF_INTEREST][item][0])
                
#                if DONE in self.trialButtonLabels:
#                    self.trialInfoPanel.removeItem(self.trialButtonLabels[DONE])
                
            def add360End():
                media360GUI = self.trialButtonLabels[TRIAL_SETUP][MEDIA_360_UI]
                row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False,border=False)
                row.setMargin(0)
                addROIButton = row.addItem(viz.addButtonLabel(t("Add")))
                
                media360GUI[ADD_ROI] = self.trialInfoPanel.addItem(row)
            
#                self.trialButtonLabels[SEPARATORS].append(self.trialInfoPanel.addSeparator())
                
#                self.trialButtonLabels[DONE] = self.trialInfoPanel.addItem(viz.addButtonLabel('Done'),align=viz.ALIGN_LEFT_CENTER)
                
#                vizact.onbuttonup(self.trialButtonLabels[DONE], trialSetup)
                vizact.onbuttonup(addROIButton, toggleTransports, viz.ON)
            
            def generate_random_color():
                r = random.uniform(0, 1)
                g = random.uniform(0, 1)
                b = random.uniform(0, 1)
                return (r, g, b)
                    
            def refreshColor(item):
                self.regionsOfInterest[item].color(generate_random_color())
                
            def deleteNode(node, name):
                roi = self.regionsOfInterest[name]
                roi.remove()
                self.regionsOfInterest.pop(name)
                self.trialInfoPanel.removeItem(node)
                self.trialSettings[self.currTrial][REGIONS_OF_INTEREST].pop(name)
                
            def changeScale(pos, name):
                customScaleMax = 0.5
                newPos = pos*customScaleMax
                self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][name][1] = newPos
                self.regionsOfInterest[name].remove()
                generateROI(name, new = False)
                
            def changeAlpha(pos, name):
                self.regionsOfInterest[name].alpha(pos)
                self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][name][2] = pos
                
            def changeName(e, name):
                self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][name][4] = e.newText
                
            lastROIShape = 'sphere'  # Default shape
            lastROI = None  # Default to no ROI initially
            
#            def generateROI(item, new = True):
#                radius = 0.2
#                alpha = 0.5
#                color = generate_random_color()
#                pos = self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item][0]
#                
#                if not new:
#                    radius = self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item][1]
#                    alpha = self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item][2]
#                    color = self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item][3]
#                    
#                else:
#                    self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item] = [pos]
#                    self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item].append(radius)
#                    self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item].append(alpha)
#                    self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item].append(color)
#                    self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item].append(item)
#                    
#                newROI = vizshape.addSphere(radius = radius, color=color, alpha = alpha)
#                newROI.disable(viz.INTERSECTION)
#                newROI.disable(viz.SHADOW_CASTING)
#                newROI.disable(viz.SHADOWS)
#                newROI.setPosition(pos)
#                
#                self.regionsOfInterest[item] = newROI

                
            def generateROI(item, new=True):
                    global lastROIShape, lastROI  # Ensure these variables are accessible if not in a class

                    radius = 0.2
#                    size = 0.2  # Default size for cube
                    alpha = 0.5
                    color = generate_random_color()
                    pos = self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item][0]

                    # Initialize lastROIShape if it doesn't exist
                    if not hasattr(self, 'lastROIShape'):
                        self.lastROIShape = 'sphere'

                    if not new:
                        if self.lastROIShape == 'sphere':
                            radius = self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item][1]
                        else:  # Cube case
                            size = self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item][1]
                        alpha = self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item][2]
                        color = self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item][3]
                        # Load 3-axis scale if available (indices 5, 6, 7)
                        roiData = self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item]
                        if len(roiData) >= 8:
                            savedScale = [roiData[5], roiData[6], roiData[7]]
                        else:
                            savedScale = [1.0, 1.0, 1.0]
                    else:
                        self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item] = [pos]
                        if self.lastROIShape == 'sphere':
                            self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item].append(radius)
                        else:  # Cube case
                            self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item].append(size)
                        self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item].append(alpha)
                        self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item].append(color)
                        self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item].append(item)
                        # Add 3-axis scale (default to [1, 1, 1])
                        self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item].append(1.0)  # scaleX
                        self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item].append(1.0)  # scaleY
                        self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item].append(1.0)  # scaleZ

                    # Function to create the ROI
                    def createROI(shape, position):
                        roi = vizshape.addSphere(radius=radius, color=color, alpha=alpha)
#                        if shape == 'sphere':
#                            roi = vizshape.addSphere(radius=radius, color=color, alpha=alpha)
#                        else:  # shape == 'cube'
#                            roi = vizshape.addCube(size=size, color=color, alpha=alpha)

                        roi.disable(viz.INTERSECTION)
                        roi.disable(viz.SHADOW_CASTING)
                        roi.disable(viz.SHADOWS)
#                        roi.disable(viz.LIGHTING)
                        roi.setPosition(position)
                        return roi

                    # Initialize with a sphere or cube based on the last shape
                    self.lastROI = createROI(self.lastROIShape, pos)
                    
                    # Apply saved scale when loading existing ROI
                    if not new and 'savedScale' in dir():
                        self.lastROI.setScale(savedScale)

                    MOVE_SPEED = 0.001
                    SCALE_SPEED = 0.01  # Scale increment per keypress

                    def moveLastROI(direction):
                        if self.lastROI:
                            current_pos = self.lastROI.getPosition()
                            if direction == 'left':
                                self.lastROI.setPosition([current_pos[0] - MOVE_SPEED, current_pos[1], current_pos[2]])
                            elif direction == 'right':
                                self.lastROI.setPosition([current_pos[0] + MOVE_SPEED, current_pos[1], current_pos[2]])
                            elif direction == 'up':
                                self.lastROI.setPosition([current_pos[0], current_pos[1] + MOVE_SPEED, current_pos[2]])
                            elif direction == 'down':
                                self.lastROI.setPosition([current_pos[0], current_pos[1] - MOVE_SPEED, current_pos[2]])
                            elif direction == 'forward':
                                self.lastROI.setPosition([current_pos[0], current_pos[1], current_pos[2] + MOVE_SPEED])
                            elif direction == 'backward':
                                self.lastROI.setPosition([current_pos[0], current_pos[1], current_pos[2] - MOVE_SPEED])
                                
                            if self.lastROI in self.regionsOfInterest.values():
                                itemKey = next((k for k, v in self.regionsOfInterest.items() if v == self.lastROI), None)
                                self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][itemKey][0] = self.lastROI.getPosition()

                    def scaleLastROI(axis, direction):
                        if self.lastROI:
                            current_scale = self.lastROI.getScale()
                            if axis == 'x':
                                self.lastROI.setScale([current_scale[0] + direction * SCALE_SPEED, current_scale[1], current_scale[2]])
                            elif axis == 'y':
                                self.lastROI.setScale([current_scale[0], current_scale[1] + direction * SCALE_SPEED, current_scale[2]])
                            elif axis == 'z':
                                self.lastROI.setScale([current_scale[0], current_scale[1], current_scale[2] + direction * SCALE_SPEED])
                            
                            # Save scale to trialSettings
                            if self.lastROI in self.regionsOfInterest.values():
                                itemKey = next((k for k, v in self.regionsOfInterest.items() if v == self.lastROI), None)
                                if itemKey and len(self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][itemKey]) >= 8:
                                    new_scale = self.lastROI.getScale()
                                    self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][itemKey][5] = new_scale[0]
                                    self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][itemKey][6] = new_scale[1]
                                    self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][itemKey][7] = new_scale[2]

#                    def rotateLastROI(axis, direction):
#                        if self.lastROI:
#                            current_euler = self.lastROI.getEuler()
#                            if axis == 'x':
#                                self.lastROI.setEuler([current_euler[0] + direction * ROTATION_SPEED, current_euler[1], current_euler[2]])
#                            elif axis == 'y':
#                                self.lastROI.setEuler([current_euler[0], current_euler[1] + direction * ROTATION_SPEED, current_euler[2]])
#                            elif axis == 'z':
#                                self.lastROI.setEuler([current_euler[0], current_euler[1], current_euler[2] + direction * ROTATION_SPEED])

#                    def toggleShape():
#                        if self.lastROI:
#                            current_pos = self.lastROI.getPosition()
#                            self.lastROI.remove()  # Remove the existing shape
#                            # Toggle the shape
#                            if self.lastROIShape == 'sphere':
#                                self.lastROI = createROI('cube', current_pos)
#                                self.lastROIShape = 'cube'
#                            else:
#                                self.lastROI = createROI('sphere', current_pos)
#                                self.lastROIShape = 'sphere'

                    # Bind keys to movement actions for the last created ROI
                    vizact.onkeydown('j', moveLastROI, 'left')       # Move left
                    vizact.onkeydown('l', moveLastROI, 'right')      # Move right
                    vizact.onkeydown('i', moveLastROI, 'up')         # Move up
                    vizact.onkeydown('k', moveLastROI, 'down')       # Move down
                    vizact.onkeydown('u', moveLastROI, 'forward')    # Move forward
                    vizact.onkeydown('o', moveLastROI, 'backward')   # Move backward

                    # Bind keys to scale the ROI (3-axis)
                    vizact.onkeydown('f', scaleLastROI, 'x', 1)      # Increase X scale
                    vizact.onkeydown('F', scaleLastROI, 'x', -1)     # Decrease X scale
                    vizact.onkeydown('g', scaleLastROI, 'y', 1)      # Increase Y scale
                    vizact.onkeydown('G', scaleLastROI, 'y', -1)     # Decrease Y scale
                    vizact.onkeydown('h', scaleLastROI, 'z', 1)      # Increase Z scale
                    vizact.onkeydown('H', scaleLastROI, 'z', -1)     # Decrease Z scale

                    self.regionsOfInterest[item] = self.lastROI

            def clearROIs():
                for roi in self.regionsOfInterest:
                    self.regionsOfInterest[roi].remove()
                    
                self.regionsOfInterest = {}
                
            if not start:
                remove360End()
                
            media360GUI = self.trialButtonLabels[TRIAL_SETUP][MEDIA_360_UI]
            media360GUI[REGIONS_OF_INTEREST] = {}
            
            clearROIs()
            
            count = 1
            for item in self.trialSettings[self.currTrial][REGIONS_OF_INTEREST]:
                if len(self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item]) == 1:
                    generateROI(item, new = True)
                else:
                    generateROI(item, new = False)
                
                properties = self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][item]
                pos = properties[0]
                scale = properties[1]
                alpha = properties[2]
                color = properties[3]
                name = properties[4]
                
                row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False,border=False)
                row.setMargin(0)
                
                editName = row.addItem(viz.addTextbox())
                editName.message(name)
                editName.setLength(0.75)
                
                scaleTest = viz.addSlider()
                scaleSlider = row.addItem(scaleTest)
                scaleSlider.setScale(0.5, 1, 1)
                scaleSlider.set(scale*2)
                
                alphaSlider = row.addItem(viz.addSlider())
                alphaSlider.setScale(0.5, 1, 1)
                alphaSlider.set(alpha)
                colorRefresh = row.addItem(viz.addButton())
                colorRefresh.uppicture(os.path.join(ICONS_PATH,'refresh_color.png'))
                
                deleteRow = row.addItem(viz.addButton())
                deleteRow.uppicture(os.path.join(ICONS_PATH,'delete.png'))
                
                labelItem = self.trialInfoPanel.addLabelItem(t("ROI") + " " + str(count), row)
                count += 1
                
                roiName = labelItem.label
                row.setMargin(0)
                
                media360GUI[REGIONS_OF_INTEREST][name] = [labelItem, roiName, editName, scaleSlider, alphaSlider, colorRefresh, deleteRow]
                
                currNode = self.regionsOfInterest[item]
                
                vizact.onbuttondown(colorRefresh, refreshColor, item)
                vizact.onbuttondown(deleteRow, deleteNode, labelItem, item)
                vizact.onslider(scaleSlider, changeScale, item)
                vizact.onslider(alphaSlider, changeAlpha, item)
                vizact.ontextbox(editName, changeName, item)
                
            add360End()
        
        def _applyPreviewAvatarState(nodeName, stateVal):
            """Apply animation state to an avatar or animated node in the GUI preview scene."""
            if self.tempEnvironment is None:
                return
            isAnimate = hasattr(self, 'animateNodes') and nodeName in self.animateNodes
            if hasattr(self, 'avatarNodes') and nodeName in self.avatarNodes:
                try:
                    child = self.tempEnvironment.getChild(nodeName)
                    if child and child.valid():
                        child.state(stateVal)
                except:
                    pass
            elif isAnimate:
                try:
                    child = self.tempEnvironment.getChild(nodeName)
                    if child and child.valid():
                        kick = 1 if int(stateVal) == 0 else 0
                        try:
                            child.setAnimationState(kick)
                        except Exception:
                            pass
                        child.setAnimationState(int(stateVal))
                        loopMode = viz.OFF if nodeName.lower().endswith('_animate_1') else viz.ON
                        child.setAnimationLoopMode(loopMode)
                        child.setAnimationSpeed(1.0)
                except:
                    pass
        
        def onStateBoxChanged(e, slotKey):
            """Handle live avatar state changes from the GUI textbox."""
            pageLabels = self.trialButtonLabels[TRIAL_SETUP][MODEL_3D_UI][CHILD_LIST]
            if slotKey not in pageLabels:
                return
            nodeName = pageLabels[slotKey][4]
            if not nodeName or nodeName == "No child found":
                return
            try:
                stateVal = int(e.newText)
            except (ValueError, TypeError):
                return
            if nodeName in self.trialSettings[self.currTrial][TRIAL_SETUP]:
                self.trialSettings[self.currTrial][TRIAL_SETUP][nodeName]["STATE"] = stateVal
            _applyPreviewAvatarState(nodeName, stateVal)
                        
        def refreshChildNodes(direction = 0):
            # Guard: check if MODEL_3D_UI and CHILD_LIST exist
            if MODEL_3D_UI not in self.trialButtonLabels[TRIAL_SETUP] or CHILD_LIST not in self.trialButtonLabels[TRIAL_SETUP][MODEL_3D_UI]:
                return
                
            prevPage = self.currPage
            
            if direction == 1:
                if self.currPage < self.totalPages:
                    self.currPage += 1
            elif direction == -1:
                if self.currPage > 1:
                    self.currPage -= 1
                
            count = 0
            
            pageLabels = self.trialButtonLabels[TRIAL_SETUP][MODEL_3D_UI][CHILD_LIST]

            for item in pageLabels:
                fixation = pageLabels[item][0]
                visible = pageLabels[item][1]
                grabbable = pageLabels[item][2]
                itemLabel = pageLabels[item][3]
                
                node = pageLabels[item][4]
                stateBox = pageLabels[item][5] if len(pageLabels[item]) > 5 else None
                
                if direction != 0 and node != "":
                    existingAvatar = self.trialSettings[self.currTrial][TRIAL_SETUP].get(node, {}).get("AVATAR", False)
                    existingAnimate = self.trialSettings[self.currTrial][TRIAL_SETUP].get(node, {}).get("ANIMATE", False)
                    try:
                        stateVal = int(stateBox.get()) if stateBox else 1
                    except (ValueError, TypeError):
                        stateVal = 1
                    self.trialSettings[self.currTrial][TRIAL_SETUP][node] = {
                    TARGET: fixation.get(),
                    VISIBLE: visible.get(),
                    GRAB: grabbable.get(),
                    "AVATAR": existingAvatar,
                    "ANIMATE": existingAnimate,
                    "STATE": stateVal
                    }
                
                if count < len(self.pageNodes[str(self.currPage)]):
                    newNode = self.pageNodes[str(self.currPage)][count]
                else:
                    continue
                
                labelLength = 30
                isAvatar = hasattr(self, 'avatarNodes') and newNode in self.avatarNodes
                isAnimate = hasattr(self, 'animateNodes') and newNode in self.animateNodes
                if isAvatar:
                    prefix = "\U0001F9D1 "
                elif isAnimate:
                    prefix = "\U0001F3AC "
                else:
                    prefix = ""
                displayName = prefix + newNode
                if len(displayName) >= labelLength:
                    itemLabel.label.message(displayName[:labelLength] + "...")
                else:
                    itemLabel.label.message(displayName)

                itemLabel.row.margin = 0

                # Show/hide State control based on avatar or animate status
                if stateBox:
                    stateBox.visible(viz.ON if (isAvatar or isAnimate) else viz.OFF)
                
                if newNode in self.trialSettings[self.currTrial][TRIAL_SETUP]:
                    fixation.set(self.trialSettings[self.currTrial][TRIAL_SETUP][newNode][TARGET])
                    visible.set(self.trialSettings[self.currTrial][TRIAL_SETUP][newNode][VISIBLE])
                    grabbable.set(self.trialSettings[self.currTrial][TRIAL_SETUP][newNode][GRAB])
                    defaultState = self.trialSettings[self.currTrial][TRIAL_SETUP][newNode].get("STATE", 0 if isAnimate else 1)
                    if stateBox:
                        stateBox.message(str(defaultState))
                    _applyPreviewAvatarState(newNode, defaultState)
                else:
                    fixation.set(viz.ON)
                    visible.set(viz.ON)
                    grabbable.set(viz.OFF)
                    defaultState = 0 if isAnimate else 1
                    if stateBox:
                        stateBox.message(str(defaultState))
                    _applyPreviewAvatarState(newNode, defaultState)
                    
                    if newNode[-4:] == "_env":
                        fixation.set(viz.OFF)
                    
                pageLabels[item] = [fixation, visible, grabbable, itemLabel, newNode, stateBox]
                
                count += 1
            
            first = True
            count += 1
            while count <= self.pageLimit:
                item = str(count)
                if first:
                    pageLabels[item][3].label.message("-End of Items-")
                    first = False
                else:
                    pageLabels[item][3].label.message("")
                pageLabels[item][4] = ""
                count += 1
                
                pageLabels[item][0].set(0)
                pageLabels[item][1].set(0)
                pageLabels[item][2].set(0)
                if len(pageLabels[item]) > 5 and pageLabels[item][5]:
                    pageLabels[item][5].message('1')
                    pageLabels[item][5].visible(viz.OFF)
            
            self.pageText.label.message(t("Page") + " " + str(self.currPage) + " " + t("of") + " " + str(self.totalPages))
            
            # Update section header to show "Animation" column when avatars or animated nodes are on this page
            hasAnimationOnPage = False
            for item in pageLabels:
                nodeName = pageLabels[item][4]
                if nodeName and nodeName != "":
                    if (hasattr(self, 'avatarNodes') and nodeName in self.avatarNodes) or \
                       (hasattr(self, 'animateNodes') and nodeName in self.animateNodes):
                        hasAnimationOnPage = True
                        break
            if hasattr(self, '_childSectionHeader') and self._childSectionHeader is not None:
                if hasAnimationOnPage:
                    self._childSectionHeader.message(t("Target, Visible, Grabbable, Animation"))
                else:
                    self._childSectionHeader.message(t("Target, Visible, Grabbable"))
                
        def onEnvironmentList(e, manual = None):
            if self.tempEnvironment is not None:
                self.tempEnvironment.remove()
                self.tempEnvironment = None
            
            trialNumber = self.trialButtonLabels[TRIAL_SETUP][TRIALS_UI][TRIAL_LIST]
            self.currTrial = trialNumber.getItems()[trialNumber.getSelection()]
            
            if manual is None:
                environment = e.object.getItem(e.newSel)
                
                if environment == "...":
                    environmentList = self.trialButtonLabels[TRIAL_SETUP][ENVIRONMENT_UI][ENVIRONMENT_LIST]
                    environmentList.clearItems()
                
                    if e.newSel == 0:
                        self.environmentCurrPage -= 1
                    else:
                        self.environmentCurrPage += 1
                        
                    environmentList.addItems(self.environmentPageDict[self.environmentCurrPage])
                    
                    if environmentList.getItems()[0] == "...":
                        environmentList.select(1)
                    else:
                        environmentList.select(0)
                        
                    environment = environmentList.getItems()[environmentList.getSelection()]
                
            else: 
                environment = manual
                selection = self.trialButtonLabels[TRIAL_SETUP][ENVIRONMENT_UI][ENVIRONMENT_LIST].getItems().index(environment)
                self.trialButtonLabels[TRIAL_SETUP][ENVIRONMENT_UI][ENVIRONMENT_LIST].select(selection)
                
                if environment == "...":
                    environmentList = self.trialButtonLabels[TRIAL_SETUP][ENVIRONMENT_UI][ENVIRONMENT_LIST]
                    environmentList.clearItems()
                    
                    self.environmentCurrPage += 1
                        
                    environmentList.addItems(self.environmentPageDict[self.environmentCurrPage])
                    
                    #print("on list manual: ", environmentList.getItems())
#                    if environmentList.getItems()[0] == "...":
#                        environmentList.select(1)
#                    else:
#                        environmentList.select(0)
                        
                    return
            
            self.trialSettings[self.currTrial][ENVIRONMENT] = environment
            
            if self.trialSettings[self.currTrial][MODE] == MEDIA_360:
                self.loadedConfig = False
                populateMedia360()
            else:
                populateModel3D(newTrial = True)
            
        def trialSetup():
            if self.trialSettings[DEFAULT][MODE] == MODEL_3D:
                getTrialSettings()
                
            else:
                if MEDIA_TYPE not in self.trialSettings[DEFAULT][MEDIA_SETUP]:
                    self.trialSettings[DEFAULT][MEDIA_SETUP][MEDIA_TYPE] = "video"
                    
                if MEDIA_FORMAT not in self.trialSettings[DEFAULT][MEDIA_SETUP]:
                    self.trialSettings[DEFAULT][MEDIA_SETUP][MEDIA_FORMAT] = "Stereoscopic T/B"
                                    
            toggleTransports(manual = False)
            
            self.refreshExperimentSetup()
            
        def builtIn():
            directory = SIGHTLAB_ENVIRONMENT_RESOURCES if self.trialSettings[self.currTrial][MODE] == MODEL_3D else SIGHTLAB_MEDIA_RESOURCES
            if self.currTrial == DEFAULT:
                self.environmentDirectory = directory
                self.mediaDirectory = SIGHTLAB_MEDIA_RESOURCES
                
            changeDirectory(directory, True)
            
        def changeDirectory(path = None, refresh = False):
            if path == None:
                if not self.trialSettings[self.currTrial][ENVIRONMENT_DIRECTORY] == "." and not os.path.normpath(self.trialSettings[self.currTrial][ENVIRONMENT_DIRECTORY]) in [SIGHTLAB_ENVIRONMENT_RESOURCES, SIGHTLAB_MEDIA_RESOURCES]:
                    directory = os.path.join(self.scriptDirectory, self.trialSettings[self.currTrial][ENVIRONMENT_DIRECTORY])
                else:
                    directory = self.scriptDirectory
                
                path = vizinput.directory(prompt='Select a directory within project folder',directory=directory)
                
                if path == "":
                    return
                
                while not path.startswith(self.scriptDirectory) or path == "":
                    path = vizinput.directory(prompt='Directory has to be within project folder',directory=directory)
                    
                    if path == "":
                        return   
                
            if os.path.normpath(path) in [SIGHTLAB_ENVIRONMENT_RESOURCES, SIGHTLAB_MEDIA_RESOURCES]:
                if self.trialSettings[self.currTrial][MODE] == MODEL_3D:
                    self.trialSettings[self.currTrial][ENVIRONMENT_DIRECTORY] = os.path.normpath(SIGHTLAB_ENVIRONMENT_RESOURCES)
                else:
                    self.trialSettings[self.currTrial][ENVIRONMENT_DIRECTORY] = os.path.normpath(SIGHTLAB_MEDIA_RESOURCES)

                self.trialButtonLabels[TRIAL_SETUP][ENVIRONMENT_UI][DIRECTORY_LABEL].message("BUILT-IN")

            else:
                directoryName = self.normalizePath(path)
                
                self.trialButtonLabels[TRIAL_SETUP][ENVIRONMENT_UI][DIRECTORY_LABEL].message(directoryName)
                self.trialSettings[self.currTrial][ENVIRONMENT_DIRECTORY] = self.relativePath(path)

            refreshEnvironmentList()
            
            if refresh:
                if self.trialSettings[self.currTrial][MODE] == MODEL_3D:
                    populateModel3D(newTrial = True)
                else:
                    populateMedia360()
            
        def toggleAll(index, state):
            pageLabels = self.trialButtonLabels[TRIAL_SETUP][MODEL_3D_UI][CHILD_LIST]
                
            for item in self.trialSettings[self.currTrial][TRIAL_SETUP]:
                self.trialSettings[self.currTrial][TRIAL_SETUP][item][index] = state
            
            refreshChildNodes()
            
        def toggleTransports(manual = None):
            if manual is None:
                manual = viz.TOGGLE
            
            if "Desktop" in VIZCONNECT_CONFIG:
                vizconnect.getRawTracker("head_tracker").setEnabled(manual)
            else:                
                if manual == viz.TOGGLE:
                    self.transportState = not self.transportState
                else: 
                    self.transportState = manual
                
                items = [self.tempAvatar, self.tempEnvironment, self.tempText, self.tempRHand, self.tempLHand]
                
                for item in items:
                    if item is not None:
                        item.renderToMain = self.transportState
                        
                        if self.transportState:
                            item.renderToAllWindows()
                        else:
                            item.renderOnlyToWindows([self.gazePointWindow])
                
            if self.trialSettings[self.currTrial][MODE] == MODEL_3D:
                vizconnect.getDisplay('main_display').setParent(vizconnect.getAvatar('main_avatar').getAttachmentPoint('head'))
                vizconnect.getTransport(name='main_transport').setEnabled(manual)
                
                viz.sendEvent(STOP_ADD_ROI_EVENT)
                
            else:
                vizconnect.getTransport(name='main_transport').setEnabled(viz.OFF)
                
                vizconnect.getDisplay('main_display').setParent(vizconnect.getTracker('merged'))
                
                if self.recordROI is None:
                    self.recordROI = vizact.onkeydown("1", addNewROI)
                self.recordROI.setEnabled(manual)
                
                if manual:
                    viz.sendEvent(ADD_ROI_EVENT)
                else:
                    viz.sendEvent(STOP_ADD_ROI_EVENT)
                
                if self.gazePointObject is not None:
                    self.gazePointObject.visible(self.updateGaze.getEnabled())
                
        def addNewROI():
            if len(self.trialSettings[self.currTrial][REGIONS_OF_INTEREST]) < 50:
                name = "region_" + str(len(self.trialSettings[self.currTrial][REGIONS_OF_INTEREST]) + 1)
                self.trialSettings[self.currTrial][REGIONS_OF_INTEREST][name] = [self.gazePointObject.getPosition()]
                
                populateROI()
            else:
                vizinput.message("Limited to 50 ROIs")
            
        if getSettings is None:
            if button:
                #self.disableSceneInfo()
                
                enableTrialInfo()
                
                if self.trialSettings[DEFAULT][MODE] == MEDIA_360:
                    enable360MediaSection()
                else:
                    enable3DModelSection()
                    
                self.modifyFlag = True
                                
                vizact.onbuttonup(self.trialButtonLabels[TRIAL_SETUP][ENVIRONMENT_UI][CHOOSE_DIRECTORY], changeDirectory, None, True)
                vizact.onbuttonup(self.trialButtonLabels[TRIAL_SETUP][ENVIRONMENT_UI][BUILT_IN], builtIn)
            else:
                if self.transportToggleAction is None:
                    self.transportToggleAction = vizact.onkeydown(viz.KEY_SHIFT_L, toggleTransports)
        else:
            if not self.clientMode:
                trialSetup()
                    
    def loadTempAvatar(self, e = None):
        if self.resourceLists is not None and len(self.resourceLists[AVATAR_HEAD]) > 0 and not self.serverMode:
            
            if self.tempText is not None:
                self.tempText.removeParent(self.tempAvatar)
                
            if self.tempAvatar is not None:
                self.tempAvatar.remove()
                self.tempAvatar = None
                
            if self.tempLHand is not None:
                self.tempLHand.remove()
                self.tempLHand = None
                
            if self.tempRHand is not None:
                self.tempRHand.remove()
                self.tempRHand = None
                
            if e is not None and self.clientMode and self.buttonLabels[AUTO_ASSIGN].get():
                if not "GlowManAuto" in self.buttonLabels[AVATAR_HEAD].getItems()[self.buttonLabels[AVATAR_HEAD].getSelection()]:
                    self.buttonLabels[AUTO_ASSIGN].set(0)
                else:
                    self.buttonLabels[AUTO_ASSIGN].set(1)
                    
                self.trialSettings[DEFAULT][AUTO_ASSIGN] = self.buttonLabels[AUTO_ASSIGN].get()
            
            self.tempAvatar = vizfx.addAvatar(AVATAR_HEAD_RESOURCE_PATH + "/" + self.buttonLabels[AVATAR_HEAD].getItems()[self.buttonLabels[AVATAR_HEAD].getSelection()])
            eyeOpenMorph = vizact.morphTo(2,1,time=0.2)
            eyeCloseMorph = vizact.morphTo(2,0,time=0.2)
            blinkSequence = vizact.sequence(eyeOpenMorph, eyeCloseMorph)
            
            if self.clientMode:
                if self.tempText is None:
                    self.tempText = viz.addText(self.clientID if self.buttonLabels[FIRST_NAME].get() == "" else self.buttonLabels[FIRST_NAME].get())
                    self.tempText.alignment(viz.ALIGN_CENTER_BOTTOM)
                    self.tempText.setBackdrop(viz.BACKDROP_BOX)
                    self.tempText.setBackdropAlpha(0.4)
                    self.tempText.resolution(1)
                    self.tempText.disable(viz.LIGHTING)
                    
                    self.tempText.visible(self.buttonLabels[SHOW_NAME].get())
                    
                #if "Desktop" in VIZCONNECT_CONFIG:
                self.tempText.setParent(self.tempAvatar)
                
                self.tempText.setScale([0.07, 0.07, 0.07])
                
                if "Desktop" in VIZCONNECT_CONFIG:
                    self.tempText.setEuler(160, 0, 0)
                    self.tempText.setPosition(0, 0.2, -0.2)
                else:
                    self.tempText.setEuler(170, 0, 0)
                    self.tempText.setPosition(0, 0.23, -0.2)
                
                
            if self.clientMode and self.buttonLabels[AUTO_ASSIGN].get():
                self.tempAvatar.color(self.clientColor)
                
            self.tempAvatarBlink = vizact.ontimer(random.uniform(2, 5), self.tempAvatar.addAction, blinkSequence)
            buffer = 0
            
            if "Desktop" in VIZCONNECT_CONFIG:
                self.tempAvatar.setEuler(180, 0, 0)
            else:
                self.tempAvatar.setEuler(192, 0, 0)

            if self.clientMode:
                buffer = 0.15
                self.tempAvatar.setPosition(buffer, 1.9, 0.5)
                self.tempAvatar.setScale(1.5, 1.5, 1.5)
                
                if "Desktop" in VIZCONNECT_CONFIG:
                    self.tempAvatar.lookAt(viz.MainView.getPosition())
            
            else:
                buffer = 0
                self.tempAvatar.setPosition(buffer, 1.8, 0.5)
                
            
            self.tempLHand = vizfx.addChild(AVATAR_HANDS_RESOURCE_PATH + "/" + self.buttonLabels[AVATAR_LEFT_HAND].getItems()[self.buttonLabels[AVATAR_LEFT_HAND].getSelection()])
            self.tempLHand.setPosition(0.2 + buffer, 1.6, 0.5)
            self.tempLHand.setEuler(200, 60, 0)
            self.tempLHand.setScale(1.5, 1.5, 1.5)
            
            self.tempRHand = vizfx.addChild(AVATAR_HANDS_RESOURCE_PATH + "/" + self.buttonLabels[AVATAR_RIGHT_HAND].getItems()[self.buttonLabels[AVATAR_RIGHT_HAND].getSelection()])
            self.tempRHand.setPosition(-0.2 + buffer, 1.6, 0.5)
            self.tempRHand.setEuler(180, 45, 0)
            self.tempRHand.setScale(1.7, 1.7, 1.7)
            
            # Define the up and down movement for the left hand (small, slow movement)
            moveUpLHand = vizact.moveTo([0.2 + buffer, 1.605, 0.5], time=2.5)
            moveDownLHand = vizact.moveTo([0.2 + buffer, 1.595, 0.5], time=2.5)
            lHandSequence = vizact.sequence([moveUpLHand, moveDownLHand])

            # Define the up and down movement for the right hand (small, slow movement)
            moveUpRHand = vizact.moveTo([-0.2 + buffer, 1.605, 0.5], time=2.5)
            moveDownRHand = vizact.moveTo([-0.2 + buffer, 1.595, 0.5], time=2.5)
            rHandSequence = vizact.sequence([moveUpRHand, moveDownRHand])

            # Use vizact.onupdate with a loop to repeat the sequence indefinitely
            lHandRepeat = vizact.onupdate(0, self.tempLHand.addAction, lHandSequence)
            rHandRepeat = vizact.onupdate(0, self.tempRHand.addAction, rHandSequence)
            
        for item in [self.tempAvatar, self.tempRHand, self.tempLHand]:
            if item is not None:
                item.renderToMain = False
#                item.renderOnlyToWindows([self.gazePointWindow])
                item.setParent(self.avatarGroup)

        if not self.clientMode and not self.serverMode:
            self.tempAvatar.visible(self.buttonLabels[SHOW_AVATAR].get())
            self.tempLHand.visible(self.buttonLabels[SHOW_AVATAR].get())
            self.tempRHand.visible(self.buttonLabels[SHOW_AVATAR].get())

    def _detect_skeleton_type(self, avatar):
        """
        Detect skeleton type by checking for specific bone and node names.
        Returns skeleton type as string: 'wolf3d', 'mixamo', 'reallusion', 'unreal_reallusion', 'complete_characters', or None
        """
        try:
            bone_list = avatar.getBoneList()
        except AttributeError:
            return 'complete_characters'  # Default fallback
        
        bone_map = {bone.getName(): bone for bone in bone_list}
        
        # Check node names for Wolf3D detection (specific ReadyPlayerMe variant)
        try:
            node_names = avatar.getNodeNames()
            has_wolf3d = any('Wolf3D_' in name for name in node_names)
        except:
            has_wolf3d = False
        
        # Check for Wolf3D first (specific ReadyPlayerMe variant that needs different rotation)
        if has_wolf3d:
            return 'wolf3d'
        # Check for Mixamo/ReadyPlayerMe (Hips) - most RPM models use same rotation as Mixamo
        elif 'Hips' in bone_map:
            return 'mixamo'
        # Check for Reallusion Character Creator (Hip)
        elif 'Hip' in bone_map or 'CC_Base_Waist' in bone_map:
            return 'reallusion'
        # Check for Unreal Reallusion (neck_01)
        elif 'neck_01' in bone_map:
            return 'unreal_reallusion'
        # Check for Complete Characters (Bip01 Pelvis)
        elif 'Bip01 Pelvis' in bone_map:
            return 'complete_characters'
        
        return None

    def loadFullBodyAvatar(self, e=None):
        """Load and display the full body avatar in the GUI preview."""
        if self.tempFullBodyAvatar is not None:
            self.tempFullBodyAvatar.remove()
            
        if not len(self.resourceLists[FULL_BODY_AVATARS]) > 0:
            return
        
        fullBodyAvatarFile = os.path.join(FULL_BODY_AVATAR_RESOURCE_PATH, self.buttonLabels[FULL_BODY_AVATARS].getItems()[self.buttonLabels[FULL_BODY_AVATARS].getSelection()])
        
        self.tempFullBodyAvatar = vizfx.addAvatar(fullBodyAvatarFile) 
        self.tempFullBodyAvatar.setPosition([0,0.8,1.2])
        
        # Detect skeleton type - most avatars need 180 rotation
        # Only Wolf3D and Reallusion avatars face the correct direction without rotation
        skeleton_type = self._detect_skeleton_type(self.tempFullBodyAvatar)
        if skeleton_type in ['wolf3d', 'reallusion']:
            self.tempFullBodyAvatar.setEuler([0,0,0])
        else:
            # Complete Characters, Mixamo, most ReadyPlayerMe, and others need 180 rotation
            self.tempFullBodyAvatar.setEuler([180,0,0])
        
        self.tempFullBodyAvatar.state(1)
        
        self.tempFullBodyAvatar.disable(viz.LIGHTING)
        
        # Respect the show avatar toggle state
        if SHOW_AVATAR in self.buttonLabels and self.buttonLabels[SHOW_AVATAR] is not None:
            self.tempFullBodyAvatar.visible(self.buttonLabels[SHOW_AVATAR].get())
        
        # Set global variable for vizconnect to pick up
        viz.custom_avatar_path = fullBodyAvatarFile
        
        # Update vizconnect config list to use full body configs
        global VIZCONNECT_CONFIG_LIST, FULL_BODY_VIZCONNECT_CONFIG_LIST
        VIZCONNECT_CONFIG_LIST = FULL_BODY_VIZCONNECT_CONFIG_LIST.copy()
        self.vizconnectConfigList = VIZCONNECT_CONFIG_LIST.copy()
        self.vizconnectConfigListArg = VIZCONNECT_CONFIG_LIST.copy()

    def launch_tool(self, exe_path, tool_name):
        """
        Launch an external tool/application.
        
        Args:
            exe_path (str): Path to the executable to launch
            tool_name (str): Name of the tool (for error messages)
        """
        import subprocess
        if not os.path.exists(exe_path):
            print(f"Error: {tool_name} not found at {exe_path}")
            return
        try:
            subprocess.Popen([exe_path], shell=False)
            print(f"Launched {tool_name}")
        except Exception as e:
            print(f"Error launching {tool_name}: {e}")

    def loadTempEnvironment(self, path = None, default = False, mode = MODEL_3D):
        if self.tempEnvironment is not None:
            self.tempEnvironment.remove()
            self.tempEnvironment = None
            
        if self.tempMedia is not None:
            self.tempMedia.remove()
            self.tempMedia = None
        
        if self.mediaToggle is not None:
            self.mediaToggle.setEnabled(viz.OFF)
        
        # --- Fast Load Mode ---
        # When fastLoad is set, skip loading the GUI-selected environment preview.
        # fastLoad=False: normal behavior (load selected environment)
        # fastLoad=True: always use default whiteroom
        # fastLoad="path/to/model.osgb": load that 3D model as preview
        # fastLoad="path/to/image.jpg": display image on a view-relative quad
        _fastLoad = getattr(self, 'fastLoad', False)
        if _fastLoad is not False and not default:
            if _fastLoad is True:
                # Redirect to default/whiteroom
                default = True
            elif isinstance(_fastLoad, str):
                _fl_ext = os.path.splitext(_fastLoad)[1].lower()
                _IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.webp', '.heif', '.heic'}
                if _fl_ext in _IMAGE_EXTENSIONS:
                    # Load image on a view-relative full-screen quad
                    _fl_tex = viz.addTexture(_fastLoad)
                    self.tempEnvironment = viz.addTexQuad(pos=[0, 0, 3], texture=_fl_tex)
                    self.tempEnvironment.setReferenceFrame(viz.RF_VIEW)
                    self.tempEnvironment.disable(viz.LIGHTING)
                    self.tempEnvironment.disable(viz.DEPTH_TEST)
                    self.tempEnvironment.disable(viz.INTERSECTION)
                    self.tempEnvironment.drawOrder(101)
                    self.tempEnvironment.setScale([8, 4.5, 1])
                else:
                    # Load as 3D model
                    try:
                        self.tempEnvironment = vizfx.addChild(_fastLoad)
                    except:
                        self.tempEnvironment = None
                
                if self.tempEnvironment is None:
                    self.loadTempEnvironment(default=True)
                else:
                    vizconnect.getDisplay('main_display').setParent(
                        vizconnect.getAvatar('main_avatar').getAttachmentPoint('head'))
                return
          
        if default:
            if not self.clientMode:
                self.tempEnvironment = vizfx.addChild(os.path.join(SIGHTLAB_TEMP_ENVIRONMENT_RESOURCES, 'whiteroom.osgb'))
            else:
                self.tempEnvironment = vizfx.addChild(os.path.join(SIGHTLAB_TEMP_ENVIRONMENT_RESOURCES, 'waiting_room.osgb'))
            
            if not "Desktop" in VIZCONNECT_CONFIG and self.clientMode:
                self.tempEnvironment.renderToMain = False
                self.tempEnvironment.renderOnlyToWindows([self.gazePointWindow])
                self.tempEnvironment.setParent(self.avatarGroup)
                
                for bgs in self.tempEnvironment.getNodeNames():
                    if "background" in bgs:
                        self.tempEnvironment.getChild(bgs).setParent(self.avatarGroup)
                
            vizconnect.getDisplay('main_display').setParent(vizconnect.getAvatar('main_avatar').getAttachmentPoint('head'))
            return
            
        mode = self.trialSettings[self.currTrial][MODE]
        if mode == MODEL_3D:
            if path is not None and not "No items found" in path:
                try:
                    self.tempEnvironment = vizfx.addChild(path)
                    viz.MainView.getHeadLight().disable()
                except:
                    self.tempEnvironment = None
            else:
                self.tempEnvironment = None
                
            vizconnect.getDisplay('main_display').setParent(vizconnect.getAvatar('main_avatar').getAttachmentPoint('head'))
                
        elif mode == MEDIA_360:
            trial = self.currTrial
            environmentPath = os.path.join(self.scriptDirectory, self.trialSettings[trial][ENVIRONMENT_DIRECTORY], self.trialSettings[trial][ENVIRONMENT])
        
            try:
                if self.trialSettings[trial][MEDIA_SETUP][MEDIA_FORMAT] == "Monoscopic":
                    self.tempEnvironment = panorama_utils.MonoSphere(self.trialSettings[trial][MEDIA_SETUP][MEDIA_TYPE])
                elif self.trialSettings[trial][MEDIA_SETUP][MEDIA_FORMAT] == "Stereoscopic T/B":
                    self.tempEnvironment = panorama_utils.StereoSphere(self.trialSettings[trial][MEDIA_SETUP][MEDIA_TYPE])
                elif self.trialSettings[trial][MEDIA_SETUP][MEDIA_FORMAT] == "Stereoscopic L/R":
                    self.tempEnvironment = panorama_utils.Stereo180Sphere(self.trialSettings[trial][MEDIA_SETUP][MEDIA_TYPE])
                
                if not "No items found" in environmentPath:
                    self.tempMedia, _ext = panorama_utils.make_video(environmentPath)
                    self.tempMedia = extract_audio.attach(environmentPath, self.tempMedia, _ext)
                    self.tempMedia.loop()
                    self.tempMedia.pause()

                    self.playBackState = False

                    self.tempEnvironment.texture(panorama_utils.get_texture(self.tempMedia))
                    
                    vizconnect.getDisplay('main_display').setParent(vizconnect.getTracker('merged'))
                    
                    self._envLink = viz.link(viz.MainView, self.tempEnvironment, mask=viz.LINK_POS)
                else:
                    self.tempEnvironment = None
                    self.tempMedia = None
            except:
                self.tempEnvironment = None
            
            viz.MainView.getHeadLight().enable()
            transportLink = vizconnect.getTransport(name='main_transport')
            transportLink.setEnabled(viz.OFF)
            
#            self.playbackSlider = viz.addProgressBar("0.0")
#            self.playbackSlider.setPosition(0.5, 0.1)
            
            def toggleMediaPlayback():
                if self.playBackState:
                    self.tempMedia.pause()
                    self.playBackState = False
                else:
                    self.tempMedia.play()
                    self.playBackState = True
                
            self.mediaToggle = vizact.onkeydown(CONTINUE_EVENT_KEY, toggleMediaPlayback)
            
        if self.tempEnvironment is None:
            self.loadTempEnvironment(default = True)
#            toggleTransports(viz.OFF)
        else:
            if not "Desktop" in VIZCONNECT_CONFIG:
                self.tempEnvironment.renderToMain = False
                self.tempEnvironment.renderOnlyToWindows([self.gazePointWindow])
                
                if self.clientMode:
                    self.tempEnvironment.setParent(self.avatarGroup)
            
        transportNode = vizconnect.getTransport(name='main_transport').getNode3d()
        
        transportNode.setPosition([0,0,0])
        transportNode.setEuler([0,0,0])
    
    def windowSizeCheck(self):
        """
        Adjust window scaling and field of view based on display size.
        
        Automatically adapts GUI scaling and camera FOV to accommodate different
        monitor resolutions and sizes. Updates global scaling factors used throughout
        the application.
        
        Returns:
            None. Updates SCALE_FACTOR, WINDOW_SIZE, proportionFactor, WINDOW_FOV globals
        """
        global SCALE_FACTOR, WINDOW_SIZE, proportionFactor, WINDOW_FOV
        
        # Skip all window resizing/rescaling for projection (CAVE) configs. They manage
        # their own per-wall windows and fullscreen span; this method would fight them.
        if "Projection" in VIZCONNECT_CONFIG:
            return
        
        if"Desktop" in VIZCONNECT_CONFIG:
            viz.MainWindow.fov(WINDOW_FOV)
            
        if not viz.MainWindow.getSize(mode = viz.WINDOW_PIXELS) == self.windowSize:
            WINDOW_SIZE = viz.MainWindow.getSize(mode = viz.WINDOW_PIXELS)
            
            if WINDOW_SIZE[0] < WINDOW_X_SIZE*0.4:
                viz.window.setSize(WINDOW_X_SIZE*0.4, WINDOW_SIZE[1])
                WINDOW_SIZE[0] = WINDOW_X_SIZE*0.4
                
            if WINDOW_SIZE[1] < WINDOW_Y_SIZE*0.5:
                viz.window.setSize(WINDOW_SIZE[0], WINDOW_Y_SIZE*0.5)
                WINDOW_SIZE[1] = WINDOW_X_SIZE*0.5

            SCALE_FACTOR = viz.window.getSize()[1]/900
            
            if self.sceneInfoPanel is not None:
                self.sceneInfoPanel.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)
            if self.trialInfoPanel is not None:
                self.trialInfoPanel.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)
            if getattr(self, 'continuePanel', None) is not None:
                baseScale = getattr(self, '_continueBaseScale', 1.25)
                self.continuePanel.setScale(baseScale * SCALE_FACTOR, baseScale * SCALE_FACTOR)
                if getattr(self, 'continueLink', None) is not None:
                    baseOffset = getattr(self, '_continueBaseOffset', (-50, 50, 0))
                    self.continueLink.setOffset((baseOffset[0] * SCALE_FACTOR, baseOffset[1] * SCALE_FACTOR, 0))
            
            self.windowSize = WINDOW_SIZE
            
    def updateGazeObject(self):
        self.eyeTracker = vizconnect.getTracker('eye_tracker').getRaw()
        gazeMat = self.eyeTracker.getMatrix()
        gazeMat.postMult(viz.MainView.getMatrix())
        line = gazeMat.getLineForward(1000)
        info = viz.intersect(line.begin, line.end)
        
        if info.valid and self.gazePointObject is not None:
            self.gazePointObject.setPosition(info.point)
            
        self.windowSizeCheck()
        
    def findNodes(self, environment, reldirectory):
        if not reldirectory == ".":
            directory = os.path.abspath(os.path.join(self.scriptDirectory, reldirectory))
        else:
            directory = self.scriptDirectory
        
        if environment is None:
            self.loadTempEnvironment(default = True)
        else:
            self.loadTempEnvironment(os.path.join(directory, environment))
                
        if self.tempEnvironment is None:
            return []
        
        self.avatarNodes = set()
        
        environmentNodes = []
        transformNodes = self.tempEnvironment.getNodeNames(flags = viz.TYPE_TRANSFORM)
        lightNodes = self.tempEnvironment.getNodeNames(flags = viz.TYPE_LIGHT)
        
        for node in self.tempEnvironment.getNodeNames(flags = viz.TYPE_GROUP):
            if not node in transformNodes and node not in lightNodes and not node in ["__VIZARD_NODE__"] and not SIGHTLAB_START_POINT in node and not node[-4:] in ["osgb", "OSGB", "_env"]:
                environmentNodes.append(node)
        
        # Detect avatar nodes: check .cfg extensions and Skeleton children
        # Only check already-filtered environmentNodes to avoid interfering 
        # with external reference (ProxyNode) loading
        avatarCandidates = set()
        
        for nodeName in environmentNodes:
            # .cfg files are definitively avatars
            if nodeName.lower().endswith('.cfg'):
                avatarCandidates.add(nodeName)
                continue
            # Skip nodes that look like external reference file names
            if nodeName.lower().endswith(('.osgb', '.osg', '.osgt', '.ive', '.flt', '.fbx', '.glb', '.gltf')):
                continue
            # Check for Skeleton child (avatar indicator)
            try:
                child = self.tempEnvironment.getChild(nodeName)
                if child and child.valid() and hasattr(child, 'getChild'):
                    skelChild = child.getChild('Skeleton')
                    if skelChild and skelChild.valid():
                        avatarCandidates.add(nodeName)
            except:
                pass
        
        # Also check for .cfg nodes that may not be in environmentNodes
        for nodeName in self.tempEnvironment.getNodeNames():
            if nodeName.lower().endswith('.cfg'):
                avatarCandidates.add(nodeName)
                if nodeName not in environmentNodes:
                    environmentNodes.append(nodeName)
        
        for avatarName in avatarCandidates:
            self.avatarNodes.add(avatarName)

        # Detect animated (non-avatar) nodes: _animate/_animate_1 suffix or getNumFrames() > 0
        # Only check already-filtered environmentNodes to avoid interfering
        # with external reference (ProxyNode) loading
        if not hasattr(self, 'animateNodes'):
            self.animateNodes = set()
        self.animateNodes.clear()
        for nodeName in environmentNodes:
            if nodeName in self.avatarNodes:
                continue
            if nodeName.lower().endswith('_animate') or nodeName.lower().endswith('_animate_1'):
                self.animateNodes.add(nodeName)
            elif not nodeName.lower().endswith(('.osgb', '.osg', '.osgt', '.ive', '.flt', '.fbx', '.glb', '.gltf')):
                try:
                    childObj = self.tempEnvironment.getChild(nodeName)
                    if childObj and childObj.valid():
                        if childObj.getNumFrames() > 0:
                            self.animateNodes.add(nodeName)
                except:
                    pass

        return environmentNodes

    def participantInfo(self):
        """
        Display participant information input dialog.
        
        Creates a modal dialog for entering participant details before experiment starts.
        Collects participant ID and up to two additional custom info fields.
        Input is validated and stored in self.participantData.
        
        Returns:
            None. Waits for user input and updates self.participantData dictionary
        """
        #Add an InfoPanel with a title bar
        title = t('Participant Information')
        
        if self.serverMode:
            title = t('Experiment Information')
        
        participantInfoPanel = vizinfo.InfoPanel('',title=title, window=self.guiWindow, align=viz.ALIGN_LEFT_TOP, icon=False)
        participantInfoPanel.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)
        
        if not self.serverMode:
            #Add name and ID fields
            textbox_last = participantInfoPanel.addLabelItem(PARTICIPANT_INFO1,viz.addTextbox())
            textbox_first = participantInfoPanel.addLabelItem(PARTICIPANT_INFO2,viz.addTextbox())
            
            if not self.demoMode:
                textbox_id = participantInfoPanel.addLabelItem(t('ID'),viz.addTextbox())
            else:
                textbox_id = participantInfoPanel.addLabelItem(t('ID'),viz.addText("SIGHTLAB_DEMO"))
        else:
            textbox_id = participantInfoPanel.addLabelItem(t('Session ID'),viz.addTextbox())

        participantInfoPanel.addSeparator(padding=(20,20))
        
        #Add submit button aligned to the right and wait until it's pressed
        submitButton = participantInfoPanel.addItem(viz.addButtonLabel(t('Submit')),align=viz.ALIGN_RIGHT_CENTER)
        submitButton.setLength(0.5)
        
        yield viztask.waitButtonUp(submitButton)
                
        participantData = {
            ID: "",
            PARTICIPANT_INFO1: "",
            PARTICIPANT_INFO2: ""
        }
        
        if not self.serverMode:
            participantData[PARTICIPANT_INFO2] = textbox_last.get()
            participantData[PARTICIPANT_INFO1] = textbox_first.get()
            
        if not self.demoMode:
            participantData[ID] = textbox_id.get()
        else:
            participantData[ID] = "SIGHTLAB_DEMO"
            
        participantInfoPanel.remove()
        
        # Return participant data
        viztask.returnValue(participantData)
        
    def setSettings(self):
        """
        Collect and save all settings from GUI controls to configuration.
        
        Reads current values from all GUI input elements (textboxes, checkboxes,
        dropdowns, etc.) and stores them in self.trialSettings[DEFAULT].
        Handles different settings for server/client modes.
        
        Returns:
            None. Updates self.trialSettings dictionary
        """
        if not self.clientMode:
            self.trialSettings[DEFAULT][SCREEN_RECORD] = self.buttonLabels[SCREEN_RECORD].get()
            self.trialSettings[DEFAULT][BARCHART] = self.buttonLabels[BARCHART].get()
            self.trialSettings[DEFAULT][BIOPAC] = self.buttonLabels[BIOPAC].get()
            
            # Start/End text are already stored directly in trialSettings by button callbacks
            
            self.trialSettings[DEFAULT][DWELL_TIME] = self.buttonLabels[DWELL_TIME].get()
            self.trialSettings[DEFAULT][DISPERSION_THRESHOLD] = self.buttonLabels[DISPERSION_THRESHOLD].get()
            self.trialSettings[DEFAULT][DURATION_THRESHOLD] = self.buttonLabels[DURATION_THRESHOLD].get()
            self.trialSettings[DEFAULT][NOISE_REDUCTION] = self.buttonLabels[NOISE_REDUCTION].get()
        
        if not self.serverMode:
            self.trialSettings[DEFAULT][AVATAR_HEAD] = self.buttonLabels[AVATAR_HEAD].getItems()[self.buttonLabels[AVATAR_HEAD].getSelection()]
            self.trialSettings[DEFAULT][AVATAR_RIGHT_HAND] = self.buttonLabels[AVATAR_RIGHT_HAND].getItems()[self.buttonLabels[AVATAR_RIGHT_HAND].getSelection()]
            self.trialSettings[DEFAULT][AVATAR_LEFT_HAND] = self.buttonLabels[AVATAR_LEFT_HAND].getItems()[self.buttonLabels[AVATAR_LEFT_HAND].getSelection()]
            
            # Full body avatar settings
            self.trialSettings[DEFAULT][FULL_BODY_TOGGLE] = self.buttonLabels[FULL_BODY_TOGGLE].get()
            
            # Seated mode setting
            self.trialSettings[DEFAULT][SEATED_MODE] = self.buttonLabels[SEATED_MODE].get()
            
            # Show avatar toggle
            if SHOW_AVATAR in self.buttonLabels and self.buttonLabels[SHOW_AVATAR] is not None:
                self.trialSettings[DEFAULT][SHOW_AVATAR] = self.buttonLabels[SHOW_AVATAR].get()
            
            if len(self.resourceLists[FULL_BODY_AVATARS]) > 0:
                self.trialSettings[DEFAULT][FULL_BODY_AVATARS] = self.buttonLabels[FULL_BODY_AVATARS].getItems()[self.buttonLabels[FULL_BODY_AVATARS].getSelection()]
            else:
                self.trialSettings[DEFAULT][FULL_BODY_AVATARS] = None
        
            if not self.clientMode:
                self.trialSettings[DEFAULT][GAZE_POINT] = self.buttonLabels[GAZE_POINT].getItems()[self.buttonLabels[GAZE_POINT].getSelection()]
        
        if not self.clientMode:
            for trial in self.trialSettings:
                if not self.modifyFlag and not self.loadedConfig and self.trialSettings[trial][MODE] == MODEL_3D:
                    nodeList = self.findNodes(self.trialSettings[trial][ENVIRONMENT], self.trialSettings[trial][ENVIRONMENT_DIRECTORY])
                    
                    for node in nodeList:
                        self.trialSettings[trial][TRIAL_SETUP][node] =  {
                        TARGET: viz.ON, 
                        VISIBLE: viz.ON, 
                        GRAB: viz.OFF
                        }
                        
        global DWELL_THRESHOLD_VALUE
        DWELL_THRESHOLD_VALUE = float(self.trialSettings[DEFAULT][DWELL_TIME])
            
    def refreshGUI(self):
        """
        Update GUI controls to reflect current configuration settings.
        
        Syncs GUI element states (dropdowns, textboxes, checkboxes) with values
        stored in self.trialSettings[DEFAULT]. Called after loading a configuration
        file or resetting to defaults.
        
        Returns:
            None. Updates GUI control states
        """
        for key in self.buttonLabels:
            index = 0
            if not key in [LOAD_CONFIG, SERVER_NAME] and type(self.buttonLabels[key]).__name__ == "VizDropList":
                item = self.trialSettings[DEFAULT][key]
                
                if item == None:
                    if key == AVATAR_HEAD and "GlowManBlue.osgb" in self.resourceLists[AVATAR_HEAD]:
                        index = self.resourceLists[AVATAR_HEAD].index("GlowManBlue.osgb")
                    if key == AVATAR_LEFT_HAND and "controller2.osgb" in self.resourceLists[AVATAR_LEFT_HAND]:
                        index = self.resourceLists[AVATAR_LEFT_HAND].index("controller2.osgb")
                    if key == AVATAR_RIGHT_HAND and "controller1.osgb" in self.resourceLists[AVATAR_RIGHT_HAND]:
                        index = self.resourceLists[AVATAR_RIGHT_HAND].index("controller1.osgb")
                    if key == FULL_BODY_AVATARS and "TrackedAvatar.osgb" in self.resourceLists[FULL_BODY_AVATARS]:
                        index = self.resourceLists[FULL_BODY_AVATARS].index("RocketBox_Male1.osgb")
                    
                else:
                    if item in self.buttonLabels[key].getItems():
                        index = self.buttonLabels[key].getItems().index(item)
                
                if len(self.buttonLabels[key].getItems()) > 0:
                    self.buttonLabels[key].select(index)
                    
            elif key in [SCREEN_RECORD, BARCHART, BIOPAC, FULL_BODY_TOGGLE, SEATED_MODE, SHOW_AVATAR]:
                if key in self.trialSettings[DEFAULT]:
                    self.buttonLabels[key].set(self.trialSettings[DEFAULT][key])
                    if key == FULL_BODY_TOGGLE:
                        if self.trialSettings[DEFAULT][key]:
                            self.buttonLabels[FULL_BODY_AVATARS].enable()
                            self.buttonLabels[SEATED_MODE].enable()
                        else:
                            self.buttonLabels[FULL_BODY_AVATARS].disable()
                            self.buttonLabels[SEATED_MODE].disable()

        if not self.clientMode:
            self.buttonLabels[DWELL_TIME].message(str(self.trialSettings[DEFAULT][DWELL_TIME]))
            self.buttonLabels[DURATION_THRESHOLD].message(str(self.trialSettings[DEFAULT][DURATION_THRESHOLD]))
            self.buttonLabels[DISPERSION_THRESHOLD].message(str(self.trialSettings[DEFAULT][DISPERSION_THRESHOLD]))
            self.buttonLabels[NOISE_REDUCTION].message(str(self.trialSettings[DEFAULT][NOISE_REDUCTION]))
            
            if DATA_SAVING in self.trialSettings[DEFAULT]:
                if self.trialSettings[DEFAULT][DATA_SAVING] == PER_TRIAL:
                    self.buttonLabels[PER_TRIAL].set(viz.ON)
                if self.trialSettings[DEFAULT][DATA_SAVING] == COMBINED:
                    self.buttonLabels[COMBINED].set(viz.ON)
    
        self.loadTempAvatar()
        
        # Load full body avatar if toggle is enabled (avatar GUI only exists outside server mode)
        if not self.serverMode and self.trialSettings[DEFAULT].get(FULL_BODY_TOGGLE, 0):
            self.loadFullBodyAvatar()
            # Hide regular head/hands preview since full body is enabled
            if self.tempAvatar is not None:
                self.tempAvatar.visible(viz.OFF)
            if self.tempLHand is not None:
                self.tempLHand.visible(viz.OFF)
            if self.tempRHand is not None:
                self.tempRHand.visible(viz.OFF)
        
        if self.trialInfoPanel is not None:
            self.trialInfo()
            
    def normalizePath(self, path):
        """
        Format file path for display in GUI with character limit.
        
        Normalizes path and creates a compact display format showing parent/child directories.
        Truncates long paths with ellipsis and pads short paths with spaces for consistent width.
        
        Args:
            path (str): File system path to normalize
            
        Returns:
            str: Formatted path string (max 30 characters)
        """
        normalized_path = os.path.normpath(path)
            
        parent_directory = os.path.basename(os.path.dirname(normalized_path))
        last_directory = os.path.basename(normalized_path)
        directoryName = parent_directory + "/" + last_directory
        
        if last_directory == ".":
            directoryName = "/" + os.path.basename(self.scriptDirectory)
            
        charLimit = 30
        if len(directoryName) > charLimit:
            directoryName = '...' + directoryName[-charLimit:]
        else:
            for i in range(0, charLimit - len(directoryName)):
                directoryName += " "
            
        return directoryName
            
    def relativePath(self, path):
        """
        Convert absolute path to relative path from script directory.
        
        Args:
            path (str): Absolute file system path
            
        Returns:
            str: Path relative to self.scriptDirectory
        """
        return os.path.relpath(path, self.scriptDirectory)
        
    def findFiles(self, directory, ext = "", recursive = False, full_path = False):
        """
        Search directory for files matching extension pattern.
        
        Args:
            directory (str): Directory path to search
            ext (str, optional): File extension filter (e.g., ".json"). Default "" (all files)
            recursive (bool, optional): Whether to search subdirectories. Default False
            full_path (bool, optional): If True, treats directory as absolute path. Default False
            
        Returns:
            list: List of matching file paths, empty list if directory not found
        """
        if full_path:
            path = os.path.normpath(directory)
        else:
            path = os.path.abspath(os.path.join(self.scriptDirectory, directory))        
            
        if os.path.exists(path):
            extension = "*" + ext
            fileList = []
            
            if recursive:
                search_pattern = os.path.join(path, '**', extension)
            else:
                search_pattern = os.path.join(path, extension)
            
            for file in glob.glob(search_pattern, recursive=True):
                if os.path.isfile(file):
                    fileList.append(file)
                
            return fileList
        else:
            return []

class HUD:
    """
    Heads-Up Display manager for in-experiment text overlays and visual feedback.
    
    Manages on-screen display elements during experiment execution including:
    - Console text (displays current gaze object and status messages)
    - Timer display (trial duration or countdown)
    - Status messages (instructions, trial state)
    - Fade-in/fade-out overlay (smooth transitions)
    - Multi-client console display for server mode
    - BIOPAC integration markers
    
    All HUD elements are rendered in screen space (ortho mode) and can be
    individually toggled on/off during runtime.
    """
    def __init__(self, overlayWindow, GUI_FLAG, FADE_QUAD = True, CONSOLE_TEXT = True, TIMER = True, STATUS = True, BIOPAC = False, clientCount = 1,
                acqServer = None, SHOW_GAZE_PATH = False, CONTINUE_KEY = True, serverMode = False, clientMode = False):
        """
        Initialize HUD display elements.
        
        Args:
            overlayWindow: Vizard window for rendering HUD elements
            GUI_FLAG (bool): Whether GUI configuration was enabled
            FADE_QUAD (bool, optional): Enable fade overlay. Default True
            CONSOLE_TEXT (bool, optional): Enable console text display. Default True
            TIMER (bool, optional): Enable timer display. Default True
            STATUS (bool, optional): Enable status message display. Default True
            BIOPAC (bool, optional): Enable BIOPAC integration. Default False
            clientCount (int, optional): Number of clients for multi-user. Default 1
            acqServer: BIOPAC acquisition server object or None
            SHOW_GAZE_PATH (bool, optional): Enable gaze path visualization. Default False
            CONTINUE_KEY (bool, optional): Show continue key instruction. Default True
            serverMode (bool, optional): Running as multi-user server. Default False
            clientMode (bool, optional): Running as multi-user client. Default False
        """
        self.sessionRecorder = None
        
        self.sceneObjects = None
        
        self.startTime = None
        self.timerLength = -1
        
        self.overlayWindow = overlayWindow
        
        self.bufferTime = None
        self.statusText = viz.addText('', parent=viz.ORTHO, scene=overlayWindow, color=viz.WHITE, fontSize=20, pos=[20,viz.window.getSize()[1]*0.065,0], align=viz.ALIGN_LEFT_BOTTOM)
        #self.statusText = viz.addText('', parent=viz.ORTHO, scene=overlayWindow, color=viz.WHITE, fontSize=20, pos=[20,50,0])
        self.statusText.setBackdrop(viz.BACKDROP_LEFT_BOTTOM)
        self.statusText.setBackdropColor(viz.BLACK)
#        self.statusText.visible(viz.ON)
        self.statusText.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)

        self.BIOPAC = BIOPAC
        self.SHOW_GAZE_PATH = SHOW_GAZE_PATH
        
        self.serverMode = serverMode
        self.clientMode = clientMode

        self.maxDistance = 1000
        self.consoleObjectName = ""
        
        self.gazeState = None
        
        self.acqServer = None
        
        if self.BIOPAC and not self.serverMode:
            self.acqServer = acqServer
            
        self.fadeQuad = None
        
        if FADE_QUAD:
            self.fadeQuad = common_utils.FadeQuad(FADE_IN_TIME, FADE_OUT_TIME)
            self.fadeQuad.visible(viz.OFF)
        
        self.timerText = viz.addText(t('Left Shift to toggle navigation'), parent=viz.ORTHO, scene=overlayWindow, color=viz.YELLOW, fontSize=20, pos=[20,viz.window.getSize()[1]*0.03,0], align=viz.ALIGN_LEFT_BOTTOM)
        self.timerText.setBackdrop(viz.BACKDROP_BOX)
        self.timerText.setBackdropColor(viz.BLACK)
        self.timerText.setBackdropAlpha(0.4)
        if self.clientMode:
            self.timerText.message("")
            
        #self.timerText.visible(viz.OFF)
        self.timerText.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)

        self.timerFlag = TIMER
        self.consoleFlag = CONSOLE_TEXT
        self.statusFlag = STATUS
        
        self.serverText = viz.addText('0 clients online', parent=viz.ORTHO, scene=overlayWindow, color=viz.GREEN, fontSize=20, pos=[20,viz.window.getSize()[1]*0.095,0], align=viz.ALIGN_LEFT_BOTTOM)
        self.serverText.setBackdrop(viz.BACKDROP_BOX)
        self.serverText.setBackdropColor(viz.BLACK)
        self.serverText.setBackdropAlpha(0.4)
        self.serverText.visible(viz.OFF)
        self.serverText.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)
        
        self.clientText = viz.addText('0 clients online', parent=viz.ORTHO, scene=overlayWindow, color=viz.GREEN, fontSize=20, pos=[20,viz.window.getSize()[1]*0.095,0], align=viz.ALIGN_LEFT_BOTTOM)
        self.clientText.setBackdrop(viz.BACKDROP_BOX)
        self.clientText.setBackdropColor(viz.BLACK)
        self.clientText.setBackdropAlpha(0.1)
        self.clientText.visible(viz.OFF)
        self.clientText.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)
        
        self.clientListText = viz.addText('', parent=viz.ORTHO, scene=overlayWindow, color=viz.GREEN, fontSize=15, pos=[viz.window.getSize()[0]*0.98,viz.window.getSize()[1]*0.095,0], align=viz.ALIGN_RIGHT_BOTTOM)
        self.clientListText.setBackdrop(viz.BACKDROP_BOX)
        self.clientListText.setBackdropColor(viz.BLACK)
        self.clientListText.setBackdropAlpha(0.4)
        self.clientListText.visible(viz.OFF)
        self.clientListText.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)
        
        self.clientCount = clientCount
        
        vizact.onkeydown(viz.KEY_TAB, self.clientListText.visible, viz.ON)
        vizact.onkeyup(viz.KEY_TAB, self.clientListText.visible, viz.OFF)
        
        if self.serverMode:
            self.clientCount = 5

        _lh = max(35, int(viz.window.getSize()[1] * 0.05))
        _h = viz.window.getSize()[1]
        self.consoleFixated = viz.addText(t('dwell onset: '), parent=viz.ORTHO, scene = overlayWindow, color=viz.YELLOW, fontSize=20, pos=[5, _h - _lh, 0], align=viz.ALIGN_LEFT_BOTTOM)
        self.consoleFixated.setBackdrop(viz.BACKDROP_BOX)
        self.consoleFixated.setBackdropColor(viz.BLACK)
        self.consoleFixated.setBackdropAlpha(0.4)
        self.consoleFixated.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)

        self.fixatedText = {}
        for i in range(0, self.clientCount):
            clientText = viz.addText('', parent=viz.ORTHO, scene = overlayWindow, color=viz.WHITE, fontSize=20, pos=[5, _h - _lh * (i + 2), 0], align=viz.ALIGN_LEFT_BOTTOM)
            clientText.setBackdrop(viz.BACKDROP_LEFT_BOTTOM)
            clientText.setBackdropColor(viz.BLACK)
            clientText.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)
            self.fixatedText[i] = clientText

        self.consoleEnded = viz.addText(t('ended: '), parent=viz.ORTHO, scene = overlayWindow, color=viz.YELLOW, fontSize=20, pos=[5, _h - _lh * (self.clientCount + 2), 0], align=viz.ALIGN_LEFT_BOTTOM)
        self.consoleEnded.setBackdrop(viz.BACKDROP_BOX)
        self.consoleEnded.setBackdropColor(viz.BLACK)
        self.consoleEnded.setBackdropAlpha(0.4)
        self.consoleEnded.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)

        self.endedText = {}
        for i in range(0, self.clientCount):
            clientText = viz.addText('', parent=viz.ORTHO, scene = overlayWindow, color=viz.WHITE, fontSize=20, pos=[5, _h - _lh * (self.clientCount + i + 3), 0], align=viz.ALIGN_LEFT_BOTTOM)
            clientText.setBackdrop(viz.BACKDROP_LEFT_BOTTOM)
            clientText.setBackdropColor(viz.BLACK)
            clientText.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)
            self.endedText[i] = clientText
            
        self.consoleOFF()

        viz.callback(eye_tracker_utils.GAZE_BEGIN_EVENT, self.onGazeBegin)
        viz.callback(eye_tracker_utils.GAZE_END_EVENT, self.onGazeEnd)
        viz.callback(eye_tracker_utils.GAZE_TIME_EVENT, self.onGazeTime)
        
        viz.callback(grabber.GRAB_EVENT, self.onGrab)
        viz.callback(grabber.RELEASE_EVENT, self.onRelease)
        
        if self.serverMode:
            self.gazeTimeObject = {}
        else:
            self.gazeTimeObject = eye_tracker_utils.GazeTime({}, threshold=DWELL_THRESHOLD_VALUE)
        
        self.currentGazeEventData = None
        self.eyeTracker = vizconnect.getTracker('eye_tracker').getRaw()
    
        self.trialLabel = "A"
        self.pID = None
        
        self.currentTime = None
        
        self.trialState = viz.ON
        self.disableProgression = viz.ON
        
        self.sceneUpdate = None
        self.continueEvent = None
        
        self.betweenTrials = False
        
        self.dispersionThreshold = DISPERSION_THRESHOLD_VALUE
        self.durationThreshold = DURATION_THRESHOLD_VALUE
        self.dwellThreshold = DWELL_THRESHOLD_VALUE
        self.noiseReductionWindowSize = 0
        
        self.timeToFixation = 0
        self.windowSize = viz.MainWindow.getSize(mode = viz.WINDOW_PIXELS)
        
        def addROIInstructions():
            self.timerText.visible(viz.ON)
            self.writeToTimer(t("Press \"{key}\" to add Regions of Interest. i,j,k,l,u & o to fine tune").format(key="1"))
        
        def stopROIInstructions():
            self.timerText.visible(viz.ON)
            self.writeToTimer(t("Left Shift to toggle navigation"))
            if vizconnect.getTransport(name='main_transport').getEnabled():
                self.writeToTimer(t("WASD and XZ to Move"))
        
        viz.callback(ADD_ROI_EVENT, addROIInstructions) 
        viz.callback(STOP_ADD_ROI_EVENT, stopROIInstructions) 

        if GUI_FLAG and CONTINUE_KEY:
            self.continueEvent = vizact.onkeydown(CONTINUE_EVENT_KEY, self.setTrialState)

    def getCurrentTime(self):
        if self.trialState and self.bufferTime is not None:
            return viz.tick() - self.startTime - self.bufferTime
        else:
            return 0.0

    def writeToConsole(self, fixatedList = None, endedList = None, clientNumber = 1):
        """
        Update console text display showing gaze fixation status.
        
        Updates HUD text showing which object is currently fixated and which
        object gaze just ended on. Supports multiple clients in server mode.
        
        Args:
            fixatedList (str, optional): Name of currently fixated object
            endedList (str, optional): Name of object where gaze just ended
            clientNumber (int, optional): Client index for multi-user. Default 1
            
        Returns:
            None. Updates console text display
        """
        if clientNumber <= self.clientCount:
            if fixatedList == "" and endedList == "":
                for i in range(len(self.fixatedText)):
                    self.fixatedText[i].message(fixatedList)
                    self.endedText[i].message(fixatedList)
                    
            if fixatedList is not None:
                self.fixatedText[clientNumber-1].message(fixatedList)
                
            if endedList is not None:
                self.fixatedText[clientNumber-1].message("")
                self.endedText[clientNumber-1].message(endedList)

    def writeToStatus(self, message):
        """
        Display status message in HUD.
        
        Args:
            message (str): Status message text to display
        """
        self.statusText.message(message)
        
    def writeToTimer(self, message):
        """
        Display timer message in HUD.
        
        Args:
            message (str): Timer text to display (e.g., elapsed time, countdown)
        """
        self.timerText.message(message)
        
    def writeToServer(self, count, readyCount, message):
        """
        Update server status display in multi-user mode.
        
        Shows connection status and ready state of connected clients.
        
        Args:
            count (int): Number of connected clients
            readyCount (int): Number of clients in ready state
            message (str): Additional status message
        """
        self.serverText.visible(viz.ON)
        self.serverText.message(str(count) + " online, " + str(readyCount) + " ready, " + message)
        
    def writeToClientList(self, clientDict):
        clientList = '\n'.join(str(value) for value in clientDict.values())
        self.clientListText.message(clientList)
        
    def writeToClient(self, message, color = viz.GREEN, clientsOnline = None, clientsReady = None):
        self.clientText.visible(viz.ON)
        
        if clientsOnline is not None:
            message = message + ", " + str(clientsOnline) + " online"
            
        if clientsReady is not None:
            message = message + ", " + str(clientsReady) + " ready"
            
        self.clientText.message(message)
        self.clientText.color(color)
        
    def windowSizeCheck(self):
        """
        Check for window resize and adjust HUD element positions/scaling.
        
        Monitors window size changes and updates HUD element positions and scale
        factors to maintain proper layout across different resolutions.
        
        Returns:
            None. Updates global SCALE_FACTOR and repositions HUD elements
        """
        global SCALE_FACTOR, WINDOW_SIZE, proportionFactor
        
        # Skip all window resizing/rescaling for projection (CAVE) configs. They manage
        # their own per-wall windows and fullscreen span; this method would fight them.
        if "Projection" in VIZCONNECT_CONFIG:
            return
        
        if not viz.MainWindow.getSize(mode = viz.WINDOW_PIXELS) == self.windowSize:
            WINDOW_SIZE = viz.MainWindow.getSize(mode = viz.WINDOW_PIXELS)

            SCALE_FACTOR = viz.window.getSize()[1]/975
            
            _lh = max(35, int(viz.window.getSize()[1] * 0.05))
            _h = viz.window.getSize()[1]
            self.consoleFixated.setPosition([5, _h - _lh, 0])
            self.consoleEnded.setPosition([5, _h - _lh * (self.clientCount + 2), 0])

            for i in range(0, self.clientCount):
                self.fixatedText[i].setPosition([5, _h - _lh * (i + 2), 0])

            for i in range(0, self.clientCount):
                self.endedText[i].setPosition([5, _h - _lh * (self.clientCount + i + 3), 0])
            
            if self.serverMode:
                self.clientListText.setPosition([viz.window.getSize()[0]*0.98,viz.window.getSize()[1]*0.095,0])
            
            self.windowSize = WINDOW_SIZE
        
    def updateGazePointObject(self):
        if VIZCONNECT_CONFIG == "Screen Based EyeTracker":
            line = vizmat.VectorToPoint(viz.MainView.getPosition(mode=viz.ABS_GLOBAL), self.eyeTracker.getPosition(mode=viz.ABS_GLOBAL))
            endPos = vizmat.MoveAlongVector(viz.MainView.getPosition(mode=viz.ABS_GLOBAL), line, self.maxDistance)
            info = viz.intersect(viz.MainView.getPosition(mode=viz.ABS_GLOBAL), endPos)
        else:
            gazeMat = self.eyeTracker.getMatrix(viz.BOTH_EYE)
            gazeMat.postMult(viz.MainView.getMatrix())
            line = gazeMat.getLineForward(self.maxDistance)
            info = viz.intersect(line.begin, line.end)
        
        if not self.serverMode:
            self.gazeTimeObject.updateGazeObject(info.object)
        
            if info.valid:
                if info.object in self.sceneObjects[GAZE_OBJECTS].values():
                    for gazeName in self.sceneObjects[GAZE_OBJECTS]:
                        if not gazeName in self.sessionRecorder.gazeTracker:
                            self.sessionRecorder.gazeTracker[gazeName] = {}
                            self.sessionRecorder.gazeTracker[gazeName][GAZE_STATE] = None
                            self.sessionRecorder.gazeTracker[gazeName][GAZE_BOOL] = False
                            self.sessionRecorder.gazeTracker[gazeName][DWELL_SPHERE_COUNT] = 1
                            self.sessionRecorder.gazeTracker[gazeName][DWELL_TIME] = DWELL_THRESHOLD_VALUE
                            
                        self.sessionRecorder.gazeTracker[gazeName][VIEW_STATUS] = False
                        if self.sceneObjects[GAZE_OBJECTS][gazeName] == info.object:
                            self.sessionRecorder.gazeTracker[gazeName][VIEW_STATUS] = True
                            
                elif info.object in self.sceneObjects[REGIONS_OF_INTEREST].values():
                    for gazeName in self.sceneObjects[REGIONS_OF_INTEREST]:
                        roiName = gazeName[4] if isinstance(gazeName, tuple) else gazeName
                        if not roiName in self.sessionRecorder.gazeTracker:
                            self.sessionRecorder.gazeTracker[roiName] = {}
                            self.sessionRecorder.gazeTracker[roiName][GAZE_STATE] = None
                            self.sessionRecorder.gazeTracker[roiName][GAZE_BOOL] = False
                            self.sessionRecorder.gazeTracker[roiName][DWELL_SPHERE_COUNT] = 1
                            self.sessionRecorder.gazeTracker[roiName][DWELL_TIME] = DWELL_THRESHOLD_VALUE
                            
                        self.sessionRecorder.gazeTracker[roiName][VIEW_STATUS] = False
                        if self.sceneObjects[REGIONS_OF_INTEREST][gazeName] == info.object:
                            self.sessionRecorder.gazeTracker[roiName][VIEW_STATUS] = True
                
                self.sessionRecorder.gazeTracker[RAW_INTERSECT] = info.name
                return info.point
            else:
                self.sessionRecorder.gazeTracker[RAW_INTERSECT] = None
                return vizmat.MoveAlongVector(line.begin, gazeMat.getForward(), self.maxDistance)

        else:
            self.sessionRecorder.gazeTracker[RAW_INTERSECT] = None

            if VIZCONNECT_CONFIG == "Screen Based EyeTracker":
                 return endPos
            else:
                return vizmat.MoveAlongVector(line.begin, gazeMat.getForward(), self.maxDistance)
                
    def updateScene(self, sessionRecorder):
        sessionRecorder.currentTime = str(round(self.getCurrentTime(), ROUND_VALUES))
        
        if not self.betweenTrials:
            self.currentTime = str(round(self.getCurrentTime(), ROUND_VALUES))
            
            if not self.timerLength == -1 and float(self.currentTime) >= float(self.timerLength):
                viz.sendEvent(INITIATE_TRIAL_END)
                
            self.writeToTimer(self.currentTime)
            
            point = self.updateGazePointObject()
            if not self.serverMode:
                sessionRecorder.updateData(self.currentTime, point, self.eyeTracker)
                
                if self.clientMode:
                    if vizmic is None:
                        raise RuntimeError('clientMode requires the vizmic module, which failed to import. Check that vizmic and its DLL dependencies are installed correctly.')
                    flap = vizmic.getMonitorLevel()
                    viznet.client.sendAll(UPDATE_MOUTH, client = viz.net.getName(), morphValue = flap)

            else:
                if not self.currentTime in sessionRecorder.replayData[OBJECT_TRACKER]:
                    sessionRecorder.replayData[OBJECT_TRACKER][self.currentTime] = {}
                                
        else:
            self.currentTime = str(round(self.getCurrentTime(), ROUND_VALUES))

            if not self.timerLength == -1:
                if float(self.currentTime) >= float(self.timerLength):
                    viz.sendEvent(INITIATE_TRIAL_START)
                    self.betweenTrials = False
                    self.timerLength = -1
            else:
                self.sceneUpdate.setEnabled(viz.OFF)
                self.betweenTrials = False
                
        self.windowSizeCheck()
        
    def setGazeTimeObject(self, gazeObjects, dwellTime = DWELL_THRESHOLD_VALUE):
        """
        Configure gaze time threshold objects for dwell-based events.
        
        Args:
            gazeObjects (list): List of scene objects to monitor for gaze dwell
            dwellTime (float, optional): Dwell threshold in seconds. Default from DWELL_THRESHOLD_VALUE
        """
        if not self.serverMode:
            self.gazeTimeObject = eye_tracker_utils.GazeTime(gazeObjects, threshold=dwellTime)
            # Reset gaze state and console name when setting new gaze objects (e.g., between trials)
            self.gazeState = None
            self.consoleObjectName = ""
            # Clear console displays
            self.writeToConsole(fixatedList = "", endedList = "")
        
    def onGazeBegin(self, e):
        """
        Handle gaze begin event callback.
        
        Called when gaze first intersects with a tracked object. Updates console,
        sets flags for recording, and sends network events in client mode.
        
        Args:
            e: Gaze event object containing object name and gaze data
        """
        self.currentGazeEventData = e
        self.gazeState = GAZE_STARTED
        
        if isinstance(e.name, tuple):
            name = str(e.name[4])
        else:
            name = str(e.name)
            
        self.consoleObjectName = name
            
        self.writeToConsole('gaze started : {:<15s}'.format(name))
        
        self.sessionRecorder.setFlag('gaze started: ' + name)
        
        self.sessionRecorder.setGazeState(name, GAZE_STARTED)
        
        print('gaze started : {:<15s}'.format(name))
        
#        print("gaze started: ", e)
        
        if self.clientMode:
            viznet.client.send(CLIENT_GAZE_BEGIN_EVENT, client = viz.net.getName(), gazeObject = name)

    def onGazeEnd(self, e):
        """
        Handle gaze end event callback.
        
        Called when gaze leaves a tracked object. Records dwell duration,
        updates console, sets flags, and sends network/BIOPAC events.
        
        Args:
            e: Gaze event object containing object name, dwell time
        """
        self.currentGazeEventData = e
        
        if isinstance(e.name, tuple):
            name = str(e.name[4])
        else:
            name = str(e.name)
            
        self.writeToConsole(endedList = '{:<15s}: {:.2f} seconds'.format(name, e.time))
        print('dwell ended : {:<15s} seconds: {:.2f}'.format(name, e.time))
        self.sessionRecorder.setFlag('dwell ended: ' + name)
        
        self.gazeState = GAZE_ENDED
        
        self.sessionRecorder.setGazeState(name, GAZE_ENDED, fixationPeriod = e.time)
        
        if self.clientMode:
            viznet.client.send(CLIENT_GAZE_END_EVENT, client = viz.net.getName(), gazeObject = name, time = self.getCurrentTime(), gazeTime = e.time)
            
        if self.BIOPAC == True and not self.serverMode:
            clientName = (viz.net.getName() + " ") if self.clientMode else ""
            self.acqServer.insertGlobalEvent(clientName + 'Dwell Ended: ' + name, 'stim', '')
        
    def onGazeTime(self, e):
        """
        Handle gaze time (dwell threshold) event callback.
        
        Called when gaze dwells on an object for the threshold duration.
        Triggers fixation onset recording and sends events for analysis.
        
        Args:
            e: Gaze time event object containing object name and threshold time
        """
        self.currentGazeEventData = e
        threshold = self.gazeTimeObject.getThreshold()
        self.timeToFixation = self.getCurrentTime()
        
        if isinstance(e.name, tuple):
            name = str(e.name[4])
        else:
            name = str(e.name)
            
        print('dwell onset   : {:<15s} seconds: {:.2f}'.format(name, threshold))
            
        self.sessionRecorder.timeLine[self.timeToFixation] = [name]
        
        self.gazeState = GAZE_FIXATED
        
        self.sessionRecorder.setFlag('dwell onset: ' + name)
        self.sessionRecorder.setGazeState(name, GAZE_FIXATED, threshold)
        
        self.writeToConsole(fixatedList = name)
        
        if self.clientMode:
            viznet.client.send(CLIENT_GAZE_TIME_EVENT, client = viz.net.getName(), gazeObject = name, time = self.getCurrentTime())
        
        if self.BIOPAC == True and not self.serverMode:
            clientName = (viz.net.getName() + " ") if self.clientMode else ""
            self.acqServer.insertGlobalEvent(clientName + 'Dwell Onset: ' + name, 'stim', '')
            
    def onGrab(self, e):
        if self.sceneObjects is not None:
            scene_objects = self.sceneObjects[GRAB_OBJECTS]
            for name in scene_objects.keys():
                if e.grabbed == scene_objects[name]:
                    print(f'grabbed {name}')
                    self.sessionRecorder.setFlag('grabbed: ' + name)
                    self.sessionRecorder.grabStatus[name] = True
                    if self.BIOPAC == True and not self.serverMode:
                        clientName = (viz.net.getName() + " ") if self.clientMode else ""
                        self.acqServer.insertGlobalEvent(clientName + f'Grabbed {name}', 'stim', '')
        
    def onRelease(self, e):
        if self.sceneObjects is not None:
            scene_objects = self.sceneObjects[GRAB_OBJECTS]
            for name in scene_objects.keys():
                if e.released == scene_objects[name]:
                    print(f'released {name}')
                    self.sessionRecorder.setFlag('released: ' + name)
                    self.sessionRecorder.grabStatus[name] = False
                    if self.BIOPAC == True and not self.serverMode:
                        clientName = (viz.net.getName() + " ") if self.clientMode else ""
                        self.acqServer.insertGlobalEvent(clientName + f'Released {name}', 'stim', '')
            
    def setTrialState(self):
        if not self.disableProgression:
            if not self.trialState:
                viz.sendEvent(INITIATE_TRIAL_START)
            else:
                viz.sendEvent(INITIATE_TRIAL_END)
            
    def preTrial(self, dateTime, participantData, isGUI, trialMode, trialNumber, trialLabel, 
                    sceneObjects, trackingDataLogging, replayDataLogging, experimentDataLogging, timeLineLogging, fixationLogging,
                    customExperimentData = None, scriptDirectory = None, trialConfigFile = None, dataFileSaving = PER_TRIAL, 
                    clientDict = None, individualEyeIntersect = True, customTrackingObjects = {}, oldHeaders = False,
                    updateRate = 0):
                        
        self.sessionRecorder = SessionRecorder(dateTime = dateTime, participant=participantData, isGUI = isGUI, trialMode = trialMode, trialNumber=trialNumber, trialLabel = trialLabel, maxDistance = self.maxDistance,
                                                sceneObjects=sceneObjects, customExperimentData = customExperimentData, 
                                                trackingDataLogging = trackingDataLogging, replayDataLogging = replayDataLogging, experimentSummary = experimentDataLogging, 
                                                trialTimeLine = timeLineLogging, fixationTimeLine = fixationLogging, scriptDirectory = scriptDirectory, trialConfigFile = trialConfigFile, dataFileSaving = dataFileSaving, 
                                                serverMode = self.serverMode, clientMode = self.clientMode, clientDict = clientDict, individualEyeIntersect = individualEyeIntersect,
                                                customTrackingObjects = customTrackingObjects, oldHeaders = oldHeaders, overlayWindow = self.overlayWindow)
        
        self.sceneObjects = sceneObjects
        
        if not self.serverMode:
            self.sessionRecorder.dispersionThreshold = self.dispersionThreshold
            self.sessionRecorder.durationThreshold = self.durationThreshold
            self.sessionRecorder.dwellThreshold = self.dwellThreshold
            self.sessionRecorder.noiseReductionWindowSize = int(self.noiseReductionWindowSize)
                        
        if self.sceneUpdate is not None:
            self.sceneUpdate.remove()
            self.sceneUpdate = None
        
        if updateRate == 0:
            self.sceneUpdate = vizact.onupdate(vizconnect.PRIORITY_ANIMATOR+1, self.updateScene, self.sessionRecorder)
        else:
            self.sceneUpdate = vizact.ontimer(updateRate, self.updateScene, self.sessionRecorder)
        self.sceneUpdate.setEnabled(viz.OFF)
        
        self.windowSizeCheck()
        
        if self.serverMode:
            viz.callback(CLIENT_TRIAL_DATA_UPDATE, self.sessionRecorder.updateClientData)
                
    def startTrial(self, BIOPAC = False, tempFlag = "-"):
        """
        Start trial recording and data collection.
        
        Initiates trial timer, enables HUD console, starts scene update loop,
        and sends BIOPAC markers if enabled. Fades out overlay quad for smooth transition.
        
        Args:
            BIOPAC (bool, optional): Whether to send BIOPAC markers. Default False
            tempFlag (str, optional): Custom flag text for this trial start. Default "-"
            
        Yields:
            Fade-out animation if fade quad is enabled
        """
#        viz.setLogLevel(viz.LOG_NOTICE)

        if self.fadeQuad is not None:
            yield self.fadeQuad.fade_out()
                
        if self.sessionRecorder is not None:
            self.sessionRecorder.flag = tempFlag
        
        self.timerON()
        
        self.consoleON()
        
        # Clear console text for new trial
        self.writeToConsole(fixatedList = "", endedList = "")
        
        self.sceneUpdate.setEnabled(viz.ON)
        
        if BIOPAC and not self.serverMode:
            if not self.acqServer.getAcquisitionInProgress():
                self.acqServer.toggleAcquisition()
            clientName = (viz.net.getName() + " ") if self.clientMode else ""
            self.acqServer.insertGlobalEvent(clientName + 'Trial Start', 'stim', '')
        
        if self.startTime is None:
            self.startTime = viz.tick()
                    
        if self.bufferTime is None:
            self.bufferTime = 0.0
            
        self.sessionRecorder.timeLine = {}
        
        viz.sendEvent(TRIAL_START)
                
        self.trialState = viz.ON
        self.sessionRecorder.trialState = viz.ON

        atexit.register(self.sessionRecorder.writeSessionData)

    def endTrial(self, BIOPAC, trialNumber):
        """
        End trial and save collected data.
        
        Writes all session data to files, disables HUD console, sends final
        gaze end events if needed, and sends BIOPAC markers if enabled.
        
        Args:
            BIOPAC (bool): Whether to send BIOPAC markers
            trialNumber (int): Current trial number for logging
            
        Yields:
            Small delay for BIOPAC marker processing
        """
        self.sessionRecorder.writeSessionData()

        self.bufferTime = 0.0
        self.consoleOFF()
        
        if not self.gazeState == GAZE_ENDED and not self.serverMode:
            viz.sendEvent(eye_tracker_utils.GAZE_END_EVENT, viz.Event(object=self.gazeTimeObject._gazeObjectOld, name=self.consoleObjectName, time=viz.tick()-self.gazeTimeObject._startTime))
        
        if BIOPAC and not self.serverMode:
            self.acqServer.insertGlobalEvent('Trial End', 'stim', '')
            yield viztask.waitTime(0.1)
            if self.acqServer.getAcquisitionInProgress():
                self.acqServer.toggleAcquisition()
        
        self.sceneUpdate.setEnabled(viz.OFF)
        #self.betweenTrials = True
        
        if self.SHOW_GAZE_PATH:
            #Displays a static scanpath visualisation of the eyetracking data
            visualization = eye_tracker_utils.DataVisualization3D()
            visualization.setList([self.sessionRecorder.replayData[OBJECT_TRACKER][timestamp][GAZE_POINT_OBJECT][POSITION] for timestamp in self.sessionRecorder.replayData[OBJECT_TRACKER][timestamp]])
            visualization.show3DPts()
            yield viztask.waitKeyDown(CONTINUE_EVENT_KEY)
            visualization.remove3DPts()
        
        self.writeToConsole(fixatedList = "", endedList = "")
        
        # Reset gaze state for next trial
        self.gazeState = None
        self.consoleObjectName = ""
        
        self.sessionRecorder.timeLine = {}
        
        if self.fadeQuad is not None:
            yield self.fadeQuad.fade_in()
        
        viz.sendEvent(TRIAL_END)
        self.trialState = viz.OFF
        self.sessionRecorder.trialState = viz.OFF

    def consoleON(self):
        if self.consoleFlag:
            self.consoleFixated.visible(viz.ON)
            self.consoleEnded.visible(viz.ON)
            self.fixatedText[0].visible(viz.ON)
            self.endedText[0].visible(viz.ON)
        
    def consoleOFF(self):
        """Disable console text display in HUD (hides gaze fixation info)."""
        self.consoleFixated.visible(viz.OFF)
        self.consoleEnded.visible(viz.OFF)
        self.fixatedText[0].visible(viz.OFF)
        self.endedText[0].visible(viz.OFF)
        
    def timerON(self):
        """Enable timer text display in HUD."""
        if self.timerFlag:
            self.timerText.visible(viz.ON)
        
    def timerOFF(self):
        """Disable timer text display in HUD."""
        self.timerText.visible(viz.OFF)
        
    def statusON(self):
        """Enable status text display in HUD."""
        if self.statusFlag:
            self.statusText.visible(viz.ON)
        
    def statusOFF(self):
        """Disable status text display in HUD."""
        self.statusText.visible(viz.OFF)
        
    def fadeQuadON(self):
        """Show fade overlay quad."""
        if self.fadeQuad is not None:
            self.fadeQuad.visible(viz.ON)
    
    def fadeQuadOFF(self):
        """Hide fade overlay quad."""
        if self.fadeQuad is not None:
            self.fadeQuad.visible(viz.OFF)
            
    def __del__(self):
        """Cleanup HUD resources on destruction."""
        pass
        
class SightLab:
    def __init__(self, gui = True, pid = True, biopac = None, timer = True, fadequad = True, 
                headlight = False, mouselock = False, gazepointvisible = True, gazepathvisible = ADDITIONAL_SETTINGS["Gaze Path Visible"], 
                console = ADDITIONAL_SETTINGS["Console"], screenrecord = False, trackingdatalogging = True, 
                replaydatalogging = True, experimentdatalogging = True, timelinelogging = True, fixationlogging = True, continuekey = False, 
                trialcount = None, configpath = None, loadenvironmentmode = LOAD_ALL, directory = None, repetitions = 1, 
                datafilesaving = PER_TRIAL, loglevel = viz.OFF, hardwareconfig = None, vizconnectconfig = None, vizconnectconfiglist = None, 
                serverMode = False, clientMode = False, highlighttool = False, title = SIGHTLAB_VERSION, individual_eye_intersect = True,
                oldHeaders = False, updateRate = 0, selectconfig = None, optimizeintersect = True, fastload = False, barchart = False, fullbody = False, fullbodyavatar = None):
        """
        gui=True, pid=True, timer=True, fadequad=True
        gazepointvisible=True, individual_eye_intersect=True
        trackingdatalogging=True, replaydatalogging=True
        experimentdatalogging=True, timelinelogging=True
        fixationlogging=True, headlight=False
        mouselock=False, screenrecord=False
        continuekey=False, oldHeaders=False
        serverMode=False, clientMode=False
        highlighttool=False, biopac=None
        trialcount=None, configpath=None
        directory=None, selectconfig=None
        hardwareconfig=None, vizconnectconfig=None
        vizconnectconfiglist=None, repetitions=1
        updateRate=0, loglevel=viz.OFF
        loadenvironmentmode=LOAD_ALL
        datafilesaving=PER_TRIAL
        title=SIGHTLAB_VERSION
        gazepathvisible=settings, console=settings
        optimizeintersect=True, fastload = False
        barchart = False, fullbody = False
        fullbodyavatar = None
        """
        import winreg
        
        self.optimizeIntersectFlag = optimizeintersect
        
        # Full body avatar flag (non-GUI equivalent of the GUI's Full Body checkbox)
        self.fullBodyFlag = fullbody
        
        # Optional explicit full body avatar path (non-GUI equivalent of the GUI's
        # avatar dropdown). When set, all full body vizconnect configs and the
        # multi-user IK syncer pick it up via viz.custom_avatar_path. Providing a
        # path also implies full body, mirroring the GUI where the dropdown only
        # matters with the Full Body checkbox on.
        self.fullBodyAvatarPath = fullbodyavatar
        if fullbodyavatar is not None:
            viz.custom_avatar_path = fullbodyavatar
            self.fullBodyFlag = True
            fullbody = True
        
        def check_registry_key_exists(key_path, key_name):
            try:
                # Open the registry key
                registry_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
                # Check if the key name exists under this path
                value, _ = winreg.QueryValueEx(registry_key, key_name)
                winreg.CloseKey(registry_key)
                if "MULTI" in value:
                    return False
                if "SINGLE" in value:
                    if clientMode or serverMode:
                        return True
                    else:
                        return False
                return True  
            except FileNotFoundError:
                return True  # Key does not exist
            except Exception as e:
                print(f"An error occurred: {e}")
                return True
                
        if viz.res.isPublished():
            self.__demoModeFlag = False
        else:
            self.__demoModeFlag  = check_registry_key_exists("SOFTWARE\\WorldViz\\Sightlab2", "EXT_PATH")
            
        def demoModeTimer():
            yield viztask.waitTime(315)
            viz.logError("SightLab Demo is limited to 5 minutes")
            viz.quit()
            
            
        if self.__demoModeFlag:
            viztask.schedule(demoModeTimer)
        
        self.__demoTrialCount = 4
        self.__demoRepetitionCount = 2
        
        self.serverMode = serverMode
        self.clientMode = clientMode
        
        self.guiFlag = gui
        self.configPath = configpath
        self.configSelect = selectconfig
        self.pidFlag = pid
        self.biopacFlag = biopac
        self.tempFlag = "-"
        self.startConfirm = False
        
        if self.biopacFlag is None and not (self.guiFlag or self.configPath is not None):
            self.biopacFlag = False
            
        self.fastLoad = fastload
        
        self.timerFlag = timer
        self.fadequadFlag = fadequad
        self.headlightFlag = headlight
        self.mouselockFlag = mouselock
        self.gazePointVisibleFlag = gazepointvisible 
        self.gazePathVisibleFlag = gazepathvisible
        self.consoleFlag = console
        self.screenRecordFlag = screenrecord
        self.barchartFlag = barchart
        self.hightlighterFlag = highlighttool
        self.loadEnvironmentMode = loadenvironmentmode
        self.oldHeaders = oldHeaders
        self.updateRate = updateRate
        
        self.individualEyeIntersect = individual_eye_intersect
        
        self.DEMO_TEXT = " Demo"
        
        global SIGHTLAB_VERSION
        titleText = title
        
        if self.clientMode:
            titleText += " Client"
        if self.serverMode:
            titleText += " Server"
            
        if self.__demoModeFlag:
            titleText += self.DEMO_TEXT
            
        SIGHTLAB_VERSION = titleText
            
        vizinput.setDefaultTitle(titleText)
        self.hardwareConfig = hardwareconfig
        self.vizconnectConfigArg = vizconnectconfig
        self.vizconnectConfigListArg = vizconnectconfiglist
       
        # Full body avatar (non-GUI): switch to the full body vizconnect configs so the
        # hardware prompt offers full body options, mirroring the GUI's Full Body checkbox.
        # Skipped when the user supplied an explicit vizconnect override, which takes precedence.
        global VIZCONNECT_CONFIG_LIST
        if fullbody and not gui and hardwareconfig is None and vizconnectconfig is None and vizconnectconfiglist is None:
            VIZCONNECT_CONFIG_LIST = FULL_BODY_VIZCONNECT_CONFIG_LIST.copy()
       
        if vizconnectconfiglist is not None:
            self.vizconnectConfigList = vizconnectconfiglist
        else:
            self.vizconnectConfigList = VIZCONNECT_CONFIG_LIST

        if vizconnectconfig is not None and isinstance(vizconnectconfig, dict):
            self.vizconnectDict = vizconnectconfig
            self.vizconnectConfigList = list(self.vizconnectDict.keys())
        else:
            self.vizconnectDict = VIZCONNECT_DICT
            
        if vizconnectconfig is not None and isinstance(vizconnectconfig, list):
            self.vizconnectConfig = vizconnectconfig[0]
            self.vizconnectPath = vizconnectconfig[1]
        else:
            self.vizconnectConfig = None
            self.vizconnectPath = None
            
        if gui:
            self.__launchVizconnect("Desktop", vizconnectconfig, vizconnectconfiglist)
            self.experimentEnd = False
        else:
            self.__launchVizconnect(hardwareconfig, vizconnectconfig, vizconnectconfiglist, False)
            
        self.dataFileSaving = datafilesaving
        
        self.repetitionCount = repetitions
        self.currentRepetition = 1
        
        self.startPoint = [0.0, 0.0, 0.0]
        self.startEuler = [0.0, 0.0, 0.0]
        
        self.headLink = None
        
        def toggleMouseLock(opt = viz.TOGGLE):
            if opt == viz.TOGGLE:
                if self.mouselockFlag:
                    viz.mouse.setTrap(viz.OFF)
                    self.mouselockFlag = viz.OFF
                else:
                    viz.mouse.setTrap(viz.ON)
                    self.mouselockFlag = viz.ON
            else:
                viz.mouse.setTrap(opt)
                self.mouselockFlag = opt
            
        if self.mouselockFlag:
            toggleMouseLock(viz.ON)
        else:
            toggleMouseLock(viz.OFF)
            
        vizact.onkeydown(";", toggleMouseLock)
            
        self.headLight = viz.MainView.getHeadLight()
        self.replayExecCode = None
        
        self.customTrackedObjects = {}
            
        if not self.headlightFlag:
            self.headLight.disable()
        else:
            self.headLight.enable()
        
        if (self.guiFlag or self.configPath is not None):
            self.sceneObjects = {
                ENVIRONMENT_OBJECT: None,
                MEDIA_OBJECT: None,

                AVATAR_HEAD_OBJECT: None,
                AVATAR_RIGHT_HAND_OBJECT: None,
                AVATAR_LEFT_HAND_OBJECT: None,

                GAZE_POINT_OBJECT: None,
                
                GAZE_OBJECTS: {},
                GRAB_OBJECTS: {},
                INVISIBLE_OBJECTS: {},
                REGIONS_OF_INTEREST: {},
                
                CUSTOM_OBJECTS: {},
                AVATAR_OBJECTS: {},
                MANUAL_ADD: {}
            }
            
        else:
            self.sceneObjects = {
                ENVIRONMENT_OBJECT: vizfx.addChild(DEFAULT_ENVIRONMENT_PATH),

                AVATAR_HEAD_OBJECT: vizfx.addChild(DEFAULT_AVATAR_HEAD_PATH),
                AVATAR_RIGHT_HAND_OBJECT: vizfx.addChild(DEFAULT_AVATAR_RIGHT_HAND_PATH),
                AVATAR_LEFT_HAND_OBJECT: vizfx.addChild(DEFAULT_AVATAR_LEFT_HAND_PATH),
                GAZE_POINT_OBJECT: vizfx.addChild(DEFAULT_GAZE_POINT_PATH),
                
                GAZE_OBJECTS: {},
                GRAB_OBJECTS: {},
                INVISIBLE_OBJECTS: {},
                REGIONS_OF_INTEREST: {},
                
                CUSTOM_OBJECTS: {},
                AVATAR_OBJECTS: {},
                MANUAL_ADD: {}
            }
            
            self.sceneObjects[AVATAR_HEAD_OBJECT].visible(viz.OFF)
            self.sceneObjects[AVATAR_HEAD_OBJECT].disable(viz.INTERSECTION)

            
        self.nameTags = {}
            
        self.initSceneObjects = self.sceneObjects
        
        self.environmentDict = {}
        self.mediaDict = {}
        self.sceneObjects[MEDIA_OBJECT] = None
        self.dome180 = viz.addChild(os.path.join(os.path.dirname(__file__), 'resources/objects/180_dome.osgb'))
        self.dome180.visible(viz.OFF)
        
        self.acqServer = None
        
        if self.biopacFlag and not self.serverMode:
            try:
                self.acqServer = biopacndt.AcqNdtQuickConnect()
                self.acqServer
            except Exception as e:
                print("No Acqknowledge server found")
                self.biopacFlag = False
                        
#        self.environmentWindow = viz.addWindow(size=(1,1), pos=(0,1), clearMask = 0, scene=viz.addScene())

#        self.gazePointWindow = viz.addWindow(size=(1,1), pos=(0,1), clearMask = 0, scene=viz.addScene())
        
#        self.gazePointWindow = viz.addWindow(size=(1,1), pos=(0,1), clearMask=0, scene=viz.MainScene)
#        self.gazePointWindow.setScene(viz.MainScene)  # Keep it in the same scene
#        self.gazePointWindow.setClearMask(viz.CLEAR_DEPTH)  # Only draws overlays

        #Original Method
        self.gazePointWindow = viz.addWindow(size=(1,1), pos=(0,1))
        self.gazePointWindow.fov(79)

        if "Projection" in VIZCONNECT_CONFIG:
            # This is a full-span mono-perspective overlay meant for Desktop/VR gaze
            # visualization. On a CAVE it sits on top of the 3 correctly-tiled off-axis
            # wall windows and visually looks like the walls don't line up, even though
            # they do underneath it. Off by default; still toggleable with ',' if needed.
            self.gazePointWindow.visible(viz.OFF)

        self.overlayWindow = viz.addWindow(size=(1,1), pos=(0,1), clearMask = 0, scene=viz.addScene())

        self.trialNumber = 1
        self.firstStart = True
        
        self.gui = GUI(self.overlayWindow, (self.guiFlag or self.configPath is not None), self.biopacFlag, self.gazePointWindow, configpath, self.configSelect, directory, self.serverMode, self.clientMode, self.__demoModeFlag)
        self.gui.fastLoad = self.fastLoad
        self.hud = HUD(self.overlayWindow, GUI_FLAG = (self.guiFlag or self.configPath is not None), FADE_QUAD = self.fadequadFlag, BIOPAC = self.biopacFlag, acqServer = self.acqServer, SHOW_GAZE_PATH = self.gazePathVisibleFlag, CONSOLE_TEXT = self.consoleFlag, TIMER = self.timerFlag, CONTINUE_KEY = continuekey, serverMode = self.serverMode, clientMode = self.clientMode)
        
        self._applyProjectionFade()
        
        self.experimentSettings = self.gui.trialSettings
        
        # Enable full body avatar for non-GUI scripts (equivalent to the GUI checkbox).
        if self.fullBodyFlag:
            self.experimentSettings[DEFAULT][FULL_BODY_TOGGLE] = viz.ON
        
        if trialcount is not None:
            self.experimentSettings[DEFAULT][NUMBER_OF_TRIALS] = trialcount
            
        self.dateTime = datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
        self.participantData = {
            ID: "",
            PARTICIPANT_INFO1: "",
            PARTICIPANT_INFO2: ""
        }
        
#        self.participantData.id = ""
#        self.participantData.lastName = ""
#        self.participantData.firstName = ""
        
        self.ResponseList = []		# Strings on the screen
        
        self.trialLength = -1
        self.trialMode = MODEL_3D
        self.trackingDataLoggingFlag = trackingdatalogging
        self.replayDataLoggingFlag = replaydatalogging
        self.experimentSummaryDataLoggingFlag = experimentdatalogging
        self.timeLineLoggingFlag = timelinelogging
        self.fixationLoggingFlag = fixationlogging
        
        self.customExperimentDataColumns = {}
        
        self.GAZE_BEGIN_EVENT = eye_tracker_utils.GAZE_BEGIN_EVENT
        self.GAZE_END_EVENT = eye_tracker_utils.GAZE_END_EVENT
        self.GAZE_TIME_EVENT = eye_tracker_utils.GAZE_TIME_EVENT
        
        self.startConditionEvent = []
        self.endConditionEvent = []
                
        self.initialScene = None
        self.experimentSetupComplete = False
        self.experimentLoaded = False
        self.loadTrialComplete = False
        self.viewPointReset = False
        
        eyeOpenMorph = vizact.morphTo(2,1,time=0.2)
        eyeCloseMorph = vizact.morphTo(2,0,time=0.2)
        self.blinkSequence = vizact.sequence(eyeOpenMorph, eyeCloseMorph)
        
        file_path = os.path.join(self.gui.scriptDirectory, DEFAULT_DATA_DIRECTORY, DEFAULT_EXPERIMENT_DIRECTORY.format(date = self.dateTime, p=self.participantData[ID]), TRIAL_LOG_FILE)
        directory = os.path.dirname(file_path)
        if not loglevel == viz.OFF and (self.trackingDataLoggingFlag or self.replayDataLoggingFlag or self.timeLineLoggingFlag or self.experimentSummaryDataLoggingFlag or self.fixationLoggingFlag):
            os.makedirs(directory, exist_ok=True)
            viz.setLogLevel(loglevel)
            viz.setLogFile(file_path)
        
        vizact.onkeydown('p', self.togglePoint)
        vizact.onkeydown('.', self.toggleHUD)
        vizact.onkeydown(',', self.toggleGazePoint)
        vizact.onkeydown('/', self.screenCapture)
        vizact.onkeydown('P', self.toggleMediaPause)
        
    def __launchVizconnect(self, hardwareconfig, vizconnectconfig, vizconnectconfiglist, firstlaunch = True):
        global VIZCONNECT_DICT, VIZCONNECT_CONFIG_LIST, VIZCONNECT_CONFIG
        
        if not firstlaunch and self.vizconnectConfig is None and self.vizconnectPath is None:
            if hardwareconfig is None:
                if self.vizconnectConfigListArg is None and not isinstance(vizconnectconfig, dict):
                    self.vizconnectConfigList = VIZCONNECT_CONFIG_LIST
                self.vizconnectChoice = vizinput.choose('Select a hardware configuration', self.vizconnectConfigList)
                
                self.vizconnectConfig = self.vizconnectConfigList[self.vizconnectChoice]
                
                if vizconnectconfig is not None and isinstance(vizconnectconfig, dict):
                    self.vizconnectPath = self.vizconnectDict[self.vizconnectConfig]
                else:
                    self.vizconnectPath = os.path.join(os.path.dirname(__file__),'vizconnect_configs/{}').format(self.vizconnectDict[self.vizconnectConfigList[self.vizconnectChoice]])
            else:
                if hardwareconfig in self.vizconnectDict:
                    self.vizconnectConfig = hardwareconfig
                    self.vizconnectPath = os.path.join(os.path.dirname(__file__),'vizconnect_configs/{}').format(self.vizconnectDict[hardwareconfig])
                else:
                    vizinput.message("Hardware config not found")
                    viz.quit()
            
        if firstlaunch:
            vizconnect.go(os.path.join(os.path.dirname(__file__),'vizconnect_configs/{}').format(VIZCONNECT_DICT["Desktop"]))
            VIZCONNECT_CONFIG = "Desktop"
        else:
            vizconnect.go(self.vizconnectPath)
            VIZCONNECT_CONFIG = self.vizconnectConfig
            if hasattr(self, "hud"):
                self._applyProjectionFade()
        
        viz.MainWindow.clearcolor(viz.GRAY)
        self.experimentEnd = False
        
        oriTracker = vizconnect.getTracker(name='head_tracker').getNode3d()
        posTracker = viz.addGroup()
        rawTracker = viz.mergeLinkable(posTracker, oriTracker)
        vizconnect.addTracker(rawTracker,'merged', make='Virtual', model='Merged')
        
        self.transportNode = vizconnect.getTransport('main_transport').getNode3d()

        # Apply automatic vertical offset for Mixamo/ReadyPlayerMe avatars (Desktop only)
        # VR modes use real trackers and don't need this offset
        if "Desktop" in VIZCONNECT_CONFIG:
            try:
                avatar_wrapper = vizconnect.getAvatar('main_avatar')
                if avatar_wrapper:
                    local_avatar = avatar_wrapper.getRaw()
                    if local_avatar and local_avatar.getBone('Hips'):
                        # Mixamo/ReadyPlayerMe avatar detected - apply -0.4m offset
                        current_pos = self.transportNode.getPosition()
                        self.transportNode.setPosition([current_pos[0], current_pos[1] - 0.4, current_pos[2]])
            except:
                pass

        vizconnect.getTransport('main_transport').setEnabled(viz.OFF)
        self.transportResetPos = vizconnect.getTransport('main_transport').getNode3d().getPosition()
        if "Desktop" in VIZCONNECT_CONFIG:
            vizconnect.getRawTracker("head_tracker").setEnabled(viz.OFF)
        else:
            vizconnect.getTransport('main_transport').getNode3d().setPosition(0, 1.5, 0)
        
        self.snapRotateState = True
        
        root = viz.addGroup()
        root.setScale([.001]*3)
        mainViewNode = vizconnect.getDisplay().getRaw().getView()
        rootLink = viz.link(mainViewNode, root, mask=viz.LINK_ALL)
        rootLink.preTrans([0,0,2.5])

        self.instructionsScreen = viz.addText("", parent=root)
        self.instructionsScreen.fontSize(125)
        self.instructionsScreen.color(viz.WHITE)
        self.instructionsScreen.alignment(viz.ALIGN_CENTER_BOTTOM)
        self.instructionsScreen.setPosition(0, -400)
        self.instructionsScreen.drawOrder(150)
        
        self.instructionsScreen.visible(viz.OFF)
        
        self.instructionsImageQuad = viz.addTexQuad(pos=[0,1.8,0.9]) #pos=[0,0,1])
        self.instructionsImageQuad.drawOrder(125)
        self.instructionsImageQuad.visible(viz.OFF)
        
        root = viz.addGroup()
        root.setScale([.001]*3)
        mainViewNode = vizconnect.getDisplay().getRaw().getView()
        rootLink = viz.link(mainViewNode, root, mask=viz.LINK_ALL)
        rootLink.preTrans([0,0,2.5])
        
        self.ratingsScreen = viz.addText("", parent=root)
        self.ratingsScreen.fontSize(125)
        self.ratingsScreen.color(viz.WHITE)
        self.ratingsScreen.alignment(viz.ALIGN_CENTER_BOTTOM )
        self.ratingsScreen.setPosition(0, 0)
        self.ratingsScreen.drawOrder(150)
        
        self.ratingsScreen.visible(viz.OFF)
        
        if not self.serverMode and not firstlaunch:
            self.setupHighlighter()
        
        #if VIZCONNECT_CONFIG is None:
        
        
        def turnLeft(e):
            try:
                if self.snapRotateState:
                    vizconnect.getRawTransport('main_transport').snapLeft()
            except:
                pass

        def turnRight(e):
            try:
                if self.snapRotateState:
                    vizconnect.getRawTransport('main_transport').snapRight()
            except:
                pass
        
        viz.callback(viz.getEventID('SNAP_LEFT'), turnLeft)
        viz.callback(viz.getEventID('SNAP_RIGHT'), turnRight)

    def compressRecording(self, input_path, output_path, bitrate=BIT_RATE):
        try:
            from moviepy.video.io.VideoFileClip import VideoFileClip
        except ImportError:
            print("MoviePy library not found. Video compression skipped.")
            return
        
        clip = VideoFileClip(input_path)
        
        file_extension = VIDEO_FILE_TYPE.lower()
        
        # Codec mapping based on the file extension
        codec_mapping = {
            '.avi': 'mpeg4',
            '.mpg': 'mpeg2video',
            '.mp4': 'libx264'
        }
        
        codec = codec_mapping.get(file_extension, None)
        
        try:
            if codec:
                clip.write_videofile(output_path, codec=codec, bitrate=bitrate)
            else:
                clip.write_videofile(output_path, bitrate=bitrate)
            
            print(f"Compressing video with bitrate: {bitrate}")
            
            # Remove the original .avi file only if the new file is successfully created
            if os.path.exists(output_path):
                os.remove(input_path)
            else:
                print("New file was not created, original file will not be removed.")
        except Exception as e:
            print(f"An error occurred while compressing the video: {e}")
    
    def setupHighlighter(self):
        self.rHandHighlighter = highlighter.Highlighter()
        self.lHandHighlighter = highlighter.Highlighter()
                
        rArrow = vizshape.addArrow(length=0.2)
        rArrow.visible(viz.OFF)
        
        lArrow = vizshape.addArrow(length=0.2)
        lArrow.visible(viz.OFF)
    
        if "Desktop" not in VIZCONNECT_CONFIG:
            self.rHandHighlighter.setParent(self.transportNode)
            self.lHandHighlighter.setParent(self.transportNode)
        
        rightHand = vizconnect.getTracker('r_hand_tracker').getNode3d()
        leftHand = vizconnect.getTracker('l_hand_tracker').getNode3d()
        
        rArrowLink = viz.link(rightHand, rArrow)
        viz.link(rArrowLink, self.rHandHighlighter)
        
        lArrowLink = viz.link(leftHand, lArrow)
        viz.link(lArrowLink, self.lHandHighlighter)
        
        # For Desktop mode, disable the left hand highlighter completely
        # (it would appear at y=-5 due to l_hand_tracker offset)
        if "Desktop" in VIZCONNECT_CONFIG:
            self.lHandHighlighter.visible(viz.OFF)

        self.highlightState = {
            self.rHandHighlighter: False, 
            self.lHandHighlighter: False
            }
            
        
        def onHighlight(target):
#            print("highlighted: ", target)
            pass
            
        def highlightUpdate(handHighlighter):
            # Skip left hand highlighter updates in Desktop mode
            if "Desktop" in VIZCONNECT_CONFIG and handHighlighter == self.lHandHighlighter:
                return
                
            if self.highlightState[handHighlighter]:
                handHighlighter.highlight()
            else:
                handHighlighter.clear()
                
            # Check if this is right or left hand
            is_right_hand = (handHighlighter == self.rHandHighlighter)
            
            # Check auto-activation state from selector_auto
            from sightlab_utils import selector_auto as selector
            auto_active = selector.getAutoActive('right' if is_right_hand else 'left')
            
            # Show highlighter if manually toggled OR auto-activated
            if self.highlightState[handHighlighter] or auto_active:
                handHighlighter.highlight()
            else:
                handHighlighter.clear()
                
        def toggleRHighlight(e):
            # Don't toggle manual state if auto-active is currently showing the highlighter
            # This prevents the highlighter from staying on after leaving the menu
            from sightlab_utils import selector_auto as selector
            if selector.getAutoActive('right'):
                return  # Ignore toggle while pointing at menu
            self.highlightState[self.rHandHighlighter] = not self.highlightState[self.rHandHighlighter]
            
        def toggleLHighlight(e):
            # Don't toggle manual state if auto-active is currently showing the highlighter
            from sightlab_utils import selector_auto as selector
            if selector.getAutoActive('left'):
                return  # Ignore toggle while pointing at menu
            # Skip for Desktop mode
            if "Desktop" in VIZCONNECT_CONFIG:
                return
            self.highlightState[self.lHandHighlighter] = not self.highlightState[self.lHandHighlighter]
       
        self.onHighlightCallback = vizact.addCallback(highlighter.HIGHLIGHT_EVENT, onHighlight)
        
        self.rHandHighlightToggle = vizact.addCallback('secondTrigger', toggleRHighlight)
        self.lHandHighlightToggle = vizact.addCallback('secondTriggerLeft', toggleLHighlight)
        
        self.rHandHighlighter.setUpdateFunction(highlightUpdate)
        self.lHandHighlighter.setUpdateFunction(highlightUpdate)

        self.rHandHighlightToggle.setEnabled(self.hightlighterFlag)
        self.lHandHighlightToggle.setEnabled(self.hightlighterFlag)
        
        if "Desktop" in VIZCONNECT_CONFIG:
             rArrowLink.postMultLinkable(viz.MainView)

    def togglePoint(self):
        if self.sceneObjects[GAZE_POINT_OBJECT] is None or self.gazePointWindow is None or not hasattr(self.sceneObjects[GAZE_POINT_OBJECT], 'renderToMain'):
            return 
        
        if isinstance(self.sceneObjects[GAZE_POINT_OBJECT], dict):
            for client in self.sceneObjects[GAZE_POINT_OBJECT]:
                if self.sceneObjects[GAZE_POINT_OBJECT][client].renderToMain:
                    self.sceneObjects[GAZE_POINT_OBJECT][client].renderOnlyToWindows([self.gazePointWindow])
                else:
                    self.sceneObjects[GAZE_POINT_OBJECT][client].renderOnlyToWindows([viz.MainWindow, self.gazePointWindow])
                    
                self.sceneObjects[GAZE_POINT_OBJECT][client].renderToMain = not self.sceneObjects[GAZE_POINT_OBJECT].renderToMain
        else:
            if self.sceneObjects[GAZE_POINT_OBJECT].renderToMain:
                self.sceneObjects[GAZE_POINT_OBJECT].renderOnlyToWindows([self.gazePointWindow])
            else:
                self.sceneObjects[GAZE_POINT_OBJECT].renderOnlyToWindows([viz.MainWindow, self.gazePointWindow])
                
            self.sceneObjects[GAZE_POINT_OBJECT].renderToMain = not self.sceneObjects[GAZE_POINT_OBJECT].renderToMain
        
    def toggleHUD(self):
        self.overlayWindow.visible(viz.TOGGLE)
        
    def toggleGazePoint(self):
        self.gazePointWindow.visible(viz.TOGGLE)
        
    def __loadExperiment(self):
        if (self.guiFlag or self.configPath is not None):
            if self.configPath is None:
                yield self.gui.sceneInfo()
            else:
                self.gui.loadConfigFile()
            
            self.experimentSettings = self.gui.trialSettings
            
            # Stop environment file polling — no longer needed once the experiment starts
            if hasattr(self.gui, '_env_poll_timer') and self.gui._env_poll_timer is not None:
                self.gui._env_poll_timer.remove()
                self.gui._env_poll_timer = None
            
            if self.guiFlag:
                self.__launchVizconnect(self.hardwareConfig, self.vizconnectConfigArg, self.vizconnectConfigListArg, False)
                self.hud.eyeTracker = vizconnect.getTracker('eye_tracker').getRaw()

                if "Projection" in VIZCONNECT_CONFIG:
                    # In GUI mode, gazePointWindow is created in __init__ while
                    # VIZCONNECT_CONFIG is still the "Desktop" placeholder, before the
                    # real hardware config loads here - re-apply the default-off state
                    # now that VIZCONNECT_CONFIG reflects the actual selected config.
                    self.gazePointWindow.visible(viz.OFF)
        
            self.dataFileSaving = self.experimentSettings[DEFAULT][DATA_SAVING]
            
            if self.sceneObjects[GAZE_POINT_OBJECT] is None:
                if self.serverMode or self.clientMode:
                    self.sceneObjects[GAZE_POINT_OBJECT] = vizfx.addChild(DEFAULT_GAZE_POINT_PATH)
                    if self.serverMode:
                        self.sceneObjects[GAZE_POINT_OBJECT].visible(viz.OFF)

                else:
                    self.sceneObjects[GAZE_POINT_OBJECT] = vizfx.addChild(GAZE_POINT_RESOURCE_PATH + "/" + self.experimentSettings[DEFAULT][GAZE_POINT])
                                        
            if self.sceneObjects[AVATAR_HEAD_OBJECT] is None:
                if self.serverMode:
                    self.sceneObjects[AVATAR_HEAD_OBJECT] = vizfx.addChild(DEFAULT_AVATAR_HEAD_PATH)
                else:
                    # A config with no avatar selected (e.g. full-body mode) stores None
                    # here; fall back to the default head instead of crashing on str + None.
                    if self.experimentSettings[DEFAULT][AVATAR_HEAD] is None:
                        self.sceneObjects[AVATAR_HEAD_OBJECT] = vizfx.addChild(DEFAULT_AVATAR_HEAD_PATH)
                    else:
                        self.sceneObjects[AVATAR_HEAD_OBJECT] = vizfx.addChild(AVATAR_HEAD_RESOURCE_PATH + "/" + self.experimentSettings[DEFAULT][AVATAR_HEAD])
                    self.sceneObjects[AVATAR_HEAD_OBJECT].visible(viz.OFF)
                    self.sceneObjects[AVATAR_HEAD_OBJECT].disable(viz.INTERSECTION)

            if self.sceneObjects[AVATAR_RIGHT_HAND_OBJECT] is None:
                if self.serverMode:
                    self.sceneObjects[AVATAR_RIGHT_HAND_OBJECT] = vizfx.addChild(DEFAULT_AVATAR_RIGHT_HAND_PATH)
                    self.sceneObjects[AVATAR_RIGHT_HAND_OBJECT].visible(viz.OFF)
                elif self.experimentSettings[DEFAULT][AVATAR_RIGHT_HAND] is None:
                    self.sceneObjects[AVATAR_RIGHT_HAND_OBJECT] = vizfx.addChild(DEFAULT_AVATAR_RIGHT_HAND_PATH)
                else:
                    self.sceneObjects[AVATAR_RIGHT_HAND_OBJECT] = vizfx.addChild(AVATAR_HANDS_RESOURCE_PATH + "/" + self.experimentSettings[DEFAULT][AVATAR_RIGHT_HAND])
                    
            if self.sceneObjects[AVATAR_LEFT_HAND_OBJECT] is None:
                if self.serverMode:
                    self.sceneObjects[AVATAR_LEFT_HAND_OBJECT] = vizfx.addChild(DEFAULT_AVATAR_LEFT_HAND_PATH)
                    self.sceneObjects[AVATAR_LEFT_HAND_OBJECT].visible(viz.OFF)
                elif self.experimentSettings[DEFAULT][AVATAR_LEFT_HAND] is None:
                    self.sceneObjects[AVATAR_LEFT_HAND_OBJECT] = vizfx.addChild(DEFAULT_AVATAR_LEFT_HAND_PATH)
                else:
                    self.sceneObjects[AVATAR_LEFT_HAND_OBJECT] = vizfx.addChild(AVATAR_HANDS_RESOURCE_PATH + "/" + self.experimentSettings[DEFAULT][AVATAR_LEFT_HAND])
                
            if self.experimentSettings[DEFAULT][BIOPAC]:
                self.biopacFlag = True
                self.hud.BIOPAC = True
                
                if self.acqServer is None and not self.serverMode:
                    try:
                        self.acqServer = biopacndt.AcqNdtQuickConnect()
                        self.hud.acqServer = self.acqServer
                    except Exception as e:
                        print("No Acqknowledge server found")
                        self.biopacFlag = False
                        self.hud.BIOPAC = False
            else:
                self.biopacFlag = False
                self.acqServer = None
                
        if self.fadequadFlag:
            self.hud.fadeQuad.visible(viz.ON)
            yield self.hud.fadeQuad.fade_in()
        
        self.hud.writeToTimer('')
        
        # Projection (CAVE) configs carve the main window into per-wall thirds, so the
        # participant info dialog renders off-screen and blocks the experiment from
        # starting. Disable the PID prompt for these configs.
        if "Projection" in VIZCONNECT_CONFIG:
            self.pidFlag = False

        # Optitrack configs open the vizconnect live web interface browser window,
        # which conflicts with the participant info dialog and prevents the
        # experiment from continuing. Disable the PID prompt for these configs.
        if "Optitrack" in VIZCONNECT_CONFIG:
            self.pidFlag = False

        if self.pidFlag:
            self.participantData = yield self.gui.participantInfo()
            
        if self.serverMode:
            self.participantData = self.gui.participantData

        if self.headLink is None and not self.serverMode:
            self.headLink = viz.link(viz.MainView, self.sceneObjects[AVATAR_HEAD_OBJECT])
        
        if not self.serverMode:
            self.sceneObjects[GAZE_POINT_OBJECT].disable(viz.INTERSECTION)
            self.sceneObjects[GAZE_POINT_OBJECT].renderToMain = False
        
        if not self.gazePointVisibleFlag:
            self.gazePointWindow.visible(viz.OFF)
            
        if self.clientMode:
            if vizmic is None:
                raise RuntimeError('clientMode requires the vizmic module, which failed to import. Check that vizmic and its DLL dependencies are installed correctly.')
            vizmic.startMonitoring()
            
        if not self.serverMode:
            self.sceneObjects[GAZE_POINT_OBJECT].renderOnlyToWindows([self.gazePointWindow])
        
            if "Desktop" in VIZCONNECT_CONFIG:
                self.headNode = vizconnect.getTracker('head_tracker').getNode3d()
                
                self.sceneObjects[AVATAR_RIGHT_HAND_OBJECT].setParent(self.headNode)
                
                self.sceneObjects[AVATAR_LEFT_HAND_OBJECT].visible(viz.OFF)
            else:
                self.sceneObjects[AVATAR_RIGHT_HAND_OBJECT].setParent(self.transportNode)
                    
                leftHand = vizconnect.getTracker('l_hand_tracker').getNode3d()
                self.sceneObjects[AVATAR_LEFT_HAND_OBJECT].setParent(self.transportNode)
                link_tracker_left = viz.link(leftHand,self.sceneObjects[AVATAR_LEFT_HAND_OBJECT])
                
            rightHand = vizconnect.getTracker('r_hand_tracker').getNode3d()
            link_tracker_right = viz.link(rightHand, self.sceneObjects[AVATAR_RIGHT_HAND_OBJECT])
                    
        if self.gui.tempFullBodyAvatar is not None:
            self.gui.tempFullBodyAvatar.remove()
            self.gui.tempFullBodyAvatar = None
            
        if self.gui.tempAvatar is not None:
            self.gui.tempAvatar.remove()
            self.gui.tempAvatar = None
            
        if self.gui.tempText is not None:
            self.gui.tempText.remove()
            self.gui.tempText = None
                
        if self.gui.tempLHand is not None:
            self.gui.tempLHand.remove()
            self.gui.tempLHand = None
            
        if self.gui.tempRHand is not None:
            self.gui.tempRHand.remove()
            self.gui.tempRHand = None
            
        if self.gui.tempEnvironment is not None:
            self.gui.tempEnvironment.remove()
            self.gui.tempEnvironment = None
        
        if self.gui.tempMedia is not None:
            self.gui.tempMedia.remove()
            self.gui.tempMedia = None
            self.gui.mediaToggle.remove()
            
        self.experimentLoaded = True
        
    def __experimentSetup(self):
        if (self.guiFlag or self.configPath is not None) and not self.clientMode:
            if self.experimentSettings[DEFAULT][RANDOM_TRIALS]:
                tempDict = deepcopy(self.gui.trialSettings)
                
                keys = list(tempDict.keys())  # Extract keys from the input dictionary
                values = list(tempDict.values())  # Extract values (nested dictionaries) from the input dictionary
                
                # Shuffle the list of nested dictionaries
                random.shuffle(values)
                
                # Create a new dictionary with the same keys and shuffled nested dictionaries
                randomized_dict = dict(zip(keys, values))
                
                self.experimentSettings = {}
                #self.experimentSettings[DEFAULT] = self.gui.trialSettings[DEFAULT]
                
                self.experimentSettings.update(randomized_dict)
                
        self.hud.trialState = viz.OFF
        
        if self.loadEnvironmentMode == LOAD_ALL and (self.guiFlag or self.configPath is not None):
            yield self.__loadEnvironments()
            
        self.experimentSetupComplete = True

        #viz.sendEvent(EXPERIMENT_START)
        
    def __loadEnvironments(self):
        for trial in self.experimentSettings:
            trialMode = self.experimentSettings[trial][MODE]
                        
            environmentPath = os.path.join(self.gui.scriptDirectory, self.experimentSettings[trial][ENVIRONMENT_DIRECTORY], self.experimentSettings[trial][ENVIRONMENT])

            if trialMode == MODEL_3D:
                if trial in [DEFAULT] or not self.experimentSettings[trial][ENVIRONMENT] == self.experimentSettings[str(int(trial)-1)][ENVIRONMENT]:
                    self.environmentDict[trial] = vizfx.addChild(environmentPath)
                    if self.optimizeIntersectFlag:
                        self.environmentDict[trial].hint(viz.OPTIMIZE_INTERSECT_HINT)
                else:
                    self.environmentDict[trial] = self.environmentDict[str(int(trial)-1)]
                    
            else:
                self.mediaDict[trial], _ext = panorama_utils.make_video(environmentPath)
                self.mediaDict[trial] = extract_audio.attach(environmentPath, self.mediaDict[trial], _ext)

                if self.experimentSettings[trial][MEDIA_SETUP][MEDIA_FORMAT] == "Monoscopic":
                    self.environmentDict[trial] = panorama_utils.MonoSphere(self.experimentSettings[trial][MEDIA_SETUP][MEDIA_TYPE])
                elif self.experimentSettings[trial][MEDIA_SETUP][MEDIA_FORMAT] == "Stereoscopic T/B":
                    self.environmentDict[trial] = panorama_utils.StereoSphere(self.experimentSettings[trial][MEDIA_SETUP][MEDIA_TYPE])
                elif self.experimentSettings[trial][MEDIA_SETUP][MEDIA_FORMAT] == "Stereoscopic L/R":
                    self.environmentDict[trial] = panorama_utils.Stereo180Sphere(self.experimentSettings[trial][MEDIA_SETUP][MEDIA_TYPE])

                self.environmentDict[trial].texture(panorama_utils.get_texture(self.mediaDict[trial]))
                
            self.environmentDict[trial].visible(viz.OFF)
            
        yield self.__loadCurrentEnvironment()
        
        if self.sceneObjects[ENVIRONMENT_OBJECT] is not None:
            self.sceneObjects[ENVIRONMENT_OBJECT].visible(viz.OFF)
    
    def __loadCurrentEnvironment(self):
        currTrial = str(self.trialNumber)
        self.trialMode = self.experimentSettings[currTrial][MODE]

        environmentPath = os.path.join(self.gui.scriptDirectory, self.experimentSettings[currTrial][ENVIRONMENT_DIRECTORY], self.experimentSettings[currTrial][ENVIRONMENT])

        if self.loadEnvironmentMode == LOAD_ALL:
            self.dome180.visible(viz.OFF)
            
            if self.trialNumber > 1:
                self.environmentDict[str(self.trialNumber-1)].visible(viz.OFF)
                
            self.sceneObjects[ENVIRONMENT_OBJECT] = self.environmentDict[currTrial]
            self.sceneObjects[ENVIRONMENT_OBJECT].visible(viz.ON)
            
            if self.trialMode == MEDIA_360:
                self.sceneObjects[MEDIA_OBJECT] = self.mediaDict[currTrial]
                
                if self.experimentSettings[currTrial][MEDIA_SETUP][MEDIA_FORMAT] == "Stereoscopic L/R":
                    self.dome180.visible(viz.ON)
            else:
                if self.sceneObjects[MEDIA_OBJECT] is not None:
                    self.sceneObjects[MEDIA_OBJECT].stop()
                    self.sceneObjects[MEDIA_OBJECT].remove()
                    self.sceneObjects[MEDIA_OBJECT] = None
     
        else:
            if self.trialMode == MODEL_3D:
                if not self.trialNumber == 1:
                    # Check if previous trial was a different mode OR different environment
                    prevTrialMode = self.experimentSettings[str(self.trialNumber-1)][MODE]
                    prevEnvironment = self.experimentSettings[str(self.trialNumber-1)][ENVIRONMENT]
                    currEnvironment = self.experimentSettings[currTrial][ENVIRONMENT]
                    
                    # Always reload if mode changed from 360 to 3D, or if environment is different
                    if prevTrialMode != MODEL_3D or currEnvironment != prevEnvironment:
                        self.sceneObjects[ENVIRONMENT_OBJECT].remove()
                        self.sceneObjects[ENVIRONMENT_OBJECT] = vizfx.addChild(environmentPath)
                        if self.optimizeIntersectFlag:
                            self.sceneObjects[ENVIRONMENT_OBJECT].hint(viz.OPTIMIZE_INTERSECT_HINT)
                else:
                    self.sceneObjects[ENVIRONMENT_OBJECT] = vizfx.addChild(environmentPath)
                    if self.optimizeIntersectFlag:
                        self.sceneObjects[ENVIRONMENT_OBJECT].hint(viz.OPTIMIZE_INTERSECT_HINT)
                    
            else:
                if not self.trialNumber == 1:
                    self.sceneObjects[ENVIRONMENT_OBJECT].remove()
                    
                self.sceneObjects[MEDIA_OBJECT], _ext = panorama_utils.make_video(environmentPath)
                self.sceneObjects[MEDIA_OBJECT] = extract_audio.attach(environmentPath, self.sceneObjects[MEDIA_OBJECT], _ext)
                if self.experimentSettings[currTrial][MEDIA_SETUP][MEDIA_FORMAT] == "Monoscopic":
                    self.sceneObjects[ENVIRONMENT_OBJECT] = panorama_utils.MonoSphere(self.experimentSettings[currTrial][MEDIA_SETUP][MEDIA_TYPE])
                elif self.experimentSettings[currTrial][MEDIA_SETUP][MEDIA_FORMAT] == "Stereoscopic T/B":
                    self.sceneObjects[ENVIRONMENT_OBJECT] = panorama_utils.StereoSphere(self.experimentSettings[currTrial][MEDIA_SETUP][MEDIA_TYPE])
                elif self.experimentSettings[currTrial][MEDIA_SETUP][MEDIA_FORMAT] == "Stereoscopic L/R":
                    self.sceneObjects[ENVIRONMENT_OBJECT] = panorama_utils.Stereo180Sphere(self.experimentSettings[currTrial][MEDIA_SETUP][MEDIA_TYPE])
                    self.dome180.visible(viz.ON)

                self.sceneObjects[ENVIRONMENT_OBJECT].texture(panorama_utils.get_texture(self.sceneObjects[MEDIA_OBJECT]))
                self.sceneObjects[MEDIA_OBJECT] = self.sceneObjects[MEDIA_OBJECT]
        
    def __loadTrial(self):
        if self.experimentSettings[DEFAULT][NUMBER_OF_TRIALS] == -1:
            self.experimentSettings[str(self.trialNumber)] = deepcopy(self.experimentSettings[DEFAULT])
            
        vizconnect.getTransport('main_transport').setEnabled(viz.ON)
        
        if "Desktop" in VIZCONNECT_CONFIG:
            vizconnect.getRawTracker("head_tracker").setEnabled(viz.ON)
        else:
            vizconnect.getTransport('main_transport').getNode3d().setPosition(self.transportResetPos)
                        
        if not (self.guiFlag or self.configPath is not None):
            self.hud.setGazeTimeObject(self.sceneObjects[GAZE_OBJECTS])
            
            if self.trialNumber == 1:
                viz.sendEvent(EXPERIMENT_START)
            return
            
        yield self.__loadCurrentEnvironment()
        
        currTrial = str(self.trialNumber)
        
        self.hud.trialLabel = self.experimentSettings[currTrial][TRIAL_LABEL]
        
        value = self.experimentSettings[currTrial][TRACKING]
        self.trackingDataLoggingFlag = value
        self.replayDataLoggingFlag = value
        self.experimentSummaryDataLoggingFlag = value
        self.timeLineLoggingFlag = value
        self.fixationLoggingFlag = value
        
        if not self.serverMode:
            if self.trialMode == MODEL_3D:
                vizconnect.getDisplay('main_display').setParent(vizconnect.getAvatar('main_avatar').getAttachmentPoint('head'))
                self.sceneObjects[AVATAR_RIGHT_HAND_OBJECT].visible(viz.ON)
                
                if not "Desktop" in VIZCONNECT_CONFIG:
                    self.sceneObjects[AVATAR_LEFT_HAND_OBJECT].visible(viz.ON)
                    
                transportLink = vizconnect.getTransport(name='main_transport')
                transportLink.setEnabled(viz.ON)
                    
            elif self.trialMode == MEDIA_360:
                self.sceneObjects[MEDIA_OBJECT].setTime(0)
                self.sceneObjects[MEDIA_OBJECT].pause()

                vizconnect.getDisplay('main_display').setParent(vizconnect.getTracker('merged'))
                self.sceneObjects[AVATAR_RIGHT_HAND_OBJECT].visible(viz.OFF)
                self.sceneObjects[AVATAR_LEFT_HAND_OBJECT].visible(viz.OFF)

                transportLink = vizconnect.getTransport(name='main_transport')
                # Keep transport enabled for Stereoscopic L/R (180 SBS) so the
                # user can move around; disable it for full 360 spheres where
                # walking would expose the back of the sphere.
                if self.experimentSettings[currTrial][MEDIA_SETUP][MEDIA_FORMAT] == "Stereoscopic L/R":
                    transportLink.setEnabled(viz.ON)
                    if "Desktop" in VIZCONNECT_CONFIG:
                        vizconnect.getTracker('head_tracker').setEnabled(viz.ON)
                else:
                    transportLink.setEnabled(viz.OFF)
                
                self._envLink = viz.link(viz.MainView, self.sceneObjects[ENVIRONMENT_OBJECT], mask=viz.LINK_POS)
        
        if self.trialMode == MODEL_3D:
            if self.headlightFlag:
                self.headLight.enable()
            else:
                self.headLight.disable()
                
            if self.clientMode:
                viz.sendEvent(MODEL_3D_CLIENT)
        
        elif self.trialMode == MEDIA_360:
            self.headLight.enable()
            self.headLight.intensity(2)
            
            if self.clientMode:
                viz.sendEvent(MEDIA_360_CLIENT)
            
        gazeList = list(self.sceneObjects[GAZE_OBJECTS].keys())
        visibleList = list(self.sceneObjects[INVISIBLE_OBJECTS].keys())
        grabList = list(self.sceneObjects[GRAB_OBJECTS].keys())
        customList = list(self.sceneObjects[CUSTOM_OBJECTS].keys())
        roiList = list(self.sceneObjects[REGIONS_OF_INTEREST].keys())
        avatarList = list(self.sceneObjects[AVATAR_OBJECTS].keys())
        
        for item in gazeList:
            if item not in self.sceneObjects[MANUAL_ADD]:
                self.sceneObjects[GAZE_OBJECTS].pop(item)
                
        for item in visibleList:
            if item not in self.sceneObjects[MANUAL_ADD]:
                self.sceneObjects[INVISIBLE_OBJECTS].pop(item)
                
        for item in grabList:
            if item not in self.sceneObjects[MANUAL_ADD]:
                self.sceneObjects[GRAB_OBJECTS].pop(item)
                
        for item in customList:
            if item not in self.sceneObjects[MANUAL_ADD]:
                self.sceneObjects[CUSTOM_OBJECTS].pop(item)
        
        for item in avatarList:
            if item not in self.sceneObjects[MANUAL_ADD]:
                self.sceneObjects[AVATAR_OBJECTS].pop(item)
                
        for item in roiList:
            self.sceneObjects[REGIONS_OF_INTEREST][item].remove()
            self.sceneObjects[REGIONS_OF_INTEREST].pop(item)

        if self.trialMode == MODEL_3D:
            for node in self.experimentSettings[currTrial][TRIAL_SETUP]:
                if self.experimentSettings[currTrial][TRIAL_SETUP][node][TARGET] and node in self.sceneObjects[ENVIRONMENT_OBJECT].getNodeNames():
                    self.sceneObjects[GAZE_OBJECTS][node] = self.sceneObjects[ENVIRONMENT_OBJECT].getChild(node)
                
                if not self.experimentSettings[currTrial][TRIAL_SETUP][node][VISIBLE]:
                    self.sceneObjects[INVISIBLE_OBJECTS][node] = self.sceneObjects[ENVIRONMENT_OBJECT].getChild(node)
                    self.sceneObjects[INVISIBLE_OBJECTS][node].alpha(viz.OFF)
                    self.sceneObjects[INVISIBLE_OBJECTS][node].disable(viz.SHADOW_CASTING)
                else:
                    prevTrial = int(currTrial)-1
                    if prevTrial > 0 and node in self.experimentSettings[str(prevTrial)][TRIAL_SETUP] and self.experimentSettings[str(prevTrial)][TRIAL_SETUP][node][VISIBLE] == viz.OFF:
                        self.sceneObjects[ENVIRONMENT_OBJECT].getChild(node).alpha(viz.ON)
                    
                if self.experimentSettings[currTrial][TRIAL_SETUP][node][GRAB]:
                    self.sceneObjects[GRAB_OBJECTS][node] = self.sceneObjects[ENVIRONMENT_OBJECT].getChild(node)
                
                # Detect avatar nodes via AVATAR flag or Skeleton child / .cfg extension
                nodeSettings = self.experimentSettings[currTrial][TRIAL_SETUP][node]
                isAvatar = nodeSettings.get("AVATAR", False)
                if not isAvatar:
                    # Fallback detection for configs saved before AVATAR flag existed
                    try:
                        if node.lower().endswith('.cfg'):
                            isAvatar = True
                        elif not node.lower().endswith(('.osgb', '.osg', '.osgt', '.ive', '.flt', '.fbx', '.glb', '.gltf')):
                            childObj = self.sceneObjects[ENVIRONMENT_OBJECT].getChild(node)
                            if childObj and childObj.valid() and hasattr(childObj, 'getChild'):
                                skelChild = childObj.getChild('Skeleton')
                                if skelChild and skelChild.valid():
                                    isAvatar = True
                    except:
                        pass
                if isAvatar and node in self.sceneObjects[ENVIRONMENT_OBJECT].getNodeNames():
                    avatarChild = self.sceneObjects[ENVIRONMENT_OBJECT].getChild(node)
                    avatarChild._childNodeName = node
                    self.sceneObjects[AVATAR_OBJECTS][node] = avatarChild
                    # Apply animation state from GUI settings
                    animState = nodeSettings.get("STATE", 1)
                    try:
                        avatarChild.state(int(animState))
                    except (AttributeError, ValueError):
                        pass

                isAnimate = nodeSettings.get("ANIMATE", False)
                if not isAnimate and not isAvatar:
                    if node.lower().endswith('_animate') or node.lower().endswith('_animate_1'):
                        isAnimate = True
                    else:
                        try:
                            childObj = self.sceneObjects[ENVIRONMENT_OBJECT].getChild(node)
                            if childObj and childObj.valid():
                                if childObj.getNumFrames() > 0:
                                    isAnimate = True
                        except:
                            pass
                if isAnimate and not isAvatar and node in self.sceneObjects[ENVIRONMENT_OBJECT].getNodeNames():
                    animState = nodeSettings.get("STATE", 0)
                    try:
                        animChild = self.sceneObjects[ENVIRONMENT_OBJECT].getChild(node)
                        if animChild and animChild.valid():
                            kick = 1 if int(animState) == 0 else 0
                            try:
                                animChild.setAnimationState(kick)
                            except Exception:
                                pass
                            animChild.setAnimationState(int(animState))
                            loopMode = viz.OFF if node.lower().endswith('_animate_1') else viz.ON
                            animChild.setAnimationLoopMode(loopMode)
                            animChild.setAnimationSpeed(1.0)
                            try:
                                animChild.setAnimationTime(0.0)
                            except Exception:
                                pass
                    except (AttributeError, ValueError):
                        pass

        elif self.trialMode == MEDIA_360:
            for item in self.experimentSettings[currTrial][REGIONS_OF_INTEREST]:
                properties = self.experimentSettings[currTrial][REGIONS_OF_INTEREST][item]
                
                pos = properties[0]
                
                radius = properties[1]
                alpha = properties[2]
                color = properties[3]
                
                # Get 3-axis scale if available (backward compatible - defaults to [1, 1, 1])
                scaleX = properties[5] if len(properties) > 5 else 1.0
                scaleY = properties[6] if len(properties) > 6 else 1.0
                scaleZ = properties[7] if len(properties) > 7 else 1.0
                    
                newROI = vizshape.addSphere(radius = radius, color=color, alpha = alpha)
                newROI.disable(viz.SHADOW_CASTING)
                newROI.disable(viz.SHADOWS)
                newROI.setPosition(pos)
                newROI.setScale([scaleX, scaleY, scaleZ])
                
                #properties.append(properties[4])
                
                hashable_properties = tuple(tuple(x) if isinstance(x, list) else x for x in properties)

                self.sceneObjects[REGIONS_OF_INTEREST][tuple(hashable_properties)] = newROI
                
        gazeObjects = {**self.sceneObjects[GAZE_OBJECTS], **self.sceneObjects[REGIONS_OF_INTEREST]}
                
        self.hud.setGazeTimeObject(gazeObjects, float(self.experimentSettings[DEFAULT][DWELL_TIME]))
        
        self.hud.dispersionThreshold = float(self.experimentSettings[DEFAULT][DISPERSION_THRESHOLD])
        self.hud.durationThreshold = float(self.experimentSettings[DEFAULT][DURATION_THRESHOLD])
        self.hud.noiseReductionWindowSize = float(self.experimentSettings[DEFAULT][NOISE_REDUCTION])
        
        if len(self.sceneObjects[GRAB_OBJECTS]) > 0:
            grabTool = vizconnect.getRawTool('grabber')
            grabTool.setItems(list(self.sceneObjects[GRAB_OBJECTS].values()))
            
            if not "Desktop" in VIZCONNECT_CONFIG:
                grabTool2 = vizconnect.getRawTool('grabber2')
                grabTool2.setItems(list(self.sceneObjects[GRAB_OBJECTS].values()))
                
        if self.trialNumber == 1:
            viz.sendEvent(EXPERIMENT_START)
            
            self._loadFullBodyAvatars()
            
    def _loadFullBodyAvatars(self):
        # Full body avatar setup - after EXPERIMENT_START
        if self.experimentSettings[DEFAULT].get(FULL_BODY_TOGGLE, False) or self.fullBodyFlag:
            from sightlab_utils import Avatar_Body_MultiUser_IK
            avatar = vizconnect.getAvatar('main_avatar').getRaw()
            avatar.disable(viz.INTERSECTION)
            
            # Only disable lighting for Complete Characters avatars
            # Detect skeleton type by checking for Bip01 bones
            try:
                bone_list = avatar.getBoneList()
                bone_names = [bone.getName() for bone in bone_list]
                is_complete_characters = 'Bip01 Pelvis' in bone_names
                if is_complete_characters:
                    avatar.disable(viz.LIGHTING)
            except:
                pass  # If bone detection fails, leave lighting enabled
        
            if self.getConfig() in ["Vive Focus Full Body",'Vive Trackers Full Body Focus Vision','Vive Trackers Full Body','Mocopi Full Body', 'Mocopi Full Body Quest 3','Optitrack Full Body']:
                    def hideHeadMeshes(avatar):
                        for mesh_name in avatar.getMeshList():
                            if mesh_name.endswith('_hipoly_head.CMF'):
                                avatar.visible(viz.OFF, mesh_name)
                                print('Hid head mesh:', mesh_name)
                    hideHeadMeshes(avatar)
                    
            if self.getConfig() in ['Meta Quest Pro Full Body', 'Meta Quest 3 Full Body']:
                    from sightlab_utils import body_tracking_ik
                
            if self.clientMode:
                if not hasattr(self, 'ik_syncer') or self.ik_syncer is None:
                    self.ik_syncer = Avatar_Body_MultiUser_IK.AvatarIKSyncer(is_server=False)
                        
            if self.serverMode:
                if not hasattr(self, 'ik_syncer') or self.ik_syncer is None:
                    self.ik_syncer = Avatar_Body_MultiUser_IK.AvatarIKSyncer(is_server=True)
                elif self.ik_syncer.receive_only:
                    # Upgrade from receive-only to full syncer (a full-body client joined)
                    self.ik_syncer.receive_only = False
                    self.ik_syncer.request_client_setups()
            
            # Single-user mode: set up wrist rotation clamper directly
            # (In multi-user mode, AvatarIKSyncer handles this in _setup_local_wrist_clamper)
            if not self.clientMode and not self.serverMode:
                try:
                    from sightlab_utils import custom_skeletons
                    skeleton_type = self._detectAvatarSkeletonType(avatar)
                    if skeleton_type in ('mixamo', 'mixamo_generic', 'readyplayerme', 'reallusion'):
                        self.local_wrist_clamper = custom_skeletons.WristRotationClamper(
                            avatar, skeleton_type, 'local'
                        )
                except Exception as ex:
                    print(f"Could not set up wrist clamper for single-user: {ex}")
        
        # Multi-user mode: if this client/server doesn't have full body enabled,
        # still create a receive-only AvatarIKSyncer to see remote full-body avatars
        if not (self.experimentSettings[DEFAULT].get(FULL_BODY_TOGGLE, False) or self.fullBodyFlag):
            if (self.clientMode or self.serverMode) and not hasattr(self, 'ik_syncer'):
                from sightlab_utils import Avatar_Body_MultiUser_IK
                self.ik_syncer = Avatar_Body_MultiUser_IK.AvatarIKSyncer(
                    is_server=self.serverMode, receive_only=True
                )
        
        # Apply seated mode if enabled
        seated_mode_value = self.experimentSettings[DEFAULT].get(SEATED_MODE, viz.OFF)
        if seated_mode_value:
            self.setSeatedMode(True)
        
        # Apply seated head-only mode if enabled
        seated_head_only_value = self.experimentSettings[DEFAULT].get(SEATED_MODE_HEAD_ONLY, viz.OFF)
        if seated_head_only_value:
            self.setSeatedModeHeadOnly(True)
        
    def identifyStartPoint(self):
        node_names = self.sceneObjects[ENVIRONMENT_OBJECT].getNodeNames()
        
        if self.clientMode:
            name = 'SIGHTLAB_START_POINT_' + self.gui.trialSettings[DEFAULT][CLIENT_INFO][SSP_SUFFIX]
            if name in node_names:
                startMarker = self.sceneObjects[ENVIRONMENT_OBJECT].getChild(name)
                
                # Hide all related nodes
                for nodeName in node_names:
                    if name in nodeName:
                        try:
                            self.sceneObjects[ENVIRONMENT_OBJECT].getChild(nodeName).visible(viz.OFF)
                        except:
                            pass
                
                self.startPoint = startMarker.getTransform(name + "_TRANSFORM").getPosition()
                self.startEuler = startMarker.getTransform(name + "_TRANSFORM").getEuler()
                
        else:
            if SIGHTLAB_START_POINT in node_names:
                startMarker = self.sceneObjects[ENVIRONMENT_OBJECT].getChild(SIGHTLAB_START_POINT)
                
                # Hide all nodes containing SIGHTLAB_START_POINT in their name
                for nodeName in node_names:
                    if SIGHTLAB_START_POINT in nodeName:
                        try:
                            self.sceneObjects[ENVIRONMENT_OBJECT].getChild(nodeName).visible(viz.OFF)
                        except:
                            pass
                
                try:
                    transform = startMarker.getTransform(SIGHTLAB_START_POINT + "_TRANSFORM")
                    self.startPoint = transform.getPosition()
                    self.startEuler = transform.getEuler()
                except:
                    pass
                
                
        if self.clientMode or self.serverMode:
            name = 'SIGHTLAB_START_POINT_'
            for node in node_names:
                if name in node:
                    self.sceneObjects[ENVIRONMENT_OBJECT].getChild(node).visible(viz.OFF)
        
        self.setStartPoint(self.startPoint, self.startEuler)
        
    def __runTrial(self, clientDict = None, midTrialClient = False):
        yield self.__loadTrial()
        
        # Show start experiment text on first trial if configured via GUI
        if self.trialNumber == 1 and (self.guiFlag or self.configPath is not None):
            startExpText = self.experimentSettings[DEFAULT].get(START_EXPERIMENT_TEXT, '')
            if startExpText:
                yield self.showInstructions(startExpText)
                
        trialMode = self.trialMode
        
        if self.trialMode == MEDIA_360:
            if (self.guiFlag or self.configPath is not None):
                trialMode = [self.trialMode, self.experimentSettings[str(self.trialNumber)][MEDIA_SETUP][MEDIA_TYPE], self.experimentSettings[str(self.trialNumber)][MEDIA_SETUP][MEDIA_FORMAT]]
            else:
                trialMode = [self.trialMode, self.experimentSettings[DEFAULT][MEDIA_SETUP][MEDIA_TYPE], self.experimentSettings[DEFAULT][MEDIA_SETUP][MEDIA_FORMAT]]
        
        if not midTrialClient:
            yield self.__conditionEventManager(START_CONDITION)
            
            if self.instructionsScreen.getVisible():
                yield self.hideInstructions()
        
        self.hud.preTrial(
                        dateTime=self.dateTime, 
                        participantData=self.participantData, 
                        isGUI=(self.guiFlag or self.configPath is not None), 
                        trialMode=trialMode, 
                        trialNumber=self.trialNumber,
                        trialLabel=self.hud.trialLabel,
                        sceneObjects=self.sceneObjects, 
                        trackingDataLogging=self.trackingDataLoggingFlag, 
                        replayDataLogging=self.replayDataLoggingFlag,
                        experimentDataLogging=self.experimentSummaryDataLoggingFlag, 
                        timeLineLogging=self.timeLineLoggingFlag, 
                        fixationLogging=self.fixationLoggingFlag, 
                        customExperimentData=self.customExperimentDataColumns, 
                        scriptDirectory=self.gui.scriptDirectory, 
                        trialConfigFile={str(self.trialNumber): self.experimentSettings[str(self.trialNumber)]}, 
                        dataFileSaving=self.dataFileSaving, 
                        clientDict=clientDict, 
                        individualEyeIntersect=self.individualEyeIntersect,
                        customTrackingObjects = self.customTrackedObjects,
                        oldHeaders = self.oldHeaders,
                        updateRate = self.updateRate)
        
        self.identifyStartPoint()
        self.loadTrialComplete = True
        
        yield self.hud.startTrial(self.biopacFlag, self.tempFlag)
        
        if self.experimentSettings[str(self.trialNumber)][MODE] == MEDIA_360:
            self.sceneObjects[MEDIA_OBJECT].play()
            self.sceneObjects[MEDIA_OBJECT].loop()
            
        if self.__demoModeFlag:
            self.hud.writeToStatus(t(f"Demo {TRIAL_OR_SCENE}") + " " + str(self.trialNumber))
        else:
            self.hud.writeToStatus(t(f"{TRIAL_OR_SCENE}") + " " + str(self.trialNumber))

        self.firstStart = False
            
        if self.experimentSettings[DEFAULT][SCREEN_RECORD] or self.screenRecordFlag:
            if viz.res.isPublished():
                # Use the persistent folder in AppData for recordings in published mode
                recordings_dir = viz.res.getPublishedPath(DEFAULT_RECORDINGS_DIRECTORY)
                print('published video saved to',recordings_dir)
            else:
                # Use the original path in development mode
                recordings_dir = os.path.join(self.gui.scriptDirectory, self.gui.recordingsDirectory)
                print('video saved to',recordings_dir)
            
            os.makedirs(recordings_dir, exist_ok=True)
#            self.recordingPath = os.path.join(self.gui.scriptDirectory, self.gui.recordingsDirectory, RECORDING_FILE).format(date = self.dateTime, p=self.participantData, t=self.trialNumber)
            self.recordingPath = os.path.join(recordings_dir, RECORDING_FILE.format(date=self.dateTime, p=self.participantData[ID], t=self.trialNumber))
            viz.window.startRecording(self.recordingPath)
                    
        yield self.__conditionEventManager(END_CONDITION)
        
        if self.experimentSettings[str(self.trialNumber)][MODE] == MEDIA_360:
            self.sceneObjects[MEDIA_OBJECT].pause()
        
        self.hud.writeToStatus(t("Saving Trial") + " " + str(self.trialNumber) + "...")
        
        self.trialNumber += 1
        yield self.hud.endTrial(self.biopacFlag, self.getTrialNumber()-1)
        
        if self.experimentSettings[DEFAULT][SCREEN_RECORD] or self.screenRecordFlag:
            viz.window.stopRecording()
            
            if COMPRESS_VIDEOS == True:
                input_path = self.recordingPath
                base_name = self.recordingPath[0]
                output_path = self.recordingPath[:-3] + VIDEO_FILE_TYPE
                self.compressRecording(input_path, output_path)
        
        if self.experimentSettings[DEFAULT].get(BARCHART, viz.OFF) or self.barchartFlag:
            self._generateBarchart()

    _BARCHART_COLORS = [
        '#008080', '#FFA500', '#4682B4', '#008000', '#0000FF', 
        '#4B0082', '#EE82EE', '#D2B48C', '#008080', '#D8BFD8', 
        '#FF6347', '#BA55D3', '#000080', '#808000', '#6B8E23', 
        '#F5F5DC', '#D2B48C', '#FF0000', '#D8BFD8', '#40E0D0', 
        '#EE82EE', '#F5DEB3', '#FFFF00', '#9ACD32'
    ]

    def _generateBarchart(self):
        """Generate a barchart PDF showing object view and dwell time data for the current trial."""
        try:
            import numpy as np
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
        except ImportError:
            viz.logWarn('Barchart requires numpy and matplotlib. Install them via the Package Manager.')
            return

        plotData = self.getPlotData()
        if not plotData:
            return

        fileName = '{d}_{p}_experiment_data_trial_{t}.pdf'.format(
            d=self.dateTime, p=self.participantData[ID], t=self.getTrialNumber() - 1)
        fullPath = os.path.join(self.getExperimentDataFolderPath(), fileName)

        data_length = len(plotData)
        ind = np.arange(2)
        width = 0.25 * 3 / data_length

        fig, ax = plt.subplots(num='Object Views and Dwell Times', figsize=(13, 10))

        views_text = 'Views per object\n\n'
        for count, d in enumerate(plotData):
            color = self._BARCHART_COLORS[count % len(self._BARCHART_COLORS)]

            if data_length % 2 == 0:
                offset = width * (count - data_length / 2.0 + 0.5)
            else:
                offset = width * (count - (data_length - (data_length / 2.0 + 0.5)))

            ax.bar(ind + offset, [d[2], d[3]], width, color=color, label=d[0])
            views_text += '{}: {}\n'.format(d[0], d[1])

        ax.set_ylabel('Seconds')
        ax.set_xticks(ind)
        ax.set_xticklabels(('Total View Time', 'Average Time'))
        ax.legend()

        fig.text(0.1, 0.45, views_text, fontsize='xx-large')
        plt.subplots_adjust(left=0.4)

        os.makedirs(os.path.dirname(fullPath), exist_ok=True)
        plt.savefig(fullPath)
        plt.close(fig)

    def resetViewPoint(self, event = None, pos = [0.0, 1.8, 0.25], ori = [0.0, 0.0, 0.0]):
        if self.gui.trialSettings[self.gui.currTrial][MODE] == MEDIA_360 and not self.experimentSetupComplete:
            return
            
        display = vizconnect.getDisplay()
        oriMode = vizconnect.VIEWPOINT_MATCH_DISPLAY
        posMode = vizconnect.VIEWPOINT_MATCH_DISPLAY
        offset = [0.0, 1.8, 0.25]
        pos[0] = self.startPoint[0] + offset[0]
        pos[1] = self.startPoint[1] + offset[1]
        pos[2] = self.startPoint[2] + offset[2]
        
        ori = self.startEuler
        
        vp = vizconnect.addViewpoint(pos=self.startPoint, euler=self.startEuler, oriMode = oriMode, posMode = posMode)
        vp.add(display)
        
        vizconnect.resetViewpoints()
        vp.getNode3d().setPosition(pos, mode = viz.ABS_GLOBAL)
        vp.getNode3d().setEuler(ori, mode = viz.ABS_GLOBAL)
        
        self.viewPointReset = True
        
    def resetTrial(self):
        self.setStartPoint(self.startPoint, self.startEuler)
        
        self.hud.bufferTime = 0.0
        self.hud.timerLength = -1
        self.startConditionEvent = []
        self.endConditionEvent = []
        self.hud.startTime = None
        self.loadTrialComplete = False
        
#        self.hud.startTimerLength = -1
        
        self.hud.sessionRecorder.timeLine = {}
    
        self.hud.writeToConsole("", "")
                
        if self.sceneObjects[MEDIA_OBJECT] is not None:
            if self.guiFlag:
                self.sceneObjects[MEDIA_OBJECT].pause()
                self.sceneObjects[MEDIA_OBJECT].stop()
                self.sceneObjects[MEDIA_OBJECT].remove()
                self.sceneObjects[MEDIA_OBJECT] = None
                
            return
            
        try:
            if len(self.hud.sessionRecorder.replayData[OBJECT_TRACKER]) > 1:
                initialSceneKey = list(self.hud.sessionRecorder.replayData[OBJECT_TRACKER].keys())[1]
            
                sceneData = self.hud.sessionRecorder.replayData[OBJECT_TRACKER][initialSceneKey]
                
                if self.serverMode:
                    sceneData = sceneData[next(iter(sceneData))]
            
                for item in [ENVIRONMENT_OBJECT]:#, AVATAR_HEAD_OBJECT, AVATAR_RIGHT_HAND_OBJECT, GAZE_POINT_OBJECT]:
                    self.sceneObjects[item].setPosition(sceneData[item][POSITION])
                    self.sceneObjects[item].setEuler(sceneData[item][ORIENTATION])
                    #self.sceneObjects[item].setScale(sceneData[item][SCALE])
                    
                for item in self.sceneObjects[GRAB_OBJECTS]:
                    self.sceneObjects[GRAB_OBJECTS][item].setPosition(sceneData[GRAB_OBJECTS][item][POSITION])
                    self.sceneObjects[GRAB_OBJECTS][item].setEuler(sceneData[GRAB_OBJECTS][item][ORIENTATION])
                    #self.sceneObjects[GRAB_OBJECTS][item].setScale(sceneData[GRAB_OBJECTS][item][SCALE])
                    
                for item in self.sceneObjects[CUSTOM_OBJECTS]:
                    self.sceneObjects[CUSTOM_OBJECTS][item].setPosition(sceneData[CUSTOM_OBJECTS][item][POSITION])
                    self.sceneObjects[CUSTOM_OBJECTS][item].setEuler(sceneData[CUSTOM_OBJECTS][item][ORIENTATION])
                    #self.sceneObjects[CUSTOM_OBJECTS][item].setScale(sceneData[CUSTOM_OBJECTS][item][SCALE])
                    
                for item in self.sceneObjects[AVATAR_OBJECTS]:
                    if item in sceneData[AVATAR_OBJECTS]:
                        avatarObj = self.sceneObjects[AVATAR_OBJECTS][item]
                        avatarData = sceneData[AVATAR_OBJECTS][item]
                        isChild = avatarData.get('isChild', False)
                        if isChild:
                            avatarObj.setPosition(avatarData[POSITION])
                            avatarObj.setEuler(avatarData[ORIENTATION])
                        else:
                            avatarObj.setPosition(avatarData[POSITION])
                            avatarObj.setEuler(avatarData[ORIENTATION])
                        #avatarObj.setScale(avatarData[SCALE])
                        animState = avatarData[AVATAR_STATE]
                        try:
                            avatarObj.state(animState)
                        except AttributeError:
                            pass
        except:
            print('reset failed')

    def setStartPoint(self, POSITION = None, ORIENTATION = None):
        enableFlag  = vizconnect.getTransport('main_transport').getEnabled()
        vizconnect.getTransport('main_transport').setEnabled(viz.ON)

        if POSITION is not None:
            self.startPoint = POSITION

            # Apply seated mode offset if enabled - ONLY for Complete Characters
            seated_mode_enabled = hasattr(self, '_seated_mode_requested') and self._seated_mode_requested

            # Detect avatar type to determine if we should apply offset
            avatar_type = None
            apply_offset = False
            try:
                avatar_wrapper = vizconnect.getAvatar('main_avatar')
                if avatar_wrapper:
                    local_avatar = avatar_wrapper.getRaw()
                    if local_avatar:
                        if local_avatar.getBone('Bip01 Pelvis'):
                            avatar_type = 'complete_characters'
                            apply_offset = True  # Only Complete Characters get transport offset
                        elif local_avatar.getBone('Hips'):
                            avatar_type = 'mixamo'
            except:
                pass

            # Calculate offset based on avatar type and mode
            is_desktop = "Desktop" in VIZCONNECT_CONFIG
            if is_desktop and avatar_type == 'mixamo':
                # Desktop Mixamo/RPM base offset + seated addon if enabled
                base_offset = -0.26
                seated_addon = -0.34 if seated_mode_enabled else 0.0
                total_offset = base_offset + seated_addon
            elif is_desktop and avatar_type == 'complete_characters':
                # Desktop Complete Characters offset for standing + seated addon
                base_offset = -0.291
                seated_addon = -0.367 if seated_mode_enabled else 0.0
                total_offset = base_offset + seated_addon
            elif not is_desktop:
                # VR full body modes need a small upward offset
                total_offset = 0.18
            else:
                total_offset = 0.0

            if self.trialMode == MEDIA_360 and self.serverMode:
                self.transportNode.setPosition([0, -1.8 + total_offset, -1])
            else:
                # Apply offset to Y position
                pos_with_offset = [POSITION[0], POSITION[1] + total_offset, POSITION[2]]
                self.transportNode.setPosition(pos_with_offset)
        if ORIENTATION is not None:
            self.startEuler = ORIENTATION
            self.transportNode.setEuler(ORIENTATION)
        if self.viewPointReset:
            self.resetViewPoint()
                    
        vizconnect.getTransport('main_transport').setEnabled(enableFlag)
        
    def runExperiment(self):
        yield self.__loadExperiment()
        
        if self.__demoModeFlag:
            if not self.repetitionCount <= self.__demoRepetitionCount:
                self.repetitionCount = self.__demoRepetitionCount
                vizinput.message("Repetition count limited to" + str(self.__demoRepetitionCount) + " on Demo Mode")
                
            if not int(self.experimentSettings[DEFAULT][NUMBER_OF_TRIALS]) <= self.__demoTrialCount and not int(self.experimentSettings[DEFAULT][NUMBER_OF_TRIALS]) == -1:
                self.experimentSettings[DEFAULT][NUMBER_OF_TRIALS] = self.__demoTrialCount
                vizinput.message("Trial count limited to " + str(self.__demoTrialCount) + " on Demo Mode")
        
        for i in range(self.repetitionCount):
            self.currentRepetition = i+1
            
            if self.repetitionCount > 1:
                global RECORDING_FILE, REPLAY_DATA_FILE, TRIAL_DATA_FILE, EXPERIMENT_SUMMARY_FILE, TRIAL_TIMELINE_DATA_FILE
                
                RECORDING_FILE = '{date}_{p}_trial_recording_' + 'block_' + str(self.currentRepetition) + '_{t}.avi'
                REPLAY_DATA_FILE = '{date}_{p}_replay_data_' + 'block_' + str(self.currentRepetition) + '_{t}.rply'
                TRIAL_DATA_FILE = '{date}_{p}_trial_data_' + 'block_' + str(self.currentRepetition) + '_{t}.csv'
                EXPERIMENT_SUMMARY_FILE = '{date}_{p}_' + 'block_' + str(self.currentRepetition) + '_experiment_summary.csv'
                TRIAL_TIMELINE_DATA_FILE = '{date}_{p}_trial_timeline_' + 'block_' + str(self.currentRepetition) + '_{t}.csv'
                
            self.hud.disableProgression = viz.ON
            yield self.__experimentSetup()

            self.hud.disableProgression = viz.OFF
            self.hud.writeToStatus(START_TEXT)
            
            while (self.trialNumber <= int(self.experimentSettings[DEFAULT][NUMBER_OF_TRIALS])) or self.experimentSettings[DEFAULT][NUMBER_OF_TRIALS] == -1:
                yield self.__runTrial()
                self.hud.writeToStatus(t("Saved Trial") + " " + str(self.trialNumber-1))
                
                self.resetTrial()
                                
            # Show end experiment text if configured via GUI
            if self.guiFlag or self.configPath is not None:
                endExpText = self.experimentSettings[DEFAULT].get(END_EXPERIMENT_TEXT, '')
                if endExpText:
                    yield self.showInstructions(endExpText)
            
            if self.currentRepetition == self.repetitionCount:
                self.hud.writeToStatus(t("Experiment Complete"))
            else:
                self.hud.writeToStatus(t("Starting Repetition") + " " + str(self.currentRepetition + 1))
                
            viz.sendEvent(EXPERIMENT_END)
            self.experimentEnd = True
            self.resetExperiment()
            
    def resetExperiment(self):
        self.trialNumber = 1
        self.firstStart = True
        self.sceneObjects[ENVIRONMENT_OBJECT].remove()
        self.pidFlag = False
        self.dateTime = datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
        self.loadTrialComplete = False
        
        self.experimentSetupComplete = False
        
#        if self.headLink is not None:
#            self.headLink.remove()
#            
#        self.headLink = None
            
    def showGazePath(self, scanPathType = GAZE, waitKey = CONTINUE_EVENT_KEY):
        playHead = len()
        viz.startLayer(viz.POINTS)
        viz.pointSize(self.scanPathConfig[POINT_SIZE])
        viz.vertexColor(self.scanPathConfig[POINT_COLOR])
        
        for i in range(0, playHead, self.samplingRate):
            viz.vertex(self.gazePoints[self.timeStampList[i]])
        
        self.scanPath[POINTS_LAYER] = viz.endLayer()
        
        viz.startLayer(viz.LINES)
        viz.lineWidth(self.scanPathConfig[LINE_WIDTH])
        viz.vertexColor(self.scanPathConfig[LINE_COLOR])
        
        self.scanPath[LINE_LAYERS] = []
        
        if scanPathType == DYNAMIC_GAZE_PATH:
            for i in range(0, playHead - self.samplingRate, self.samplingRate):
                begin = self.gazePoints[self.timeStampList[i]]
                end = self.gazePoints[self.timeStampList[i + self.samplingRate]]
                
                if vizmat.Distance(begin, end) > self.scanPathDistanceThreshold:
                    lineLayer = viz.endLayer()
                    lineLayer.alpha(0.5)
                    self.scanPath[LINE_LAYERS].append(lineLayer)
                    
                    viz.startLayer(viz.LINES)
                    viz.lineWidth(self.scanPathConfig[LINE_WIDTH])
                    viz.vertexColor(self.scanPathConfig[LINE_COLOR])
                else:
                    viz.vertex(begin)
                    viz.vertex(end)
                    
        elif scanPathType == DYNAMIC_SACCADE_PATH:
            for i in range(0, playHead - self.samplingRate, self.samplingRate):
                begin = self.gazePoints[self.timeStampList[i]]
                end = self.gazePoints[self.timeStampList[i + self.samplingRate]]
                
                avatarHead = self.currentTrialData[OBJECT_TRACKER][self.timeStampList[i]][AVATAR_HEAD_OBJECT][POSITION]
                beginVector = [begin[0] - avatarHead[0], begin[1] - avatarHead[1], begin[2] - avatarHead[2]]
                endVector = [end[0] - avatarHead[0], end[1] - avatarHead[1], end[2] - avatarHead[2]]
                
                saccadeAngle = vizmat.AngleBetweenVector(endVector, beginVector)

                if saccadeAngle > self.scanPathMinSaccadeAngle and saccadeAngle < self.scanPathMaxSaccadeAngle:
                    viz.startLayer(viz.LINES)
                    viz.lineWidth(self.scanPathConfig[LINE_WIDTH])
                    viz.vertexColor(self.scanPathConfig[LINE_COLOR])
                    
                    viz.vertex(begin)
                    viz.vertex(end)
                    
                    lineLayer = viz.endLayer()
                    
                    self.scanPath[LINE_LAYERS].append(lineLayer)
                
        lineLayer = viz.endLayer()
        lineLayer.alpha(0.5)
        self.scanPath[LINE_LAYERS].append(lineLayer)
        
    def sceneToggle(self, state):
        """Toggle visibility of scene objects.
        
        Controls visibility of environment, avatars, gaze points, and custom objects.
        Used during instruction screens to hide/show the experiment scene.
        
        Args:
            state: viz.ON to show objects, viz.OFF to hide objects.
        """
        toggleList = [ENVIRONMENT_OBJECT, AVATAR_HEAD_OBJECT, AVATAR_RIGHT_HAND_OBJECT, GAZE_POINT_OBJECT]
        if not "Desktop" in VIZCONNECT_CONFIG:
            toggleList.append(AVATAR_LEFT_HAND_OBJECT)
            
        for item in toggleList:
            if self.sceneObjects[item] is not None:
                if not isinstance(self.sceneObjects[item], dict):
                    self.sceneObjects[item].visible(state)
                else:
                    for client in self.sceneObjects[item]:
                        self.sceneObjects[item][client].visible(state)
            
        for item in self.sceneObjects[CUSTOM_OBJECTS]:
            if self.sceneObjects[CUSTOM_OBJECTS][item] is not None:
                if not isinstance(self.sceneObjects[CUSTOM_OBJECTS][item], list):
                    self.sceneObjects[CUSTOM_OBJECTS][item].visible(state)
                else:
                    self.sceneObjects[CUSTOM_OBJECTS][item][0].visible(state)

                
#        for highlighter in self.highlightState:
#            self.highlightState[highlighter] = state
            
    def showInstructions(self, message = '', image = None, pauseTimer = False):
        """Display an instruction screen with optional image.
        
        This is a generator function. Fades in, shows text/image, and optionally pauses data logging.
        
        Args:
            message: Instruction text to display (default '').
            image: Path to image file to display (default None).
            pauseTimer: Pause data logging during display (default False).
            
        Yields:
            Waits for fade-in to complete.
            
        Returns:
            viz.VizNode: The image quad if image provided, None otherwise.
        """
        if pauseTimer and self.hud.sceneUpdate is not None:
            self.setDataLoggingState(False)
        
        self.headLight.enable()
        
        yield self.hud.fadeQuad.fade_in()
        self.hud.fadeQuad.visible(viz.ON)
        
        self.instructionsScreen.message(message.replace('\\n', '\n'))
        self.instructionsScreen.visible(viz.ON)
        
        self.sceneToggle(viz.OFF)
        
        if image is not None:
            pic = viz.addTexture(image)
            self.instructionsImageQuad.texture(pic)
            self.instructionsImageQuad.visible(viz.ON)
            return self.instructionsImageQuad

        
    def hideInstructions(self, pauseTimer = False, endFade = True):
        """Hide the instruction screen and resume scene.
        
        This is a generator function. Optionally resumes data logging and fades out.
        
        Args:
            pauseTimer: Resume data logging after hiding (default False).
            endFade: Fade out before hiding (default True).
            
        Yields:
            Waits for fade-out to complete (if endFade=True).
        """
        if pauseTimer and self.hud.sceneUpdate is not None and not self.hud.sceneUpdate.getEnabled():
            self.setDataLoggingState(True)
            
        if not self.headlightFlag:
            if not self.trialMode == MEDIA_360:
                self.headLight.disable()
        
        self.sceneToggle(viz.ON)
            
        self.instructionsScreen.visible(viz.OFF)
        self.instructionsImageQuad.visible(viz.OFF)
        
        if endFade:
            yield self.hud.fadeQuad.fade_out()
            self.hud.fadeQuad.visible(viz.OFF)
        
        
#    def showRatings(self, message, ratingScale = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'], color = viz.WHITE, characterLimit = 8, pauseTimer = True, endFade = True):
#        """Display a rating scale interface for participant responses.
#        
#        This is a generator function. Shows a message with selectable rating options.
#        
#        Args:
#            message: Question or prompt text to display.
#            ratingScale: List of rating options (default ['0'..'10']).
#            color: Text color (default viz.WHITE).
#            characterLimit: Maximum characters in text input (default 8).
#            pauseTimer: Pause data logging during display (default True).
#            endFade: Fade out after selection (default True).
#            
#        Yields:
#            Waits for fade-in, user selection, and optional fade-out.
#            
#        Returns:
#            str: The selected rating value.
#        """
#        if pauseTimer:
#            self.setDataLoggingState(False)
#            
#        self.headLight.enable()
#        
#        yield self.hud.fadeQuad.fade_in()
#        self.hud.fadeQuad.visible(viz.ON)
#        
#        self.ratingsScreen.message(message)
#        self.ratingsScreen.visible(viz.ON)
#        
#        self.snapRotateState = False
#        
#        if "Desktop" in VIZCONNECT_CONFIG:
#            headNode = vizconnect.getTracker('head_tracker')
#            headNode.setEnabled(viz.OFF)
#        
#        optionsCount = len(ratingScale)
#        
#        start_x = -800
#        start_y = -400
#        
#        end_x = 1400
#        end_y = -400
#        
#        increment = (end_x - start_x)/optionsCount
#        
#        root = viz.addGroup()
#        root.setScale([.001]*3)
#        mainViewNode = vizconnect.getDisplay().getRaw().getView()
#        rootLink = viz.link(mainViewNode, root, mask=viz.LINK_ALL)
#        rootLink.preTrans([0,0,2.5])
#        
#        self.currChoice = 0
#        
#        def split_text(text, char_limit=8):
#            words = text.split()
#            lines = []
#            line = ""
#            
#            for word in words:
#                while len(word) > 0:
#                    remaining_space = char_limit - len(line)
#                    
#                    if remaining_space >= len(word) + 1:  # 1 for the space
#                        line += word + " "
#                        break  # Exit the while loop, proceed to the next word
#                    else:
#                        if remaining_space > 1:
#                            line += word[:remaining_space - 1] + "-"
#                            word = word[remaining_space - 1:]
#                        lines.append(line.rstrip())
#                        line = ""
#                        
#            lines.append(line.rstrip())
#            
#            return "\n".join(lines)
#            
#        for option in ratingScale:
#            cleanedOption = split_text(option, characterLimit)
#            
#            ResponseText = viz.addText(cleanedOption, parent=root)
#            ResponseText.fontSize(150)
#            ResponseText.color(color)
#            ResponseText.alignment(viz.ALIGN_CENTER_BOTTOM)
#            ResponseText.setPosition(start_x + ratingScale.index(option)*increment, start_y)
#            ResponseText.drawOrder(150)
#            ResponseText.visible(viz.OFF)
#            self.ResponseList.append(ResponseText)
#            
#        self.ResponseList[self.currChoice].fontSize(150)
#        self.ResponseList[self.currChoice].color(viz.GREEN)
#        self.headLight.enable()
#        
#        yield self.hud.fadeQuad.fade_in()
#        self.hud.fadeQuad.visible(viz.ON)
# 
#        self.ratingsScreen.message(message)
#        self.ratingsScreen.visible(viz.ON)
#        
#        for i in self.ResponseList:
#            i.visible(viz.ON)
#        
#        self.sceneToggle(viz.OFF)
#
#        def change_feeling(change):
#            # reset the current text
#            self.ResponseList[self.currChoice].color(color)
#            self.ResponseList[self.currChoice].fontSize(150)
#            # check the limits of emotions
#            if self.currChoice + change >= optionsCount:
#                self.currChoice = optionsCount-1
#            elif self.currChoice + change < 0:
#                self.currChoice = 0
#            else:
#                self.currChoice = self.currChoice + change
#            # announce how you feel
#            self.ResponseList[self.currChoice].color(viz.GREEN)
#
#        def show_final_feeling():
#            self.ResponseList[self.currChoice].fontSize(175)
#            self.ResponseList[self.currChoice].color(viz.GREEN)
#                
#        def pressRight(e):
#            change_feeling(1)
#                
#        def pressLeft(e):
#            change_feeling(-1)
#
#        def pressConfirm(e):
#            show_final_feeling()
#            print('subject chose: ' + ratingScale[self.currChoice])
#            if pauseTimer:
#                self.setDataLoggingState(True)
#            self.setCustomTrialData(' subject chose: ' + ratingScale[self.currChoice])
#            self.ratingChoice = ratingScale[self.currChoice]
#
#        viz.callback(viz.getEventID('pressRight'), pressRight)
#        viz.callback(viz.getEventID('pressLeft'), pressLeft)
#        viz.callback(viz.getEventID('triggerPress'), pressConfirm)
#        
#        yield viztask.waitEvent('triggerPress')
#        
#        yield self.hideRatings(endFade)
#                        
#        if "Desktop" in VIZCONNECT_CONFIG:
#            headNode = vizconnect.getTracker('head_tracker')
#            headNode.setEnabled(viz.ON)

    def showRatings(self, message, ratingScale = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'], color = viz.WHITE, characterLimit = 8, pauseTimer = True, endFade = True, uiScale = 1.0):
        """Display a rating scale interface for participant responses.

        This is a generator function. Shows a message with selectable rating options.
        Automatically switches to vertical layout for long answer options.
        
        Args:
            message: Question or prompt text to display.
            ratingScale: List of rating options (default ['0'..'10']).
            color: Text color (default viz.WHITE).
            characterLimit: Maximum characters in text input (default 8).
            pauseTimer: Pause data logging during display (default True).
            endFade: Fade out after selection (default True).
            
        Yields:
            Waits for fade-in, user selection, and optional fade-out.
            
        Returns:
            str: The selected rating value.
        """
        if pauseTimer:
            self.setDataLoggingState(False)
            
        self.headLight.enable()
        
        yield self.hud.fadeQuad.fade_in()
        self.hud.fadeQuad.visible(viz.ON)
        
        # Wrap the question message for better readability in VR
        def wrap_question(text, char_limit=45):
            """Wrap question text at word boundaries."""
            if len(text) <= char_limit:
                return text, 1
            
            words = text.split()
            lines = []
            current_line = ""
            
            for word in words:
                if len(current_line) + len(word) + 1 <= char_limit:
                    current_line += (" " if current_line else "") + word
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            return "\n".join(lines), len(lines)
        
        wrapped_message, question_lines = wrap_question(message, 45)
        
        self.ratingsScreen.fontSize(int(125 * uiScale))
        self.ratingsScreen.message(wrapped_message)
        self.ratingsScreen.visible(viz.ON)

        self.snapRotateState = False
        
        if "Desktop" in VIZCONNECT_CONFIG:
            headNode = vizconnect.getTracker('head_tracker')
            headNode.setEnabled(viz.OFF)
        
        optionsCount = len(ratingScale)
        
        # Determine if we should use vertical layout
        # Use vertical if any option has more than 7 characters
        # This keeps horizontal layout for short options like ['0'..'10'] but switches to vertical for longer text
        max_option_len = max(len(opt) for opt in ratingScale)
        use_vertical = max_option_len > 7

        root = viz.addGroup()
        root.setScale([.001 * uiScale]*3)
        mainViewNode = vizconnect.getDisplay().getRaw().getView()
        rootLink = viz.link(mainViewNode, root, mask=viz.LINK_ALL)
        rootLink.preTrans([0, 0, 2.5])
        
        self.currChoice = 0
        
        # Calculate extra offset for answers if question wraps to multiple lines
        # Each additional line of question text needs ~100 units of space
        question_offset = (question_lines - 1) * 100
        
        if use_vertical:
            # VERTICAL LAYOUT - options stacked top to bottom with letter prefixes
            # Position BELOW the question text (which appears around y=0 to y=200)
            start_x = -1300  # Left-aligned (further left)
            start_y = -100 - question_offset   # Start BELOW the question, adjusted for multi-line questions
            line_height = 180  # Space between options (more room for highlighting)
            
            # Adjust line height based on longest option (for wrapped text)
            if max_option_len > 80:
                line_height = 220
            elif max_option_len > 50:
                line_height = 200
            
            def wrap_text_vertical(text, char_limit=80):
                """Wrap text at word boundaries for readability."""
                if len(text) <= char_limit:
                    return text
                
                words = text.split()
                lines = []
                current_line = ""
                
                for word in words:
                    if len(current_line) + len(word) + 1 <= char_limit:
                        current_line += (" " if current_line else "") + word
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                
                if current_line:
                    lines.append(current_line)
                
                return "\n".join(lines)
            
            for idx, option in enumerate(ratingScale):
                # Add letter prefix for easy identification
                letter = chr(65 + idx)  # A, B, C, D...
                display_text = f"{letter}) {option}"
                wrapped_text = wrap_text_vertical(display_text, 80)
                
                ResponseText = viz.addText(wrapped_text, parent=root)
                ResponseText.fontSize(80)
                ResponseText.color(color)
                ResponseText.alignment(viz.ALIGN_LEFT_TOP)
                ResponseText.setPosition(start_x, start_y - idx * line_height)
                ResponseText.drawOrder(150)
                ResponseText.visible(viz.OFF)
                self.ResponseList.append(ResponseText)
        else:
            # HORIZONTAL LAYOUT - original behavior for short options
            start_x = -800
            start_y = -400 - question_offset  # Adjusted for multi-line questions
            end_x = 1400
            end_y = -400 - question_offset
            increment = (end_x - start_x) / optionsCount
            
            def split_text(text, char_limit=8):
                words = text.split()
                lines = []
                line = ""
                
                for word in words:
                    while len(word) > 0:
                        remaining_space = char_limit - len(line)
                        
                        if remaining_space >= len(word) + 1:  # 1 for the space
                            line += word + " "
                            break  # Exit the while loop, proceed to the next word
                        else:
                            if remaining_space > 1:
                                line += word[:remaining_space - 1] + "-"
                                word = word[remaining_space - 1:]
                            lines.append(line.rstrip())
                            line = ""
                            
                lines.append(line.rstrip())
                
                return "\n".join(lines)
                
            for option in ratingScale:
                cleanedOption = split_text(option, characterLimit)
                
                ResponseText = viz.addText(cleanedOption, parent=root)
                ResponseText.fontSize(150)
                ResponseText.color(color)
                ResponseText.alignment(viz.ALIGN_CENTER_BOTTOM)
                ResponseText.setPosition(start_x + ratingScale.index(option)*increment, start_y)
                ResponseText.drawOrder(150)
                ResponseText.visible(viz.OFF)
                self.ResponseList.append(ResponseText)
            
        self.ResponseList[self.currChoice].fontSize(100 if use_vertical else 150)
        self.ResponseList[self.currChoice].color(viz.GREEN)
        self.headLight.enable()
        
        yield self.hud.fadeQuad.fade_in()
        self.hud.fadeQuad.visible(viz.ON)

        self.ratingsScreen.message(wrapped_message)
        self.ratingsScreen.visible(viz.ON)
        
        for i in self.ResponseList:
            i.visible(viz.ON)
        
        self.sceneToggle(viz.OFF)

        def change_feeling(change):
            # reset the current text
            self.ResponseList[self.currChoice].color(color)
            self.ResponseList[self.currChoice].fontSize(80 if use_vertical else 150)
            # check the limits of emotions
            if self.currChoice + change >= optionsCount:
                self.currChoice = optionsCount-1
            elif self.currChoice + change < 0:
                self.currChoice = 0
            else:
                self.currChoice = self.currChoice + change
            # announce how you feel
            self.ResponseList[self.currChoice].color(viz.GREEN)
            self.ResponseList[self.currChoice].fontSize(100 if use_vertical else 150)

        def show_final_feeling():
            self.ResponseList[self.currChoice].fontSize(110 if use_vertical else 175)
            self.ResponseList[self.currChoice].color(viz.GREEN)
                
        def pressRight(e):
            change_feeling(1)
                
        def pressLeft(e):
            change_feeling(-1)

        def pressConfirm(e):
            show_final_feeling()
            print('subject chose: ' + ratingScale[self.currChoice])
            if pauseTimer:
                self.setDataLoggingState(True)
            self.setCustomTrialData(' subject chose: ' + ratingScale[self.currChoice])
            self.ratingChoice = ratingScale[self.currChoice]

        viz.callback(viz.getEventID('pressRight'), pressRight)
        viz.callback(viz.getEventID('pressLeft'), pressLeft)
        viz.callback(viz.getEventID('triggerPress'), pressConfirm)
        
        yield viztask.waitEvent('triggerPress')
        
        yield self.hideRatings(endFade)
                        
        if "Desktop" in VIZCONNECT_CONFIG:
            headNode = vizconnect.getTracker('head_tracker')
            headNode.setEnabled(viz.ON)
    
    def hideRatings(self, endFade):
        if not self.headlightFlag:
            self.headLight.disable()
            
        viz.callback(viz.getEventID('pressRight'), 0)
        viz.callback(viz.getEventID('pressLeft'), 0)
        viz.callback(viz.getEventID('triggerPress'), 0)
        
        self.sceneToggle(viz.ON)
        self.snapRotateState = True
        
        self.ratingsScreen.visible(viz.OFF)
        
        for r in self.ResponseList:
                r.message(' ')
                r.visible(viz.OFF)
                r.remove()
                
        self.ResponseList = []
        
        if self.hud.trialState and endFade:
            yield self.hud.fadeQuad.fade_out()
            self.hud.fadeQuad.visible(viz.OFF)
        else:
            self.hud.fadeQuad.visible(viz.ON)
            
    def setEnvironment(self, environmentObject, trial = DEFAULT, mode = MODEL_3D, mediaType = "video", mediaFormat = "Stereoscopic T/B", headlightIntensity = 0):
        """
        Set the experiment environment or 360° media.
        
        Configures the virtual environment for trials. Supports both 3D model environments
        and 360° video/image media. Handles display parenting and headlight intensity.
        
        Args:
            environmentObject: Vizard 3D object or media file path
            trial (str, optional): Trial ID to configure. Default DEFAULT
            mode (str, optional): Environment mode (MODEL_3D or MEDIA_360). Default MODEL_3D
            mediaType (str, optional): Media type for 360° mode ("video" or "image"). Default "video"
            mediaFormat (str, optional): Stereoscopic format for 360° media. Default "Stereoscopic T/B"
            headlightIntensity (float, optional): Scene headlight brightness (0-1). Default 0
            
        Returns:
            None. Updates experiment settings and scene configuration
        """
        if not (self.guiFlag or self.configPath is not None):
            self.trialMode = mode
            self.experimentSettings[DEFAULT][MODE] = mode
            self.experimentSettings[DEFAULT][ENVIRONMENT] = os.path.basename(environmentObject.getFilename())
            self.experimentSettings[DEFAULT][ENVIRONMENT_DIRECTORY] = os.path.dirname(environmentObject.getFilename())
            
            if mode == MODEL_3D:
                vizconnect.getDisplay('main_display').setParent(vizconnect.getAvatar('main_avatar').getAttachmentPoint('head'))
            else:
                vizconnect.getDisplay('main_display').setParent(vizconnect.getTracker('merged'))
                
                self.experimentSettings[DEFAULT][MEDIA_SETUP][MEDIA_TYPE] = mediaType
                self.experimentSettings[DEFAULT][MEDIA_SETUP][MEDIA_FORMAT] = mediaFormat
                
            trialCount = self.experimentSettings[DEFAULT][NUMBER_OF_TRIALS]
        
            for i in range(1, trialCount + 1):
                self.experimentSettings[str(i)] = deepcopy(self.experimentSettings[DEFAULT])
                
        if mode == MODEL_3D:
            if self.sceneObjects[ENVIRONMENT_OBJECT] is not None:
                self.sceneObjects[ENVIRONMENT_OBJECT].remove()
                
            self.sceneObjects[ENVIRONMENT_OBJECT] = environmentObject
            
            if not self.headlightFlag:
                self.headLight.disable()
            
            if not headlightIntensity == 0:
                self.headLight.enable()
                self.headLight.intensity(headlightIntensity)
            
        elif mode == MEDIA_360:
            self.headLight.enable()
            
            if not headlightIntensity == 0:
                self.headLight.intensity(headlightIntensity)
            else:
                self.headLight.intensity(2)
            
            self.sceneObjects[MEDIA_OBJECT] = environmentObject
            
            if mediaFormat == "Monoscopic":
                self.sceneObjects[ENVIRONMENT_OBJECT] = panorama_utils.MonoSphere(mediaType)
            elif mediaFormat == "Stereoscopic T/B":
                self.sceneObjects[ENVIRONMENT_OBJECT] = panorama_utils.StereoSphere(mediaType)
            elif mediaFormat == "Stereoscopic L/R":
                self.sceneObjects[ENVIRONMENT_OBJECT] = panorama_utils.Stereo180Sphere(mediaType)
            
            self.sceneObjects[ENVIRONMENT_OBJECT].texture(panorama_utils.get_texture(self.sceneObjects[MEDIA_OBJECT]))

            self.experimentSettings[trial][MEDIA_SETUP][MEDIA_TYPE] = mediaType
            self.experimentSettings[trial][MEDIA_SETUP][MEDIA_FORMAT] = mediaFormat
            
            self._envLink = viz.link(viz.MainView, self.sceneObjects[ENVIRONMENT_OBJECT], mask=viz.LINK_POS)
        
    def setEnvironmentOffset(self, pos=(0.0, 0.0, 0.0), euler=None, scale=None):
        """Shift the 360/180 environment sphere relative to the viewer.

        Useful for nudging the captured scene up/down/forward so that the
        subject in a stereo 180 video sits at a comfortable position.

        Args:
            pos (tuple): (x, y, z) offset in meters. +x = right, +y = up,
                +z = forward (away from viewer). Default (0, 0, 0).
            euler (tuple, optional): (yaw, pitch, roll) in degrees applied
                to the sphere itself (re-orient the scene).
            scale (float or tuple, optional): Uniform scale (float) or per-axis
                scale (tuple) for the sphere. Smaller = subject appears closer.
        """
        env = self.sceneObjects.get(ENVIRONMENT_OBJECT)
        link = getattr(self, '_envLink', None)
        if link is not None:
            try:
                link.postTrans(list(pos))
            except Exception:
                pass
        if env is not None:
            if euler is not None:
                env.setEuler(list(euler))
            if scale is not None:
                if hasattr(scale, '__len__'):
                    env.setScale(list(scale))
                else:
                    env.setScale([float(scale)] * 3)

    def getEnvironment(self):
        """Get the current environment object.
        
        Returns:
            viz.VizNode: The current environment (3D model or 360° sphere).
        """
        return self.sceneObjects[ENVIRONMENT_OBJECT]
        
    def getCurrentEnvironmentName(self):
        """Get the filename of the current environment.
        
        Returns:
            str: Base filename of the current environment (e.g., 'room.osgb').
        """
        return os.path.basename(self.sceneObjects[ENVIRONMENT_OBJECT].getFilename())
        
    def getCurrentTrialDirectory(self):
        """Get the directory path for the current trial's environment.
        
        Returns:
            str: Absolute path to the directory containing the trial environment.
        """
        return self.experimentSettings[str(self.trialNumber)][ENVIRONMENT_DIRECTORY]
        
    def getMediaObject(self):
        """Get the 360° media object (video or image texture).
        
        Returns:
            viz.VizNode or None: The media object if in 360° mode, None otherwise.
        """
        return self.sceneObjects[MEDIA_OBJECT]
        
    def setGazePointObject(self, gazePointObject):
        if self.sceneObjects[GAZE_POINT_OBJECT] is not None:
            self.sceneObjects[GAZE_POINT_OBJECT].remove()
            
        self.sceneObjects[GAZE_POINT_OBJECT] = gazePointObject
        
    def getGazePointObject(self, clientNumber = 1):
        """Get the gaze point visualization object.
        
        Args:
            clientNumber: Client ID (default 1, currently unused).
            
        Returns:
            viz.VizNode or None: The gaze point object if set.
        """
        return self.sceneObjects[GAZE_POINT_OBJECT]
        
    def getAvatarHead(self):
        """Get the avatar head object.
        
        Returns:
            viz.VizNode or None: The avatar head object.
        """
        return self.sceneObjects[AVATAR_HEAD_OBJECT]
        
    def getAvatarRHand(self):
        """Get the avatar right hand object.
        
        Returns:
            viz.VizNode or None: The avatar right hand object.
        """
        return self.sceneObjects[AVATAR_RIGHT_HAND_OBJECT]
        
    def getAvatarLHand(self):
        """Get the avatar left hand object.
        
        Returns:
            viz.VizNode or None: The avatar left hand object.
        """
        return self.sceneObjects[AVATAR_LEFT_HAND_OBJECT]
        
    def getEyeTracker(self):
        """Get the eye tracker object.
        
        Returns:
            Eye tracker object or None: The active eye tracker instance.
        """
        return self.hud.eyeTracker
        
    def addSceneObject(self, objectName, sceneObject, gaze = False, grab = False, visible = True, avatar = False, customChildOf = None):
        """Add an object to the scene with optional gaze tracking and grab interaction.
        
        Args:
            objectName: Unique identifier for the object.
            sceneObject: The viz object to add to the scene.
            gaze: Enable gaze-based interaction tracking (default False).
            grab: Enable VR controller grab interaction (default False).
            visible: Make object visible (False hides and disables shadow casting, default True).
            avatar: Mark as an avatar component object (default False).
            customChildOf: Name of parent object to link to (default None).
        """
        if avatar:
            self.sceneObjects[AVATAR_OBJECTS][objectName] = sceneObject
            # Detect the actual child node name for environment children (needed for replay)
            try:
                env = self.sceneObjects.get(ENVIRONMENT_OBJECT)
                if env is not None and env.isChild(sceneObject):
                    for _name in env.getNodeNames():
                        try:
                            if env.getChild(_name) == sceneObject:
                                sceneObject._childNodeName = _name
                                break
                        except:
                            pass
            except:
                pass
        elif (self.guiFlag or self.configPath is not None):
            self.sceneObjects[CUSTOM_OBJECTS][objectName] = sceneObject
        elif not self.sceneObjects[ENVIRONMENT_OBJECT].isChild(sceneObject):
            self.sceneObjects[CUSTOM_OBJECTS][objectName] = sceneObject
        
        if customChildOf is not None:
            if customChildOf in self.sceneObjects[CUSTOM_OBJECTS]:
                self.sceneObjects[CUSTOM_OBJECTS][objectName] = [sceneObject, customChildOf, self.sceneObjects[CUSTOM_OBJECTS][customChildOf]]
            else:
                print("customChildOf not in scene objects")
            
        self.sceneObjects[MANUAL_ADD][objectName] = sceneObject
        
        if gaze:
            self.sceneObjects[GAZE_OBJECTS][objectName] = sceneObject
            self.hud.setGazeTimeObject(self.sceneObjects[GAZE_OBJECTS])
#            self.hud.gazeTimeObject = eye_tracker_utils.GazeTime(self.sceneObjects[GAZE_OBJECTS], threshold=0.5)
            
        if grab:
            self.sceneObjects[GRAB_OBJECTS][objectName] = sceneObject
            
            grabTool = vizconnect.getRawTool('grabber')
            grabTool.setItems(list(self.sceneObjects[GRAB_OBJECTS].values()))
            
            if not "Desktop" in VIZCONNECT_CONFIG:
                grabTool2 = vizconnect.getRawTool('grabber2')
                grabTool2.setItems(list(self.sceneObjects[GRAB_OBJECTS].values()))
            
        if not visible:
            sceneObject.alpha(viz.OFF)
            sceneObject.disable(viz.SHADOW_CASTING)
            self.sceneObjects[INVISIBLE_OBJECTS][objectName] = sceneObject
        
    def removeGazeObject(self, objectName):
        """Remove an object from gaze tracking.
        
        Args:
            objectName: Name of the object to remove from gaze tracking.
        """
        self.sceneObjects[GAZE_OBJECTS].pop(objectName)
        self.hud.gazeTimeObject = eye_tracker_utils.GazeTime(self.sceneObjects[GAZE_OBJECTS], threshold=0.5)

    def removeGrabObject(self, objectName):
        """Remove an object from grab interaction.
        
        Args:
            objectName: Name of the object to remove from grab interaction.
        """
        self.sceneObjects[GRAB_OBJECTS].pop(objectName)
        
        grabTool = vizconnect.getRawTool('grabber')
        grabTool.setItems(list(self.sceneObjects[GRAB_OBJECTS].values()))
        
        if not "Desktop" in VIZCONNECT_CONFIG:
            grabTool2 = vizconnect.getRawTool('grabber2')
            grabTool2.setItems(list(self.sceneObjects[GRAB_OBJECTS].values()))
            
    def removeInvisibleObject(self, objectName):
        """Make an invisible object visible again.
        
        Args:
            objectName: Name of the invisible object to make visible.
        """
        self.sceneObjects[INVISIBLE_OBJECTS][objectName].alpha(viz.ON)
        self.sceneObjects[INVISIBLE_OBJECTS][objectName].enable(viz.SHADOW_CASTING)
        self.sceneObjects[INVISIBLE_OBJECTS].pop(objectName)
        
    def removeSceneObject(self, objectName):
        """Remove a scene object and clean up all associated tracking.
        
        Automatically removes from gaze tracking, grab interaction, and invisible
        object lists as needed, then removes the object from the scene.
        
        Args:
            objectName: Name of the object to remove.
        """
        sceneObject = None
        
        if objectName in self.sceneObjects[GAZE_OBJECTS]:
            sceneObject = self.sceneObjects[GAZE_OBJECTS][objectName]
            self.removeGazeObject(objectName)
        
        if objectName in self.sceneObjects[GRAB_OBJECTS]:
            sceneObject = self.sceneObjects[GRAB_OBJECTS][objectName]
            self.removeGrabObject(objectName)
            
        if objectName in self.sceneObjects[INVISIBLE_OBJECTS]:
            sceneObject = self.sceneObjects[INVISIBLE_OBJECTS][objectName]
            self.removeInvisibleObject(objectName)
            
        if sceneObject is not None:
            sceneObject.remove()
    
    def getCurrentRepetition(self):
        """Get the current repetition number.
        
        Returns:
            int: The current repetition number.
        """
        return self.currentRepetition
        
    def getTrialCount(self):
        """Get the total number of trials in the experiment.
        
        Returns:
            int: Number of trials (default is 1).
        """
        return int(self.experimentSettings[DEFAULT][NUMBER_OF_TRIALS])
        
    def setTrialCount(self, trialCount):
        """Set the number of trials and initialize their settings.
        
        Creates a deep copy of the default settings for each trial.
        
        Args:
            trialCount: Number of trials to run.
        """
        self.experimentSettings[DEFAULT][NUMBER_OF_TRIALS] = trialCount
        
        for i in range(1, trialCount + 1):
            self.experimentSettings[str(i)] = deepcopy(self.experimentSettings[DEFAULT])
    
    def setTrialLength(self, length):
        """Set the trial duration in seconds.
        
        Args:
            length: Trial duration in seconds.
        """
        self.trialLength = length
    
    def startTrial(
        self, condition = None, trialLength = -1, trialLabel = None, startTrialText = None, startExperimentText = None, startRatings = None, textContinueEvent = 'triggerPress', textContinueKey = None, trackingDataLogging = None, replayDataLogging = None, experimentSummaryLogging = None, timeLineLogging = None, fixationLogging = None, startPoint = None, startEuler = None):
        """Start a trial with optional configuration.
        
        condition=None, trialLength=-1, trialLabel=None
        startTrialText=None, startExperimentText=None
        startRatings=None, textContinueKey=None
        textContinueEvent='triggerPress'
        trackingDataLogging=None, replayDataLogging=None
        experimentSummaryLogging=None, timeLineLogging=None
        fixationLogging=None, startPoint=None, startEuler=None
        """
        if not self.experimentSetupComplete or self.experimentEnd:
            return
            
        if condition is not None:
            self.experimentSettings[str(self.trialNumber)][START_CONDITION] = condition
            
            if not condition[0] == NO_CONDITION:
                yield self.__conditionEventManager(START_CONDITION)
        
        if trackingDataLogging is not None:
            self.trackingDataLoggingFlag = trackingDataLogging
        if replayDataLogging is not None:
            self.replayDataLoggingFlag = replayDataLogging
        if experimentSummaryLogging is not None:
            self.experimentSummaryDataLoggingFlag = experimentSummaryLogging
        if timeLineLogging is not None:
            self.timeLineLoggingFlag = timeLineLogging
        if fixationLogging is not None:
            self.fixationLoggingFlag = fixationLogging
        
        if self.instructionsScreen.getVisible():
            yield self.hideInstructions()
            
        if trialLabel is not None:
            self.hud.trialLabel = trialLabel
        
        if self.hud.trialState:
            viz.sendEvent(INITIATE_TRIAL_END)
            
        if not trialLength == -1:
            self.trialLength = trialLength
            self.hud.timerLength = trialLength
            
        if startPoint is not None:
            self.startPoint = startPoint
        
        if startEuler is not None:
            self.startEuler = startEuler
        
        if startPoint is None and startEuler is None and self.sceneObjects[ENVIRONMENT_OBJECT] is not None and SIGHTLAB_START_POINT in self.sceneObjects[ENVIRONMENT_OBJECT].getNodeNames():
            startMarker = self.sceneObjects[ENVIRONMENT_OBJECT].getChild(SIGHTLAB_START_POINT)

            startMarker.visible(viz.OFF)
            
            if self.startPoint == [0.0, 0.0, 0.0]:
                self.startPoint = startMarker.getTransform(SIGHTLAB_START_POINT + "_TRANSFORM").getPosition()
            
            if self.startEuler == [0.0, 0.0, 0.0]:
                self.startEuler = startMarker.getTransform(SIGHTLAB_START_POINT + "_TRANSFORM").getEuler()
            
        yield self.setStartPoint(self.startPoint, self.startEuler)
        
        if startExperimentText is not None and self.firstStart:
            self.hud.disableProgression = viz.ON
            self.hud.writeToStatus('')
            
            yield self.showInstructions(startExperimentText)
            self.firstStart = False
            
            if textContinueKey is not None:
                yield viztask.waitKeyDown(textContinueKey)
            else:
                yield viztask.waitEvent(textContinueEvent)
            
            self.hud.disableProgression = viz.OFF
                
            yield self.hideInstructions()
            
        if startTrialText is not None:
            self.hud.disableProgression = viz.ON
            yield self.showInstructions(startTrialText)
            
            if textContinueKey is not None:
                yield viztask.waitKeyDown(textContinueKey)
            else:
                yield viztask.waitEvent(textContinueEvent)
            
            yield self.hideInstructions()
            self.hud.disableProgression = viz.OFF
            
        if startRatings is not None:
            if isinstance(startRatings, dict):
                yield self.showRatings(**startRatings)
            else:
                yield self.showRatings(startRatings)
        
        if self.clientMode:
            viznet.client.sendAll(INITIATE_TRIAL_START_SERVER, client = viz.net.getName())
        else:
            viz.sendEvent(INITIATE_TRIAL_START)
        
    def endTrial(self, 
                 condition = NO_CONDITION, 
                 endTrialText = None, 
                 endExperimentText = None, 
                 textContinueEvent = "triggerPress", 
                 textContinueKey = None, 
                 textContinueTimer = None, 
                 endRatings = None):
        """End the current trial and save data.
        
        condition=NO_CONDITION, endTrialText=None
        endExperimentText=None, endRatings=None
        textContinueEvent='triggerPress'
        textContinueKey=None, textContinueTimer=None
        """
        
        self.hud.writeToStatus(t("Saving Trial") + " " + str(self.trialNumber) + "...")
        
        if not self.experimentSetupComplete or self.experimentEnd:
            return
    
        if not condition == NO_CONDITION:
            self.experimentSettings[str(self.trialNumber)][END_CONDITION] = condition
            yield self.__conditionEventManager(END_CONDITION)
                
        if endTrialText is not None:
            yield self.showInstructions(endTrialText, pauseTimer = True)
            
            if textContinueKey is not None:
                yield viztask.waitKeyDown(textContinueKey)
            elif textContinueTimer is not None:
                yield viztask.waitTime(textContinueTimer)
            else:
                yield viztask.waitEvent(textContinueEvent)
                
            yield self.hideInstructions(pauseTimer = True)
            
        if endRatings is not None:
            if isinstance(endRatings, dict):
                yield self.showRatings(**endRatings)
            else:
                yield self.showRatings(endRatings)
                
        if endExperimentText is not None and self.trialNumber == self.getTrialCount():
            yield self.showInstructions(endExperimentText)
        
        if self.clientMode:
            viznet.client.sendAll(INITIATE_TRIAL_END_SERVER, client = viz.net.getName())
        else:
            viz.sendEvent(INITIATE_TRIAL_END)

    def setAvatarHead(self, head):
        if self.sceneObjects[AVATAR_HEAD_OBJECT]:
            if self.headLink is not None:
                self.headLink.remove()
                
            self.sceneObjects[AVATAR_HEAD_OBJECT].remove()
            
        self.sceneObjects[AVATAR_HEAD_OBJECT] = head
        
        self.headLink = viz.link(viz.MainView, self.sceneObjects[AVATAR_HEAD_OBJECT])
        
    def setAvatarLeftHand(self, leftHand):
        if self.sceneObjects[AVATAR_LEFT_HAND_OBJECT]:
            self.sceneObjects[AVATAR_LEFT_HAND_OBJECT].remove()
            
        self.sceneObjects[AVATAR_LEFT_HAND_OBJECT] = leftHand
        
    def setAvatarRightHand(self, rightHand):
        if self.sceneObjects[AVATAR_RIGHT_HAND_OBJECT]:
            self.sceneObjects[AVATAR_RIGHT_HAND_OBJECT].remove()
            
        self.sceneObjects[AVATAR_RIGHT_HAND_OBJECT] = rightHand
    
    def setSeatedMode(self, state=True):
        """Enable or disable seated mode for avatar leg positioning.

        Locks the avatar's legs in a seated position, overriding IK tracking.
        Works for both single-user and multi-user (client/server) scenarios.

        Args:
            state: True to enable seated mode, False to disable (default True).
        """
        # Store the state for later use (in case avatar isn't ready yet)
        self._seated_mode_requested = state

        # Set global flag for multi-user scenarios (AvatarIKSyncer will read this)
        viz.SEATED_MODE = state

        # Also set module-level flag if Avatar_Body_MultiUser_IK is imported
        try:
            from sightlab_utils import Avatar_Body_MultiUser_IK as ik_module
            ik_module.SEATED_MODE = state
        except:
            pass

        # Apply transport offset for seated mode (affects local avatar position)
        # ONLY for Complete Characters - Mixamo/ReadyPlayerMe handle positioning via server offset
        # This needs to happen after vizconnect is fully initialized
        def apply_transport_offset():
            try:
                # Detect avatar skeleton type
                avatar_type = None
                try:
                    avatar_wrapper = vizconnect.getAvatar('main_avatar')
                    if avatar_wrapper:
                        local_avatar = avatar_wrapper.getRaw()
                        if local_avatar:
                            # Check for Complete Characters bones
                            if local_avatar.getBone('Bip01 Pelvis'):
                                avatar_type = 'complete_characters'
                            # Check for Mixamo/ReadyPlayerMe bones
                            elif local_avatar.getBone('Hips'):
                                avatar_type = 'mixamo'
                except:
                    pass

                # Only apply transport offset for Complete Characters
                if avatar_type != 'complete_characters':
                    return

                if hasattr(self, 'transportNode') and self.transportNode:
                    if state:
                        # Store original transport position if not already stored
                        if not hasattr(self, '_transport_seated_original_pos'):
                            self._transport_seated_original_pos = self.transportNode.getPosition(viz.ABS_GLOBAL)

                        # Apply seated offset (-0.35m down to match remote avatar seated offset)
                        current_pos = self.transportNode.getPosition(viz.ABS_GLOBAL)
                        new_y = current_pos[1] - 0.35
                        self.transportNode.setPosition([current_pos[0], new_y, current_pos[2]], viz.ABS_GLOBAL)
                    else:
                        # Restore original transport position
                        if hasattr(self, '_transport_seated_original_pos'):
                            self.transportNode.setPosition(self._transport_seated_original_pos, viz.ABS_GLOBAL)
                            del self._transport_seated_original_pos
            except Exception as e:
                import traceback
                traceback.print_exc()

        # Apply offset immediately if transport is available, otherwise schedule it
        if hasattr(self, 'transportNode') and self.transportNode:
            apply_transport_offset()
        else:
            # Schedule for next frame to ensure transport is ready
            import vizact
            vizact.ontimer2(0.1, 0, apply_transport_offset)

        # For single-user, directly lock the local avatar's legs
        if state:
            self._enableSeatedLegs()
        else:
            self._disableSeatedLegs()


    
    def _enableSeatedLegs(self):
        """Lock local avatar's legs in a seated position (internal method)."""
        try:
            # Try multiple ways to get the local avatar
            local_avatar = None
            
            # Method 1: Try vizconnect
            try:
                avatar_wrapper = vizconnect.getAvatar('main_avatar')
                if avatar_wrapper:
                    local_avatar = avatar_wrapper.getRaw()
            except:
                pass
            
            # Method 2: Try getting from sceneObjects if available
            if not local_avatar and hasattr(self, 'sceneObjects'):
                if AVATAR_HEAD_OBJECT in self.sceneObjects and self.sceneObjects[AVATAR_HEAD_OBJECT]:
                    # The avatar head might give us access to the full avatar
                    try:
                        head_obj = self.sceneObjects[AVATAR_HEAD_OBJECT]
                        if hasattr(head_obj, 'getBoneList'):
                            local_avatar = head_obj
                    except:
                        pass
            
            if not local_avatar:
                # Schedule a retry after a short delay
                if not hasattr(self, '_seated_retry_timer') or self._seated_retry_timer is None:
                    self._seated_retry_count = 0
                    def retry_enable():
                        self._seated_retry_count += 1
                        if self._seated_retry_count < 10:  # Try up to 10 times
                            if hasattr(self, '_seated_mode_requested') and self._seated_mode_requested:
                                self._enableSeatedLegs()
                        else:
                            if hasattr(self, '_seated_retry_timer') and self._seated_retry_timer:
                                self._seated_retry_timer.remove()
                                self._seated_retry_timer = None
                    self._seated_retry_timer = vizact.ontimer(0.5, retry_enable)
                return
            
            # Cancel retry timer if we got the avatar
            if hasattr(self, '_seated_retry_timer') and self._seated_retry_timer:
                self._seated_retry_timer.remove()
                self._seated_retry_timer = None
            
            # Import the seated leg euler values from Avatar_Body_MultiUser_IK
            try:
                from sightlab_utils.Avatar_Body_MultiUser_IK import SEATED_LOCKED_LEG_EULER
            except ImportError:
                return
            
            # Detect skeleton type
            skeleton_type = self._detectAvatarSkeletonType(local_avatar)
            
            # Map skeleton type to lookup key
            if skeleton_type == 'complete_characters':
                lookup_key = 'complete_characters'
            elif skeleton_type == 'readyplayerme':
                lookup_key = 'readyplayerme'
            elif skeleton_type in ('mixamo', 'mixamo_generic'):
                lookup_key = 'mixamo'
            else:
                return
            
            leg_euler_dict = SEATED_LOCKED_LEG_EULER.get(lookup_key)
            if not leg_euler_dict:
                return
            
            # Determine if we should use ABS_GLOBAL (for Complete Characters)
            use_global = (lookup_key == 'complete_characters')
            
            # Get and lock all leg bones
            leg_bones = {}
            for bone_name in leg_euler_dict.keys():
                bone = local_avatar.getBone(bone_name)
                if bone:
                    bone.lock()
                    leg_bones[bone_name] = bone
            
            # Set initial euler values
            for bone_name, bone in leg_bones.items():
                euler = leg_euler_dict[bone_name]
                if use_global:
                    bone.setEuler(euler[0], euler[1], euler[2], viz.ABS_GLOBAL)
                else:
                    bone.setEuler(euler[0], euler[1], euler[2])
            
            # Store reference to bones for the update callback
            self._seated_leg_bones = leg_bones
            self._seated_leg_euler_dict = leg_euler_dict
            self._seated_use_global = use_global
            
            # Create vizact.onupdate to continuously enforce leg rotations
            # Use priority 200 to run AFTER IK animator (which typically uses priority 0-100)
            def update_seated_legs():
                try:
                    for bone_name, bone in self._seated_leg_bones.items():
                        euler = self._seated_leg_euler_dict[bone_name]
                        if self._seated_use_global:
                            bone.setEuler(euler[0], euler[1], euler[2], viz.ABS_GLOBAL)
                        else:
                            bone.setEuler(euler[0], euler[1], euler[2])
                except:
                    pass
            
            # Remove any existing seated legs update
            if hasattr(self, '_seated_legs_update') and self._seated_legs_update:
                self._seated_legs_update.remove()
            
            # Priority 100 matches the client mode priority (Avatar_Body_MultiUser_IK uses 100)
            self._seated_legs_update = vizact.onupdate(100, update_seated_legs)
            
        except Exception as ex:
            import traceback
            traceback.print_exc()
    
    def _disableSeatedLegs(self):
        """Unlock local avatar's legs from seated position (internal method)."""
        try:
            # Remove the update callback
            if hasattr(self, '_seated_legs_update') and self._seated_legs_update:
                self._seated_legs_update.remove()
                self._seated_legs_update = None
            
            # Unlock the bones (they'll return to IK control)
            if hasattr(self, '_seated_leg_bones') and self._seated_leg_bones:
                for bone_name, bone in self._seated_leg_bones.items():
                    try:
                        bone.unlock()
                    except:
                        pass
                self._seated_leg_bones = None
            
        except Exception as ex:
            pass
    
    def setSeatedModeHeadOnly(self, state=True, mode='default', transport_euler=None):
        """Enable or disable seated head-only mode for avatar positioning.

        Locks ALL bones below the neck so only the head tracks the HMD.
        Legs are placed in a seated position; arms, spine, and everything
        else remain in their rest (T-pose) orientation.

        This implies regular seated mode. When enabled, seated mode is also
        activated automatically. When disabled, regular seated mode remains
        active unless explicitly disabled separately.

        Args:
            state: True to enable head-only seated mode, False to disable (default True).
            mode: Arm pose style - 'default' (arms at sides) or 'coaster' (arms raised forward).
            transport_euler: Euler values [yaw, pitch, roll] matching the transportNode orientation.
                The yaw is added to each locked arm bone's global yaw so that the arms
                face the correct direction when the transport is rotated (e.g. [180,0,0]).
        """
        if transport_euler is None:
            transport_euler = [0, 0, 0]

        self._seated_mode_head_only_requested = state
        self._seated_head_only_mode = mode
        self._seated_head_only_transport_euler = list(transport_euler)

        # Set global flag for multi-user scenarios (AvatarIKSyncer will read this)
        viz.SEATED_MODE_HEAD_ONLY = state
        viz.SEATED_HEAD_ONLY_MODE = mode
        viz.SEATED_HEAD_ONLY_TRANSPORT_EULER = list(transport_euler)

        # Also set module-level flag if Avatar_Body_MultiUser_IK is imported
        try:
            from sightlab_utils import Avatar_Body_MultiUser_IK as ik_module
            ik_module.SEATED_MODE_HEAD_ONLY = state
            ik_module.SEATED_HEAD_ONLY_MODE = mode
            ik_module.SEATED_HEAD_ONLY_TRANSPORT_EULER = list(transport_euler)
        except:
            pass

        # Head-only implies seated mode
        if state:
            self.setSeatedMode(True)

        # Re-send avatar setup so the server/other clients learn about the mode change
        ik_syncer = getattr(self, 'ik_syncer', None)
        if ik_syncer is not None and hasattr(ik_syncer, 'send_setup'):
            ik_syncer.send_setup()

        # For single-user, directly lock/unlock the local avatar body
        if state:
            self._enableSeatedHeadOnly()
        else:
            self._disableSeatedHeadOnly()

    def _enableSeatedHeadOnly(self):
        """Lock local avatar's body below the neck (head-only mode).
        
        Disables the local IK animator's arm tracking so the arms assume
        their natural rest pose via defaultPostureEnabled.  Locks leg bones
        in seated position with per-frame enforcement.
        """
        try:
            # Try to get the local avatar
            local_avatar = None
            try:
                avatar_wrapper = vizconnect.getAvatar('main_avatar')
                if avatar_wrapper:
                    local_avatar = avatar_wrapper.getRaw()
            except:
                pass

            if not local_avatar:
                # Schedule a retry
                if not hasattr(self, '_head_only_retry_timer') or self._head_only_retry_timer is None:
                    self._head_only_retry_count = 0
                    def retry_enable():
                        self._head_only_retry_count += 1
                        if self._head_only_retry_count < 10:
                            if hasattr(self, '_seated_mode_head_only_requested') and self._seated_mode_head_only_requested:
                                self._enableSeatedHeadOnly()
                        else:
                            if hasattr(self, '_head_only_retry_timer') and self._head_only_retry_timer:
                                self._head_only_retry_timer.remove()
                                self._head_only_retry_timer = None
                    self._head_only_retry_timer = vizact.ontimer(0.5, retry_enable)
                return

            # Cancel retry timer
            if hasattr(self, '_head_only_retry_timer') and self._head_only_retry_timer:
                self._head_only_retry_timer.remove()
                self._head_only_retry_timer = None

            try:
                from sightlab_utils.Avatar_Body_MultiUser_IK import (
                    SEATED_LOCKED_LEG_EULER,
                    HEAD_ONLY_CC_ARM_EULER,
                    HEAD_ONLY_MIXAMO_ARM_EULER,
                    HEAD_ONLY_CC_ARM_EULER_COASTER,
                    HEAD_ONLY_MIXAMO_ARM_EULER_COASTER,
                )
            except ImportError:
                return

            skeleton_type = self._detectAvatarSkeletonType(local_avatar)

            if skeleton_type == 'complete_characters':
                lookup_key = 'complete_characters'
            elif skeleton_type == 'readyplayerme':
                lookup_key = 'readyplayerme'
            elif skeleton_type in ('mixamo', 'mixamo_generic'):
                lookup_key = 'mixamo'
            else:
                return

            leg_euler_dict = SEATED_LOCKED_LEG_EULER.get(lookup_key, {})
            use_global = (lookup_key == 'complete_characters')

            # ---- Disable vizconnect hand tracker wrappers ----
            # This freezes the link from the physical controllers to the
            # tracker node3d objects, so no new hand data reaches the IK.
            try:
                vizconnect.getTracker('l_hand_tracker').setEnabled(False)
            except:
                pass
            try:
                vizconnect.getTracker('r_hand_tracker').setEnabled(False)
            except:
                pass

            # ---- Disable hand IK on the local avatar's animator ----
            # With no hand trackers and defaultPostureEnabled=True, arms
            # assume their natural rest pose (arms at sides) automatically.
            try:
                if avatar_wrapper:
                    animator_wrapper = avatar_wrapper.getAnimator()
                    if animator_wrapper:
                        raw_animator = animator_wrapper.getRaw()
                        if raw_animator:
                            if hasattr(raw_animator, '_leftArmIK'):
                                raw_animator._leftArmIK = None
                            if hasattr(raw_animator, '_rightArmIK'):
                                raw_animator._rightArmIK = None
                            from vizconnect.util.avatar import skeleton as skel_module
                            if hasattr(raw_animator, '_trackerAssignmentDict'):
                                raw_animator._trackerAssignmentDict.pop(skel_module.AVATAR_L_HAND, None)
                                raw_animator._trackerAssignmentDict.pop(skel_module.AVATAR_R_HAND, None)
            except:
                pass  # Animator access not available

            # ---- Lock leg bones in seated position ----
            leg_bones = {}
            for bone_name, euler in leg_euler_dict.items():
                bone = local_avatar.getBone(bone_name)
                if bone:
                    bone.lock()
                    leg_bones[bone_name] = bone
                    if use_global:
                        bone.setEuler(euler[0], euler[1], euler[2], viz.ABS_GLOBAL)
                    else:
                        bone.setEuler(euler[0], euler[1], euler[2])

            # For non-CC skeletons, capture each leg bone's GLOBAL orientation
            # after the seated local-pose is applied, then re-apply globally
            # each frame.  This keeps the legs facing forward regardless of
            # how head IK rotates the Hips bone.
            global_leg_euler = {}
            if not use_global:
                for bone_name, bone in leg_bones.items():
                    try:
                        global_leg_euler[bone_name] = list(bone.getEuler(viz.ABS_GLOBAL))
                    except:
                        pass

            # NOTE: We intentionally do NOT pin the pelvis (Hips) bone. The
            # pelvis is the root of the whole skeleton (spine/head hang off it),
            # so locking it prevents the user from looking around. Looking
            # around must always work; we only hold the leg ORIENTATION.
            self._head_only_leg_bones = leg_bones
            self._head_only_leg_euler_dict = leg_euler_dict
            self._head_only_use_global = use_global
            self._head_only_global_leg_euler = global_leg_euler
            self._head_only_pelvis_bone = None
            self._head_only_pelvis_global_euler = None

            # ---- Lock arm bones ----
            # defaultPostureEnabled can produce twisted arms on the local
            # avatar, so we enforce the natural rest-pose eulers instead.
            head_only_mode = getattr(self, '_seated_head_only_mode', 'default')
            if lookup_key == 'complete_characters':
                if head_only_mode == 'coaster':
                    arm_euler_dict = HEAD_ONLY_CC_ARM_EULER_COASTER
                else:
                    arm_euler_dict = HEAD_ONLY_CC_ARM_EULER
            else:
                if head_only_mode == 'coaster':
                    arm_euler_dict = HEAD_ONLY_MIXAMO_ARM_EULER_COASTER
                else:
                    arm_euler_dict = HEAD_ONLY_MIXAMO_ARM_EULER

            # Apply transport yaw offset to arm euler values
            yaw_offset = getattr(self, '_seated_head_only_transport_euler', [0,0,0])[0]
            adjusted_arm_euler_dict = {}
            for bname, beuler in arm_euler_dict.items():
                adjusted_arm_euler_dict[bname] = [beuler[0] + yaw_offset, beuler[1], beuler[2]]

            arm_bones = {}
            for bone_name, euler in adjusted_arm_euler_dict.items():
                bone = local_avatar.getBone(bone_name)
                if bone:
                    bone.lock()
                    arm_bones[bone_name] = bone
                    bone.setEuler(euler[0], euler[1], euler[2], viz.ABS_GLOBAL)
            self._head_only_arm_bones = arm_bones
            self._head_only_arm_euler_dict = adjusted_arm_euler_dict

            # ---- Per-frame enforcement for legs + arms (runs AFTER IK solver) ----
            def update_head_only():
                try:
                    if self._head_only_use_global:
                        for bone_name, bone in self._head_only_leg_bones.items():
                            euler = self._head_only_leg_euler_dict[bone_name]
                            bone.setEuler(euler[0], euler[1], euler[2], viz.ABS_GLOBAL)
                    else:
                        # Re-apply captured GLOBAL leg orientations so the legs
                        # stay forward-facing even when head IK rotates Hips.
                        te = getattr(self, '_seated_head_only_transport_euler', [0, 0, 0])
                        leg_yaw = te[0] if te else 0
                        # Pin pelvis first so the legs sit on a stable root.
                        pbone = getattr(self, '_head_only_pelvis_bone', None)
                        pge = getattr(self, '_head_only_pelvis_global_euler', None)
                        if pbone is not None and pge is not None:
                            pbone.setEuler(pge[0] + leg_yaw, pge[1], pge[2], viz.ABS_GLOBAL)
                        for bone_name, bone in self._head_only_leg_bones.items():
                            ge = self._head_only_global_leg_euler.get(bone_name)
                            if ge is not None:
                                bone.setEuler(ge[0] + leg_yaw, ge[1], ge[2], viz.ABS_GLOBAL)
                            else:
                                euler = self._head_only_leg_euler_dict[bone_name]
                                bone.setEuler(euler[0], euler[1], euler[2])
                    for bone_name, bone in self._head_only_arm_bones.items():
                        euler = self._head_only_arm_euler_dict[bone_name]
                        bone.setEuler(euler[0], euler[1], euler[2], viz.ABS_GLOBAL)
                except:
                    pass

            if hasattr(self, '_head_only_body_update') and self._head_only_body_update:
                self._head_only_body_update.remove()

            # Run AFTER the IK animator (priority 21). Vizard executes lower
            # priority numbers later, so PRIORITY_LAST_UPDATE runs after IK has
            # rotated the Hips. Priority 100 would run BEFORE IK and let the
            # legs get dragged by the head-driven Hips rotation.
            self._head_only_body_update = vizact.onupdate(viz.PRIORITY_LAST_UPDATE + 2, update_head_only)

        except Exception as ex:
            import traceback
            traceback.print_exc()

    def _disableSeatedHeadOnly(self):
        """Unlock local avatar's body from head-only mode."""
        try:
            if hasattr(self, '_head_only_body_update') and self._head_only_body_update:
                self._head_only_body_update.remove()
                self._head_only_body_update = None

            # Unlock leg bones
            if hasattr(self, '_head_only_leg_bones') and self._head_only_leg_bones:
                for bone_name, bone in self._head_only_leg_bones.items():
                    try:
                        bone.unlock()
                    except:
                        pass
                self._head_only_leg_bones = None

            # Unlock arm bones
            if hasattr(self, '_head_only_arm_bones') and self._head_only_arm_bones:
                for bone_name, bone in self._head_only_arm_bones.items():
                    try:
                        bone.unlock()
                    except:
                        pass
                self._head_only_arm_bones = None

            # Re-enable vizconnect hand tracker wrappers
            try:
                vizconnect.getTracker('l_hand_tracker').setEnabled(True)
            except:
                pass
            try:
                vizconnect.getTracker('r_hand_tracker').setEnabled(True)
            except:
                pass

            # Re-enable hand IK on the local avatar's animator
            try:
                avatar_wrapper = vizconnect.getAvatar('main_avatar')
                if avatar_wrapper:
                    animator_wrapper = avatar_wrapper.getAnimator()
                    if animator_wrapper:
                        raw_animator = animator_wrapper.getRaw()
                        if raw_animator and hasattr(raw_animator, '_trackerAssignmentDict'):
                            from vizconnect.util.avatar import skeleton as skel_module
                            from vizconnect.util.avatar import animator
                            try:
                                l_hand = vizconnect.getTracker('l_hand_tracker').getNode3d()
                                raw_animator._trackerAssignmentDict[skel_module.AVATAR_L_HAND] = (l_hand, None, animator.DOF_6DOF)
                            except:
                                pass
                            try:
                                r_hand = vizconnect.getTracker('r_hand_tracker').getNode3d()
                                raw_animator._trackerAssignmentDict[skel_module.AVATAR_R_HAND] = (r_hand, None, animator.DOF_6DOF)
                            except:
                                pass
            except:
                pass
        except Exception as ex:
            pass
    
    def _detectAvatarSkeletonType(self, avatar):
        """Detect skeleton type of an avatar (internal method)."""
        try:
            bone_list = avatar.getBoneList()
        except AttributeError:
            return 'complete_characters'
        
        bone_map = {bone.getName(): bone for bone in bone_list}
        
        if 'Hips' in bone_map:
            if 'LeftEye' in bone_map or 'RightEye' in bone_map:
                return 'readyplayerme'
            return 'mixamo'
        elif 'Hip' in bone_map or 'CC_Base_Waist' in bone_map:
            return 'reallusion'
        elif 'neck_01' in bone_map:
            return 'unreal_reallusion'
        elif 'Bip01 Pelvis' in bone_map:
            return 'complete_characters'
        
        return None
        
    def addTrackingTrialDataColumn(self, columnName, trackedObject, dataType = SIXDOF, mode = viz.ABS_GLOBAL):
        if self.serverMode:
            return
                
        if columnName not in self.customTrackedObjects:
            self.customTrackedObjects[columnName] = []
                        
        if dataType == SIXDOF:
            self.customTrackedObjects[columnName].append([POSITION, trackedObject, mode])
            self.customTrackedObjects[columnName].append([ORIENTATION, trackedObject, mode])
        else:
            self.customTrackedObjects[columnName].append([dataType, trackedObject, mode])
        
    def setExperimentSummaryData(self, columnName, data):
        self.customExperimentDataColumns[columnName] = data
        
    def setCustomTrialData(self, data, columnName = SIGHTLAB_FLAG):
        if self.hud.sessionRecorder is not None:
            if columnName == SIGHTLAB_FLAG:
                self.hud.sessionRecorder.setFlag(data)
            else:
                self.hud.sessionRecorder.setFlag(data, columnName)
        else:
            self.tempFlag = data
        
    def getPlotData(self):
        return self.hud.sessionRecorder.plotData
        
    def getGazeTimeObject(self):
        return self.hud.gazeTimeObject
        
    def setConsoleState(self, state):
        if state:
            self.hud.consoleON()
        else:
            self.hud.consoleOFF()
        
    def setTransportState(self, state = viz.TOGGLE):
        vizconnect.getTransport('main_transport').setEnabled(state)
        
        if "Desktop" in VIZCONNECT_CONFIG:
            headNode = vizconnect.getTracker('head_tracker')
            headNode.setEnabled(state)

    def enableTransportToggleKey(self, key='y'):
        """Bind a keyboard key to toggle the main transport on/off.

        Useful in 360/Stereo180 modes where the transport may be disabled by
        default but you want to be able to walk/fly during the trial.

        Args:
            key (str): Keyboard key to bind. Default 'y'.
        """
        vizact.onkeydown(key, self.setTransportState, viz.TOGGLE)

    def enableEnvironmentNudgeKeys(self, forwardKey=']', backKey='[', step=0.1):
        """Bind keys to nudge the 360/180 environment sphere along Z.

        Pressing ``forwardKey`` pushes the scene away from the viewer; pressing
        ``backKey`` pulls it closer. Each press shifts by ``step`` meters.

        Args:
            forwardKey (str): Key for +Z (push away). Default ']'.
            backKey (str): Key for -Z (pull closer). Default '['.
            step (float): Distance per keypress, in meters. Default 0.1.
        """
        vizact.onkeydown(forwardKey, self.setEnvironmentOffset, (0.0, 0.0,  step))
        vizact.onkeydown(backKey,    self.setEnvironmentOffset, (0.0, 0.0, -step))

    def enableEnvironmentVerticalKeys(self, upKey='0', downKey='9', step=0.1):
        """Bind keys to nudge the 360/180 environment sphere along Y.

        Pressing ``upKey`` raises the scene; pressing ``downKey`` lowers it.
        Each press shifts by ``step`` meters.

        Args:
            upKey: Key for +Y (raise). Default '0'.
            downKey: Key for -Y (lower). Default '9'.
            step (float): Distance per keypress, in meters. Default 0.1.
        """
        def _up():
            self.setEnvironmentOffset(pos=(0.0,  step, 0.0))
            print('[env nudge] +Y', step)
        def _down():
            self.setEnvironmentOffset(pos=(0.0, -step, 0.0))
            print('[env nudge] -Y', step)
        vizact.onkeydown(upKey,   _up)
        vizact.onkeydown(downKey, _down)

    def enableEnvironmentPitchKeys(self, upKey='7', downKey='8', step=5.0):
        """Bind keys to pitch-rotate the 360/180 environment sphere.

        Pressing ``upKey`` tilts the scene up (increases pitch); pressing
        ``downKey`` tilts it down. Each press rotates by ``step`` degrees.

        Args:
            upKey (str): Key for +pitch (tilt up). Default '7'.
            downKey (str): Key for -pitch (tilt down). Default '8'.
            step (float): Degrees per keypress. Default 5.0.
        """
        def _pitch(delta):
            env = self.sceneObjects.get(ENVIRONMENT_OBJECT)
            if env is None:
                viz.logWarn('enableEnvironmentPitchKeys: no environment object loaded.')
                return
            try:
                current = env.getEuler()
                new_pitch = current[2] + delta
                env.setEuler([current[0], current[1], new_pitch])
                print('[env pitch] pitch=%.2f' % new_pitch)
            except Exception as ex:
                viz.logWarn('enableEnvironmentPitchKeys: pitch failed: %s' % ex)

        vizact.onkeydown(upKey,   _pitch,  step)
        vizact.onkeydown(downKey, _pitch, -step)

    def enableMediaSkipKeys(self, forwardKey='v', backKey='c', step=5.0):
        """Bind keys to skip forward/back in the current 360 or SBS 180 video.

        Args:
            forwardKey (str): Key to skip forward. Default 'v'.
            backKey (str): Key to skip backward. Default 'c'.
            step (float): Seconds to jump per keypress. Default 5.0.
        """
        def _seek(delta):
            media = self.sceneObjects.get(MEDIA_OBJECT)
            if media is None:
                viz.logWarn('enableMediaSkipKeys: no media object loaded.')
                return
            try:
                t = media.getTime() + delta
                if t < 0:
                    t = 0
                media.setTime(t)
                print('[media skip] t=%.2f' % t)
            except Exception as ex:
                viz.logWarn('enableMediaSkipKeys: seek failed: %s' % ex)

        vizact.onkeydown(forwardKey, _seek,  step)
        vizact.onkeydown(backKey,    _seek, -step)

    def toggleMediaPause(self):
        """Toggle play/pause on the current 360 or SBS 180 video.

        Bound by default to Shift+P (uppercase 'P'). No-op when the current
        trial has no media object (e.g. 3D model trials).
        """
        media = self.sceneObjects.get(MEDIA_OBJECT)
        print('[toggleMediaPause] fired. media=%r' % media)
        if media is None:
            return
        try:
            state = media.getState()
        except Exception as ex:
            viz.logWarn('toggleMediaPause: getState failed: %s' % ex)
            state = None

        try:
            if state == viz.MEDIA_RUNNING:
                media.pause()
                print('[media] paused at t=%.2f' % media.getTime())
            else:
                media.play()
                print('[media] playing at t=%.2f (prev state=%s)' % (media.getTime(), state))
        except Exception as ex:
            viz.logWarn('toggleMediaPause: failed: %s' % ex)

    def setTransportPosition(self, pos, euler = None):
        self.transportNode.setPosition(pos)
        
        if euler is not None:
            self.transportNode.setEuler(euler)
           
    def setDataLoggingState(self, state, buffer = True):
        """Enable or disable data logging and timer tracking.

        Controls whether tracking data is being recorded. When disabled, pauses
        the data collection timer to exclude instruction/rating screen time.

        Args:
            state: True to enable logging, False to disable.
            buffer: Track buffer time for timer adjustment (default True).
        """
        if state:
            if self.hud.sceneUpdate is not None:
                self.hud.sceneUpdate.setEnabled(viz.ON)

                if not self.firstStart:
                    self.hud.bufferTime = viz.tick() - self.hud.bufferTime
        else:
            if self.hud.sceneUpdate is not None:
                self.hud.sceneUpdate.setEnabled(viz.OFF)

                self.hud.bufferTime = viz.tick()

    def resetTimer(self):
        """Reset the trial timer to zero.
        
        Clears the start time and buffer time, typically called at trial start.
        """
        self.hud.startTime = viz.tick()
        self.hud.bufferTime = 0.0
        
    def getConfig(self):
        """Get the current vizconnect configuration name.
        
        Returns:
            str: The vizconnect hardware configuration name.
        """
        return self.vizconnectConfig

    def setPassthrough(self, state=True, clearColor=viz.BLACK):
        """Enable or disable OpenXR video passthrough (mixed reality).

        Uses the first passthrough extension the headset's OpenXR runtime
        offers: FB (Meta Quest 3, Quest Pro), HTC (Vive Focus Vision) or
        Varjo (XR-3, XR-4). Every hardware profile of those headsets works,
        the hand, full body and eye-tracker variants included. Sets the
        framebuffer clear alpha to 0 so the OpenXR compositor composites the
        Vizard scene over the real world.

        Uses only the OpenXR client the headset's rig has made: on Desktop it
        warns and does nothing, and never starts the OpenXR runtime.

        Args:
            state (bool): True to enable passthrough, False to disable.
            clearColor: Clear color to use while passthrough is on. Alpha is
                always forced to 0 when enabling.
        """
        if state:
            config = self.getConfig() or ''
            try:
                import openxr
            except ImportError:
                viz.logWarn('setPassthrough: openxr module is not available.')
                return

            # openxr.getClient() makes a client when there is none, connecting
            # to (and starting) the OpenXR runtime; an OpenXR profile's rig has
            # already made one.
            if hasattr(openxr, '_client'):
                xr = openxr._client
            elif 'Desktop' not in config:
                xr = openxr.getClient()
            else:
                xr = None
            if not xr:
                viz.logWarn('setPassthrough: no OpenXR headset in this session '
                            '(vizconnect config "{}").'.format(config))
                return

            # Each getter returns None when the runtime does not offer it.
            passthrough = (xr.getPassthroughFB() or xr.getPassthroughHTC()
                           or xr.getPassthroughVarjo())
            if not passthrough:
                viz.logWarn('setPassthrough: the OpenXR runtime offers no '
                            'passthrough extension (vizconnect config "{}").'.format(config))
                return

            if not hasattr(self, '_savedClearColor') or self._savedClearColor is None:
                try:
                    self._savedClearColor = viz.MainWindow.getClearColor()
                except Exception:
                    self._savedClearColor = (0.0, 0.0, 0.0, 1.0)

            viz.clearcolor(clearColor, 0.0)
            passthrough.setEnabled(True)
            self._passthrough = passthrough
        else:
            passthrough = getattr(self, '_passthrough', None)
            self._passthrough = None
            if not passthrough:
                # Never turned on: leave the clear color alone.
                return
            passthrough.setEnabled(False)

            saved = getattr(self, '_savedClearColor', None)
            if saved is not None:
                try:
                    if len(saved) >= 4:
                        viz.clearcolor(saved[0:3], saved[3])
                    else:
                        viz.clearcolor(saved)
                except Exception:
                    viz.clearcolor(viz.BLACK, 1.0)
                self._savedClearColor = None
            else:
                viz.clearcolor(viz.BLACK, 1.0)

    def enableMixedReality(self, keyColor=(0.20, 0.23, 0.28), threshold=0.02,
                           softness=0.02, spill=0.2):
        """Enable OpenXR passthrough and chroma-key the current 180 SBS video.

        Convenience wrapper: turns on passthrough via ``setPassthrough()`` and,
        if the current environment object is a ``Stereo180Sphere``, applies
        the chroma-key shader so the solid backdrop in the video is keyed out
        and the real world shows through.

        Args:
            keyColor (tuple): Backdrop color (r, g, b) in 0..1.
            threshold (float): Chroma distance cutoff (see
                ``Stereo180Sphere.setChromaKey``).
            softness (float): Soft-edge width.
            spill (float): Spill suppression strength (0 disables).
        """
        self.setPassthrough(True)

        env = self.sceneObjects.get(ENVIRONMENT_OBJECT)
        if isinstance(env, panorama_utils.AbstractSphere):
            env.setChromaKey(color=keyColor, threshold=threshold,
                             softness=softness, spill=spill, enabled=True)
        else:
            viz.logWarn('enableMixedReality: current environment is not a '
                        'panorama sphere; chroma key not applied.')

    def disableMixedReality(self):
        """Disable passthrough and remove the chroma-key shader."""
        env = self.sceneObjects.get(ENVIRONMENT_OBJECT)
        if isinstance(env, panorama_utils.AbstractSphere):
            env.clearChromaKey()
        self.setPassthrough(False)
        
    def getTrialNumber(self):
        """Get the current trial number.
        
        Returns:
            int: The current trial number (1-indexed).
        """
        return self.trialNumber
        
    def setfadeQuadState(self, state: bool):
        """Control the fade quad visibility.
        
        Args:
            state: True to show fade quad, False to hide it.
        """
        if state:
            self.hud.fadeQuadON()
        else:
            self.hud.fadeQuadOFF()
            
    def _applyProjectionFade(self):
        """Switch the fade quad to per-window ortho mode for Projection configs.
        
        Projection (CAVE) configs render each wall in its own window, so the
        default single view-locked quad only covers the front window. This
        replaces it with one ortho quad per projection window so the fade
        covers all screens.
        """
        if "Projection" not in VIZCONNECT_CONFIG:
            return
        if not getattr(self, "hud", None) or self.hud.fadeQuad is None:
            return
        windows = getattr(viz.MainWindow, "windowList", None) or [viz.MainWindow]
        self.hud.fadeQuad.enableProjectionMode(windows)
            
    def setDwellTimeThreshold(self, dwellTime = DWELL_THRESHOLD_VALUE):
        """Set the dwell time threshold for gaze events.
        
        Controls how long gaze must remain on an object before triggering
        an onGazeTime event. Updates the global threshold value.
        
        Args:
            dwellTime: Threshold in seconds (default from DWELL_THRESHOLD_VALUE).
        """
        self.hud.gazeTimeObject.setThreshold(dwellTime)
        global DWELL_THRESHOLD_VALUE
        DWELL_THRESHOLD_VALUE = dwellTime
        
    def setFixationSaccadeThresholds(self, dispersionThreshold = 1, durationThreshold = 0.1):
        """Set thresholds for fixation/saccade detection algorithm.
        
        Args:
            dispersionThreshold: Maximum angle dispersion for fixation in degrees (default 1).
            durationThreshold: Minimum duration for fixation in seconds (default 0.1).
        """
        self.hud.dispersionThreshold = dispersionThreshold
        self.hud.durationThreshold = durationThreshold
        
    def setEnvironmentFolder(self, path, mode = MODEL_3D):
        """Set the resource folder for environments or media files.
        
        Updates the GUI resource lists with files from the specified directory.
        Used to dynamically change where environment/media files are loaded from.
        
        Args:
            path: Absolute path to the resource folder.
            mode: MODEL_3D for 3D environments or MEDIA_360 for 360° media (default MODEL_3D).
        """
        if mode == MODEL_3D:
            global ENVIRONMENT_RESOURCE_PATH
            ENVIRONMENT_RESOURCE_PATH = path 
            
            self.gui.environmentFileList = []
            for file in os.listdir(ENVIRONMENT_RESOURCE_PATH):
                self.gui.environmentFileList.append(file)
                
            self.gui.resourceLists[ENVIRONMENT] = self.gui.environmentFileList
        elif mode == MEDIA_360:
            global MEDIA_RESOURCE_PATH
            MEDIA_RESOURCE_PATH = path
            
            self.gui.mediaFileList = []
            for file in os.listdir(MEDIA_RESOURCE_PATH):
                self.gui.mediaFileList.append(file)
                
            self.gui.resourceLists[MEDIA] = self.gui.mediaFileList
        
    def setStartText(self, startText):
        """Set the text displayed on the start trial button.
        
        Args:
            startText: Text to display on the trial start button.
        """
        global START_TEXT
        START_TEXT = startText
        
    def setMaxDistance(self, distance):
        """Set the maximum distance for gaze intersection checks.
        
        Args:
            distance: Maximum ray cast distance in meters.
        """
        self.hud.maxDistance = distance
        
        if self.hud.sessionRecorder is not None:
            self.hud.sessionRecorder.maxDistance = distance
        
    def getCurrentGazeEventData(self):
        """Get the current gaze event data.
        
        Returns:
            dict: Current gaze event data (object, duration, timestamps, etc.).
        """
        return self.hud.currentGazeEventData
        
    def addRegionOfInterest(self, regionObject):
        pass
        
    def getRegionOfInterest(self, name):
        for i in self.sceneObjects[REGIONS_OF_INTEREST].keys():
            if i[-1] == name:
                return self.sceneObjects[REGIONS_OF_INTEREST][i]
        
        return None
        
    def setConfigDirectory(self, directoryName):
        os.makedirs(directoryName, exist_ok=True)
        
        self.gui.configDirectory = directoryName
        self.gui.loadConfigFileList = self.gui.findFiles(directoryName, ".stlb")
        
    def setEnvironmentDirectory(self, directoryName, mode = MODEL_3D):
        if mode == MODEL_3D:
            self.gui.environmentDirectory = directoryName
            self.experimentSettings[DEFAULT][ENVIRONMENT_DIRECTORY] = directoryName           
        else:
            self.gui.mediaDirectory = directoryName
        
    def setDataDirectory(self, directoryName):
        global DEFAULT_DATA_DIRECTORY
        DEFAULT_DATA_DIRECTORY = directoryName
        
    def setConditionName(self, conditionName):
        self.hud.trialLabel = conditionName
        
    def getConditionName(self):
        return self.hud.trialLabel
    
    def setRecordingsDirectory(self, directoryName):
        os.makedirs(directoryName, exist_ok=True)
        
        global DEFAULT_RECORDINGS_DIRECTORY
        DEFAULT_RECORDINGS_DIRECTORY = directoryName
        
    def screenCapture(self):
        image_timestamp = datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
        image_filename = f'{image_timestamp}_image.jpg'
        
        os.makedirs(os.path.join(self.gui.scriptDirectory, self.gui.recordingsDirectory), exist_ok=True)
        
        path = os.path.join(self.gui.scriptDirectory, self.gui.recordingsDirectory, image_filename)
        
        viz.window.screenCapture(path)    
        print('Screen captured:', path)
        
    def __conditionEventManager(self, condition):
        def checkGazeObject(target):
            if self.hud.currentGazeEventData is not None:
                if isinstance(self.hud.currentGazeEventData.name, tuple):
                    name = self.hud.currentGazeEventData.name[4]
                else:
                    name = self.hud.currentGazeEventData.name
                    
                if target == name and self.hud.gazeState == GAZE_FIXATED:
                    return True
            return False
            
        waitCondition = self.experimentSettings[str(self.trialNumber)][condition]
        
        if condition == START_CONDITION:
            waitTask = viztask.waitEvent(INITIATE_TRIAL_START)
        else:
            waitTask = viztask.waitEvent(INITIATE_TRIAL_END)

        if not self.clientMode:
            if waitCondition[0] == KEY_PRESS:
                key = waitCondition[1]
                
                if self.trialNumber == 1 and condition == START_CONDITION:
                    if key == " ":
                        key = "SPACEBAR"
                        
                    self.hud.writeToStatus(t("Press") + " " + key + " " + t("to Start"))
                
                if not len(key) == 1:
                    if key == "SPACEBAR":
                        key = " "
                else:
                    key = key[0]
                        
                waitTask = viztask.waitKeyDown(key)
                
            elif waitCondition[0] == TIMER:
                if self.trialNumber == 1 and condition == START_CONDITION:
                    self.hud.writeToStatus(t("Wait") + " " + waitCondition[1] + " " + t("seconds to Start"))
                    
                if condition == START_CONDITION:
                    waitTask = viztask.waitTime(float(waitCondition[1]))
                else:
                    self.hud.timerLength = float(waitCondition[1])
                
            elif waitCondition[0] == CUSTOM_EVENT:
                if self.trialNumber == 1 and condition == START_CONDITION:
                    self.hud.writeToStatus(t("Waiting for") + " " + waitCondition[1] + " " + t("to Start"))
                    
                waitTask = viztask.waitEvent(waitCondition[1])
                
            elif waitCondition[0] == ON_MEDIA_END and self.sceneObjects[MEDIA_OBJECT] is not None:                
                self.sceneObjects[MEDIA_OBJECT].stoptime(float(waitCondition[1]))
                self.hud.timerLength = float(waitCondition[1])
                #waitTask = viztask.waitMediaEnd(self.sceneObjects[MEDIA_OBJECT])
                
            elif waitCondition[0] == ON_GAZE_TIME:
                gazeTime = viztask.waitEvent(self.GAZE_TIME_EVENT)
                checkObject = viztask.waitTrue(lambda: checkGazeObject(waitCondition[1]))
                waitTask = viztask.waitAll([gazeTime, checkObject])
                
            else:
                if self.guiFlag and not any(sub in self.hud.statusText.getMessage() for sub in ["Sav", TRIAL_OR_SCENE]):
                    self.hud.writeToStatus("")
                #else:
                    #pass
                    #self.hud.writeToStatus(START_TEXT)

                        
        if condition == START_CONDITION:
            yield viztask.waitAny([viztask.waitEvent(INITIATE_TRIAL_START), waitTask])
            if self.serverMode:
                viznet.server.send(INITIATE_TRIAL_START_SERVER, client = viz.net.getName())
                
                print("sent start")
                yield viztask.waitAny([viztask.waitEvent(START_CONFIRM), viztask.waitTime(2.5)])
                
                print(self.startConfirm)
                
                while not self.startConfirm:
                    viznet.server.send(INITIATE_TRIAL_START_SERVER, client = viz.net.getName())
                    print("sent start again")
                    yield viztask.waitTime(2.5)
                    
                self.startConfirm = False
                    
        else:
            yield viztask.waitAny([viztask.waitEvent(INITIATE_TRIAL_END), waitTask])
            if self.serverMode:
                viznet.server.send(INITIATE_TRIAL_END_SERVER, client = viz.net.getName())
            
    def experimentSetupCompleteStatus(self):
        return self.experimentSetupComplete
        
    def setHeadlight(self, state, intensity = None, color = None):
        self.headlightFlag = state
        
        if state:
            self.headLight.enable()
        else:
            self.headLight.disable()
        
        if intensity is not None:
            self.headLight.intensity(intensity)
            
        if color is not None:
            self.headLight.color(color)
            
    def getExperimentDataFolderPath(self):
        """Get the absolute path to the experiment data folder.
        
        Returns:
            str: Path to the data folder for this participant and date. In the
            extended-length form when the folder is too deep for Windows' path
            limit; long_paths.plain_path gives the ordinary spelling for display.
        """
        folder = os.path.join(self.hud.sessionRecorder.scriptDirectory, DEFAULT_DATA_DIRECTORY, DEFAULT_EXPERIMENT_DIRECTORY.format(date = self.dateTime, p=self.participantData[ID]))
        return long_paths.long_path(folder, reserve=long_paths.session_reserve(self.participantData[ID]))
    
    def storeReplayExecCode(self, method):
        """Store Python source code for replay execution.
        
        Extracts and stores source code from a method for later replay.
        
        Args:
            method: Python method to extract source from.
            
        Returns:
            str: The extracted source code.
        """
        self.replayExecCode = inspect.getsource(method)
        return self.replayExecCode
        
    def addToTimeline(self, flag = None, objectName = None, dwellTime = None):
        """Add an event to the timeline log.
        
        Records timestamped events for timeline reconstruction during replay.
        
        Args:
            flag: Event flag/label (default None).
            objectName: Name of object involved in event (default None).
            dwellTime: Duration of gaze dwell if applicable (default None).
        """
        if self.timeLineLoggingFlag:
            if flag is not None:
                self.hud.sessionRecorder.timeLine[self.hud.getCurrentTime()] = flag
            if objectName is not None:
                currTime = self.hud.getCurrentTime()
                self.hud.sessionRecorder.timeLine[currTime] = [objectName]
                if dwellTime is not None:
                    self.hud.sessionRecorder.timeLine[currTime].append(dwellTime)
                
    def getTimeLineData(self, client = None):
        """Get timeline event data.
        
        Args:
            client: Client ID for multi-user mode (default None).
            
        Returns:
            dict: Timeline data with timestamps as keys.
        """
        if self.serverMode and client is not None:
                return self.hud.sessionRecorder.timeLine[self.hud.sessionRecorder.clientDict[client]]
        else:
            return self.hud.sessionRecorder.timeLine
            
    def setHighlighter(self, mode = None, setItems = None, enable = None, client = None):
        if client is None:
            if mode is not None:
                self.rHandHighlighter.setHighlightMode(mode)
                self.lHandHighlighter.setHighlightMode(mode)
            
            if setItems is not None:
                self.rHandHighlighter.setItems(setItems)
                self.lHandHighlighter.setItems(setItems)
                
            if enable is not None:
                self.highlightState[self.rHandHighlighter] = enable
                self.highlightState[self.lHandHighlighter] = enable
                
                self.rHandHighlightToggle.setEnabled(enable)
                self.lHandHighlightToggle.setEnabled(enable)
        else:
            if self.clientMode:
                viznet.client.sendAll(SET_HIGHLIGHTER_EVENT, mode = mode, enable = enable, setItems = setItems, client = client)
            elif self.serverMode:
                viznet.server.sendAll(SET_HIGHLIGHTER_EVENT, mode = mode, enable = enable, setItems = setItems, client = client)
        
    def setCustomReplayFlag(self, flagName, data):
        self.hud.sessionRecorder.customReplayFlags[flagName] = data
        
    def removeGazePointWindow(self):
        self.gazePointWindow.remove()
#        self.gazePointWindow = None
        
    def addGazePointWindow(self):
        self.gazePointWindow = viz.addWindow(size=(1,1), pos=(0,1))
        self.gazePointWindow.fov(79)
        
    def regenerateDataFiles(self, 
                            folderPath, 
                            dispersionThreshold = DISPERSION_THRESHOLD_VALUE, 
                            durationThreshold = DURATION_THRESHOLD_VALUE, 
                            dwellThreshold = DWELL_THRESHOLD_VALUE, 
                            fileType = PER_TRIAL,
                            noiseReductionThreshold = 0,
                            flipEyePitch = False):
        '''
        folderPath, 
        dispersionThreshold = DISPERSION_THRESHOLD_VALUE, 
        durationThreshold = DURATION_THRESHOLD_VALUE, 
        dwellThreshold = DWELL_THRESHOLD_VALUE, 
        fileType = PER_TRIAL,
        noiseReductionThreshold = 0,
        flipEyePitch = False):
        '''
                                
        def collectFileDirectory():
            # Dictionary to store replay files categorized by experiment folders
            experiment_data = {}

            # Loop through all directories (experiments) in the input folder
            for experiment_folder in os.listdir(folderPath):
                experiment_path = os.path.join(folderPath, experiment_folder)
                
                # Ensure it's a directory (experiment folder)
                if os.path.isdir(experiment_path):
                        # initialize lists for each file type
                    experiment_data[experiment_folder] = {
                        'replay_files': [],
                        'trial_data_files': [],
                        'trial_timeline_files': [],
                        'summary_files': []
                    }
                    
                    # Path to replay data folder
                    replay_data_folder = os.path.join(experiment_path, 'replay_data')
                    
                    # Check for .rply files in the replay data folder
                    if os.path.exists(replay_data_folder):
                        for file in os.listdir(replay_data_folder):
                            if file.endswith('.rply'):
                                replay_file_path = os.path.join(replay_data_folder, file)
                                experiment_data[experiment_folder]['replay_files'].append(replay_file_path)
                                
                                
                    td_dir = os.path.join(experiment_path, 'trial_data')
                    if os.path.isdir(td_dir):
                        for fname in os.listdir(td_dir):
                            full = os.path.join(td_dir, fname)
                            # trial_data files (normal + client)
                            if '_trial_data_' in fname and fname.endswith('.csv'):
                                experiment_data[experiment_folder]['trial_data_files'].append(full)
                            # trial_timeline (new *_timeline_dwell_* or legacy *_timeline_*)
                            elif ('_trial_timeline_dwell_' in fname or '_trial_timeline_' in fname) and fname.endswith('.csv'):
                                experiment_data[experiment_folder]['trial_timeline_files'].append(full)

                    # 3) summary CSVs one level up
                    for fname in os.listdir(experiment_path):
                        if 'experiment_summary' in fname and fname.endswith('.csv'):
                            experiment_data[experiment_folder]['summary_files'].append(
                                os.path.join(experiment_path, fname)
                            )
                            
            return experiment_data
            
        def readDataFiles(files, date_str, pid, trial_num, ts_col='timestamp'):
            """
            files: dict with keys 'trial_data_files', 'trial_timeline_files', 'summary_files'
            date_str, pid: strings
            trial_num: int or 'ALL_TRIALS'
            ts_col: name of your time-key column (falls back to first col)
            """
            def load_df(path):
                print("reading: ", path)
#                with open(path, newline='') as f:
#                    sample = f.read(8192)  # bigger sample helps
#                try:
#                    dialect = csv.Sniffer().sniff(sample, delimiters=[',',';'])
#                    delim = dialect.delimiter
#                except csv.Error:
#                    # fallback: pick the delimiter that appears more often
#                    delim = ';' if sample.count(';') > sample.count(',') else ','
#                quoting = csv.QUOTE_NONE if delim == ';' else csv.QUOTE_MINIMAL
#                return pd.read_csv(
#                    path,
#                    sep=delim,
#                    engine='python',
#                    quoting=quoting,
#                    on_bad_lines='warn'
#                )
                return pd.read_csv(path)

            def by_ts(df):
                if ts_col in df.columns:
                    key_col = ts_col
                elif 'Time Stamp' in df.columns:
                    key_col = 'Time Stamp'
                else:
                    key_col = next((c for c in df.columns if 'time' in c.lower()), df.columns[0])

                # now index on that column
                df2 = df.set_index(key_col)

                # handle duplicates
                if df2.index.has_duplicates:
                    out = {}
                    for tstamp, group in df2.groupby(level=0):
                        out[tstamp] = (
                            group
                            .reset_index(level=0, drop=False)
                            .to_dict(orient='index')
                        )
                    return out
#
#                return df2.to_dict(orient='index')
                return {
                    tstamp: {**{key_col: tstamp}, **row}
                    for tstamp, row in df2.to_dict(orient='index').items()
                }

            # 1 TRIAL_DATA
            td_paths = [p for p in files['trial_data_files']
                        if f"_trial_data_" in os.path.basename(p)]
            trial_data = {}

            if trial_num != 'ALL_TRIALS':
                # combine all files, but filter to this trial
                combined = {}
                for p in td_paths:
                    df = load_df(p)
                    if 'trial number' in df.columns:
                        df = df[df['trial number'] == trial_num]
                    combined.update(by_ts(df)) 
                trial_data[trial_num] = combined

            else:
                # group across all trials
                for p in td_paths:
                    df = load_df(p)
                    if 'trial number' not in df.columns:
                        continue
                    for tn, group in df.groupby('trial number'):
                        trial_data.setdefault(tn, {}).update(by_ts(group))
            
            # 2) TRIAL_TIMELINE (single trial only)
            tl_paths = [
                p
                for p in files['trial_timeline_files']
                if f"_trial_timeline_" in os.path.basename(p)
            ]
            trial_timeline = {}

            combined = {}
            for p in tl_paths:
                df = load_df(p)
                combined.update(by_ts(df))

            trial_timeline[trial_num] = combined

            # 3) SUMMARIES (nested trial?object)
            summaries = {}
            for p in files['summary_files']:
                df = pd.read_csv(p)
                if 'Trial Number' not in df.columns or 'Object' not in df.columns:
                    continue
                for row in df.to_dict(orient='records'):
                    tn, obj = row['Trial Number'], row['Object']
                    summaries.setdefault(tn, {})[obj] = row

            return {
                'trial_data':     trial_data,
                'trial_timeline': trial_timeline,
                'summaries':      summaries
            }
            
        def fixGazeBool(replayData, trialData):
            gazeTrueTimestamps = {}
            gazeTrueBool = False
            currGazeObject = None
            
            objectTracker = replayData[OBJECT_TRACKER]
            objectTracker = {float(k): v for k, v in objectTracker.items()}
            for timestamp in trialData:
                if timestamp not in objectTracker:
                    continue
                    
                currData = objectTracker[timestamp]
                
                for gazeObject in currData[GAZE_OBJECTS]:
                    #if currData[GAZE_OBJECTS][gazeObject][GAZE_STATE] == GAZE_STARTED:
                    if "started: " in trialData[timestamp]['flag'] and gazeObject in trialData[timestamp]['flag']:
                        if gazeTrueBool:
                            gazeTrueTimestamps = {}
                            
                        currGazeObject = gazeObject
                        gazeTrueBool = True
                        
                    elif "fixated: " in trialData[timestamp]['flag'] and gazeObject in trialData[timestamp]['flag']:
                        for item in gazeTrueTimestamps:
                            objectTracker[item][GAZE_OBJECTS][gazeTrueTimestamps[item]][GAZE_BOOL] = True
                        
                        gazeTrueBool = False
                        gazeTrueTimestamps = {}
                        currGazeObject = None
                        
                    if gazeTrueBool:
                        gazeTrueTimestamps[timestamp] = currGazeObject
                        
            replayData[OBJECT_TRACKER] = objectTracker
                        
                                
        global DEFAULT_DATA_DIRECTORY
        DEFAULT_DATA_DIRECTORY = folderPath + "_regenerated"
        
        path = sys.argv[0]
        scriptDirectory = os.path.abspath(os.path.dirname(path))
        
        experiment_data = collectFileDirectory()
        
        viz.window.setSize(600, 600)
        
        self.hud.writeToTimer(t("Regenerating files.."))
                            
        for experiment in experiment_data:
            for replay_file in experiment_data[experiment]['replay_files']:
                self.hud.writeToTimer("Regenerating Experiment: " + experiment + "...")
                filename = open(replay_file) #experiment_data[experiment]['replay_files'][replay_file]
                
                base, _ = os.path.splitext(os.path.basename(replay_file))
                parts = base.split('_')
                date_str       = parts[0]
                participant_id = parts[1]
                trial_number   = int(parts[-1])
                
                if not participant_id:
                    participant_id = ""
                
                replayData = json.load(filename)
                # Extract date, participant ID, and trial number from the filename
                
                if not RPLY_VERSION in replayData:
                    below_2_5_flag = True
                else:
                    below_2_5_flag = False
                
                dateTime = replayData.get(DATE_TIME, date_str)
                replayData[DATE_TIME] = dateTime
                
                participant = replayData.get(PARTICIPANT, {ID: participant_id, PARTICIPANT_INFO1: "", PARTICIPANT_INFO2: ""})
                participant[ID] += "-regenerated"
                
                replayData[PARTICIPANT] = participant
                
                trialNumber = replayData.get(TRIAL_NUMBER, trial_number)
                replayData[TRIAL_NUMBER] = trialNumber
                
                trialLabel = replayData.get(TRIAL_LABEL, 'A')
                
                trialMode = replayData.get(MODE, MODEL_3D)
                
                replayData[THRESHOLDS] = {
                DISPERSION_THRESHOLD: dispersionThreshold,
                DURATION_THRESHOLD: durationThreshold,
                DWELL_THRESHOLD: dwellThreshold
                }
                
                if below_2_5_flag:
                    data = readDataFiles(
                        experiment_data[experiment],
                        date_str,
                        participant_id,
                        trial_number
                    )
                    
                    fixGazeBool(replayData, data['trial_data'][trial_number])
                    
                if flipEyePitch:
                    for timestamp in replayData[OBJECT_TRACKER]:
                        currData = replayData[OBJECT_TRACKER][timestamp]
                        if EYE_TRACKER in currData:
                            currData[EYE_TRACKER][BOTH_EYES][ORIENTATION][1] *= -1
                            currData[EYE_TRACKER][LEFT_EYE][ORIENTATION][1] *= -1
                            currData[EYE_TRACKER][RIGHT_EYE][ORIENTATION][1] *= -1

                sr = SessionRecorder(dateTime = dateTime, participant = participant, 
                                        trialNumber = trialNumber, trialLabel = trialLabel,
                                        trialMode = trialMode, scriptDirectory = scriptDirectory,
                                        dispersionThreshold = dispersionThreshold, durationThreshold = durationThreshold,
                                        dwellThreshold = dwellThreshold, noiseReductionThreshold = noiseReductionThreshold,
                                        regenerateMode = True)
                
                sr.replayData = replayData
                
                if below_2_5_flag:
                    sr.trialData     = data['trial_data']
                    sr.timelineData = data['trial_timeline']
                    sr.summaryData   = data['summaries']
                    
                    print("summary data: ", data['summaries'])
                
                sr.trialState = viz.ON
                
                sr.writeSessionData()
                
        self.hud.writeToTimer(t("Regenerated files!"))
        
class SightLabServer(SightLab):

    
    def __init__(self, 
                 gui = True, 
                 biopac = None, 
                 timer = True, 
                 fadequad = True, 
                 hardwareconfig = "Desktop Server",
                 headlight = False, 
                 mouselock = False, 
                 gazepointvisible = True, 
                 gazepathvisible = ADDITIONAL_SETTINGS["Gaze Path Visible"], 
                 gazerayvisible = True, 
                 console = ADDITIONAL_SETTINGS["Console"], 
                 screenrecord = False, 
                 trackingdatalogging = True, 
                 replaydatalogging = True, 
                 experimentdatalogging = True, 
                 timelinelogging = True, 
                 fixationlogging = True, 
                 continuekey = False, 
                 trialcount = None, 
                 configpath = None, 
                 loadenvironmentmode = LOAD_ALL, 
                 directory = None, 
                 repetitions = 1, 
                 avatarintersect = True, 
                 individualeyeintersect = True,
                 datafilesaving = PER_TRIAL, 
                 loglevel = viz.OFF, 
                 vizconnectconfig = None, 
                 vizconnectconfiglist = None, 
                 title = SIGHTLAB_VERSION,
                 mumble_server = None, 
                 mumble_port = 64738, 
                 mumble_password = "", 
                 mumble_channel = "SightLab",
                 optimizeintersect = True,
                 fastload = False):
        """
        gui=True, timer=True, fadequad=True, gazerayvisible=True
        gazepointvisible=True, avatarintersect=True
        individualeyeintersect=True, trackingdatalogging=True
        replaydatalogging=True, experimentdatalogging=True
        timelinelogging=True, fixationlogging=True
        headlight=False, mouselock=False, continuekey=False
        screenrecord=False, repetitions=1, mumble_port=64738
        hardwareconfig='Desktop Server', mumble_channel='SightLab'
        loadenvironmentmode=LOAD_ALL, datafilesaving=PER_TRIAL
        loglevel=viz.OFF, title=SIGHTLAB_VERSION, optimizeintersect=True
        fastload=False
        gazepathvisible=SETTINGS, console=SETTINGS
        biopac=None, trialcount=None, configpath=None
        directory=None, vizconnectconfig=None
        vizconnectconfiglist=None, mumble_server=None
        mumble_password=''
        """

        global SIGHTLAB_VERSION, RECENT_CONFIG_FILE, RECENT_CONFIG_PATH

        RECENT_CONFIG_FILE = RECENT_CONFIG_SERVER_FILE
        RECENT_CONFIG_PATH = os.path.join(DEFAULT_CONFIG_DIRECTORY, RECENT_CONFIG_FILE)
        
        super().__init__(gui = gui, pid = False, biopac = biopac, timer = timer, fadequad = fadequad, 
                headlight = headlight, mouselock = mouselock, gazepointvisible = gazepointvisible, gazepathvisible = gazepathvisible, 
                console = console, screenrecord = screenrecord, trackingdatalogging = trackingdatalogging, 
                replaydatalogging = replaydatalogging, experimentdatalogging = experimentdatalogging, timelinelogging = timelinelogging, fixationlogging = fixationlogging,continuekey = continuekey, 
                trialcount = trialcount, configpath = configpath, loadenvironmentmode = loadenvironmentmode, directory = directory, repetitions = repetitions, 
                datafilesaving = datafilesaving, loglevel = loglevel, serverMode = True, hardwareconfig = hardwareconfig, vizconnectconfig = vizconnectconfig, 
                vizconnectconfiglist = vizconnectconfiglist, title = title + ",", individual_eye_intersect = individualeyeintersect, optimizeintersect = optimizeintersect, fastload = fastload)
        
        viznet.server.start(port_in=14950,port_out=14951)
        _startSightLabSync()

        self.clientCount = 0
        self.clientReadyCount = 0
        
        self.clientStatus = {}
        
        self.readyClientDict = {}
        
        #self.clientTrialStatus = {}
        
        self.hud.writeToServer(self.clientCount, self.clientReadyCount, t("Waiting for clients..."))
        
        self.clientDict = {}
        
        self.startPoint = [0.2, 0.0, -1]
        
        self.clientSetupData = {}
        
        self.sharedServerData = None
        
        self.avatarIntersect = avatarintersect
        
        self.clientHighlighters = {}
        self.clientHighlightersState = {}
        
        self.clientColors = [viz.GREEN, viz.RED, viz.YELLOW, viz.MAGENTA, viz.CYAN, viz.PURPLE,
                            viz.ORANGE, viz.AZURE, viz.ROSE, viz.VIOLET, viz.ORANGE_RED, viz.YELLOW_ORANGE,
                            viz.BLUE, viz.SPRING_GREEN, viz.CHARTREUSE_GREEN]
        
        self.gazeRayDict = {}
        self.gazeRayWidth = 2
        
        self.colorsDict = {}
        
        self.gazeRayFlag = gazerayvisible
        
        self.sceneObjects[AVATAR_HEAD_OBJECT] = {}
        self.sceneObjects[AVATAR_LEFT_HAND_OBJECT] = {}
        self.sceneObjects[AVATAR_RIGHT_HAND_OBJECT] = {}
        self.sceneObjects[GAZE_POINT_OBJECT] = {}
        
        viz.callback(viznet.CLIENT_CONNECT_EVENT, self.__onNewClient)
        viz.callback(CLIENT_AVATAR_UPDATE, self.__updateClientAvatar)
        viz.callback(CLIENT_SETUP_UPDATE, self.__updateClientSetup)
        viz.callback(UPDATE_MOUTH, self.__updateClientMouth)
        viz.callback(viznet.CLIENT_DISCONNECT_EVENT, self.__onClientDisconnect)

        viz.callback(CLIENT_SETUP_READY_UPDATE, self.__clientSetupReady)
        
        vizact.addCallback(CLIENT_GAZE_BEGIN_EVENT, self.__clientGazeBegin)
        vizact.addCallback(CLIENT_GAZE_END_EVENT, self.__clientGazeEnd)
        vizact.addCallback(CLIENT_GAZE_TIME_EVENT, self.__clientGazeTime)
        
        self.CLIENT_GAZE_BEGIN_EVENT = CLIENT_GAZE_BEGIN_EVENT
        self.CLIENT_GAZE_END_EVENT = CLIENT_GAZE_END_EVENT
        self.CLIENT_GAZE_TIME_EVENT = CLIENT_GAZE_TIME_EVENT
        
        viz.callback(INITIATE_TRIAL_START_SERVER, self.startTrialServer)
        viz.callback(INITIATE_TRIAL_END_SERVER, self.endTrialServer)
        
        viz.callback(START_CONFIRM, self.startConfirmFlag)
        
        viz.callback(UPDATE_HIGHLIGHTER, self.__updateHighlighters)
        
        def updateSharedData():
            viznet.server.send(SHARED_SERVER_DATA_UPDATE, data = self.sharedServerData)
            
        vizact.onupdate(0, updateSharedData)
        
        # Initialize Mumble voice chat for server
        self.mumbleManager = None
        if mumble_server:
            import socket
            try:
                # Quick reachability check before attempting to connect
                ip = socket.gethostbyname(mumble_server)
                with socket.create_connection((ip, int(mumble_port)), timeout=3):
                    print(f"Resolved {mumble_server} -> {ip}, port {mumble_port} reachable")
            except Exception as e:
                print(f"? Can't reach Mumble at {mumble_server}:{mumble_port} ({e}). "
                      f"Is Murmur running and is the firewall open?")
                self.mumbleManager = None
            else:
                try:
                    # Lazy import - only load when needed
                    from sightlab_utils.mumble_manager import MumbleManager

                    username = (
                        f"Server_{self.gui.participantData[ID]}"
                        if self.gui.participantData[ID]
                        else "Server_Host"
                    )
                    self.mumbleManager = MumbleManager(
                        server=mumble_server,
                        port=mumble_port,
                        username=username,
                        password=mumble_password,
                        channel=mumble_channel,
                        debug=True,
                    )

                    if self.mumbleManager and self.mumbleManager.is_connected():
                        print(f"? Server connected to Mumble: {mumble_server}:{mumble_port} as '{username}'")
                    else:
                        print(f"? Failed to connect to Mumble at {mumble_server}:{mumble_port}")
                        self.mumbleManager = None

                except Exception as e:
                    print(f"? Failed to connect to Mumble server: {e}")
                    self.mumbleManager = None

        # Voice chat keyboard controls
        vizact.onkeydown("m", self.toggleMute)
        vizact.onkeydown("n", self.toggleDeafen)
                
    def __onNewClient(self, e):
        self.clientCount += 1
        clientID = self.clientCount
        
        self.clientDict[e.sender] = clientID
        
        if self.hud.sessionRecorder is not None:
            self.hud.sessionRecorder.clientDict = self.clientDict
        
        self.clientStatus[e.sender] = CLIENT_ONLINE
        
        self.hud.writeToServer(self.clientCount, self.clientReadyCount, "client_" + str(clientID) + " " + t("connected"))
        
        self.colorsDict[clientID] = self.clientColors[clientID-1 if clientID < len(self.clientColors) else ((clientID+1)%len(self.clientColors))-1]
        
        viznet.server.send(ASSIGN_CLIENT_ID, client = e.sender, clientID = clientID, color = self.colorsDict[clientID], clientData = self.clientSetupData, onlineCount = self.clientCount, readyCount = self.clientReadyCount, sharedServerData = self.sharedServerData, trialNumber = self.trialNumber, currentTime = self.hud.getCurrentTime())
        
        if self.experimentSetupComplete:
            viznet.server.send(UPDATE_CONFIG, config = self.experimentSettings, currentTime = self.hud.getCurrentTime(), trialNumber = self.trialNumber, repetitions = self.repetitionCount)

    def __onClientDisconnect(self, e):
        self.clientCount -= 1
        
        if self.clientStatus[e.sender] in [CLIENT_READY, CLIENT_SETUP_READY]:
            self.clientReadyCount -= 1
            viznet.server.send(CLIENT_DISCONNECTED_EVENT, client = e.sender)
            
        self.hud.writeToServer(self.clientCount, self.clientReadyCount, "client_" + str(self.clientCount + 1) + " " + t("disconnected"))
        
        self.clientStatus[e.sender] = CLIENT_DISCONNECTED
        
        if e.sender in self.readyClientDict:
            self.readyClientDict.pop(e.sender)
            self.hud.writeToClientList(self.readyClientDict)
            
        if e.sender in self.clientDict:
            clientID = self.clientDict[e.sender]
            
            for item in [AVATAR_HEAD_OBJECT, AVATAR_RIGHT_HAND_OBJECT, AVATAR_LEFT_HAND_OBJECT, GAZE_POINT_OBJECT]:
                if clientID in self.sceneObjects[item]:
                    self.sceneObjects[item][clientID].remove()
                
            if clientID in self.gazeRayDict:
                self.gazeRayDict[clientID].remove()
            
            # Remove full-body IK avatar for this client
            if hasattr(self, 'ik_syncer') and self.ik_syncer is not None:
                self.ik_syncer.removeClient(e.sender)
            
            self.clientDict.pop(e.sender)
    
    def __clientSetupReady(self, e):
        self.clientStatus[e.client] = CLIENT_SETUP_READY

        if e.midtrial:            
            keyDict = {
                AVATAR_HEAD_OBJECT: AVATAR_HEAD_FILE,
                AVATAR_RIGHT_HAND_OBJECT: AVATAR_RIGHT_HAND_FILE, 
                AVATAR_LEFT_HAND_OBJECT: AVATAR_LEFT_HAND_FILE, 
                GAZE_POINT_OBJECT: GAZE_POINT_FILE
                }
                
            for item in [AVATAR_HEAD_OBJECT, AVATAR_RIGHT_HAND_OBJECT, AVATAR_LEFT_HAND_OBJECT, GAZE_POINT_OBJECT]:
                for client in self.sceneObjects[item]:
                    if not item == GAZE_POINT_OBJECT:
                        self.hud.sessionRecorder.replayData[keyDict[item]][client] = self.sceneObjects[item][client].getFilename().split('\\')[-1]
                    else:
                        self.hud.sessionRecorder.replayData[keyDict[item]][client] = [self.sceneObjects[item][client].getFilename().split('\\')[-1], self.sceneObjects[item][client].getColor()]
                
            self.hud.sessionRecorder.sceneObjects = self.sceneObjects
    
#            self.hud.sessionRecorder.dwellFixationDict[self.clientDict[e.client]] = {}
#            self.hud.sessionRecorder.dwellObjectFixationDict[self.clientDict[e.client]] = {}
                                    
            viznet.server.send(MID_TRIAL_CLIENT_CONNECTED, client = e.client, currentTime = self.hud.getCurrentTime(), startTime = (self.hud.startTime + self.hud.bufferTime))
        
    def startTrialServer(self, e):
        viz.sendEvent(INITIATE_TRIAL_START)
        
    def endTrialServer(self, e):
        viz.sendEvent(INITIATE_TRIAL_END)
        
    def startConfirmFlag(self, e):
        self.startConfirm = True
        
    def __drawGazeRay(self, clientID, begin, end):
        if self.gazeRayFlag:
            if clientID in self.gazeRayDict:
                self.gazeRayDict[clientID].remove()
            
            viz.startLayer(viz.LINES)
            viz.lineWidth(self.gazeRayWidth)
            viz.vertexColor(self.colorsDict[clientID])
            
            viz.vertex(begin)
            viz.vertex(end)
            
            self.gazeRayDict[clientID] = viz.endLayer()
            
    def clientAvatarsVisible(self, state):
        for client in self.sceneObjects[AVATAR_HEAD_OBJECT]:
            self.sceneObjects[AVATAR_HEAD_OBJECT][client].visible(state)
            
        for client in self.sceneObjects[AVATAR_RIGHT_HAND_OBJECT]:
            self.sceneObjects[AVATAR_RIGHT_HAND_OBJECT][client].visible(state)
            
        for client in self.sceneObjects[AVATAR_LEFT_HAND_OBJECT]:
            self.sceneObjects[AVATAR_LEFT_HAND_OBJECT][client].visible(state)
            
        for client in self.sceneObjects[GAZE_POINT_OBJECT]:
            self.sceneObjects[GAZE_POINT_OBJECT][client].visible(state)
        
        # Also control full-body IK avatars visibility
        if hasattr(self, 'ik_syncer') and self.ik_syncer is not None:
            self.ik_syncer.setVisible(state)

    def __updateClientScene(self, objectTracker, changedObjects):
        for objectType in changedObjects:
            for objectName in changedObjects[objectType]:
                self.sceneObjects[objectType][objectName].setPosition(objectTracker[objectType][objectName][POSITION], mode = viz.ABS_GLOBAL)
                self.sceneObjects[objectType][objectName].setEuler(objectTracker[objectType][objectName][ORIENTATION], mode = viz.ABS_GLOBAL)
                
    def __updateClientAvatar(self, e):
        # Check if client still exists before processing
        if e.client not in self.clientDict:
            return
        
        objectTracker = e.objectTracker
        
        clientID = self.clientDict[e.client]
        
        # Check if clientID exists in the sceneObjects (not clientAvatars - that's for Client class)
        if AVATAR_HEAD_OBJECT not in self.sceneObjects or clientID not in self.sceneObjects[AVATAR_HEAD_OBJECT]:
            return
                
        for item in [AVATAR_HEAD_OBJECT, AVATAR_RIGHT_HAND_OBJECT, AVATAR_LEFT_HAND_OBJECT, GAZE_POINT_OBJECT]:
            if item in objectTracker:
                self.sceneObjects[item][clientID].setPosition(objectTracker[item][POSITION])
                self.sceneObjects[item][clientID].setEuler(objectTracker[item][ORIENTATION])
            else:
                self.sceneObjects[item][clientID].visible(viz.OFF)

        # Get gaze ray origin - use IK avatar's head TARGET position if available
        # We use head_target (set from client data) rather than head bone position,
        # because the head bone position can flicker when avatar root is repositioned
        # each frame before IK has solved.
        gaze_ray_origin = objectTracker[AVATAR_HEAD_OBJECT][POSITION]
        if hasattr(self, 'ik_syncer') and self.ik_syncer is not None:
            try:
                # Get the client name from clientID (reverse lookup in clientDict)
                client_name = None
                for c_name, c_id in self.clientDict.items():
                    if c_id == clientID:
                        client_name = c_name
                        break

                if client_name and client_name in self.ik_syncer.remote_avatars:
                    remote = self.ik_syncer.remote_avatars[client_name]
                    # Use head_target position — this is always stable since it comes
                    # directly from the client's tracker data, unaffected by IK timing
                    head_target = remote.get('head_target')
                    if head_target:
                        ht_pos = head_target.getPosition(viz.ABS_GLOBAL)
                        # For full-body avatars, offset DOWN to eye level
                        # Head target is at top of skull; eyes are ~3cm below
                        gaze_ray_origin = [ht_pos[0], ht_pos[1] - 0.03, ht_pos[2]]
            except:
                pass  # Fall back to objectTracker position if anything fails

        self.__drawGazeRay(clientID, gaze_ray_origin, objectTracker[GAZE_POINT_OBJECT][POSITION])
        
        if not e.changedObjects == {}:
            self.__updateClientScene(objectTracker, e.changedObjects)
    
#    def __updateClientAvatar(self, e):
#        objectTracker = e.objectTracker
#        
#        clientID = self.clientDict[e.client]
#                
#        for item in [AVATAR_HEAD_OBJECT, AVATAR_RIGHT_HAND_OBJECT, AVATAR_LEFT_HAND_OBJECT, GAZE_POINT_OBJECT]:
#            if item in objectTracker:
#                self.sceneObjects[item][clientID].setPosition(objectTracker[item][POSITION])
#                self.sceneObjects[item][clientID].setEuler(objectTracker[item][ORIENTATION])
#            else:
#                self.sceneObjects[item][clientID].visible(viz.OFF)
#            
#        self.__drawGazeRay(clientID, objectTracker[AVATAR_HEAD_OBJECT][POSITION], objectTracker[GAZE_POINT_OBJECT][POSITION])
#        
##        print(e.changedObjects)
#        if not e.changedObjects == {}:
#            self.__updateClientScene(objectTracker, e.changedObjects)
        
    def __updateClientMouth(self, e):
        if e.client in self.clientDict and self.clientDict[e.client] in self.sceneObjects[AVATAR_HEAD_OBJECT]:
            self.sceneObjects[AVATAR_HEAD_OBJECT][self.clientDict[e.client]].setMorph(14, e.morphValue*2)
        
    def __updateClientSetup(self, e):
        clientID = self.clientDict[e.client]
        settings = e.settings
            
        if settings[DEFAULT][AVATAR_HEAD] is None:
            self.sceneObjects[AVATAR_HEAD_OBJECT][clientID] = vizfx.addAvatar(DEFAULT_AVATAR_HEAD_PATH)
        else:
            self.sceneObjects[AVATAR_HEAD_OBJECT][clientID] = vizfx.addAvatar(AVATAR_HEAD_RESOURCE_PATH + "/" + settings[DEFAULT][AVATAR_HEAD])
        
        if not self.avatarIntersect:
            self.sceneObjects[AVATAR_HEAD_OBJECT][clientID].disable(viz.INTERSECTION)
        
        vizact.ontimer(random.uniform(2, 5), self.sceneObjects[AVATAR_HEAD_OBJECT][clientID].addAction, self.blinkSequence)
            
        if settings[DEFAULT][AVATAR_RIGHT_HAND] is None:
            self.sceneObjects[AVATAR_RIGHT_HAND_OBJECT][clientID] = vizfx.addChild(DEFAULT_AVATAR_RIGHT_HAND_PATH)
        else:
            self.sceneObjects[AVATAR_RIGHT_HAND_OBJECT][clientID] = vizfx.addChild(AVATAR_HANDS_RESOURCE_PATH + "/" + settings[DEFAULT][AVATAR_RIGHT_HAND])
            
        if settings[DEFAULT][AVATAR_LEFT_HAND] is None:
            self.sceneObjects[AVATAR_LEFT_HAND_OBJECT][clientID] = vizfx.addChild(DEFAULT_AVATAR_LEFT_HAND_PATH)
        else:
            self.sceneObjects[AVATAR_LEFT_HAND_OBJECT][clientID] = vizfx.addChild(AVATAR_HANDS_RESOURCE_PATH + "/" + settings[DEFAULT][AVATAR_LEFT_HAND])
            
        self.sceneObjects[GAZE_POINT_OBJECT][clientID] = vizfx.addChild(DEFAULT_GAZE_POINT_PATH)
        self.sceneObjects[GAZE_POINT_OBJECT][clientID].color(self.colorsDict[clientID])
        
        if settings[DEFAULT][AUTO_ASSIGN] and "GlowManAuto" in settings[DEFAULT][AVATAR_HEAD]:
            self.sceneObjects[AVATAR_HEAD_OBJECT][clientID].color(self.colorsDict[clientID])
        
        self.clientHighlighters[e.client] = {}
        self.clientHighlighters[e.client][CLIENT_R_HIGHLIGHTER] = highlighter.Highlighter()
        self.clientHighlighters[e.client][CLIENT_L_HIGHLIGHTER] = highlighter.Highlighter()
        
        def highlightUpdateFunction(handHighlighter):
            if self.clientHighlightersState[handHighlighter]:
                handHighlighter.highlight()
            else:
                handHighlighter.clear()
        
        self.clientHighlightersState[self.clientHighlighters[e.client][CLIENT_R_HIGHLIGHTER]] = False
        self.clientHighlightersState[self.clientHighlighters[e.client][CLIENT_L_HIGHLIGHTER]] = False
        
        self.clientHighlighters[e.client][CLIENT_R_HIGHLIGHTER].setUpdateFunction(highlightUpdateFunction)
        self.clientHighlighters[e.client][CLIENT_L_HIGHLIGHTER].setUpdateFunction(highlightUpdateFunction)
        
        self.clientSetupData[e.client] = e
        
        clientInfo = e.settings[DEFAULT][CLIENT_INFO]
        
        # Store full body settings from client (will be applied after experimentSetup)
        if FULL_BODY_TOGGLE in e.settings[DEFAULT]:
            self.clientFullBodyToggle = e.settings[DEFAULT][FULL_BODY_TOGGLE]
            self.experimentSettings[DEFAULT][FULL_BODY_TOGGLE] = self.clientFullBodyToggle
        if FULL_BODY_AVATARS in e.settings[DEFAULT]:
            self.clientFullBodyAvatars = e.settings[DEFAULT][FULL_BODY_AVATARS]
            self.experimentSettings[DEFAULT][FULL_BODY_AVATARS] = self.clientFullBodyAvatars
        
        # Store seated mode setting from client
        if SEATED_MODE in e.settings[DEFAULT]:
            self.experimentSettings[DEFAULT][SEATED_MODE] = e.settings[DEFAULT][SEATED_MODE]
        
        self._loadFullBodyAvatars()
        
        self.clientStatus[e.client] = CLIENT_READY
        
        self.clientReadyCount += 1
        
#        self.hud.gazeTimeObject[clientID] = e.gazeTimeObject
        
        name = clientInfo[FIRST_NAME]
        if name == "":
            name = "client_" + str(clientID)
            
        self.readyClientDict[clientID] = name
        
        if not isinstance(self.participantData[PARTICIPANT_INFO1], dict):
            self.participantData[PARTICIPANT_INFO1] = {}
            
        self.participantData[PARTICIPANT_INFO1][clientID] = name
        
        self.nameTags[e.client] = viz.addText(name, parent = self.sceneObjects[AVATAR_HEAD_OBJECT][clientID])
        self.nameTags[e.client].alignment(viz.ALIGN_CENTER_BOTTOM)
        self.nameTags[e.client].setBackdrop(viz.BACKDROP_BOX)
        self.nameTags[e.client].setBackdropAlpha(0.4)
        self.nameTags[e.client].resolution(1)
        self.nameTags[e.client].disable(viz.LIGHTING)
        
        self.nameTags[e.client].setScale([0.07, 0.07, 0.07])
        self.nameTags[e.client].setPosition(0, 0.2, -0.1)
        self.nameTags[e.client].setEuler(180, 0, 0)
        
        if not settings[DEFAULT][CLIENT_INFO][SHOW_NAME]:
            self.nameTags[e.client].visible(viz.OFF)
        
        self.hud.writeToClientList(self.readyClientDict)
        
        self.hud.writeToServer(self.clientCount, self.clientReadyCount, name + " " + t("ready"))
        
        if not self.experimentSetupComplete:
            self.clientAvatarsVisible(viz.OFF)
        
    def __checkClientSetupComplete(self):
        setupReadyCount = 0
        for client in self.clientStatus:
            if self.clientStatus[client] == CLIENT_SETUP_READY:
                setupReadyCount += 1
            elif self.clientStatus[client] == CLIENT_READY:
                viznet.server.sendClient(client, UPDATE_CONFIG, config = self.experimentSettings, currentTime = self.hud.getCurrentTime(), trialNumber = self.trialNumber, repetitions = self.repetitionCount)
                
        if setupReadyCount == self.clientReadyCount:
            return True
        else:
            return False
           
#    def sendEnvironment(self):
#        filename = os.path.join(self.gui.scriptDirectory, "resources/environments/dojo2.osgb")
#        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
#            server_socket.bind((viz.net.getIP(), 5001))
#            viznet.server.send(SEND_ENVIRONMENT, serverIP = viz.net.getIP())
#            server_socket.listen(1)
#            print("Server listening on port:", 5001)
#            
#            conn, addr = server_socket.accept()
#            with conn:
#                print(f"Connected by {addr}")
#                with open(filename, 'rb') as file:
#                    while (chunk := file.read(1024)):
#                        conn.sendall(chunk)
#                print(f"File {filename} sent successfully.")
#                return True

    def runServer(self):
        yield self._SightLab__loadExperiment()

        for i in range(self.repetitionCount):
            self.currentRepetition = i+1
            
            if self.repetitionCount > 1:
                global RECORDING_FILE, REPLAY_DATA_FILE, TRIAL_DATA_FILE, EXPERIMENT_SUMMARY_FILE, TRIAL_TIMELINE_DATA_FILE
                
                RECORDING_FILE = '{date}_{p}_trial_recording_' + 'block_' + str(self.currentRepetition) + '_{t}_client_{c}.avi'
                CLIENT_REPLAY_DATA_FILE = '{date}_{p}_replay_data_' + 'block_' + str(self.currentRepetition) + '_{t}_client_{c}.rply'
                CLIENT_TRIAL_DATA_FILE = '{date}_{p}_trial_data_' + 'block_' + str(self.currentRepetition) + '_{t}_client_{c}.csv'
                CLIENT_EXPERIMENT_SUMMARY_FILE = '{date}_{p}_' + 'block_' + str(self.currentRepetition) + '_experiment_summary_client_{c}.csv'
                CLIENT_TRIAL_TIMELINE_DATA_FILE = '{date}_{p}_trial_timeline_' + 'block_' + str(self.currentRepetition) + '_{t}_client_{c}.csv'
                
            self.hud.disableProgression = viz.ON
            yield self._SightLab__experimentSetup()
            self.clientAvatarsVisible(viz.ON)
            
            viznet.server.send(UPDATE_CONFIG, config = self.experimentSettings, currentTime = self.hud.getCurrentTime(), trialNumber = self.trialNumber, repetitions = self.repetitionCount)
            
            self.hud.writeToStatus(t("Setting up clients..."))
            
            yield viztask.waitTrue(lambda: self.__checkClientSetupComplete())
                    
            #yield viztask.waitTrue(lambda: self.sendEnvironment())

            self.hud.disableProgression = viz.OFF
            
            self.hud.writeToStatus(START_TEXT)
            
            while (self.trialNumber <= int(self.experimentSettings[DEFAULT][NUMBER_OF_TRIALS])) or self.experimentSettings[DEFAULT][NUMBER_OF_TRIALS] == -1:
                yield self._SightLab__runTrial(self.clientDict)
                self.hud.writeToStatus(t("Saved Trial") + " " + str(self.trialNumber-1))
                
                self.resetTrial()
                                
            if self.currentRepetition == self.repetitionCount:
                self.hud.writeToStatus(t("Experiment Complete"))
            else:
                self.hud.writeToStatus(t("Starting Repetition") + " " + str(self.currentRepetition + 1))
                
            viz.sendEvent(EXPERIMENT_END)
            self.experimentEnd = True
            self.resetExperiment()
            
    def updateSharedServerData(self, data):
        self.sharedServerData = data
        viznet.server.send(SHARED_SERVER_DATA_UPDATE, data = self.sharedServerData)
            
    def __updateDwellFixationDict(self, e):
        clientID = self.clientDict[e.client]
        
#        self.hud.gazeTimeObject[clientID] = e.gazeTimeObject
        
    def __clientGazeBegin(self, e):
        viznet.server.send(NETWORK_GAZE_BEGIN_EVENT, gazeObject = e.gazeObject)
        viz.sendEvent(NETWORK_GAZE_BEGIN_EVENT, e.gazeObject)
            
    def __clientGazeEnd(self, e):        
        self.__updateDwellFixationDict(e)
        
        print("gaze end for client")
        
        self.hud.writeToConsole(endedList = '{:<15s}: {:.2f} seconds'.format(e.gazeObject, e.gazeTime), clientNumber = int(self.clientDict[e.client]))
        
        viznet.server.send(NETWORK_GAZE_END_EVENT, gazeObject = e.gazeObject)
        viz.sendEvent(NETWORK_GAZE_END_EVENT, e.gazeObject)
        
    def __clientGazeTime(self, e):
        self.__updateDwellFixationDict(e)
        
        print("gaze time for client")

        
        self.hud.writeToConsole(fixatedList = e.gazeObject, clientNumber = int(self.clientDict[e.client]))
        
        viznet.server.send(NETWORK_GAZE_TIME_EVENT, gazeObject = e.gazeObject)
        viz.sendEvent(NETWORK_GAZE_TIME_EVENT, e.gazeObject)
        
    def __updateHighlighters(self, e):
        self.clientHighlighters[e.client][CLIENT_R_HIGHLIGHTER].setPosition(e.rPos)
        self.clientHighlighters[e.client][CLIENT_L_HIGHLIGHTER].setPosition(e.lPos)
        
        self.clientHighlighters[e.client][CLIENT_R_HIGHLIGHTER].setEuler(e.rEuler)
        self.clientHighlighters[e.client][CLIENT_L_HIGHLIGHTER].setEuler(e.lEuler)
        
        self.clientHighlightersState[self.clientHighlighters[e.client][CLIENT_R_HIGHLIGHTER]] = e.rState
        self.clientHighlightersState[self.clientHighlighters[e.client][CLIENT_L_HIGHLIGHTER]] = e.lState
        
        for client in self.nameTags:
            self.nameTags[client].lookAt(viz.MainView.getPosition(), mode = viz.ABS_GLOBAL)
            ori = self.nameTags[client].getEuler()
            self.nameTags[client].setEuler(ori[0] + 180, 0, ori[2])
    
    def toggleMute(self):
        """Toggle microphone mute"""
        if self.mumbleManager:
            muted = self.mumbleManager.toggle_mute()
            status = "muted" if muted else "unmuted"
            self.hud.writeToStatus(f"Microphone {status}")
            print(f"Server microphone {status}")
            return muted
        return None
    
    def toggleDeafen(self):
        """Toggle audio deafen"""
        if self.mumbleManager:
            deafened = self.mumbleManager.toggle_deafen()
            status = "deafened" if deafened else "undeafened"
            self.hud.writeToStatus(f"Audio {status}")
            print(f"Server audio {status}")
            return deafened
        return None
    
    def disconnectVoice(self):
        """Disconnect from voice server"""
        if self.mumbleManager:
            self.mumbleManager.disconnect()
            self.mumbleManager = None
            print("Server disconnected from voice chat")
            
        
class SightLabClient(SightLab):

    
    def __init__(self, 
                 biopac = None, 
                 gui = True, 
                 timer = True,
                 mouselock = False, 
                 headlight = False, 
                 fadequad = True,
                 gazepointvisible = True,
                 console = ADDITIONAL_SETTINGS["Console"], 
                 screenrecord = False, 
                 loadenvironmentmode = LOAD_ALL, 
                 configpath = None,
                 hardwareconfig = None, 
                 highlighttool = False, 
                 avatarintersect = True,
                 vizconnectconfig = None, 
                 vizconnectconfiglist = None, 
                 server = None, 
                 title = SIGHTLAB_VERSION, 
                 individual_eye_intersect = True,
                 mumble_server = None, 
                 mumble_port = 64738, 
                 mumble_password = "", 
                 mumble_channel = "SightLab",
                 optimizeintersect = True,
                 fastload = False,
                 fullbody = False,
                 fullbodyavatar = None):
        """
        gui=True, timer=True, fadequad=True, gazepointvisible=True
        avatarintersect=True, headlight = False, individual_eye_intersect=True
        mouselock=False, screenrecord=False, highlighttool=False
        mumble_port=64738, mumble_channel='SightLab', optimizeintersect=True
        fastload=False, fullbody=False
        fullbodyavatar=None
        loadenvironmentmode=LOAD_ALL, title=SIGHTLAB_VERSION
        console=SETTINGS
        biopac=None, configpath=None, hardwareconfig=None
        vizconnectconfig=None, vizconnectconfiglist=None
        server=None, mumble_server=None, mumble_password=''
        """
                    
        global SIGHTLAB_VERSION, RECENT_CONFIG_FILE, START_TEXT, GUI_TEXT, RECENT_CONFIG_PATH

        RECENT_CONFIG_FILE = RECENT_CONFIG_CLIENT_FILE
        RECENT_CONFIG_PATH = os.path.join(DEFAULT_CONFIG_DIRECTORY, RECENT_CONFIG_FILE)
        
        START_TEXT = t("Waiting for server to start trial")
        GUI_TEXT = t('Configure your client. Last saved configuration\nwill be auto-filled on every run.')
        
        super().__init__(gui = gui, pid = False, biopac = biopac, timer = timer,
                gazepointvisible = gazepointvisible, headlight = headlight,
                mouselock = mouselock, fadequad = fadequad, configpath = configpath,
                console = console, screenrecord = screenrecord, highlighttool = highlighttool,
                loadenvironmentmode = loadenvironmentmode, hardwareconfig = hardwareconfig,
                vizconnectconfig = vizconnectconfig, vizconnectconfiglist = vizconnectconfiglist, 
                clientMode = True, title = title + ",", individual_eye_intersect = individual_eye_intersect, optimizeintersect = optimizeintersect, fastload = fastload, fullbody = fullbody, fullbodyavatar = fullbodyavatar)
    
        if not "Desktop" in VIZCONNECT_CONFIG:
            vizconnect.getTransport('main_transport').getNode3d().setPosition(0, 1, 0)
        
        self.server = server
        
        self.clientDict = {}
        
        self.onlineCount = 0
        self.readyCount = 0
        
        self.avatarIntersect = avatarintersect
        
#        if server is None:
#            choice = vizinput.choose('Choose a Server', serverList)
#            SERVER_NAME = serverList[choice]
#        else:
#            SERVER_NAME = server
#        
#        if SERVER_NAME == "[NEW]":
#            SERVER_NAME = vizinput.input("Server Name")
#            serverList.insert(0, SERVER_NAME)
#        else:
#            serverList.remove(SERVER_NAME)
#            serverList.insert(0, SERVER_NAME)
#            
#        serverList.remove("[NEW]")
#        
#        with open(server_list_path, 'w') as file:
#            json.dump(serverList, file)

#        while not viznet.client.connect(SERVER_NAME,port_in=14951,port_out=14950):
#            if vizinput.ask(SERVER_NAME + "isn't on the network, would you like to try another?"):
#                serverList.remove(SERVER_NAME)
#                SERVER_NAME = vizinput.input('Enter Server Name')
#                serverList.insert(0, SERVER_NAME)
#                with open(server_list_path, 'w') as file:
#                    json.dump(serverList, file)
#            else:
#                viz.quit()
               
        self.hud.writeToClient("Not connected to server", viz.RED)
                
        self.serverExperimentSettings = None
        self.serverSetupComplete = False
        
        self.clientID = None
        self.clientColor = viz.GREEN
        
        self.midTrialClient = False
        
        self.clientAvatars = {}
        self.clientHighlighters = {}
        
        self.clientHighlightersState = {}
        
        self.sharedServerData = None
        
        self.CLIENT_GAZE_BEGIN_EVENT = CLIENT_GAZE_BEGIN_EVENT
        self.CLIENT_GAZE_END_EVENT = CLIENT_GAZE_END_EVENT
        self.CLIENT_GAZE_TIME_EVENT = CLIENT_GAZE_TIME_EVENT
        
        self.onHighlightUpdate = vizact.onupdate(vizconnect.PRIORITY_ANIMATOR + 2, self.__sendHighlighters)
        self.onHighlightUpdate.setEnabled(viz.OFF)
        
        viz.callback(UPDATE_CONFIG, self.__receiveServerSettings)
#        viz.callback(SEND_ENVIRONMENT, self.receiveEnvironment)
        
        viz.callback(INITIATE_TRIAL_START_SERVER, self.startTrialClient)
        viz.callback(INITIATE_TRIAL_END_SERVER, self.endTrialClient)
        viz.callback(ASSIGN_CLIENT_ID, self.__assignClientID)
        
        viz.callback(CLIENT_SETUP_UPDATE, self.__clientAvatarsSetup)
        viz.callback(CLIENT_AVATAR_UPDATE, self.__updateClientAvatar)
        viz.callback(MID_TRIAL_CLIENT_CONNECTED, self.__midTrialClientSetup)
        viz.callback(UPDATE_MOUTH, self.__updateClientMouth)
        
        viz.callback(viznet.SERVER_DISCONNECT_EVENT, self.__quitClient)

        viz.callback(SERVER_CONNECTED, self.__serverConnectedStatus)
        viz.callback(SERVER_DISCONNECTED, self.__serverDisconnectedStatus)
        viz.callback(CLIENT_DISCONNECTED_EVENT, self.__clientDisconnected)
        
        viz.callback(MODEL_3D_CLIENT, self.clientAvatarsON)
        viz.callback(MEDIA_360_CLIENT, self.clientAvatarsOFF)
        
        viz.callback(UPDATE_HIGHLIGHTER, self.__updateHighlighters)
        viz.callback(SET_HIGHLIGHTER_EVENT, self.__setHighlighterClient)
        
        viz.callback(SHARED_SERVER_DATA_UPDATE, self.__updateSharedServerData)
        
        # Initialize Mumble voice chat for client
        self.mumbleManager = None
        if mumble_server:
            try:
                # Lazy import - only load when needed
                from sightlab_utils.mumble_manager import MumbleManager
                
                # Try to get client name from settings, otherwise use generic name
                client_name = "Client_Unknown"
                try:
                    if hasattr(self.gui, 'trialSettings') and self.gui.trialSettings.get('default', {}).get('client_info', {}).get('first_name'):
                        client_name = self.gui.trialSettings['default']['client_info']['first_name']
                except:
                    pass
                
                self.mumbleManager = MumbleManager(
                    server=mumble_server,
                    port=mumble_port,
                    username=client_name,
                    password=mumble_password,
                    channel=mumble_channel,
                    debug=True
                )
                print(f"✓ Client connected to Mumble: {mumble_server}:{mumble_port} as '{client_name}'")
            except Exception as e:
                print(f"✗ Failed to connect to Mumble server: {e}")
                self.mumbleManager = None
        
        # Voice chat keyboard controls
        vizact.onkeydown('m', self.toggleMute)
        vizact.onkeydown('d', self.toggleDeafen)
        
    def __updateSharedServerData(self, e):
        self.sharedServerData = e.data
        viz.sendEvent(SHARED_SERVER_DATA_UPDATE_EVENT, self.sharedServerData)
        
    def receiveSharedServerData(self):
        return self.sharedServerData
        
    def startTrialClient(self, e):
        viz.sendEvent(INITIATE_TRIAL_START)
        
        viznet.client.send(START_CONFIRM, client = viz.net.getName())
        
        print("received and sent handshake")
        
        if not self.loadTrialComplete:
            self.midTrialClient = True
        
    def endTrialClient(self, e):
        viz.sendEvent(INITIATE_TRIAL_END)
        
    def getClientName(self):
        return self.gui.trialSettings[DEFAULT][CLIENT_INFO][FIRST_NAME]
        
    def __updateHighlighters(self, e):
        try:
            if e.client != viz.net.getName():
                self.clientHighlighters[e.client][CLIENT_R_HIGHLIGHTER].setPosition(e.rPos)
                self.clientHighlighters[e.client][CLIENT_L_HIGHLIGHTER].setPosition(e.lPos)
                
                self.clientHighlighters[e.client][CLIENT_R_HIGHLIGHTER].setEuler(e.rEuler)
                self.clientHighlighters[e.client][CLIENT_L_HIGHLIGHTER].setEuler(e.lEuler)
                
                self.clientHighlightersState[self.clientHighlighters[e.client][CLIENT_R_HIGHLIGHTER]] = e.rState
                self.clientHighlightersState[self.clientHighlighters[e.client][CLIENT_L_HIGHLIGHTER]] = e.lState
                
                for client in self.nameTags:
                    self.nameTags[client].lookAt(viz.MainView.getPosition(), mode = viz.ABS_GLOBAL)
                    ori = self.nameTags[client].getEuler()
                    self.nameTags[client].setEuler(ori[0] + 180, 0, ori[2])
        except:
            print("client not found")
        
    def __sendHighlighters(self):
        # Only send manual toggle state - auto-activation (menu hover) is local-only
        # This matches Desktop behavior where auto-highlighter is not broadcast
        viznet.client.sendAll(UPDATE_HIGHLIGHTER, client = viz.net.getName(), rPos = self.rHandHighlighter.getPosition(viz.ABS_GLOBAL), rEuler = self.rHandHighlighter.getEuler(viz.ABS_GLOBAL),
                        lPos = self.lHandHighlighter.getPosition(viz.ABS_GLOBAL), lEuler = self.lHandHighlighter.getEuler(viz.ABS_GLOBAL),
                        rState = self.highlightState[self.rHandHighlighter], lState = self.highlightState[self.lHandHighlighter])
    
    def __setHighlighterClient(self, e):
        if e.client == viz.net.getName():
            self.setHighlighter(e.mode, e.setItems, e.enable)
        
    def setStartPointSuffix(self, suffix):
        if isinstance(suffix, str):
            self.gui.trialSettings[DEFAULT][CLIENT_INFO][SSP_SUFFIX] = suffix

    def clientAvatarsON(self):
        for client in self.clientAvatars:
            self.clientAvatars[client][AVATAR_HEAD_OBJECT].visible(viz.ON)
    
    def clientAvatarsOFF(self):
        for client in self.clientAvatars:
            self.clientAvatars[client][AVATAR_HEAD_OBJECT].visible(viz.OFF)
        
    def __serverConnectedStatus(self):
        try:
            self.hud.writeToClient("Connected to: " + self.gui.buttonLabels[SERVER_NAME].getItem(self.gui.buttonLabels[SERVER_NAME].getSelection()), color = viz.GREEN, clientsOnline = self.onlineCount, clientsReady = self.readyCount)
            if self.gui.sceneInfoPanel.getEnabled():
                self.gui.buttonLabels[SERVER_REFRESH].message("Disconnect")
        except:
            pass
        
    def __serverDisconnectedStatus(self):
        try:
            self.hud.writeToClient("Not connected to: " + self.gui.buttonLabels[SERVER_NAME].getItem(self.gui.buttonLabels[SERVER_NAME].getSelection()), color = viz.RED, clientsOnline = self.onlineCount, clientsReady = self.readyCount)
            if self.gui.sceneInfoPanel.getEnabled():
                self.gui.buttonLabels[SERVER_REFRESH].message("Connect")
        except:
            pass
            
    def __clientDisconnected(self, e):
        if e.client in self.clientDict:
            # Remove head/hand avatars if they exist
            if e.client in self.clientAvatars:
                for item in [AVATAR_HEAD_OBJECT, AVATAR_RIGHT_HAND_OBJECT, AVATAR_LEFT_HAND_OBJECT]:
                    if item in self.clientAvatars[e.client]:
                        self.clientAvatars[e.client][item].remove()
                self.clientAvatars.pop(e.client)
            
            # Remove full-body IK avatar for this client
            if hasattr(self, 'ik_syncer') and self.ik_syncer is not None:
                self.ik_syncer.removeClient(e.client)
                                        
            self.clientDict.pop(e.client)
            self.hud.writeToClientList(self.clientDict)
        
    def __assignClientID(self, e):
        if viz.net.getName() == e.client:
            if hasattr(e, 'trialNumber') and hasattr(e, 'currentTime'):
                self.midTrialClient = (e.trialNumber != 1 or e.currentTime != 0.0)

            self.clientID = e.clientID
            self.clientColor = e.color
            
            self.gui.clientColor = self.clientColor
            
            if self.gui.trialSettings[DEFAULT][AUTO_ASSIGN]:
                self.gui.loadTempAvatar()
            
            if self.gui.tempText is not None and self.gui.tempText.getMessage() == self.gui.clientID:
                self.gui.tempText.message("client_" + str(self.clientID))
                
            self.gui.clientID = "client_" + str(self.clientID)
            
            self.gui.serverConnected = True
            if SERVER_STATUS in self.gui.buttonLabels:
                self.gui.buttonLabels[SERVER_STATUS].uppicture(os.path.join(ICONS_PATH, "green_status.png"))
            viz.sendEvent(SERVER_CONNECTED)
                
            for client in e.clientData:
                self.__clientAvatarsSetup(e.clientData[client])
        
        self.hud.writeToClient(self.hud.clientText.getMessage().split(",")[0], clientsOnline = e.onlineCount, clientsReady = e.readyCount)
        self.onlineCount = e.onlineCount
        self.readyCount = e.readyCount
        
        self.sharedServerData = e.sharedServerData
        
    def __setupBIOPAC(self):
        if self.experimentSettings[DEFAULT][BIOPAC]:
            self.biopacFlag = True
            self.hud.BIOPAC = True
            
            if self.acqServer is None and not self.serverMode:
                try:
                    self.acqServer = biopacndt.AcqNdtQuickConnect()
                    self.hud.acqServer = self.acqServer
                except Exception as e:
                    print("No Acqknowledge server found")
                    self.biopacFlag = False
                    self.hud.BIOPAC = False
            
    def clientAvatarsVisible(self, state):
        for client in self.clientAvatars:
            self.clientAvatars[client][AVATAR_HEAD_OBJECT].visible(state)
            self.clientAvatars[client][AVATAR_RIGHT_HAND_OBJECT].visible(state)
            self.clientAvatars[client][AVATAR_LEFT_HAND_OBJECT].visible(state)
        
        # Also control full-body IK avatars visibility
        if hasattr(self, 'ik_syncer') and self.ik_syncer is not None:
            self.ik_syncer.setVisible(state)
        
    def runClient(self):
        _startSightLabSync()
        yield self._SightLab__loadExperiment()
        
        self.clientDict[self.clientID] = self.experimentSettings[DEFAULT][CLIENT_INFO][FIRST_NAME] if not self.experimentSettings[DEFAULT][CLIENT_INFO][FIRST_NAME] == "" else "client_" + str(self.clientID)
        
        self.readyCount += 1
        
        self.hud.writeToClientList(self.clientDict)
        self.hud.writeToClient(self.hud.clientText.getMessage().split(",")[0], clientsOnline = self.onlineCount, clientsReady = self.readyCount)
            
        clientSetupSent = False
        
        if self.server is not None or not self.guiFlag:
            if not self.guiFlag:
                self.server = self.experimentSettings[DEFAULT][CLIENT_INFO][SERVER_NAME]
                
            if self.configPath is not None or not self.guiFlag:
                # Non-GUI / auto-start client: it may be launched before the server app
                # is running. viznet.client.connect() returns True as long as the target
                # *machine* is reachable, so it can't tell us whether the SightLab server
                # is actually up. Instead we retry the whole handshake (fresh reconnect +
                # setup broadcast) until the server responds with its config. Fully
                # disconnecting at the start of each attempt lets the server clean up any
                # partial registration, so retries never duplicate this client's avatars.
                connectAttempt = 0
                # While we deliberately disconnect/reconnect between attempts, suspend the
                # SERVER_DISCONNECT_EVENT handler so our own teardown doesn't trigger
                # __quitClient (which would pop a "Server disconnected" dialog and quit).
                viz.callback(viznet.SERVER_DISCONNECT_EVENT, None)
                while not self.serverSetupComplete:
                    connectAttempt += 1
                    # Tear down any previous client interface before reconnecting. A fresh
                    # interface has no internal handler yet, so guard disconnect() against
                    # an uninitialized client to avoid 'NoneType has no attribute disconnect'.
                    if viznet.client is not None:
                        try:
                            viznet.client.disconnect()
                        except AttributeError:
                            pass
                    viznet.client = None
                    viznet.client = viznet._ClientInterface()
                    viznet.client.connect(self.server, port_in=14951, port_out=14950)
                    viznet.client.sendAll(CLIENT_SETUP_UPDATE, client = viz.net.getName(), settings = self.experimentSettings, gazeTimeObject = self.hud.gazeTimeObject, color = self.clientColor, midtrial = self.midTrialClient)
                    self.hud.writeToClient(
                        "Waiting for server '{}' to come online... (attempt {})".format(self.server, connectAttempt),
                        color = viz.YELLOW, clientsOnline = self.onlineCount, clientsReady = self.readyCount
                    )
                    print("[Client] Handshake attempt {} to server '{}' (waiting up to {}s for response)".format(connectAttempt, self.server, SERVER_CONNECT_RETRY_INTERVAL))
                    yield viztask.waitAny([
                        viztask.waitTrue(lambda: self.serverSetupComplete),
                        viztask.waitTime(SERVER_CONNECT_RETRY_INTERVAL)
                    ])
                # Connected for real now — restore the disconnect handler so a genuine
                # server drop later still quits the client cleanly.
                viz.callback(viznet.SERVER_DISCONNECT_EVENT, self.__quitClient)
                clientSetupSent = True
                print("[Client] Server '{}' responded; client setup complete".format(self.server))
            else:
                # Standard GUI client: keep the interactive prompt so the operator can
                # correct a mistyped server name or choose another machine.
                while not viznet.client.connect(self.server, port_in=14951, port_out=14950):
                    if vizinput.ask(self.server + "isn't on the network, would you like to try another?"):
                        self.server = vizinput.input('Enter Server Name')
                
                if not self.serverSetupComplete:
                    # Give auto-start clients a brief window to receive server settings before broadcasting
                    wait_tasks = [
                        viztask.waitTrue(lambda: self.serverSetupComplete),
                        viztask.waitTime(5)
                    ]
                    yield viztask.waitAny(wait_tasks)
        
        if not clientSetupSent:
            viznet.client.sendAll(CLIENT_SETUP_UPDATE, client = viz.net.getName(), settings = self.experimentSettings, gazeTimeObject = self.hud.gazeTimeObject, color = self.clientColor, midtrial = self.midTrialClient)
            
        self.hud.writeToClient("Waiting for server to start session...", clientsOnline = self.onlineCount, clientsReady = self.readyCount)
        
        yield viztask.waitTrue(lambda: self.serverSetupComplete)

        self.__mergeSettings()
        
        self.__setupBIOPAC()
        
        self.onHighlightUpdate.setEnabled(viz.ON)
        
        for i in range(self.repetitionCount):
            self.currentRepetition = i+1
            
            if self.repetitionCount > 1:
                global RECORDING_FILE
                RECORDING_FILE = '{date}_{p}_trial_recording_' + 'block_' + str(self.currentRepetition) + '_{t}.avi'
                
            self.hud.disableProgression = viz.ON
            yield self._SightLab__experimentSetup()
            
            self.clientAvatarsVisible(viz.ON)
            
            self.hud.writeToClient("Session active", clientsOnline = self.onlineCount, clientsReady = self.readyCount)
            viznet.client.send(CLIENT_SETUP_READY_UPDATE, client = viz.net.getName(), midtrial = self.midTrialClient)
            
            self.hud.disableProgression = viz.OFF
            self.hud.writeToStatus(START_TEXT)
            
            while (self.trialNumber <= int(self.experimentSettings[DEFAULT][NUMBER_OF_TRIALS])) or self.experimentSettings[DEFAULT][NUMBER_OF_TRIALS] == -1:
                yield self._SightLab__runTrial(midTrialClient = self.midTrialClient)
                self.hud.writeToStatus("Saved Trial " + str(self.trialNumber-1))
                
                self.resetTrial()
                self.midTrialClient = False
                                
            if self.currentRepetition == self.repetitionCount:
                self.hud.writeToStatus("Experiment Complete")
            else:
                self.hud.writeToStatus("Starting Repetition " + str(self.currentRepetition + 1))
                
            viz.sendEvent(EXPERIMENT_END)
            self.experimentEnd = True
            self.resetExperiment()
            
#    def receiveEnvironment(self, e):
#        filename = "environment.osgb"
#        
#        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
#            client_socket.connect((e.serverIP, 5001))
#            with open(filename, 'wb') as file:
#                while True:
#                    data = client_socket.recv(1024)
#                    if not data:
#                        break
#                    file.write(data)
#            print(f"File {filename} received successfully.")
        
    def __receiveServerSettings(self, e):
        if self.serverSetupComplete:
            return
            
        self.serverExperimentSettings = e.config
        
        if e.trialNumber != 1 or e.currentTime != 0.0:
            self.midTrialClient = True
            
        self.trialNumber = e.trialNumber
        
        self.serverSetupComplete = True
        
        self.repetitionCount = e.repetitions
        
    def __mergeSettings(self):
        head = self.experimentSettings[DEFAULT][AVATAR_HEAD]
        lhand = self.experimentSettings[DEFAULT][AVATAR_LEFT_HAND]
        rhand = self.experimentSettings[DEFAULT][AVATAR_RIGHT_HAND]

        # Preserve full body settings from client
        full_body_toggle = self.experimentSettings[DEFAULT].get(FULL_BODY_TOGGLE, viz.OFF)
        full_body_avatar = self.experimentSettings[DEFAULT].get(FULL_BODY_AVATARS, "")
        seated_mode = self.experimentSettings[DEFAULT].get(SEATED_MODE, viz.OFF)
        
        self.serverExperimentSettings[DEFAULT][AVATAR_HEAD] = head
        self.serverExperimentSettings[DEFAULT][AVATAR_LEFT_HAND] = lhand
        self.serverExperimentSettings[DEFAULT][AVATAR_RIGHT_HAND] = rhand
        
        self.experimentSettings = self.serverExperimentSettings
        
        # Restore full body settings
        self.experimentSettings[DEFAULT][FULL_BODY_TOGGLE] = full_body_toggle
        self.experimentSettings[DEFAULT][FULL_BODY_AVATARS] = full_body_avatar
        self.experimentSettings[DEFAULT][SEATED_MODE] = seated_mode
        
        self.experimentSettings[DEFAULT][SCREEN_RECORD] = self.screenRecordFlag
            
    def __clientAvatarsSetup(self, e):
        if e.client != viz.net.getName():
            settings = e.settings
            
            self.clientAvatars[e.client] = {}
            self.clientAvatars[e.client][AVATAR_HEAD_OBJECT] = vizfx.addAvatar(AVATAR_HEAD_RESOURCE_PATH + "/" + settings[DEFAULT][AVATAR_HEAD])
            
            if not self.avatarIntersect:
                self.clientAvatars[e.client][AVATAR_HEAD_OBJECT].disable(viz.INTERSECTION)
            
            if settings[DEFAULT][AUTO_ASSIGN] and "GlowManAuto" in settings[DEFAULT][AVATAR_HEAD]:
                self.clientAvatars[e.client][AVATAR_HEAD_OBJECT].color(e.color)
        
            vizact.ontimer(random.uniform(2, 5), self.clientAvatars[e.client][AVATAR_HEAD_OBJECT].addAction, self.blinkSequence)
            
            self.clientAvatars[e.client][AVATAR_RIGHT_HAND_OBJECT] = vizfx.addChild(AVATAR_HANDS_RESOURCE_PATH + "/" + settings[DEFAULT][AVATAR_RIGHT_HAND])
            self.clientAvatars[e.client][AVATAR_LEFT_HAND_OBJECT] = vizfx.addChild(AVATAR_HANDS_RESOURCE_PATH + "/" + settings[DEFAULT][AVATAR_LEFT_HAND])
            
            self.clientHighlighters[e.client] = {}
            self.clientHighlighters[e.client][CLIENT_R_HIGHLIGHTER] = highlighter.Highlighter()
            self.clientHighlighters[e.client][CLIENT_L_HIGHLIGHTER] = highlighter.Highlighter()
            
            def highlightUpdateFunction(handHighlighter):
                if self.clientHighlightersState[handHighlighter]:
                    handHighlighter.highlight()
                else:
                    handHighlighter.clear()
            
            self.clientHighlightersState[self.clientHighlighters[e.client][CLIENT_R_HIGHLIGHTER]] = False
            self.clientHighlightersState[self.clientHighlighters[e.client][CLIENT_L_HIGHLIGHTER]] = False
            
            self.clientHighlighters[e.client][CLIENT_R_HIGHLIGHTER].setUpdateFunction(highlightUpdateFunction)
            self.clientHighlighters[e.client][CLIENT_L_HIGHLIGHTER].setUpdateFunction(highlightUpdateFunction)
            
            self.nameTags[e.client] = viz.addText((e.client if e.client is not None else "") if settings[DEFAULT][CLIENT_INFO][FIRST_NAME] == "" else settings[DEFAULT][CLIENT_INFO][FIRST_NAME], parent = self.clientAvatars[e.client][AVATAR_HEAD_OBJECT])
            self.nameTags[e.client].alignment(viz.ALIGN_CENTER_BOTTOM)
            self.nameTags[e.client].setBackdrop(viz.BACKDROP_BOX)
            self.nameTags[e.client].setBackdropAlpha(0.4)
            self.nameTags[e.client].resolution(1)
            self.nameTags[e.client].disable(viz.LIGHTING)
            
            self.nameTags[e.client].setScale([0.07, 0.07, 0.07])
            self.nameTags[e.client].setPosition(0, 0.2, -0.1)
            self.nameTags[e.client].setEuler(180, 0, 0)
            
            clientInfo = e.settings[DEFAULT][CLIENT_INFO]
        
            name = clientInfo[FIRST_NAME]
            if name == "":
                name = e.client
                
            self.clientDict[e.client] = name
            self.readyCount = len(self.clientDict)
            
            self.hud.writeToClientList(self.clientDict)
            self.hud.writeToClient(self.hud.clientText.getMessage().split(",")[0], clientsOnline = self.onlineCount, clientsReady = self.readyCount)
            
            if not settings[DEFAULT][CLIENT_INFO][SHOW_NAME]:
                self.nameTags[e.client].visible(viz.OFF)
        
    def __updateClientScene(self, objectTracker, changedObjects):
        if self.hud.sessionRecorder is not None:
            self.hud.sessionRecorder.changedObjects.update(changedObjects)
        
        for objectType in changedObjects:
            for objectName in changedObjects[objectType]:
                if objectName in self.sceneObjects[objectType]:
                    self.sceneObjects[objectType][objectName].setPosition(objectTracker[objectType][objectName][POSITION], mode = viz.ABS_GLOBAL)
                    self.sceneObjects[objectType][objectName].setEuler(objectTracker[objectType][objectName][ORIENTATION], mode = viz.ABS_GLOBAL)
#                self.sceneObjects[objectType][objectName].setScale(objectTracker[objectType][objectName][SCALE], mode = viz.ABS_GLOBAL)

                
#    def __updateClientAvatar(self, e):
#        objectTracker = e.objectTracker
#        if e.client != viz.net.getName():
#            
#            for item in [AVATAR_HEAD_OBJECT, AVATAR_RIGHT_HAND_OBJECT, AVATAR_LEFT_HAND_OBJECT]:
#                if item in objectTracker:
#                    if e.client in self.clientAvatars:
#                        self.clientAvatars[e.client][item].setPosition(objectTracker[item][POSITION])
#                        self.clientAvatars[e.client][item].setEuler(objectTracker[item][ORIENTATION])
#                else:
#                    self.clientAvatars[e.client][item].visible(viz.OFF)
#        
#            if not e.changedObjects == {}:
#                self.__updateClientScene(objectTracker, e.changedObjects)
                
    def __updateClientAvatar(self, e):
        objectTracker = e.objectTracker
        if e.client != viz.net.getName():
            
            # Check if client avatar exists before processing
            if e.client not in self.clientAvatars:
                return
            
            for item in [AVATAR_HEAD_OBJECT, AVATAR_RIGHT_HAND_OBJECT, AVATAR_LEFT_HAND_OBJECT]:
                if item in objectTracker:
                    self.clientAvatars[e.client][item].setPosition(objectTracker[item][POSITION])
                    self.clientAvatars[e.client][item].setEuler(objectTracker[item][ORIENTATION])
                else:
                    self.clientAvatars[e.client][item].visible(viz.OFF)
        
            if not e.changedObjects == {}:
                self.__updateClientScene(objectTracker, e.changedObjects)
    
    def __updateClientMouth(self, e):
        if e.client in self.clientAvatars:
            self.clientAvatars[e.client][AVATAR_HEAD_OBJECT].setMorph(14, e.morphValue*2)

    def __midTrialClientSetup(self, e):
        if e.client == viz.net.getName():
            self.hud.bufferTime = -e.currentTime
            
            #if not e.currentTime == 0.0:
            self.midTrialStart = True
        
    def __quitClient(self, e):
        self.disconnectVoice()  # Disconnect from Mumble before quitting
        
        if self.experimentLoaded:
            if VIZCONNECT_CONFIG == "Desktop":
                vizinput.message("Server disconnected")
            viz.quit()
        else:
            self.gui.buttonLabels[SERVER_STATUS].uppicture(os.path.join(ICONS_PATH, "red_status.png"))
            self.__serverDisconnectedStatus()
    
    def toggleMute(self):
        """Toggle microphone mute"""
        if self.mumbleManager:
            muted = self.mumbleManager.toggle_mute()
            status = "muted" if muted else "unmuted"
            self.hud.writeToStatus(f"Microphone {status}")
            print(f"Client microphone {status}")
            return muted
        return None
    
    def toggleDeafen(self):
        """Toggle audio deafen"""
        if self.mumbleManager:
            deafened = self.mumbleManager.toggle_deafen()
            status = "deafened" if deafened else "undeafened"
            self.hud.writeToStatus(f"Audio {status}")
            print(f"Client audio {status}")
            return deafened
        return None
    
    def disconnectVoice(self):
        """Disconnect from voice server"""
        if self.mumbleManager:
            self.mumbleManager.disconnect()
            self.mumbleManager = None
            print("Client disconnected from voice chat")

if __name__ == '__main__':    
    sightlab = SightLab(gui = True)
    viztask.schedule(sightlab.runExperiment())
    