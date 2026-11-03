import viz
import vizfx
import vizconnect
import vizshape
import vizinput
import vizinfo
import vizact
import viztask
import vizmat
import math
import json
import orjson
import sys
import vizfx.postprocess
import inspect
import glob
import vizdlg
import re

import sightlab_utils.heatmap_config as heatmap_config
import sightlab_utils.attention_map as attention_map

import os
import subprocess
from os import path
from copy import deepcopy

from queue import Queue
from collections import deque

from sightlab_utils import eye_tracker_utils
from sightlab_utils import panorama_utils

from sightlab_utils import sightlab

from sightlab_utils.replay_settings import *
from sightlab_utils.replay_config import *

viz.res.addPath(r"C:\Program Files\WorldViz\Sightlab2")

class ReplayGUI:
    """
    GUI control panel for replay visualization settings and preferences.
    
    Provides an interactive interface panel for controlling all aspects of eye tracking
    replay visualization including scan paths, heatmaps, fixation spheres, avatars,
    walk paths, ROI displays, and playback modes. The GUI is displayed as a right-aligned
    panel with checkboxes, sliders, and dropdowns for real-time adjustment of replay parameters.
    
    The GUI manages visualization settings across multiple clients in multi-user recordings,
    synchronizing changes to all ReplayVisualisations instances. It also handles trial
    selection, AcqKnowledge integration, and view mode switching (follow mode, third person).
    """
    
    def __init__(self, sceneObjects, replayHUD, replayVisualisations, trialMode, trialNumber = None, clientCount = 0):
        """
        Initialize the replay GUI control panel.
        
        Args:
            sceneObjects (dict): Dictionary containing all scene objects organized by type:
                - AVATAR_HEAD_OBJECT: Head tracker visualization objects
                - AVATAR_RIGHT_HAND_OBJECT: Right hand controller objects
                - AVATAR_LEFT_HAND_OBJECT: Left hand controller objects
                - GAZE_POINT_OBJECT: Gaze point visualization spheres
                - REGIONS_OF_INTEREST: ROI boundary objects from scene
            replayHUD (ReplayHUD): HUD display manager for timestamps, console, and status text
            replayVisualisations (dict): Dictionary mapping client IDs to ReplayVisualisations instances
            trialMode (str): Current trial mode - MODEL_3D, MEDIA_360, or other mode constants
            trialNumber (int, optional): Specific trial number to load on startup. Defaults to None.
            clientCount (int): Number of clients in multi-user recording. Defaults to 0 for single user.
        """
        #Initialize info box with some instructions
        self.replayInfoPanel = vizinfo.InfoPanel('Press i key to toggle the Instructions', align=viz.ALIGN_RIGHT_TOP, icon=False, window = overlayWindow)
        self.replayInfoPanel.setTitle('Replay Preferences')
        self.replayInfoPanel.addSeparator()
        
        self.replayInfoPanel.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)
        
        vizact.onkeydown('.', self.replayInfoPanel.setPanelVisible, viz.TOGGLE)
        
        self.trialMode = trialMode
        
        instructionsWindow = viz.addWindow(size=(1,1), pos=(0,1), clearMask = 0, scene=viz.addScene())
        
        self.instructionsInfoPanel = vizinfo.InfoPanel(GUI_TEXT, align=viz.ALIGN_RIGHT_TOP, icon=True, window = instructionsWindow)
        self.instructionsInfoPanel.setTitle('Instructions')
        self.instructionsInfoPanel.setPanelVisible(viz.OFF)
        self.instructionsInfoPanel.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)
        
        vizact.onkeydown('i', self.instructionsInfoPanel.setPanelVisible, viz.TOGGLE)
        
        self.replaySceneSettings = {
            TRIAL_NUMBER: 0,
            GAZE_PATH_TYPE: DEFAULT_GAZE_PATH,
            STATIC_GAZE_PATH: viz.OFF,
            
            SCAN_PATH_VISIBLE: viz.ON,
            GAZE_POINT_VISIBLE: viz.ON,
            GAZE_RAY_VISIBLE: viz.ON if trialMode == MODEL_3D else viz.OFF,
            
            AVATAR_VISIBLE: viz.ON,
            CONTROLLERS_VISIBLE: viz.ON,
            
            TIME_STAMP_VISIBLE: viz.ON,
            CONSOLE_VISIBLE: viz.ON,
            
            ROIS_VISIBLE: viz.ON,
            ROI_TAG_VISIBLE: viz.ON,
            
            DWELL_SPHERES_VISIBLE: viz.ON,
            FIXATION_SPHERES_VISIBLE: viz.ON,
            FIXATION_SPHERES_STATIC: viz.OFF,
            HEAT_MAP_ALPHA_GRADIENT: viz.OFF,
            HEAT_MAP_ALPHA_GRADIENT_SLIDER: 5,
            FIXATION_SPHERES_SCALE: 0.23,
            FIRST_FIXATION_VISIBLE: viz.ON,
            ALL_FIXATION_VISIBLE: viz.OFF,
            
            HEAT_MAP_SLIDER: 0.5,
            HEAT_MAP_TIME: 0.8,
            HEAT_MAP_STATIC: viz.OFF,
            HEAT_MAP_OCCLUSION: viz.OFF,
            
#            HEAT_MAP_RADIUS: viz.radians(heatmap_config.ATTENTION_MAP_ANGULAR_RADIUS),
            HEAT_MAP_RADIUS: 0.14,
            FOLLOW_MODE: viz.ON if trialMode == MEDIA_360 else viz.OFF,
            THIRD_PERSON_MODE: viz.OFF,
            WALK_PATH_VISIBLE: viz.ON
            
#            DISPERSION_THRESHOLD_SLIDER: 0.1,
#            DURATION_THRESHOLD_SLIDER: 0.1,
           # PUPIL_DIAMETER: viz.ON,
            #HEAT_MAP_VISIBLE: viz.ON,
            #
        }
        
        self.defaultSceneSettings = deepcopy(self.replaySceneSettings)
        
        self.lastPlayHead = None
        self.sceneObjects = sceneObjects
        self.replayHUD = replayHUD
        self.replayVisualisations = replayVisualisations
            
        self.replayButtonLabels = {}
        
        self.replayInfoPanel.addItem(viz.addText('Date/Time: ' + PARTICIPANT_ID))
        
        self.replayButtonLabels[TRIAL_NUMBER] = self.replayInfoPanel.addLabelItem('Trial Number', viz.addDropList())

        self.trialList = list(sorted(REPLAY_FILE_LIST.keys(), key = int))
        self.pageCount = 1
        self.pageLimit = 25
        self.pageDict = {}
        self.currPage = 1
        
        if len(self.trialList) > self.pageLimit:
            self.pageCount = len(self.trialList)//self.pageLimit + 1
            if len(self.trialList)%self.pageLimit == 0:
                self.pageCount -= 1
                
            for page in range(self.pageCount):
                start_index = page * self.pageLimit
                end_index = min(start_index + self.pageLimit, len(self.trialList))
                self.pageDict[page + 1] = self.trialList[start_index:end_index]
                
                if page + 1 == 1:
                    self.pageDict[page + 1].append("...")
                elif page + 1 == self.pageCount:
                    self.pageDict[page + 1].insert(0, "...")
                else:
                    self.pageDict[page + 1].append("...")
                    self.pageDict[page + 1].insert(0, "...")
        else:
            self.pageDict[self.currPage] = self.trialList
            
        if trialNumber is not None and trialNumber in self.trialList:
            for i in self.pageDict:
                if trialNumber in self.pageDict[i]:
                    self.currPage = i
                    break
                                
        self.replayButtonLabels[TRIAL_NUMBER].addItems(self.pageDict[self.currPage])
        
        self.showClients = {}
        
        if not clientCount == 0:
            self.replayButtonLabels[CLIENT_ID] = self.replayInfoPanel.addLabelItem("Client ID", viz.addDropList())
            
            clientIDList = ["All"]
            self.showClients["All"] = True
            
            for i in range(1, clientCount+1):
                clientIDList.append("client_" + str(i))
                self.showClients[str(i)] = False

            self.replayButtonLabels[CLIENT_ID].addItems(clientIDList)

        self.replayButtonLabels[DATA_FOLDER] = self.replayInfoPanel.addLabelItem('', viz.addButtonLabel('Open Data Folder'))

        #Add radio buttons
        self.headTracker = vizconnect.getRawTracker("head_tracker")
        self.headLink = None
        self.mediaLink = None

        self.thirdPersonOffset = list(THIRD_PERSON_OFFSET)
        self.thirdPersonPitch = THIRD_PERSON_PITCH

        # Right mouse drag orbits the third person camera around the head (see updateThirdPersonLook)
        self.thirdPersonOrbit = None        # the head link operator that does the orbiting
        self.thirdPersonLook = [0.0, 0.0]   # yaw, pitch currently orbited by
        self.lastMousePos = None
        vizact.onupdate(0, self.updateThirdPersonLook)

        self.replayInfoPanel.addSection('Avatar')

        avatarRow = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False, border=False)
        avatarRow.setMargin(0)

        self.replayButtonLabels[AVATAR_VISIBLE] = avatarRow.addItem(viz.addCheckbox())
        #avatarRow.addItem(viz.addText(' Head   '))
        avatarRow.addItem(viz.addText('     Controllers'))
        self.replayButtonLabels[CONTROLLERS_VISIBLE] = avatarRow.addItem(viz.addCheckbox())
        
        self.replayInfoPanel.addLabelItem('Head', avatarRow)
        
        self.replayInfoPanel.addSection('Gaze Visualisations')

        gazeRow = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False, border=False)
        gazeRow.setMargin(0)

        self.replayButtonLabels[GAZE_RAY_VISIBLE] = gazeRow.addItem(viz.addCheckbox())
        #gazeRow.addItem(viz.addText(' Ray   '))
        gazeRow.addItem(viz.addText('     Point'))
        self.replayButtonLabels[GAZE_POINT_VISIBLE] = gazeRow.addItem(viz.addCheckbox())

        self.replayInfoPanel.addLabelItem('Ray', gazeRow)
        self.replayButtonLabels[DWELL_SPHERES_VISIBLE] = self.replayInfoPanel.addLabelItem('Dwell Spheres', viz.addCheckbox())

        self.replayInfoPanel.addSection('Fixation Spheres')
        fixationRow = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False, border=False)
        fixationRow.setMargin(0)

        self.replayButtonLabels[FIXATION_SPHERES_VISIBLE] = fixationRow.addItem(viz.addCheckbox())
        #fixationRow.addItem(viz.addText(' Visible   '))
        fixationRow.addItem(viz.addText('   Static'))

        self.replayButtonLabels[FIXATION_SPHERES_STATIC] = fixationRow.addItem(viz.addCheckbox())

        self.replayInfoPanel.addLabelItem('Visible', fixationRow)
        
        self.replayButtonLabels[FIXATION_SPHERES_SCALE] = self.replayInfoPanel.addLabelItem('Scale', viz.addProgressBar(str(self.replaySceneSettings[FIXATION_SPHERES_SCALE])))
        vizact.onslider(self.replayButtonLabels[FIXATION_SPHERES_SCALE], self.fixationScaleSlider)
        row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False,border=False)
        row.setMargin(0)
        
        self.replayButtonLabels[HEAT_MAP_ALPHA_GRADIENT] = row.addItem(viz.addCheckbox())
        self.replayButtonLabels[HEAT_MAP_ALPHA_GRADIENT_SLIDER] = row.addItem(viz.addProgressBar(str(self.replaySceneSettings[HEAT_MAP_ALPHA_GRADIENT_SLIDER]) + " secs"))
        self.replayButtonLabels[HEAT_MAP_ALPHA_GRADIENT_SLIDER].setLength(0.9)
        
        vizact.onslider(self.replayButtonLabels[HEAT_MAP_ALPHA_GRADIENT_SLIDER], self.heatmapGradientSlider)
        
        self.replayInfoPanel.addLabelItem('Gradient', row)
        
        row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False,border=False)
        row.setMargin(0)
        
        self.replayButtonLabels[FIRST_FIXATION_VISIBLE] = row.addItem(viz.addCheckbox())
        
        row.addItem(viz.addText(" All"))
        
        self.replayButtonLabels[ALL_FIXATION_VISIBLE] = row.addItem(viz.addCheckbox())
        
        self.replayInfoPanel.addLabelItem('First', row)
        
        #self.replayButtonLabels[HEAT_MAP_VISIBLE] = self.replayInfoPanel.addLabelItem('Heat Map', viz.addCheckbox())
        
        self.replayInfoPanel.addSection('Heat Map')
        
        self.replayButtonLabels[HEAT_MAP_STATIC] = self.replayInfoPanel.addLabelItem('Static', viz.addCheckbox())
#        self.replayButtonLabels[HEAT_MAP_OCCLUSION] = self.replayInfoPanel.addLabelItem('Occlusion', viz.addCheckbox())
        
        self.replayButtonLabels[HEAT_MAP_SLIDER] = self.replayInfoPanel.addLabelItem('Intensity', viz.addProgressBar(str(self.replaySceneSettings[HEAT_MAP_SLIDER])))
        
        vizact.onslider(self.replayButtonLabels[HEAT_MAP_SLIDER], self.heatmapSlider)
        
        self.replayButtonLabels[HEAT_MAP_RADIUS] = self.replayInfoPanel.addLabelItem('Radius', viz.addProgressBar(str(self.replaySceneSettings[HEAT_MAP_RADIUS]) + " rads"))
        
        vizact.onslider(self.replayButtonLabels[HEAT_MAP_RADIUS], self.heatmapRadiusSlider)
        
        self.replayButtonLabels[HEAT_MAP_TIME] = self.replayInfoPanel.addLabelItem('Rate', viz.addProgressBar(str(self.replaySceneSettings[HEAT_MAP_TIME]) + " secs"))
        
        vizact.onslider(self.replayButtonLabels[HEAT_MAP_TIME], self.heatmapTimeSlider)
        
        self.replayInfoPanel.addSection('Paths')
    
        row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False,border=False)
        row.setMargin(0)
        
        self.replayButtonLabels[SCAN_PATH_VISIBLE] = row.addItem(viz.addCheckbox())
        row.addItem(viz.addText("Visible   "))
        
        self.replayButtonLabels[STATIC_GAZE_PATH] = row.addItem(viz.addCheckbox())
        row.addItem(viz.addText("Static"))
        
        self.replayInfoPanel.addLabelItem("Scan Path", row)
        
        #self.replayButtonLabels[NO_GAZE_PATH] = self.replayInfoPanel.addLabelItem('None', viz.addRadioButton('scanpath'))
        
#        self.replayButtonLabels[DYNAMIC_GAZE_PATH] = self.replayInfoPanel.addLabelItem('Gaze Path', viz.addRadioButton('scanpath'))
#        #self.replayButtonLabels[DYNAMIC_SACCADE_PATH] = self.replayInfoPanel.addLabelItem('Saccade Path', viz.addRadioButton('scanpath'))
#        self.replayButtonLabels[DYNAMIC_DISPERSION_PATH] = self.replayInfoPanel.addLabelItem('Dispersion Path', viz.addRadioButton('scanpath'))
#        
        row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False,border=False)
        row.setMargin(0)
        
        self.replayButtonLabels[DYNAMIC_GAZE_PATH] = row.addItem(viz.addRadioButton('scanpath'))
        row.addItem(viz.addText(f"Gaze      "))

        self.replayButtonLabels[DYNAMIC_DISPERSION_PATH] = row.addItem(viz.addRadioButton('scanpath'))
        row.addItem(viz.addText("Dispersion"))
        
        self.replayInfoPanel.addLabelItem("Type", row)
        
        self.replayInfoPanel.addSeparator()
        
        row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False,border=False)
        row.setMargin(0)
        
        self.replayButtonLabels[WALK_PATH_VISIBLE] = row.addItem(viz.addCheckbox())
        row.addItem(viz.addText("Visible   "))
        
        self.replayButtonLabels[WALK_PATH_STATIC] = row.addItem(viz.addCheckbox())
        row.addItem(viz.addText("Static"))
        
        self.replayInfoPanel.addLabelItem("Walk Path", row)
        
#        self.replayButtonLabels[WALK_PATH_VISIBLE] = self.replayInfoPanel.addLabelItem('Walk Path', viz.addCheckbox())
                
#        self.replayButtonLabels[DISPERSION_THRESHOLD_SLIDER] = self.replayInfoPanel.addLabelItem('Dispersion Threshold', viz.addProgressBar("1.0"))
#        self.replayButtonLabels[DISPERSION_THRESHOLD_SLIDER].set(0.1)
#        vizact.onslider(self.replayButtonLabels[DISPERSION_THRESHOLD_SLIDER], self.dispersionThresholdSlider)
#        
#        self.replayButtonLabels[DURATION_THRESHOLD_SLIDER] = self.replayInfoPanel.addLabelItem('Duration Threshold', viz.addProgressBar("0.1"))
#        self.replayButtonLabels[DURATION_THRESHOLD_SLIDER].set(0.1)
#        vizact.onslider(self.replayButtonLabels[DURATION_THRESHOLD_SLIDER], self.durationThresholdSlider)
        
        self.replayInfoPanel.addSection('Console')

        row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False,border=False)
        row.setMargin(0)
        
        self.replayButtonLabels[TIME_STAMP_VISIBLE] = row.addItem(viz.addCheckbox())
        row.addItem(viz.addText(" Fixations"))
        
        self.replayButtonLabels[CONSOLE_VISIBLE] = row.addItem(viz.addCheckbox())
        
#        self.replayButtonLabels[TIME_STAMP_VISIBLE] = self.replayInfoPanel.addLabelItem('Pupil Diameter', viz.addCheckbox())
#        self.replayButtonLabels[CONSOLE_VISIBLE] = self.replayInfoPanel.addLabelItem('Fixations', viz.addCheckbox())

        self.replayInfoPanel.addLabelItem('Pupil Diameter', row)
        
        row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False,border=False)
        row.setMargin(0)
        
        self.replayButtonLabels[ROIS_VISIBLE] = row.addItem(viz.addCheckbox())
        row.addItem(viz.addText(" Tags"))
        
        self.replayButtonLabels[ROI_TAG_VISIBLE] = row.addItem(viz.addCheckbox())
        
        self.replayInfoPanel.addLabelItem('ROIs', row)
        
        self.replayInfoPanel.addSection('Views')
        
        row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False,border=False)
        row.setMargin(0)

        self.replayButtonLabels[FOLLOW_MODE] = row.addItem(viz.addCheckbox())
        row.addItem(viz.addText("   Third Person"))

        self.replayButtonLabels[THIRD_PERSON_MODE] = row.addItem(viz.addCheckbox())

        self.replayInfoPanel.addLabelItem('Follow Mode', row)

        self.replayInfoPanel.addSeparator()

        biopacRow = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER, align=vizdlg.ALIGN_LEFT_CENTER, background=False, border=False)
        biopacRow.setMargin(0)

        self.replayButtonLabels[CONNECT_BIOPAC] = biopacRow.addItem(viz.addButtonLabel('Connect BIOPAC'))
        biopacRow.addItem(viz.addText('   '))
        self.replayButtonLabels[ATTACH_GRAPH] = biopacRow.addItem(viz.addButtonLabel('Attach Graph'))

        self.replayInfoPanel.addItem(biopacRow)
        
        self.replayButtonLabels[RESET_SETTINGS] = self.replayInfoPanel.addItem(viz.addButtonLabel('Reset to Default'))
        
        self.setSettings()
        
        #vizact.onbuttondown(self.replayButtonLabels[DYNAMIC_SACCADE_PATH], self.dynamicSaccadeScanPath)
        vizact.onbuttondown(self.replayButtonLabels[DYNAMIC_GAZE_PATH], self.dynamicScanPath)
        vizact.onbuttondown(self.replayButtonLabels[DYNAMIC_DISPERSION_PATH], self.dynamicDispersionScanPath)
        
        vizact.onbuttondown(self.replayButtonLabels[STATIC_GAZE_PATH], self.staticScanPathON)
        vizact.onbuttonup(self.replayButtonLabels[STATIC_GAZE_PATH], self.staticScanPathOFF)
        
        vizact.onbuttondown(self.replayButtonLabels[SCAN_PATH_VISIBLE], self.scanPathON)
        vizact.onbuttonup(self.replayButtonLabels[SCAN_PATH_VISIBLE], self.scanPathOFF)
        vizact.onbuttondown(self.replayButtonLabels[WALK_PATH_VISIBLE], self.walkPathON)
        vizact.onbuttonup(self.replayButtonLabels[WALK_PATH_VISIBLE], self.walkPathOFF)
        vizact.onbuttondown(self.replayButtonLabels[WALK_PATH_STATIC], self.walkPathStaticON)
        vizact.onbuttonup(self.replayButtonLabels[WALK_PATH_STATIC], self.walkPathStaticOFF)
        vizact.onbuttondown(self.replayButtonLabels[AVATAR_VISIBLE], self.avatarON)
        vizact.onbuttonup(self.replayButtonLabels[AVATAR_VISIBLE], self.avatarOFF)
        vizact.onbuttondown(self.replayButtonLabels[TIME_STAMP_VISIBLE], self.timeStampON)
        vizact.onbuttonup(self.replayButtonLabels[TIME_STAMP_VISIBLE], self.timeStampOFF)
        vizact.onbuttondown(self.replayButtonLabels[ROIS_VISIBLE], self.roiON)
        vizact.onbuttonup(self.replayButtonLabels[ROIS_VISIBLE], self.roiOFF)
        vizact.onbuttondown(self.replayButtonLabels[ROI_TAG_VISIBLE], self.roiTagON)
        vizact.onbuttonup(self.replayButtonLabels[ROI_TAG_VISIBLE], self.roiTagOFF)
        vizact.onbuttondown(self.replayButtonLabels[DWELL_SPHERES_VISIBLE], self.dwellSpheresON)
        vizact.onbuttonup(self.replayButtonLabels[DWELL_SPHERES_VISIBLE], self.dwellSpheresOFF)
        vizact.onbuttondown(self.replayButtonLabels[FIXATION_SPHERES_VISIBLE], self.fixationSpheresON)
        vizact.onbuttonup(self.replayButtonLabels[FIXATION_SPHERES_VISIBLE], self.fixationSpheresOFF)
        vizact.onbuttondown(self.replayButtonLabels[FIXATION_SPHERES_STATIC], self.fixationSpheresStaticON)
        vizact.onbuttonup(self.replayButtonLabels[FIXATION_SPHERES_STATIC], self.fixationSpheresStaticOFF)
        vizact.onbuttondown(self.replayButtonLabels[FIRST_FIXATION_VISIBLE], self.firstFixationON)
        vizact.onbuttonup(self.replayButtonLabels[FIRST_FIXATION_VISIBLE], self.firstFixationOFF)
        vizact.onbuttondown(self.replayButtonLabels[ALL_FIXATION_VISIBLE], self.allFixationON)
        vizact.onbuttonup(self.replayButtonLabels[ALL_FIXATION_VISIBLE], self.allFixationOFF)
        vizact.onbuttondown(self.replayButtonLabels[GAZE_RAY_VISIBLE], self.gazeRayON)
        vizact.onbuttonup(self.replayButtonLabels[GAZE_RAY_VISIBLE], self.gazeRayOFF)
        vizact.onbuttondown(self.replayButtonLabels[CONTROLLERS_VISIBLE], self.controllersON)
        vizact.onbuttonup(self.replayButtonLabels[CONTROLLERS_VISIBLE], self.controllersOFF)
        vizact.onbuttondown(self.replayButtonLabels[GAZE_POINT_VISIBLE], self.gazePointON)
        vizact.onbuttonup(self.replayButtonLabels[GAZE_POINT_VISIBLE], self.gazePointOFF)
        vizact.onbuttondown(self.replayButtonLabels[CONSOLE_VISIBLE], self.consoleON)
        vizact.onbuttonup(self.replayButtonLabels[CONSOLE_VISIBLE], self.consoleOFF)
        vizact.onbuttondown(self.replayButtonLabels[FOLLOW_MODE], self.followON)
        vizact.onbuttonup(self.replayButtonLabels[FOLLOW_MODE], self.followOFF)
        vizact.onbuttondown(self.replayButtonLabels[THIRD_PERSON_MODE], self.thirdPersonON)
        vizact.onbuttonup(self.replayButtonLabels[THIRD_PERSON_MODE], self.thirdPersonOFF)
        vizact.onbuttondown(self.replayButtonLabels[HEAT_MAP_STATIC], self.heatmapStaticON)
        vizact.onbuttonup(self.replayButtonLabels[HEAT_MAP_STATIC], self.heatmapStaticOFF)
#        vizact.onbuttondown(self.replayButtonLabels[HEAT_MAP_OCCLUSION], self.heatmapOcclusionON)
#        vizact.onbuttonup(self.replayButtonLabels[HEAT_MAP_OCCLUSION], self.heatmapOcclusionOFF)
        vizact.onbuttondown(self.replayButtonLabels[HEAT_MAP_ALPHA_GRADIENT], self.heatmapGradientON)
        vizact.onbuttonup(self.replayButtonLabels[HEAT_MAP_ALPHA_GRADIENT], self.heatmapGradientOFF)
        
        vizact.onbuttonup(self.replayButtonLabels[CONNECT_BIOPAC], connectToAcqKnowledge)
        vizact.onbuttonup(self.replayButtonLabels[ATTACH_GRAPH], attachToGraph)


        vizact.onbuttonup(self.replayButtonLabels[RESET_SETTINGS], self.setDefaultSettings)
        
    def dynamicScanPath(self):
        """
        Switch scan path visualization to dynamic gaze path mode.
        
        Sets the scan path type to show every gaze point connected sequentially,
        creating a continuous path that follows the exact gaze trajectory.
        """
        self.replaySceneSettings[GAZE_PATH_TYPE] = DYNAMIC_GAZE_PATH
        
        for client in self.replayVisualisations:
            if self.showClients == {} or self.showClients[client] or self.showClients["All"]:
                self.replayVisualisations[client].drawScanPath(self.lastPlayHead, visible = self.replaySceneSettings[SCAN_PATH_VISIBLE], scanPathType = self.replaySceneSettings[GAZE_PATH_TYPE])
        
    def dynamicSaccadeScanPath(self):
        """
        Switch scan path visualization to dynamic saccade path mode.
        
        Sets the scan path type to show only saccadic eye movements (rapid jumps
        between fixation points), filtering out fixation periods.
        """
        self.replaySceneSettings[GAZE_PATH_TYPE] = DYNAMIC_SACCADE_PATH
        
        for client in self.replayVisualisations:
            if self.showClients == {} or self.showClients[client] or self.showClients["All"]:
                self.replayVisualisations[client].drawScanPath(self.lastPlayHead, visible = self.replaySceneSettings[SCAN_PATH_VISIBLE], scanPathType = self.replaySceneSettings[GAZE_PATH_TYPE])
        
    def dynamicDispersionScanPath(self):
        """
        Switch scan path visualization to dispersion-based path mode.
        
        Sets the scan path type to show gaze paths calculated using dispersion-threshold
        identification (I-DT) algorithm, connecting fixation points with smooth paths.
        """
        self.replaySceneSettings[GAZE_PATH_TYPE] = DYNAMIC_DISPERSION_PATH
        
        for client in self.replayVisualisations:
            if self.showClients == {} or self.showClients[client] or self.showClients["All"]:
                self.replayVisualisations[client].drawScanPath(self.lastPlayHead, visible = self.replaySceneSettings[SCAN_PATH_VISIBLE], scanPathType = self.replaySceneSettings[GAZE_PATH_TYPE])
        
    def staticScanPathON(self):
        """
        Enable static scan path mode.
        
        When enabled, displays the entire scan path from start to current playhead position
        as a static visualization, rather than animating it progressively.
        """
        self.replaySceneSettings[STATIC_GAZE_PATH] = viz.ON
        
        for client in self.replayVisualisations:
            if self.showClients == {} or self.showClients[client] or self.showClients["All"]:
                self.replayVisualisations[client].drawScanPath(self.lastPlayHead, visible = self.replaySceneSettings[SCAN_PATH_VISIBLE], scanPathType = self.replaySceneSettings[GAZE_PATH_TYPE], static = self.replaySceneSettings[STATIC_GAZE_PATH])
        
    def staticScanPathOFF(self):
        """
        Disable static scan path mode.
        
        Returns to dynamic scan path mode where the path is animated progressively
        as the replay playhead advances.
        """
        self.replaySceneSettings[STATIC_GAZE_PATH] = viz.OFF
        
        for client in self.replayVisualisations:
            if self.showClients == {} or self.showClients[client] or self.showClients["All"]:
                self.replayVisualisations[client].drawScanPath(self.lastPlayHead, visible = self.replaySceneSettings[SCAN_PATH_VISIBLE], scanPathType = self.replaySceneSettings[GAZE_PATH_TYPE], static = self.replaySceneSettings[STATIC_GAZE_PATH])
        
    def scanPathON(self):
        """
        Enable scan path visualization.
        
        Shows the gaze scan path connecting sequential gaze points, using the currently
        selected scan path type (gaze, saccade, or dispersion).
        """
        self.replaySceneSettings[SCAN_PATH_VISIBLE] = viz.ON
        
        for client in self.replayVisualisations:
            if self.showClients == {} or self.showClients[client] or self.showClients["All"]:
                self.replayVisualisations[client].drawScanPath(self.lastPlayHead, visible = self.replaySceneSettings[SCAN_PATH_VISIBLE], scanPathType = self.replaySceneSettings[GAZE_PATH_TYPE])
      
    def durationThresholdSlider(self, sliderPOS):
        if sliderPOS < 0.1:
            sliderPOS = 0.1
        
        val = sliderPOS * float(1.0)
        
        self.replayButtonLabels[DURATION_THRESHOLD_SLIDER].message('%.2f'%(val))
        
        for client in self.replayVisualisations:
            if self.showClients == {} or self.showClients[client] or self.showClients["All"]:
                self.replayVisualisations[client].scanPathDurationThreshold = val
                if len(self.replayVisualisations[client].timeStampList) > 0:
                    self.replayVisualisations[client].dispersionWindowSize = int(val/(float(self.replayVisualisations[client].timeStampList[-1])/len(self.replayVisualisations[client].timeStampList)))
                else:
                    self.replayVisualisations[client].dispersionWindowSize = 5
                    
                self.replayVisualisations[client].sessionRecorder.saccadeFixationCalculate(self.replayVisualisations[client].currentTrialData, self.replayVisualisations[client].scanPathDispersionThreshold, self.replayVisualisations[client].scanPathDurationThreshold)
                self.replayVisualisations[client].clearFixationSpheres()
        
#        val = sliderPos * float(self.timeStampList[-1])
#        self.playbackSlider.message('%.2f'%(val))
#        
#        currTimeStampIndex = int(sliderPos * len(self.timeStampList))
#        self.playHead = currTimeStampIndex
#        self.updateScene()
        
    def dispersionThresholdSlider(self, sliderPOS):
        minVal = 0.5
        maxVal = 3
        normalized_value = minVal + sliderPOS * (maxVal - minVal) #(sliderPOS - minVal) / (maxVal - minVal)
        
        self.replayButtonLabels[DISPERSION_THRESHOLD_SLIDER].message('%.2f'%(normalized_value))
        
        for client in self.replayVisualisations:
            if self.showClients == {} or self.showClients[client] or self.showClients["All"]:
                self.replayVisualisations[client].scanPathDispersionThreshold = normalized_value
                self.replayVisualisations[client].sessionRecorder.saccadeFixationCalculate(self.replayVisualisations[client].currentTrialData, self.replayVisualisations[client].scanPathDispersionThreshold, self.replayVisualisations[client].scanPathDurationThreshold)
                self.replayVisualisations[client].clearFixationSpheres()
            
    def scanPathOFF(self):
        """
        Disable scan path visualization.
        
        Hides and clears the gaze scan path from all replay visualizations.
        """
        self.replaySceneSettings[SCAN_PATH_VISIBLE] = viz.OFF
        
        for client in self.replayVisualisations:
            if self.showClients == {} or self.showClients[client] or self.showClients["All"]:
                self.replayVisualisations[client].clearScanPath()
                
    def walkPathON(self):
        """
        Enable walk path visualization.
        
        Shows the participant's physical movement trajectory through the environment,
        visualized as a colored path with directional arrows.
        """
        self.replaySceneSettings[WALK_PATH_VISIBLE] = viz.ON
        
        for client in self.replayVisualisations:
            self.replayVisualisations[client].drawWalkPath(self.lastPlayHead, self.replaySceneSettings[WALK_PATH_VISIBLE])
    
    def walkPathOFF(self):
        """
        Disable walk path visualization.
        
        Hides and clears the physical movement trajectory path.
        """
        self.replaySceneSettings[WALK_PATH_VISIBLE] = viz.OFF
        
        for client in self.replayVisualisations:
            self.replayVisualisations[client].clearWalkPath()
            
    def walkPathStaticON(self):
        """
        Enable static walk path mode.
        
        Displays the entire walk path from start to current playhead position
        as a static visualization.
        """
        self.replaySceneSettings[WALK_PATH_STATIC] = viz.ON
        
        for client in self.replayVisualisations:
            self.replayVisualisations[client].drawWalkPath(self.lastPlayHead, self.replaySceneSettings[WALK_PATH_VISIBLE], self.replaySceneSettings[WALK_PATH_STATIC])
        
    def walkPathStaticOFF(self):
        self.replaySceneSettings[WALK_PATH_STATIC] = viz.OFF
        
        for client in self.replayVisualisations:
            self.replayVisualisations[client].drawWalkPath(self.lastPlayHead, self.replaySceneSettings[WALK_PATH_VISIBLE], self.replaySceneSettings[WALK_PATH_STATIC])
               
    def avatarON(self):
        """
        Enable avatar head visualization.
        
        Shows the 3D avatar head model representing the participant's head position
        and orientation during the recording.
        """
        for client in self.sceneObjects[AVATAR_HEAD_OBJECT]:
            self.sceneObjects[AVATAR_HEAD_OBJECT][client].visible(viz.ON)
            
        self.replaySceneSettings[AVATAR_VISIBLE] = viz.ON
        
    def avatarOFF(self):
        """
        Disable avatar head visualization.
        
        Hides the 3D avatar head model from the replay scene.
        """
        for client in self.sceneObjects[AVATAR_HEAD_OBJECT]:
            self.sceneObjects[AVATAR_HEAD_OBJECT][client].visible(viz.OFF)
            
        self.replaySceneSettings[AVATAR_VISIBLE] = viz.OFF
                
    def timeStampON(self):
        """
        Enable timestamp/pupil diameter display.
        
        Shows the HUD timer text displaying current replay timestamp and pupil diameter data.
        """
        self.replaySceneSettings[TIME_STAMP_VISIBLE] = viz.ON
        
        self.replayHUD.timerText.visible(viz.ON)
            
    def timeStampOFF(self):
        """
        Disable timestamp/pupil diameter display.
        
        Hides the HUD timer text from the overlay.
        """
        self.replaySceneSettings[TIME_STAMP_VISIBLE] = viz.OFF
        
        self.replayHUD.timerText.visible(viz.OFF)
        
    def roiON(self):
        """
        Enable region of interest (ROI) boundary visualization.
        
        Shows all ROI objects in the scene as 3D boundary representations.
        """
        self.replaySceneSettings[ROIS_VISIBLE] = viz.ON
        
        for item in self.sceneObjects[REGIONS_OF_INTEREST]:
            self.sceneObjects[REGIONS_OF_INTEREST][item].visible(viz.ON)
        
    def roiOFF(self):
        """
        Disable region of interest (ROI) boundary visualization.
        
        Hides all ROI boundary objects from the scene.
        """
        self.replaySceneSettings[ROIS_VISIBLE] = viz.OFF
        
        for item in self.sceneObjects[REGIONS_OF_INTEREST]:
            self.sceneObjects[REGIONS_OF_INTEREST][item].visible(viz.OFF)
        
    def roiTagON(self):
        """
        Enable ROI name tag labels.
        
        Shows text labels displaying the names of regions of interest,
        positioned at the centroid of each ROI and oriented toward the viewer.
        """
        self.replaySceneSettings[ROI_TAG_VISIBLE] = viz.ON
        
        firstClient = next(iter(self.replayVisualisations))
        
        for tag in self.replayVisualisations[firstClient].roiTags:
            self.replayVisualisations[firstClient].roiTags[tag].visible(viz.ON)
        
    def roiTagOFF(self):
        self.replaySceneSettings[ROI_TAG_VISIBLE] = viz.OFF
        
        firstClient = next(iter(self.replayVisualisations))
        
        for tag in self.replayVisualisations[firstClient].roiTags:
            self.replayVisualisations[firstClient].roiTags[tag].visible(viz.OFF)
           
    def dwellSpheresON(self):
        """
        Enable dwell sphere visualization.
        
        Shows colored spheres at each gaze object indicating cumulative dwell time.
        Sphere size and color intensity scale with dwell duration on the object.
        """
        self.replaySceneSettings[DWELL_SPHERES_VISIBLE] = viz.ON
        
        for client in self.replayVisualisations:
            for fixationItem in self.replayVisualisations[client].dwellSpheres:
                self.replayVisualisations[client].dwellSpheres[fixationItem].visible(viz.ON)
#                self.replayVisualisations[client].dwellSpheres[fixationItem].alpha(0.5)
              
    def dwellSpheresOFF(self):
        """
        Disable dwell sphere visualization.
        
        Hides all dwell spheres showing cumulative gaze duration on objects.
        """
        self.replaySceneSettings[DWELL_SPHERES_VISIBLE] = viz.OFF
        
        for client in self.replayVisualisations:
            for fixationItem in self.replayVisualisations[client].dwellSpheres:
                self.replayVisualisations[client].dwellSpheres[fixationItem].visible(viz.OFF)
    
    def fixationSpheresON(self):
        """
        Enable fixation sphere visualization.
        
        Shows colored spheres at fixation locations calculated using dispersion-threshold
        identification (I-DT) algorithm. Sphere size and color indicate fixation duration.
        """
        self.replaySceneSettings[FIXATION_SPHERES_VISIBLE] = viz.ON
        
        for client in self.replayVisualisations:
            self.replayVisualisations[client].drawFixationSpheres(self.lastPlayHead, static = (self.replayButtonLabels[FIXATION_SPHERES_STATIC].get() == viz.DOWN))
              
    def fixationSpheresOFF(self):
        """
        Disable fixation sphere visualization.
        
        Hides and clears all fixation spheres from the replay scene.
        """
        self.replaySceneSettings[FIXATION_SPHERES_VISIBLE] = viz.OFF
        
        for client in self.replayVisualisations:
            self.replayVisualisations[client].clearFixationSpheres()

    def fixationSpheresStaticON(self):
        """
        Enable static fixation sphere mode.
        
        Displays all fixation spheres from start to current playhead position
        simultaneously, rather than revealing them progressively.
        """
        self.replaySceneSettings[FIXATION_SPHERES_STATIC] = viz.ON
        
        for client in self.replayVisualisations:
            self.replayVisualisations[client].drawFixationSpheres(self.lastPlayHead, static = (self.replayButtonLabels[FIXATION_SPHERES_STATIC].get() == viz.DOWN))

    def fixationSpheresStaticOFF(self):
        """
        Disable static fixation sphere mode.
        
        Returns to dynamic mode where fixation spheres appear progressively
        as the replay advances.
        """
        self.replaySceneSettings[FIXATION_SPHERES_STATIC] = viz.OFF

        for client in self.replayVisualisations:
            self.replayVisualisations[client].drawFixationSpheres(self.lastPlayHead, static = (self.replayButtonLabels[FIXATION_SPHERES_STATIC].get() == viz.DOWN))
    
    def firstFixationON(self):
        """
        Enable first fixation label display.
        
        Shows a text label marking the first detected fixation in the recording.
        """
        self.replaySceneSettings[FIRST_FIXATION_VISIBLE] = viz.ON

        for client in self.replayVisualisations:
            if len(self.replayVisualisations[client].fixationTags) > 0:
                firstKey = next(iter(self.replayVisualisations[client].fixationTags))
                firstFixation = self.replayVisualisations[client].fixationTags[firstKey].visible(viz.ON)
            
    def firstFixationOFF(self):
        """
        Disable first fixation label display.
        
        Hides the text label marking the first fixation.
        """
        self.replaySceneSettings[FIRST_FIXATION_VISIBLE] = viz.OFF

        for client in self.replayVisualisations:
            if len(self.replayVisualisations[client].fixationTags) > 0:
                firstKey = next(iter(self.replayVisualisations[client].fixationTags))
                firstFixation = self.replayVisualisations[client].fixationTags[firstKey].visible(viz.OFF)
                
    def allFixationON(self):
        """
        Enable all fixation label displays.
        
        Shows text labels for all detected fixations with index numbers,
        respecting the First Fixation visibility setting.
        """
        self.replaySceneSettings[ALL_FIXATION_VISIBLE] = viz.ON

        for client in self.replayVisualisations:
            for sphere in self.replayVisualisations[client].fixationTags:
                if sphere == next(iter(self.replayVisualisations[client].fixationTags)):
                    if not self.replaySceneSettings[FIRST_FIXATION_VISIBLE]:
                        continue
                self.replayVisualisations[client].fixationTags[sphere].visible(viz.ON)
        
    def allFixationOFF(self):
        """
        Disable all fixation label displays.
        
        Hides text labels for all fixations except the first if it's enabled separately.
        """
        self.replaySceneSettings[ALL_FIXATION_VISIBLE] = viz.OFF

        for client in self.replayVisualisations:
            for sphere in self.replayVisualisations[client].fixationTags:
                if sphere == next(iter(self.replayVisualisations[client].fixationTags)):
                    if self.replaySceneSettings[FIRST_FIXATION_VISIBLE]:
                        continue
                self.replayVisualisations[client].fixationTags[sphere].visible(viz.OFF)
            
    def gazeRayON(self):
        """
        Enable gaze ray visualization.
        
        Shows a colored line projecting from the eyes to the gaze point in 3D space.
        Only applicable for MODEL_3D trial mode.
        """
        self.replaySceneSettings[GAZE_RAY_VISIBLE] = viz.ON
        
        for client in self.replayVisualisations:
            self.replayVisualisations[client].drawGazeRay(self.lastPlayHead, visible = self.replaySceneSettings[GAZE_RAY_VISIBLE])
       
    def gazeRayOFF(self):
        """
        Disable gaze ray visualization.
        
        Hides and clears the gaze ray line from the scene.
        """
        self.replaySceneSettings[GAZE_RAY_VISIBLE] = viz.OFF
        
        for client in self.replayVisualisations:
            self.replayVisualisations[client].clearGazeRay()
            
    def controllersON(self):
        """
        Enable hand controller visualization.
        
        Shows 3D models of left and right hand controllers representing tracked
        hand positions during the recording.
        """
        self.replaySceneSettings[CONTROLLERS_VISIBLE] = viz.ON
        
        for client in self.sceneObjects[AVATAR_RIGHT_HAND_OBJECT]:
            self.sceneObjects[AVATAR_RIGHT_HAND_OBJECT][client].visible(viz.ON)
            self.sceneObjects[AVATAR_LEFT_HAND_OBJECT][client].visible(viz.ON)  
        
    def controllersOFF(self):
        """
        Disable hand controller visualization.
        
        Hides the left and right hand controller models from the scene.
        """
        self.replaySceneSettings[CONTROLLERS_VISIBLE] = viz.OFF
        
        for client in self.sceneObjects[AVATAR_RIGHT_HAND_OBJECT]:
            self.sceneObjects[AVATAR_RIGHT_HAND_OBJECT][client].visible(viz.OFF)
            self.sceneObjects[AVATAR_LEFT_HAND_OBJECT][client].visible(viz.OFF)
                
    def gazePointON(self):
        """
        Enable gaze point sphere visualization.
        
        Shows a small colored sphere at the current gaze point location in the environment.
        """
        self.replaySceneSettings[GAZE_POINT_VISIBLE] = viz.ON
        
        for client in self.sceneObjects[GAZE_POINT_OBJECT]:
            self.sceneObjects[GAZE_POINT_OBJECT][client].visible(viz.ON)
            self.sceneObjects[GAZE_POINT_OBJECT_L][client].visible(viz.ON)
            self.sceneObjects[GAZE_POINT_OBJECT_R][client].visible(viz.ON)
            
    def gazePointOFF(self):
        """
        Disable gaze point sphere visualization.
        
        Hides the gaze point sphere from the scene.
        """
        self.replaySceneSettings[GAZE_POINT_VISIBLE] = viz.OFF
        
        for client in self.sceneObjects[GAZE_POINT_OBJECT]:
            self.sceneObjects[GAZE_POINT_OBJECT][client].visible(viz.OFF)
            self.sceneObjects[GAZE_POINT_OBJECT_L][client].visible(viz.OFF)
            self.sceneObjects[GAZE_POINT_OBJECT_R][client].visible(viz.OFF)
        
    def consoleON(self):
        """
        Enable fixation console display.
        
        Shows HUD console panels displaying currently fixated objects and recently
        ended fixations for real-time tracking during replay.
        """
        self.replaySceneSettings[CONSOLE_VISIBLE] = viz.ON
        self.replayHUD.consoleFixated.visible(viz.ON)
        for i in self.replayHUD.fixatedText:
            self.replayHUD.fixatedText[i].visible(viz.ON)
        
        self.replayHUD.consoleEnded.visible(viz.ON)
        for i in self.replayHUD.endedText:
            self.replayHUD.endedText[i].visible(viz.ON)
        
    def consoleOFF(self):
        """
        Disable fixation console display.
        
        Hides the HUD console panels showing fixation status information.
        """
        self.replaySceneSettings[CONSOLE_VISIBLE] = viz.OFF
        self.replayHUD.consoleFixated.visible(viz.OFF)
        for i in self.replayHUD.fixatedText:
            self.replayHUD.fixatedText[i].visible(viz.OFF)
        
        self.replayHUD.consoleEnded.visible(viz.OFF)
        for i in self.replayHUD.endedText:
            self.replayHUD.endedText[i].visible(viz.OFF)
            
    def pupilDiameterON(self):
        """Enable pupil diameter display (placeholder for future implementation)."""
        pass
        
    def pupilDiameterOFF(self):
        """Disable pupil diameter display (placeholder for future implementation)."""
        pass
            
    def followON(self):
        """
        Enable follow mode camera view.
        
        Links the viewpoint camera directly to the participant's head tracker,
        providing a first-person perspective of the recorded experience, or the
        third person view if that is on (see thirdPersonON). Disables free
        navigation and hides the avatar head in first person to avoid self-occlusion.
        """
        self.replaySceneSettings[FOLLOW_MODE] = viz.ON
        transportNode = vizconnect.getTransport('main_transport').getNode3d()
        
        vizconnect.getTransport('main_transport').setEnabled(viz.OFF)
        
        if not self.replayButtonLabels[FOLLOW_MODE].get():
            self.replayButtonLabels[FOLLOW_MODE].set(1)
        
        if self.trialMode == MODEL_3D:
            #pos = self.sceneObjects[AVATAR_HEAD_OBJECT].getPosition(viz.ABS_GLOBAL)
            #offset = vizmat.Distance(viz.MainView.getPosition(mode = viz.ABS_GLOBAL), transportNode.getPosition(mode = viz.ABS_GLOBAL))

            #pos[1] = transportNode.getPosition(viz.ABS_GLOBAL)[1]
            
            #transportNode.setPosition(pos, mode = viz.ABS_GLOBAL)
            
            transportNode.setPosition([0,0,0], mode = viz.ABS_GLOBAL)

        # Already following: replace the link rather than leave a second one driving the view
        if self.headLink is not None:
            self.headLink.remove()

        self.headLink = viz.link(self.sceneObjects[AVATAR_HEAD_OBJECT][next(iter(self.sceneObjects[AVATAR_HEAD_OBJECT]))], self.headTracker)

        self.updateFollowView()

    def followOFF(self):
        """
        Disable follow mode camera view.
        
        Unlinks the viewpoint from the head tracker, re-enables free navigation,
        repositions the transport node, and shows the avatar. For 360 media, maintains
        position lock to the media object. Also turns third person off.
        """
        self.replaySceneSettings[FOLLOW_MODE] = viz.OFF
        self.replaySceneSettings[THIRD_PERSON_MODE] = viz.OFF

        if self.replayButtonLabels[THIRD_PERSON_MODE].get():
            self.replayButtonLabels[THIRD_PERSON_MODE].set(0)

        if self.headLink is not None:
            self.headLink.remove()
            self.headLink = None
        
        transportNode = vizconnect.getTransport('main_transport').getNode3d()
        
        vizconnect.getTransport('main_transport').setEnabled(viz.ON)
        
        if self.trialMode == MEDIA_360:
            self.mediaLink = viz.link(viz.MainView, self.sceneObjects[MEDIA_OBJECT], mask=viz.LINK_POS)
            self.avatarOFF()
            
        else:
            yPos = transportNode.getPosition(mode = viz.ABS_GLOBAL)[1]
            newPos = vizmat.MoveAlongVector(transportNode.getPosition(mode = viz.ABS_GLOBAL), transportNode.getMatrix().getForward(), -1)
            newPos = [newPos[0], yPos, newPos[2]]
            transportNode.setPosition(newPos, mode = viz.ABS_GLOBAL)

            self.avatarON()
        
    def thirdPersonON(self):
        """
        Enable third person follow mode.

        Follows the participant from behind and above their head instead of from
        their eyes, so the avatar head stays in view. Turns follow mode on if it is
        off. The camera placement is set with setThirdPersonOffset. 3D model trials
        only: a 360 video can only be viewed from its center.
        """
        if not self.trialMode == MODEL_3D:
            self.replayButtonLabels[THIRD_PERSON_MODE].set(0)
            return

        self.replaySceneSettings[THIRD_PERSON_MODE] = viz.ON

        if not self.replayButtonLabels[THIRD_PERSON_MODE].get():
            self.replayButtonLabels[THIRD_PERSON_MODE].set(1)

        if self.headLink is None:
            self.followON()
        else:
            self.updateFollowView()

    def thirdPersonOFF(self):
        """
        Disable third person follow mode.

        Returns the follow camera to the participant's eyes if follow mode is on.
        """
        self.replaySceneSettings[THIRD_PERSON_MODE] = viz.OFF

        if self.replayButtonLabels[THIRD_PERSON_MODE].get():
            self.replayButtonLabels[THIRD_PERSON_MODE].set(0)

        self.updateFollowView()

    def setThirdPersonOffset(self, offset = None, pitch = None):
        """
        Set where the third person follow camera sits relative to the participant.

        Takes effect right away if third person follow is on.

        Args:
            offset (list, optional): [x, y, z] in meters from the participant's head,
                in the direction they face: +y is up and -z is behind them. None keeps
                the current offset (THIRD_PERSON_OFFSET until changed).
            pitch (float, optional): Degrees the camera tilts down toward the
                participant. None keeps the current pitch (THIRD_PERSON_PITCH until changed).
        """
        if offset is not None:
            self.thirdPersonOffset = list(offset)
        if pitch is not None:
            self.thirdPersonPitch = pitch

        if self.replaySceneSettings[THIRD_PERSON_MODE]:
            self.updateFollowView()

    def updateFollowView(self):
        """
        Place the follow mode camera in first or third person.

        First person puts the camera at the participant's eyes and hides the avatar
        head. Third person moves it by the third person offset and tilts it down by the
        third person pitch, and shows the avatar head if the Head checkbox is on. The
        offset turns with the head's heading only, so the participant nodding or
        tilting their head does not swing the camera around or tip the horizon.
        """
        if self.headLink is None:
            return

        self.headLink.reset(viz.RESET_OPERATORS)
        self.thirdPersonOrbit = None

        if self.replaySceneSettings[THIRD_PERSON_MODE]:
            self.headLink.setEuler([None, 0, 0])
            # Before the offset, so it turns the camera around the head rather than in place
            self.thirdPersonOrbit = self.headLink.preEuler(self.thirdPersonLook + [0])
            self.headLink.preTrans(self.thirdPersonOffset)
            self.headLink.preEuler([0, self.thirdPersonPitch, 0])

            if self.replayButtonLabels[AVATAR_VISIBLE].get():
                self.avatarON()
        else:
            self.avatarOFF()

    def updateThirdPersonLook(self):
        """
        Orbit the third person camera around the participant's head with the mouse.

        While the right mouse button is held, dragging left/right circles the camera
        around the head and dragging up/down swings it below/above, always pointing
        at the head. Dragging across the full width of the window goes once around.
        When the button is released the camera eases back behind the participant.
        """
        if self.thirdPersonOrbit is None or self.headLink is None:
            self.thirdPersonLook = [0.0, 0.0]
            self.lastMousePos = None
            return

        if viz.mouse.getState() & viz.MOUSEBUTTON_RIGHT:
            pos = viz.mouse.getPosition(viz.WINDOW_NORMALIZED)
            if self.lastMousePos is not None:
                yaw = self.thirdPersonLook[0] + (pos[0] - self.lastMousePos[0]) * 360.0
                self.thirdPersonLook[0] = (yaw + 180.0) % 360.0 - 180.0   # eases back the short way round
                self.thirdPersonLook[1] -=(pos[1] - self.lastMousePos[1]) * 180.0
                self.thirdPersonLook[1] = max(-89.0, min(89.0, self.thirdPersonLook[1]))
            self.lastMousePos = pos
        else:
            self.lastMousePos = None
            if self.thirdPersonLook == [0.0, 0.0]:
                return
            # Ease back, most of the way within about a third of a second
            keep = math.exp(-viz.getFrameElapsed() / 0.1)
            self.thirdPersonLook = [angle * keep if abs(angle * keep) > 0.05 else 0.0 for angle in self.thirdPersonLook]

        self.thirdPersonOrbit.setEuler(self.thirdPersonLook + [0])

    def heatmapStaticON(self):
        """
        Enable static heatmap mode.
        
        Displays the entire accumulated heatmap from start to current playhead position
        as a static visualization, rather than animating it progressively.
        """
        self.replaySceneSettings[HEAT_MAP_STATIC] = viz.ON
        
        for client in self.replayVisualisations:
            self.replayVisualisations[client].drawHeatmap(self.lastPlayHead, sliderPOS = self.replayButtonLabels[HEAT_MAP_SLIDER].get(), radius = self.replayButtonLabels[HEAT_MAP_RADIUS].get(), time = self.replayButtonLabels[HEAT_MAP_TIME].get(), static = (self.replayButtonLabels[HEAT_MAP_STATIC].get() == viz.DOWN))
        
    def heatmapStaticOFF(self):
        """
        Disable static heatmap mode.
        
        Returns to dynamic heatmap mode where fixation intensity accumulates
        progressively as replay advances.
        """
        self.replaySceneSettings[HEAT_MAP_STATIC] = viz.OFF
        
        for client in self.replayVisualisations:
            self.replayVisualisations[client].drawHeatmap(self.lastPlayHead, sliderPOS = self.replayButtonLabels[HEAT_MAP_SLIDER].get(), radius = self.replayButtonLabels[HEAT_MAP_RADIUS].get(), time = self.replayButtonLabels[HEAT_MAP_TIME].get(), static = (self.replayButtonLabels[HEAT_MAP_STATIC].get() == viz.DOWN))
    
#    def heatmapOcclusionON(self):
#        self.replaySceneSettings[HEAT_MAP_OCCLUSION] = viz.ON
#        
#    def heatmapOcclusionOFF(self):
#        self.replaySceneSettings[HEAT_MAP_OCCLUSION] = viz.OFF
        
        for client in self.replayVisualisations:
            self.replayVisualisations[client].drawHeatmap(self.lastPlayHead, sliderPOS = self.replayButtonLabels[HEAT_MAP_SLIDER].get(), radius = self.replayButtonLabels[HEAT_MAP_RADIUS].get(), time = self.replayButtonLabels[HEAT_MAP_TIME].get(), static = (self.replayButtonLabels[HEAT_MAP_STATIC].get() == viz.DOWN))
    
    def heatmapGradientON(self):
        """
        Enable time-recency alpha gradient for fixation spheres.
        
        Applies time-based transparency to fixation spheres where older fixations
        fade toward transparency, emphasizing more recent gaze activity.
        """
        self.replaySceneSettings[HEAT_MAP_ALPHA_GRADIENT] = viz.ON
        
        # Enable time recency alpha for all clients
        for client in self.replayVisualisations:
            self.replayVisualisations[client].useTimeRecencyAlpha = True
            self.replayVisualisations[client].timeRecencyGradientValue = self.replayButtonLabels[HEAT_MAP_ALPHA_GRADIENT_SLIDER].get()
            self.replayVisualisations[client].drawFixationSpheres(self.lastPlayHead, static = (self.replayButtonLabels[FIXATION_SPHERES_STATIC].get() == viz.DOWN))
        
    def heatmapGradientOFF(self):
        """
        Disable time-recency alpha gradient for fixation spheres.
        
        Returns all fixation spheres to uniform opacity regardless of temporal distance
        from current playhead.
        """
        self.replaySceneSettings[HEAT_MAP_ALPHA_GRADIENT] = viz.OFF
        
        # Disable time recency alpha for all clients
        for client in self.replayVisualisations:
            self.replayVisualisations[client].useTimeRecencyAlpha = False
            self.replayVisualisations[client].drawFixationSpheres(self.lastPlayHead, static = (self.replayButtonLabels[FIXATION_SPHERES_STATIC].get() == viz.DOWN))
        
    def heatmapSlider(self, sliderPOS):
        """
        Adjust heatmap intensity/opacity slider.
        
        Args:
            sliderPOS (float): Slider position value (0.0-1.0) controlling overall heatmap alpha/visibility.
        """
        self.replayButtonLabels[HEAT_MAP_SLIDER].message('%.2f'%(sliderPOS))
        self.replaySceneSettings[HEAT_MAP_SLIDER] = sliderPOS
        
        for client in self.replayVisualisations:
            self.replayVisualisations[client].setHeatmapAlpha(sliderPOS)
            
    def heatmapGradientSlider(self, sliderPOS):
        """
        Adjust time-recency gradient time window slider.
        
        Controls the time window over which fixation sphere opacity fades from full
        to transparent. Maps slider range (0.0-1.0) to 1-10 seconds.
        
        Args:
            sliderPOS (float): Slider position value (0.0-1.0).
        """
        min_val, max_val = 1, 10  # your custom range
        mapped_val = min_val + sliderPOS * (max_val - min_val)
        self.replayButtonLabels[HEAT_MAP_ALPHA_GRADIENT_SLIDER].message('%.2f secs' % mapped_val)
        self.replaySceneSettings[HEAT_MAP_ALPHA_GRADIENT_SLIDER] = mapped_val
        
        # Update the gradient value for all clients
        for client in self.replayVisualisations:
            self.replayVisualisations[client].timeRecencyGradientValue = sliderPOS
            self.replayVisualisations[client].drawFixationSpheres(self.lastPlayHead, static = (self.replayButtonLabels[FIXATION_SPHERES_STATIC].get() == viz.DOWN))
#        self.replayButtonLabels[HEAT_MAP_ALPHA_GRADIENT_SLIDER].message('%.2f secs'%(sliderPOS))
            
    def fixationScaleSlider(self, sliderPOS):
        """
        Adjust fixation sphere scale/size slider.
        
        Controls the base scale factor for fixation sphere visualization.
        Maps slider range (0.0-1.0) to 0.1-1.0 scale multiplier.
        
        Args:
            sliderPOS (float): Slider position value (0.0-1.0).
        """
        min_val, max_val = 0.1, 1  # your custom range
        mapped_val = min_val + sliderPOS * (max_val - min_val)
        self.replayButtonLabels[FIXATION_SPHERES_SCALE].message('%.2f' % mapped_val)
        self.replaySceneSettings[FIXATION_SPHERES_SCALE] = mapped_val
        # Update the gradient value for all clients
        for client in self.replayVisualisations:
            self.replayVisualisations[client].fixationSpheresScaleFactor = sliderPOS
            self.replayVisualisations[client].drawFixationSpheres(self.lastPlayHead, static = (self.replayButtonLabels[FIXATION_SPHERES_STATIC].get() == viz.DOWN))
        
    def heatmapRadiusSlider(self, sliderPOS):
        """
        Adjust heatmap gaussian radius slider.
        
        Controls the radius of the gaussian blur kernel applied to heatmap fixations,
        affecting the spread/diffusion of attention intensity.
        
        Args:
            sliderPOS (float): Slider position value in radians (0.0-1.0).
        """
        self.replayButtonLabels[HEAT_MAP_RADIUS].message('%.2f rads'%(sliderPOS))
        self.replaySceneSettings[HEAT_MAP_RADIUS] = sliderPOS
        
        for client in self.replayVisualisations:
            self.replayVisualisations[client].drawHeatmap(self.lastPlayHead, sliderPOS = self.replayButtonLabels[HEAT_MAP_SLIDER].get(), radius = self.replayButtonLabels[HEAT_MAP_RADIUS].get(), time = self.replayButtonLabels[HEAT_MAP_TIME].get(), static = (self.replayButtonLabels[HEAT_MAP_STATIC].get() == viz.DOWN), redraw = True)
        
    def heatmapTimeSlider(self, sliderPOS):
        """
        Adjust heatmap accumulation rate slider.
        
        Controls the time interval for heatmap intensity accumulation,
        affecting how quickly fixations build up visual intensity.
        
        Args:
            sliderPOS (float): Slider position value in seconds (0.0-1.0).
        """
        self.replayButtonLabels[HEAT_MAP_TIME].message('%.2f secs'%(sliderPOS))
        
        for client in self.replayVisualisations:
            self.replayVisualisations[client].drawHeatmap(self.lastPlayHead, sliderPOS = self.replayButtonLabels[HEAT_MAP_SLIDER].get(), radius = self.replayButtonLabels[HEAT_MAP_RADIUS].get(), time = self.replayButtonLabels[HEAT_MAP_TIME].get(), static = (self.replayButtonLabels[HEAT_MAP_STATIC].get() == viz.DOWN), redraw = True)
        
    def setSettings(self):
        """
        Apply current replay settings to all GUI controls.
        
        Synchronizes the visual state of GUI controls (checkboxes, sliders, dropdowns)
        with the current values stored in replaySceneSettings dictionary.
        """
        #self.replaySceneSettings = self.defaultSceneSettings
        for item in self.replaySceneSettings:
            if not item in [GAZE_PATH_TYPE, HEAT_MAP_ALPHA_GRADIENT_SLIDER, HEAT_MAP_OCCLUSION]:
                if type(self.replayButtonLabels[item]).__name__ == "VizDropList":
                    self.replayButtonLabels[item].select(self.replaySceneSettings[item])
                else:
                    self.replayButtonLabels[item].set(self.replaySceneSettings[item])
            elif item == HEAT_MAP_ALPHA_GRADIENT_SLIDER:
                self.replayButtonLabels[item].set(self.replaySceneSettings[item]/10)
                self.replayButtonLabels[item].message(str(self.replaySceneSettings[item]) + " secs")
        
    def setDefaultSettings(self):
        """
        Reset all replay settings to default values.
        
        Restores the replay scene settings dictionary to its initial state from
        defaultSceneSettings backup, then updates all GUI controls and redraws
        visualizations with default parameters.
        """
        self.replaySceneSettings = self.defaultSceneSettings
        for item in self.replaySceneSettings:
            if not item in [GAZE_PATH_TYPE, HEAT_MAP_ALPHA_GRADIENT_SLIDER, HEAT_MAP_OCCLUSION]:
                if type(self.replayButtonLabels[item]).__name__ == "VizDropList":
                    self.replayButtonLabels[item].select(self.replaySceneSettings[item])
                else:
                    self.replayButtonLabels[item].set(self.replaySceneSettings[item])
                    
        self.heatmapSlider(self.replaySceneSettings[HEAT_MAP_SLIDER])
        self.heatmapRadiusSlider(self.replaySceneSettings[HEAT_MAP_RADIUS])
        self.heatmapTimeSlider(self.replaySceneSettings[HEAT_MAP_TIME])
        
class ReplayHUD:
    """
    Heads-Up Display (HUD) manager for replay overlay information.
    
    Manages all overlay text displays during replay including the playback timer,
    status messages, fixation console showing currently fixated objects and recently
    ended fixations. Text elements are positioned in screen space and scale with
    window size for multi-user recordings.
    """
    
    def __init__(self, clientCount = 1):
        """
        Initialize the replay HUD overlay display system.
        
        Args:
            clientCount (int): Number of clients in multi-user recording. Defaults to 1.
                Determines how many fixation console rows to create.
        """
        if clientCount == 0:
            clientCount = 1
            
        global overlayWindow
        
        self.startTime = viz.tick()
        self.startTimestamp = 0.0
        
        self.statusText = viz.addText('', parent=viz.ORTHO, scene=overlayWindow, color=viz.WHITE, fontSize=20, pos=[20,20,0])
        self.statusText.setBackdrop(viz.BACKDROP_LEFT_BOTTOM)
        self.statusText.setBackdropColor(viz.BLACK)
        
        self.timerText = viz.addText('Press Spacebar to Start', parent=viz.ORTHO, scene=overlayWindow, color=viz.YELLOW, fontSize=20, pos=[20,viz.window.getSize()[1]*0.075,0], align=viz.ALIGN_LEFT_BOTTOM)
        self.timerText.setBackdrop(viz.BACKDROP_BOX)
        self.timerText.setBackdropColor(viz.BLACK)
        self.timerText.setBackdropAlpha(0.4)
        self.timerText.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)
        
#        self.pupilDiameterText = viz.addText('', parent=viz.ORTHO, scene=overlayWindow, color=viz.YELLOW, fontSize=20, pos=[20,20,0])
#        self.pupilDiameterText.setBackdrop(viz.BACKDROP_BOX)
#        self.pupilDiameterText.setBackdropColor(viz.BLACK)
#        self.pupilDiameterText.setBackdropAlpha(0.4)
#        self.pupilDiameterText.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)
        
        #self.pupilDiameterText.visible(viz.OFF)

        self.consoleText = viz.addText('', parent=viz.ORTHO, scene=overlayWindow, color=viz.WHITE, fontSize=20, pos=[20,20,0])
        self.consoleText.setBackdrop(viz.BACKDROP_LEFT_BOTTOM)
        self.consoleText.setBackdropColor(viz.BLACK)
        self.consoleText.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)
        
        _lh = max(35, int(viz.window.getSize()[1] * 0.05))
        _h = viz.window.getSize()[1]
        self.consoleFixated = viz.addText('dwell onset: ', parent=viz.ORTHO, scene = overlayWindow, color=viz.YELLOW, fontSize=20, pos=[5, _h - _lh, 0], align=viz.ALIGN_LEFT_BOTTOM)
        self.consoleFixated.setBackdrop(viz.BACKDROP_BOX)
        self.consoleFixated.setBackdropColor(viz.BLACK)
        self.consoleFixated.setBackdropAlpha(0.4)
        self.consoleFixated.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)

        self.fixatedText = {}
        for i in range(0, clientCount):
            clientText = viz.addText('', parent=viz.ORTHO, scene = overlayWindow, color=viz.WHITE, fontSize=20, pos=[5, _h - _lh * (i + 2), 0], align=viz.ALIGN_LEFT_BOTTOM)
            clientText.setBackdrop(viz.BACKDROP_LEFT_BOTTOM)
            clientText.setBackdropColor(viz.BLACK)
            clientText.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)

            self.fixatedText[i] = clientText

        self.consoleEnded = viz.addText('ended: ', parent=viz.ORTHO, scene = overlayWindow, color=viz.YELLOW, fontSize=20, pos=[5, _h - _lh * (clientCount + 2), 0], align=viz.ALIGN_LEFT_BOTTOM)
        self.consoleEnded.setBackdrop(viz.BACKDROP_BOX)
        self.consoleEnded.setBackdropColor(viz.BLACK)
        self.consoleEnded.setBackdropAlpha(0.4)
        self.consoleEnded.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)

        self.endedText = {}
        for i in range(0, clientCount):
            clientText = viz.addText('', parent=viz.ORTHO, scene = overlayWindow, color=viz.WHITE, fontSize=20, pos=[5, _h - _lh * (clientCount + i + 3), 0], align=viz.ALIGN_LEFT_BOTTOM)
            clientText.setBackdrop(viz.BACKDROP_LEFT_BOTTOM)
            clientText.setBackdropColor(viz.BLACK)
            clientText.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)

            self.endedText[i] = clientText

        self.currentTime = None

    def getCurrentTimeElapsed(self):
        """
        Get elapsed time since replay start.
        
        Returns:
            float: Time in seconds since startTime was set.
        """
        return viz.tick() - self.startTime

    def writeToConsole(self, fixatedList, endedList, clientNumber):
        """
        Update fixation console with current gaze activity.
        
        Args:
            fixatedList (str): Comma-separated list of currently fixated object names.
            endedList (str): Comma-separated list of recently ended fixation object names.
            clientNumber (int): Client number (1-indexed) to update console for.
        """
        self.fixatedText[int(clientNumber)-1].message(fixatedList)
        self.endedText[int(clientNumber)-1].message(endedList)

    def writeToStatus(self, message):
        """
        Update status text display.
        
        Args:
            message (str): Status message to display in bottom-left corner.
        """
        self.statusText.message(message)
        
    def writeTimerText(self, message):
        """
        Update timer text display.
        
        Args:
            message (str): Timer/timestamp message to display.
        """
        self.timerText.message(message)
    
    def resetStartTime(self, start):
        """
        Reset replay start time reference.
        
        Args:
            start (str or float): Timestamp value to set as the new start reference point.
        """
        self.startTime = viz.tick()
        self.startTimestamp = float(start)
        
class ReplayVisualisations:
    """
    Core visualization engine for eye tracking replay rendering.
    
    Manages all gaze visualization rendering including scan paths, heatmaps, fixation spheres,
    dwell spheres, walk paths, gaze rays, and ROI tags. Processes raw tracking data to calculate
    fixations and saccades using dispersion-threshold identification (I-DT) algorithm, then
    renders these analyses as dynamic or static visualizations.
    
    Key visualization modes:
    - Scan paths: Sequential gaze point connections (gaze, saccade, or dispersion-based)
    - Heatmaps: Attention intensity maps with gaussian blur and time-recency gradients
    - Fixation spheres: Color-coded spheres scaled by fixation duration
    - Dwell spheres: Cumulative dwell time visualization on gaze objects
    - Walk paths: Physical movement trajectories with directional arrows
    - Gaze rays: 3D lines from eyes to gaze points (3D mode only)
    
    Supports multi-user replay with per-client color coding and independent visualization settings.
    """
    
    def __init__(self, currentTrialData, sceneObjects, noiseFilter, color = None, clientID = None, fastHeatmap = False):
        """
        Initialize the replay visualization engine for a single client's data.
        
        Args:
            currentTrialData (dict): Dictionary mapping timestamps to tracking data frames.
                Each frame contains position/orientation data for tracked objects.
            sceneObjects (dict): Dictionary of scene objects organized by type:
                - GAZE_OBJECTS: List of interactive objects that can be gazed upon
                - REGIONS_OF_INTEREST: ROI boundary objects for tagging
            noiseFilter (bool): Whether to apply noise reduction filtering to gaze data.
            color (dict, optional): Dictionary mapping client IDs to viz.Color objects for
                color-coding visualizations in multi-user recordings. Defaults to None (red).
            clientID (str, optional): Client identifier for multi-user recordings. Defaults to None.
            fastHeatmap (bool): Whether to use optimized fast heatmap rendering. Defaults to False.
        """
        self.sceneObjects = sceneObjects
        self.fastHeatmap = fastHeatmap
        
        if clientID is None:
            self.currentTrialData = currentTrialData[OBJECT_TRACKER]
        else:
#            self.currentTrialData = {}
#            for timestamp, data in currentTrialData[OBJECT_TRACKER].items():
#                if data.get(clientID, None) is not None:
#                    self.currentTrialData[timestamp] = data.get(clientID, None)
            self.currentTrialData = {timestamp:  data.get(clientID, None) for timestamp, data in currentTrialData[OBJECT_TRACKER].items()}
            
        #print(self.currentTrialData)

        self.timeStampList = list(self.currentTrialData.keys())
        self.gazePoints = {}
        self.avatarHeadPoints = {}
                    
#        self.walkArrow = viz.addChild(os.path.join(os.path.dirname(__file__), 'resources/objects/direction_arrow.osgb'))
#        self.walkArrow.visible(viz.OFF)
        
        self.walkPathArrows = None
        
        self.walkPathArrowsAlt = None
#        self.walkPathArrows.dynamic()

        self.walkPathPos = {}
        frameCount = 0
        self.walkPathFrequency = 3
        avgHeight = 1.8
        heightBuffer = 0.30
        
        latestWalkData = []
        prevPos = None
        self.pupilDiameterDict = {}
        
#        print(clientID)
#        print("9")
        self.firstFixation = None
        self.firstFixationSkipFrames = 5
        
        for i in self.currentTrialData:
            if self.currentTrialData[i] is not None:
                self.gazePoints[i] = self.currentTrialData[i][GAZE_POINT_OBJECT][POSITION]
                self.avatarHeadPoints[i] = self.currentTrialData[i][AVATAR_HEAD_OBJECT][POSITION]
                
                if PUPIL_DIAMETER in self.currentTrialData[i]:
                    if isinstance(self.currentTrialData[i][PUPIL_DIAMETER], dict):
                        self.pupilDiameterDict[i] = self.currentTrialData[i][PUPIL_DIAMETER]["pupilDiameter"]
                    else: 
                        self.pupilDiameterDict[i] = self.currentTrialData[i][PUPIL_DIAMETER]
                
                if frameCount % self.walkPathFrequency == 0:
#                    pos = self.avatarHeadPoints[i]
#                    pos[1] = 0.1
#                    latestWalkData.append(pos)
                        
                    endPos = vizmat.MoveAlongVector(self.avatarHeadPoints[i], [0, -1, 0], 1000)
                    intersectInfo = viz.intersect(self.avatarHeadPoints[i], endPos)
                    
                    pos = self.avatarHeadPoints[i].copy()
                    pos[1] -= avgHeight
                    
                    if intersectInfo.valid:
                        pos = intersectInfo.point
                        prevPos = pos
                       
                    distanceCheck = vizmat.Distance(pos, self.avatarHeadPoints[i])
                    
                    if distanceCheck < (avgHeight - heightBuffer*avgHeight) or distanceCheck > (avgHeight + heightBuffer*avgHeight):
                        pos = self.avatarHeadPoints[i].copy()
                        pos[1] -= avgHeight
                        
                    if pos[1] < 0:
                        pos[1] = 0
                        
                    pos[1] += 0.05
                    
                    latestWalkData.append(pos)
                  
                self.walkPathPos[i] = latestWalkData.copy()
                frameCount += 1
        
#        print("walk path data: ", self.walkPathPos)
        self.scanPath = {}
        self.scanPathDistanceThreshold = 1.0
        self.scanPathMinSaccadeAngle = 20
        self.scanPathMaxSaccadeAngle = 100
        
#        print("8")
        if THRESHOLDS in currentTrialData:
            self.scanPathDispersionThreshold = currentTrialData[THRESHOLDS][DISPERSION_THRESHOLD]
            self.scanPathDurationThreshold = currentTrialData[THRESHOLDS][DURATION_THRESHOLD]
            self.dwellThreshold = currentTrialData[THRESHOLDS][DWELL_THRESHOLD]
        else:
            self.scanPathDispersionThreshold = 1.0
            self.scanPathDurationThreshold = 0.1
            self.dwellThreshold = 0.5
        
        self.noiseReductionFilter = noiseFilter
        
        if noiseFilter:
            self.noiseReductionWindowSize = 50
        else:
            self.noiseReductionWindowSize = 0
        
        self.dispersionWindowSize = int(self.scanPathDurationThreshold/(float(self.timeStampList[-1])/len(self.timeStampList)))
        
        self.scanPathConfig = {
            POINT_COLOR: viz.RED if clientID is None else color[clientID],
            POINT_SIZE: 5,
            LINE_COLOR: viz.RED if clientID is None else color[clientID],
            LINE_WIDTH: 5
        }
        self.samplingRate = 1
        
        self.walkPathColor = viz.YELLOW if clientID is None else color[clientID]
        
        self.scanPathRefreshRate = 1
        self.heatmapRefreshRate = 1
        self.fixationSpheresRefreshRate = 1
        
        self.gazeRay = None
        self.gazeRayL = None
        self.gazeRayR = None
        
        self.gazeRayConfig = {
            GAZE_COLOR: viz.GREEN if clientID is None else color[clientID],
            L_GAZE_COLOR: viz.BLUE,
            R_GAZE_COLOR: viz.RED,
            GAZE_WIDTH: 1
        }
        
#        print("7")
        self.heatmapPlayhead = 0
        
        self.heatmapClusters = {}
        self.heatmapFlag = viz.ON
        
        self.fixationTags = {}
        self.roiTags = {}
        
        self.attentionMap = attention_map.AttentionMapEffect()
        self.attentionMapDict = {}
        self.attentionMap.setActiveUser('default')
        self.attentionMap.setEnabled(True)
        vizfx.postprocess.addEffect(self.attentionMap)
        self.attentionMap.setAlpha(0.5)
        
        self.dwellSpheres = {}
        #self.dwellSpheresParameters = {}
        #self.dwellSpheresGradient = None
        
        self.fixationSpheres = {}
        
        for gaze_item in self.sceneObjects[GAZE_OBJECTS]:
            newSphere = vizshape.addSphere(0.1)
            newSphere.alpha(0)
            newSphere.disable(viz.SHADOW_CASTING)
            newSphere.setPosition(self.sceneObjects[GAZE_OBJECTS][gaze_item].getPosition(viz.ABS_GLOBAL))
            #newSphere.setParent(self.sceneObjects[GAZE_OBJECTS][gaze_item])
            
            self.dwellSpheres[gaze_item] = newSphere
        
        #Adjusts sensitivity of fixation spheres, lower number is more sensitive
        self.dwellSpheresBase = 15
        #Adjusts size of sphere, larger would a larger size sphere(max value)
        self.dwellSpheresScaleFactor = 0.7
        
        self.dwellSpheresMaxValue = 200
        self.dwellSpheresAlpha = 0.3
        
        #Adjusts sensitivity of fixation spheres, lower number is more sensitive
        self.fixationSpheresBase = 10
        #Adjusts size of sphere, larger would a larger size sphere(max value)
        self.fixationSpheresScaleFactor = 0.23
        
        self.fixationSpheresMaxValue = 100
        self.fixationSpheresAlpha = 0.5
        
        self.fixationSphereIndex = 0
        self.fixationCount = 0
        
        self.gazePointsFiltered = {}
        
        self.saccadeFixationDict = {}
        self.fixationSphereDict = {}
        self.fixationSphereLookupDict = {}
        self.fixationSphereDataList = []
        
        #self.saccadeFixationCalculate()
        self.sessionRecorder = sightlab.SessionRecorder()
#        print("7.5")

#        from itertools import islice
#
#        self.currentTrialData = dict(islice(self.currentTrialData.items(), 300))
        
        self.analyzeViews, self.fixationSaccadeMetrics = self.sessionRecorder.saccadeFixationCalculate(self.currentTrialData, self.scanPathDispersionThreshold, self.scanPathDurationThreshold, self.dwellThreshold, self.noiseReductionWindowSize)
        
        self.fixationSaccadeMetrics = dict(sorted(self.fixationSaccadeMetrics.items(), key = lambda x:float(x[0])))
        
#        print("6")
        for timestamp in self.fixationSaccadeMetrics:
            eventData = self.fixationSaccadeMetrics[timestamp]
            if eventData['eventType'] == FIXATION:
                self.fixationSphereLookupDict[self.fixationSphereIndex] = [eventData['position'], eventData['startTime'], eventData['endTime']]
                
                #if not fastHeatmap:
                self.fixationSphereIndex += 1
        
        for sphere in self.fixationSphereLookupDict:
            pos = self.fixationSphereLookupDict[sphere][0]
            
            newSphere = vizshape.addSphere(0.1)
            newSphere.disable(viz.SHADOW_CASTING)
            newSphere.setPosition(pos)
            #newSphere.alpha(0)
            newSphere.visible(viz.OFF)
            #newSphere.setParent(self.sceneObjects[GAZE_OBJECTS][gaze_item])
            
            self.fixationSpheres[sphere] = newSphere
            
#        print("5")
        for cluster in self.fixationSphereLookupDict:
            if self.fastHeatmap:
                cluster = 0
                
            attentionMap = attention_map.AttentionMapEffect()
            attentionMap.setActiveUser('default')
            attentionMap.setEnabled(True)
            vizfx.postprocess.addEffect(attentionMap)
            attentionMap.setAlpha(0.5)
            
            self.heatmapClusters[cluster] = attentionMap
            
            if self.fastHeatmap:
                break
            
        
#        print("4")
     
    def drawScanPath(self, playHead, visible = True, scanPathType = DYNAMIC_GAZE_PATH, static = False):
        """
        Draw gaze scan path visualization.
        
        Renders the sequential path of gaze points as connected lines and points,
        with different modes for raw gaze, saccades only, or dispersion-based paths.
        
        Args:
            playHead (int): Current playback frame index in timeStampList.
            visible (bool): Whether to render the scan path. Defaults to True.
            scanPathType (str): Type of scan path to render:
                - DYNAMIC_GAZE_PATH: All sequential gaze points
                - DYNAMIC_SACCADE_PATH: Saccadic movements only
                - DYNAMIC_DISPERSION_PATH: Dispersion-threshold based paths
            static (bool): If True, renders entire path to current frame. If False,
                renders progressively. Defaults to False.
        """
        self.clearScanPath()
        
        if visible:
            if static:
                playHead = len(self.timeStampList) #- 1
                
            if len(self.gazePoints.keys()) > 0 and self.timeStampList.index(list(self.gazePoints.keys())[0]) > playHead:
               return
            
            if scanPathType == DYNAMIC_GAZE_PATH:
                viz.startLayer(viz.POINTS)
                viz.pointSize(self.scanPathConfig[POINT_SIZE])
                viz.vertexColor(self.scanPathConfig[POINT_COLOR])
                
                for i in range(self.timeStampList.index(list(self.gazePoints.keys())[0]), playHead, self.samplingRate):
                    if self.timeStampList[i] in self.gazePoints:
                        viz.vertex(self.gazePoints[self.timeStampList[i]])
                
                self.scanPath[POINTS_LAYER] = viz.endLayer()
                
                viz.startLayer(viz.LINES)
                viz.lineWidth(self.scanPathConfig[LINE_WIDTH])
                viz.vertexColor(self.scanPathConfig[LINE_COLOR])
                
                self.scanPath[LINE_LAYERS] = []
                for i in range(self.timeStampList.index(list(self.gazePoints.keys())[0]), playHead - self.samplingRate, self.samplingRate):
                    if self.timeStampList[i] in self.gazePoints:
                        begin = self.gazePoints[self.timeStampList[i]]
                    else:
                        continue
                    
                    if self.timeStampList[i + self.samplingRate] in self.gazePoints:
                        end = self.gazePoints[self.timeStampList[i + self.samplingRate]]
                    else:
                        continue
                    
                    if vizmat.Distance(begin, end) > self.scanPathDistanceThreshold:
                        lineLayer = viz.endLayer()
                        lineLayer.disable(viz.SHADOW_CASTING)
                        lineLayer.alpha(0.5)
                        self.scanPath[LINE_LAYERS].append(lineLayer)
                        
                        viz.startLayer(viz.LINES)
                        viz.lineWidth(self.scanPathConfig[LINE_WIDTH])
                        viz.vertexColor(self.scanPathConfig[LINE_COLOR])
                    else:
                        viz.vertex(begin)
                        viz.vertex(end)
                lineLayer = viz.endLayer()
#                lineLayer.dynamic()
                lineLayer.alpha(0.5)
                self.scanPath[LINE_LAYERS].append(lineLayer)
                        
            elif scanPathType == DYNAMIC_SACCADE_PATH:
                viz.startLayer(viz.POINTS)
                viz.pointSize(self.scanPathConfig[POINT_SIZE])
                viz.vertexColor(self.scanPathConfig[POINT_COLOR])
                
                for i in range(self.timeStampList.index(list(self.gazePoints.keys())[0]), playHead, self.samplingRate):
                    viz.vertex(self.gazePoints[self.timeStampList[i]])
                
                self.scanPath[POINTS_LAYER] = viz.endLayer()
                
                viz.startLayer(viz.LINES)
                viz.lineWidth(self.scanPathConfig[LINE_WIDTH])
                viz.vertexColor(self.scanPathConfig[LINE_COLOR])
                
                self.scanPath[LINE_LAYERS] = []
                for i in range(self.timeStampList.index(list(self.gazePoints.keys())[0]), playHead - self.samplingRate, self.samplingRate):
                    begin = self.gazePoints[self.timeStampList[i]]
                    end = self.gazePoints[self.timeStampList[i + self.samplingRate]]
                    
                    avatarHead = self.currentTrialData[self.timeStampList[i]][AVATAR_HEAD_OBJECT][POSITION]
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
                        
                        #print("Saccade")
                        
                        self.scanPath[LINE_LAYERS].append(lineLayer)
                    else:
                        pass
                        #print("Fixation")
                lineLayer = viz.endLayer()
                lineLayer.alpha(0.5)
                self.scanPath[LINE_LAYERS].append(lineLayer)
                        
            elif scanPathType == DYNAMIC_DISPERSION_PATH:
                currentFixation = [self.timeStampList[0]]
                
                self.scanPath[LINE_LAYERS] = []
                #dispersionDequeue = deque(maxlen = self.dispersionWindowSize)
                
                viz.startLayer(viz.LINES)
                viz.lineWidth(self.scanPathConfig[LINE_WIDTH])
                viz.vertexColor(self.scanPathConfig[LINE_COLOR])
                
                for i in range(self.timeStampList.index(list(self.gazePoints.keys())[0]), playHead - self.samplingRate, self.samplingRate):
                    currTimestamp = self.timeStampList[i]
                    #nextTimeStamp = self.timeStampList[i + self.samplingRate]
                    
                    begin = self.gazePoints[currTimestamp]
                    #end = self.gazePoints[nextTimeStamp]
        
                    #print(i)
                    
                    if self.currentTrialData[self.timeStampList[i]][FIXATION_TRACKER][FIXATION_STATUS] == FIXATION:
                        #print("Fixation" + str(i))
                        #fixationSphereConfig = self.fixationSphereDict[self.timeStampList[i]]
                        
                        if self.timeStampList[i-1] in self.currentTrialData and self.currentTrialData[self.timeStampList[i-1]][FIXATION_TRACKER][FIXATION_STATUS] == SACCADE:
                            viz.vertex(begin)

                    elif self.currentTrialData[self.timeStampList[i]][FIXATION_TRACKER][FIXATION_STATUS] == SACCADE:
                        pass
                        #print("Saccade" + str(i))
                        #viz.vertex(begin)
                        
                        
                    #nextTimeStamp = self.timeStampList[i + self.samplingRate]
                    #end = self.gazePoints[nextTimeStamp]
                    
                    
                    #viz.vertex(begin)
                    #viz.vertex(end)
                
                lineLayer = viz.endLayer()
                self.scanPath[LINE_LAYERS].append(lineLayer)
                
        
    def clearScanPath(self):
        """
        Clear all scan path visualizations.
        
        Removes both the point cloud layer and all line layers from the scan path
        rendering, resetting the gaze trajectory visualization to an empty state.
        """
        if POINTS_LAYER in self.scanPath:
            self.scanPath[POINTS_LAYER].remove()
        
        if LINE_LAYERS in self.scanPath:
            for item in self.scanPath[LINE_LAYERS]:
                item.remove()
            
    def drawGazeRay(self, playHead, visible = True):
        """
        Draw 3D gaze ray line from head to gaze point.
        
        Renders a colored line projecting from the avatar head position to the
        current gaze point in 3D space. Only applicable for MODEL_3D trial mode.
        
        Args:
            playHead (int): Current playback frame index in timeStampList.
            visible (bool): Whether to render the gaze ray. Defaults to True.
        """
        self.clearGazeRay()
        
        if visible:
            sceneData = self.currentTrialData[self.timeStampList[playHead]]
            
            if sceneData is None:
                return
                
            viz.startLayer(viz.LINES)
            viz.lineWidth(self.gazeRayConfig[GAZE_WIDTH])
            viz.vertexColor(self.gazeRayConfig[GAZE_COLOR])
            begin = sceneData[AVATAR_HEAD_OBJECT][POSITION]
            end = sceneData[GAZE_POINT_OBJECT][POSITION]
            viz.vertex(begin)
            viz.vertex(end)
            self.gazeRay = viz.endLayer()
            self.gazeRay.disable(viz.SHADOW_CASTING)
            self.gazeRay.disable(viz.SHADOWS)
            
            headPos = sceneData[AVATAR_HEAD_OBJECT][POSITION]
            headEuler = sceneData[AVATAR_HEAD_OBJECT][ORIENTATION]
            m = viz.Matrix()
            m.setEuler(headEuler)
            m.setPosition(headPos)

            if EYE_TRACKER in sceneData and sceneData[EYE_TRACKER][LEFT_EYE][POSITION] is not None and not sceneData[EYE_TRACKER][LEFT_EYE][POSITION] == sceneData[EYE_TRACKER][BOTH_EYES][POSITION]:
                viz.startLayer(viz.LINES)
                viz.lineWidth(self.gazeRayConfig[GAZE_WIDTH])
                viz.vertexColor(self.gazeRayConfig[L_GAZE_COLOR])
                beginL = m.preMultVec([-0.0325, 0, 0])
                endL = sceneData[EYE_TRACKER][LEFT_EYE][POSITION]
                viz.vertex(beginL)
                viz.vertex(endL)
                self.gazeRayL = viz.endLayer()
                self.gazeRayL.disable(viz.SHADOW_CASTING)
                self.gazeRayL.disable(viz.SHADOWS)
            
            if EYE_TRACKER in sceneData and sceneData[EYE_TRACKER][RIGHT_EYE][POSITION] is not None and not sceneData[EYE_TRACKER][RIGHT_EYE][POSITION] == sceneData[EYE_TRACKER][BOTH_EYES][POSITION]:
                viz.startLayer(viz.LINES)
                viz.lineWidth(self.gazeRayConfig[GAZE_WIDTH])
                viz.vertexColor(self.gazeRayConfig[R_GAZE_COLOR])
                beginR = m.preMultVec([0.0325, 0, 0])
                endR = sceneData[EYE_TRACKER][RIGHT_EYE][POSITION]
                viz.vertex(beginR)
                viz.vertex(endR)
                self.gazeRayR = viz.endLayer()
                self.gazeRayR.disable(viz.SHADOW_CASTING)
                self.gazeRayR.disable(viz.SHADOWS)
            
        
    def clearGazeRay(self):
        """
        Clear the gaze ray line visualization.
        
        Removes the 3D line rendering between avatar head and gaze point,
        if one currently exists.
        """
        if self.gazeRay is not None:
            self.gazeRay.remove()
            
        if self.gazeRayL is not None:
            self.gazeRayL.remove()
            
        if self.gazeRayR is not None:
            self.gazeRayR.remove()
            
    def drawFixationSpheres(self, playHead, static = False, firstFixation = True, allFixation = False):
        """
        Draw fixation sphere visualizations.
        
        Renders color-coded spheres at detected fixation locations, with size and color
        scaled by fixation duration. Supports static (all fixations) or progressive
        (animated) display modes, and optional time-recency alpha gradients.
        
        Args:
            playHead (int): Current playback frame index in timeStampList.
            static (bool): If True, displays all fixations up to current frame simultaneously.
                If False, reveals fixations progressively. Defaults to False.
            firstFixation (bool): Whether to show the first fixation label. Defaults to True.
            allFixation (bool): Whether to show all fixation labels. Defaults to False.
        """
        def colorCalculate(val):
                # clamp value between 0 and 1
                val = min(max(val, 0.0), 1.0)

                # if val is between 0 to 0.5, we interpolate between green and yellow
                if val < 0.5:
                    red = 1 * (2 * val)
                    green = 1
                    blue = 0
                # if val is between 0.5 to 1, we interpolate between yellow and red
                else:
                    red = 1
                    green = 1 * (2 * (1 - val))
                    blue = 0

                # return as list
                return [red, green, blue]
        
        def calculateTimeRecencyAlpha(sphereIndex, currTimestamp):
            """Calculate alpha based on time recency if gradient is enabled"""
            # Check if gradient mode is enabled
            use_gradient = getattr(self, 'useTimeRecencyAlpha', False)
            if not use_gradient:
                return self.fixationSpheresAlpha
            
            def skew(t, gamma=3.0, mode='ease-out'):
                t = max(0.0, min(1.0, float(t)))
                if mode == 'ease-in':
                    return t ** gamma
                if mode == 'ease-out':
                    return 1.0 - (1.0 - t) ** gamma
                return 0.5 * (2*t) ** gamma if t < 0.5 else 1.0 - 0.5 * (2*(1.0 - t)) ** gamma
            
            # Get gradient settings
            min_val, max_val = 1, 10
            gradientPOS = getattr(self, 'timeRecencyGradientValue', 0.5)
            mapped_val = min_val + gradientPOS * (max_val - min_val)
            
            window_sec = mapped_val
            min_alpha = 0.01
            # Use the fixation spheres alpha as the maximum alpha value
            max_alpha = self.fixationSpheresAlpha
            
            # Get start time for this sphere
            start = float(self.fixationSphereLookupDict[sphereIndex][1])
            
            # Calculate age
            age = currTimestamp - start
            
            if age >= window_sec:
                return min_alpha
            else:
                # 1 = newest, 0 = oldest within window
                t = 1.0 - (age / window_sec)
                t = skew(t, gamma=6.0, mode='ease-out')
                # blend between min_alpha and max_alpha (using fixationSpheresAlpha)
                return min_alpha + (max_alpha - min_alpha) * t
                
        def drawFirstFixation(pos, time, index):
            fixationText = str(index + 1) #+ ": " + str(time)
            
            self.fixationTags[index] = viz.addText(fixationText)

            #print("fixation tag")
            
            self.fixationTags[index].alignment(viz.ALIGN_CENTER_BOTTOM)
            self.fixationTags[index].setBackdrop(viz.BACKDROP_BOX)
            self.fixationTags[index].setBackdropAlpha(0.4)
            self.fixationTags[index].resolution(1)
            self.fixationTags[index].disable(viz.LIGHTING)
            
            if len(self.fixationTags) == 1:
                self.fixationTags[index].message(str(index + 1) + ": " + str(time) + "s")
                self.fixationTags[index].setBackdropColor(viz.YELLOW)
                self.fixationTags[index].visible(firstFixation)
            else:
                self.fixationTags[index].setBackdropColor(viz.BLACK)
                self.fixationTags[index].visible(allFixation)
            
            self.fixationTags[index].setScale([0.07, 0.07, 0.07])
            self.fixationTags[index].setPosition(pos)
            
            # world-space unit vector that points straight *away* from the head
#            forward = viz.MainView.getMatrix().getForward()   # e.g. (0,0,-1) at reset
#
#            # flip it so it points toward the head
#            toward_head = [-f for f in forward]               # same length (1.0)
#
#            # move the label `offset_m` toward the head
#            closer_pos = [pos[i] + toward_head[i]*offset_m for i in range(3)]
#            self.fixationTags[index].setPosition(closer_pos)

                
        if static:
            playHead = len(self.timeStampList)-1
            
            if self.fixationSpherePlayhead == len(self.timeStampList)-1:
                return

        currTimestamp = float(self.timeStampList[playHead])
        
        for sphere in self.fixationSphereLookupDict:
            try:
                pos, start, end = self.fixationSphereLookupDict[sphere]
            except ValueError:
                pos, start = self.fixationSphereLookupDict[sphere]
                end = len(self.timeStampList)
                
            sphereObject = self.fixationSpheres[sphere]
                
            if float(start) < currTimestamp:
                if float(end) < currTimestamp:
                    frameCount = self.timeStampList.index(end) - self.timeStampList.index(start)
                else:
                    frameCount = playHead - self.timeStampList.index(start)
                
                if frameCount > 0:
                    scaleXYZ = self.fixationSpheresScaleFactor * math.log(frameCount, self.fixationSpheresBase)
                else:
                    scaleXYZ = 0.1
                    
                scale = [scaleXYZ, scaleXYZ, scaleXYZ] 
                
                # Calculate alpha using time recency if enabled, otherwise use default
                # alpha = self.fixationSpheresAlpha
                alpha = self.fixationSpheresAlpha if static else calculateTimeRecencyAlpha(sphere, currTimestamp)
                
                maxValue = self.fixationSpheresMaxValue
                minValue = 0
                value = frameCount
                normalized = (value - minValue) / (maxValue - minValue)
                
                if not sphere in self.fixationTags:
                    drawFirstFixation(pos, start, sphere)
                
                if allFixation:
                    self.fixationTags[sphere].visible(viz.ON)
                
                sphereObject.visible(viz.ON)
                
                sphereObject.setScale(scale)
                color = colorCalculate(normalized)
                
                sphereObject.color(color)
                sphereObject.alpha(alpha)
                sphereObject.emissive(color)
            else:
                sphereObject.visible(viz.OFF)
                
                if sphere in self.fixationTags:
                    self.fixationTags[sphere].visible(viz.OFF)

        self.fixationSpherePlayhead = playHead         

    def clearFixationSpheres(self):
        """
        Clear all fixation sphere visualizations.
        
        Hides all I-DT detected fixation spheres by setting their visibility to OFF.
        Spheres remain in memory for performance but are not rendered.
        """
        for sphere in self.fixationSpheres:
            self.fixationSpheres[sphere].visible(viz.OFF)
            #self.fixationSpheres[sphere].remove()
            
    def clearFixationTags(self):
        """
        Clear all fixation label text tags.
        
        Removes all fixation number labels from memory and empties the fixationTags
        dictionary. Used when resetting fixation visualization state.
        """
        for sphere in self.fixationTags:
            self.fixationTags[sphere].remove()
            
        self.fixationTags = {}
            
    def clearDwellSpheres(self):
        """
        Clear all dwell sphere visualizations.
        
        Hides all cumulative dwell time spheres on gaze objects by setting their
        visibility to OFF. Spheres remain in memory for performance.
        """
        for sphere in self.dwellSpheres:
            self.dwellSpheres[sphere].visible(viz.OFF)
        
    def drawDwellSpheres(self, playHead):
        """
        Draw dwell sphere visualizations on gaze objects.
        
        Renders color-coded spheres at each gaze object showing cumulative dwell time.
        Sphere size grows logarithmically with dwell count, and color transitions from
        green (low dwell) to yellow to red (high dwell).
        
        Args:
            playHead (int): Current playback frame index in timeStampList.
        """
        def colorCalculate(val):
            # clamp value between 0 and 1
            val = min(max(val, 0.0), 1.0)

            # if val is between 0 to 0.5, we interpolate between green and yellow
            if val < 0.5:
                red = 1 * (2 * val)
                green = 1
                blue = 0
            # if val is between 0.5 to 1, we interpolate between yellow and red
            else:
                red = 1
                green = 1 * (2 * (1 - val))
                blue = 0

            # return as list
            return [red, green, blue]
        
        if self.currentTrialData[self.timeStampList[playHead]] is None:
            return
                
        for fixationItem in self.dwellSpheres:
            tracker = GAZE_TRACKER
                
            if tracker not in self.currentTrialData[self.timeStampList[playHead]]:
                tracker = GAZE_OBJECTS
                
            if self.currentTrialData[self.timeStampList[playHead]] is None or not fixationItem in self.currentTrialData[self.timeStampList[playHead]][tracker]:
                return
                
            sphereCount = self.currentTrialData[self.timeStampList[playHead]][tracker][fixationItem][DWELL_SPHERE_COUNT]       
            
            #print(self.currentTrialData[self.timeStampList[playHead]][GAZE_TRACKER][fixationItem])
            scaleXYZ = self.dwellSpheresScaleFactor * math.log(sphereCount, self.dwellSpheresBase)
            scale = [scaleXYZ, scaleXYZ, scaleXYZ] 
            alpha = self.dwellSpheresAlpha
            
            sphere = self.dwellSpheres[fixationItem]
            
            if sphereCount == 1:
                sphere.visible(viz.OFF)
            else:
                sphere.visible(viz.ON)
            
            maxValue = self.dwellSpheresMaxValue #math.log(self.dwellSpheresMaxValue, self.fixationSphereBase)
            minValue = 0
            value = sphereCount #math.log(sphereCount, self.fixationSphereBase)
            normalized = (value - minValue) / (maxValue - minValue)
            
#            sphere.setScale(scale)
            color = colorCalculate(normalized)
            #print(normalized, color)
            sphere.color(colorCalculate(normalized))
            sphere.alpha(alpha)
            
            if self.currentTrialData[self.timeStampList[playHead]][tracker][fixationItem][GAZE_BOOL]:
                sphere.setPosition(self.currentTrialData[self.timeStampList[playHead]][GAZE_POINT_OBJECT][POSITION]) 
            
    def drawWalkPath(self, playHead, visible, static = viz.OFF):
        """
        Draw walk path visualization showing participant movement.
        
        Renders the participant's physical movement trajectory through the environment
        as a series of directional arrow triangles. Alpha gradient shows temporal progression
        from low opacity (early) to full opacity (current position).
        
        Args:
            playHead (int): Current playback frame index in timeStampList.
            visible (bool): Whether to render the walk path.
            static (viz.ON/viz.OFF): If viz.ON, renders entire path. If viz.OFF, renders
                progressively. Defaults to viz.OFF.
        """
        def arrow_head_triangle(A, B, width):
            """
            A and B are 3D points.
            The base of the arrow (centered at A) will be computed on the ground (x-y plane).
            B is the tip.
            """
            # Compute horizontal (ground plane) 2D direction from A to B.
            dx = B[0] - A[0]
            dz = B[2] - A[2]
            mag = math.sqrt(dx*dx + dz*dz)
            if mag == 0:
                return -1, -1
            
            # Normalize the horizontal vector.
            dx_norm = dx / mag
            dz_norm = dz / mag

            # Compute a perpendicular vector on the ground plane.
            # One common perpendicular is (-dz, dx).
            perp_x = -dz_norm
            perp_z = dx_norm

            # Offset A by the perpendicular vector (keeping the same z as A).
           # Compute the base vertices (force y to be A's y)
            base1 = [A[0] + perp_x*width, A[1], A[2] + perp_z*width]
            base2 = [A[0] - perp_x*width, A[1], A[2] - perp_z*width]
            
            # B is the tip.
            return base1, base2
            
        self.clearWalkPath()
        minAlpha = 0.1
        
        if static:
            playHead = -1
        
        if visible:
            viz.startLayer(viz.TRIANGLES)
            
            if isinstance(self.walkPathColor, list):
                color = self.walkPathColor + [1]
            else:
                color = self.walkPathColor + (1,)
                
            viz.vertexColor(color)
            
            viz.lineWidth(7)
            
            if not self.timeStampList[playHead] in self.walkPathPos:
                return
                
#            lastVertex = self.walkPathPos[self.timeStampList[0]]
            for index in range(0, len(self.walkPathPos[self.timeStampList[playHead]])-1, 2):
                alpha = minAlpha + (index/len(self.walkPathPos[self.timeStampList[playHead]]))*(1-minAlpha)
                
                if isinstance(self.walkPathColor, list):
                    color = self.walkPathColor + [alpha]
                else:
                    color = self.walkPathColor + (alpha, )
                    
                viz.vertexColor(color)
                            
                b1, b2 = arrow_head_triangle(self.walkPathPos[self.timeStampList[playHead]][index], self.walkPathPos[self.timeStampList[playHead]][index+1], 0.05)
                
                if b1 == -1 and b2 == -1:
                    continue
                    
                viz.vertex(self.walkPathPos[self.timeStampList[playHead]][index+1])

                viz.vertex(b1)
                viz.vertex(b2)
                
                #newPoint.alpha(playHead/len(self.timeStampList))
                    
            self.walkPathArrows = viz.endLayer()
            self.walkPathArrows.disable(viz.INTERSECTION)
        
    def drawWalkPathAlt(self, playHead):
        self.clearWalkPathAlt()
        
        for newVertex in self.walkPathPos[self.timeStampList[playHead]]:
            pass
            
        self.walkPathArrows
        #newPoint.alpha(playHead/len(self.timeStampList))   
        
    def clearWalkPath(self):
        """
        Clear the walk path arrow visualization.
        
        Removes all arrow triangles showing the participant's physical movement
        trajectory through the environment.
        """
        if self.walkPathArrows is not None:
            self.walkPathArrows.remove()
            
    def clearWalkPathAlt(self):
        if self.walkPathArrows is not None:
            for arrow in self.walkPathArrows:
                arrow.remove()
                
            self.walkPathArrows = None
            
    def drawHeatmapOld(self, playHead, sliderPOS, radius, time, static = False, redraw = False):
        if static:
            playHead = -1
            
            if self.heatmapPlayhead == -1 and redraw == False:
                return

        prevTimestamp = self.timeStampList[self.heatmapPlayhead]
        currTimestamp = self.timeStampList[playHead]
        
        currCluster = None
        
        timestampDiff = self.timeStampList.index(currTimestamp) - self.timeStampList.index(prevTimestamp)
                
        if timestampDiff < 0 or timestampDiff > 1 or redraw:
            self.clearHeatmap()
            self.attentionMap.addPoint(self.gazePoints[i], radius=radius, time=time)
                
        else:
            if not currTimestamp == self.timeStampList[0] and currTimestamp in self.gazePoints and currCluster in self.heatmapClusters:
                self.heatmapClusters[currCluster].addPoint(self.gazePoints[currTimestamp], radius=radius, time=time)
                
        self.heatmapPlayhead = playHead
        self.fixationSpherePlayhead = playHead
        
    def drawHeatmap(self, playHead, sliderPOS, radius, time, static = False, redraw = False):
        """
        Draw attention heatmap visualization.
        
        Renders a gaussian-blurred heatmap overlay showing fixation intensity across
        the environment. Uses accumulation-based rendering where fixation intensity
        builds up progressively over time.
        
        Args:
            playHead (int): Current playback frame index in timeStampList.
            sliderPOS (float): Heatmap intensity/alpha value (0.0-1.0).
            radius (float): Gaussian blur kernel radius in radians.
            time (float): Accumulation time interval in seconds.
            static (bool): If True, renders entire heatmap to current frame. If False,
                renders progressively. Defaults to False.
            redraw (bool): If True, forces complete heatmap redraw from scratch.
                Defaults to False.
        """
        if self.heatmapFlag:
            if static:
                playHead = -1
                
                if self.heatmapPlayhead == -1 and redraw == False:
                    return

            prevTimestamp = self.timeStampList[self.heatmapPlayhead]
            currTimestamp = self.timeStampList[playHead]
            
            currCluster = None
            
            timestampDiff = self.timeStampList.index(currTimestamp) - self.timeStampList.index(prevTimestamp)
                    
            if timestampDiff < 0 or timestampDiff > 1 or redraw:
#                print("redraw")
                self.clearHeatmap()
                breakFlag = False

                currCluster = 0
                if len(self.fixationSphereLookupDict) == 0:
                    return
                    
                start = self.fixationSphereLookupDict[currCluster][1]
                for i in self.gazePoints:
                    if float(i) > float(self.timeStampList[playHead]):
                        break

                    if float(i) <= float(start):
                        if self.fastHeatmap:
                            self.heatmapClusters[0].addPoint(self.gazePoints[i], radius=radius, time=time)
                        else:
                            self.heatmapClusters[currCluster].addPoint(self.gazePoints[i], radius=radius, time=time)
                    else:
                        if currCluster+1  < len(self.fixationSphereLookupDict):
                            currCluster += 1
                                
                            start = self.fixationSphereLookupDict[currCluster][1]
            else:
#                print("real time")
                if self.fastHeatmap:
                    currCluster = 0
                else:
                    for index in self.fixationSphereLookupDict:
                        try:
                            pos, start, end = self.fixationSphereLookupDict[index]
                        except ValueError:
                            pos, start = self.fixationSphereLookupDict[index]
                            end = len(self.timeStampList)
                        
                        if float(start) < float(currTimestamp):
                            currCluster = index
                            break
                        else:        
                            if index == 1:
                                currCluster = index
                                break
                            
    #            print(currCluster, currCluster in self.heatmapClusters, currTimestamp, currTimestamp in self.gazePoints)
                if not currTimestamp == self.timeStampList[0] and currTimestamp in self.gazePoints and currCluster in self.heatmapClusters:
                    self.heatmapClusters[currCluster].addPoint(self.gazePoints[currTimestamp] , radius=radius, time=time)
                    
            self.heatmapPlayhead = playHead
            self.fixationSpherePlayhead = playHead
            
    def heatmapAlphaGradientOld(self, sliderPOS, gradientPOS, playHead):
        def skew(t, gamma=2.0, mode='ease-out'):
            t = max(0.0, min(1.0, float(t)))
            if mode == 'ease-in':
                return t ** gamma
            if mode == 'ease-out':
                return 1.0 - (1.0 - t) ** gamma
            # ease-in-out
            return 0.5 * (2*t) ** gamma if t < 0.5 else 1.0 - 0.5 * (2*(1.0 - t)) ** gamma
            
        playHead = playHead if playHead < len(self.timeStampList) else len(self.timeStampList) - 1
        currTimestamp = float(self.timeStampList[playHead])
        currIndex = 1
        for index in self.fixationSphereLookupDict:
            start = float(self.fixationSphereLookupDict[index][1])
            end = float(self.fixationSphereLookupDict[index][2])
            
            currIndex = index + 1
            if start > currTimestamp:
                break
                
#            targetAlpha = (sliderPOS * (index + 1)/currIndex) if index <= currIndex else sliderPOS
            t = index / max(currIndex, 1)
            targetAlpha = sliderPOS * skew(t, gamma=6.0, mode='ease-out')
            self.heatmapClusters[index].setAlpha(targetAlpha)
            
    def heatmapAlphaGradient(self, sliderPOS, gradientPOS, playHead):
        """
        OLD METHOD - Works with heatmap clusters instead of fixation spheres.
        Currently not in use - see heatmapAlphaGradientNew for active implementation.
        """
        def skew(t, gamma=3.0, mode='ease-out'):
            t = max(0.0, min(1.0, float(t)))
            if mode == 'ease-in':
                return t ** gamma
            if mode == 'ease-out':
                return 1.0 - (1.0 - t) ** gamma
            return 0.5 * (2*t) ** gamma if t < 0.5 else 1.0 - 0.5 * (2*(1.0 - t)) ** gamma

        # configurable time window (seconds) and floor alpha
        min_val, max_val = 1, 10  # your custom range
        mapped_val = min_val + gradientPOS * (max_val - min_val)
        
        window_sec = getattr(self, 'heatmapFadeWindowSec', mapped_val)
        min_alpha  = getattr(self, 'heatmapMinAlpha', 0.01)

        playHead = playHead if playHead < len(self.timeStampList) else len(self.timeStampList) - 1
        currTimestamp = float(self.timeStampList[playHead])

        for index in self.fixationSphereLookupDict:
            start = float(self.fixationSphereLookupDict[index][1])
            
#            if index not in self.heatmapClusters:
#                continue
            
            heatmapIndex = index if not self.fastHeatmap else 0
            
            # not started yet ? invisible
            
            if start > currTimestamp:
                self.heatmapClusters[heatmapIndex].setAlpha(0.0)
                continue

            age = currTimestamp - start  # seconds since this sphere started

            if age >= window_sec:
                a = min_alpha  # fully tapered
            else:
                # 1 = newest, 0 = oldest within window
                t = 1.0 - (age / window_sec)
                t = skew(t, gamma=6.0, mode='ease-out')  # crank gamma for stronger recency bias
                # blend between min_alpha and sliderPOS
                a = min_alpha + (sliderPOS - min_alpha) * t

            self.heatmapClusters[heatmapIndex].setAlpha(a)
    
    def heatmapAlphaGradientNew(self, sliderPOS, gradientPOS, playHead):
        """
        Apply time-recency alpha gradient to fixation spheres.
        
        Sets configuration variables that drawFixationSpheres() uses to calculate
        temporal alpha fade-out. Recent fixations appear at full opacity while older
        fixations fade toward transparency, creating a recency-weighted visualization.
        
        Args:
            sliderPOS (float): Base alpha value for newest fixations (0.0-1.0).
            gradientPOS (float): Gradient intensity controlling fade-out rate (0.0-1.0).
                Higher values create steeper temporal gradients.
            playHead (int): Current playback frame index (triggers immediate redraw).
        """
        # Enable time recency alpha mode
        self.useTimeRecencyAlpha = True
        self.timeRecencyBaseAlpha = sliderPOS
        self.timeRecencyGradientValue = gradientPOS
        
        # Force an immediate redraw to see the effect
        if hasattr(self, 'fixationSpheres') and len(self.fixationSpheres) > 0:
            self.drawFixationSpheres(playHead, static=False, firstFixation=True, allFixation=False)
    
    def setTimeRecencyAlpha(self, sliderPOS, gradientPOS, playHead):
        """
        Enable time-recency alpha gradient for fixation spheres.
        
        Activates temporal transparency mode where fixation sphere alpha values decay
        based on age. Sets configuration variables used by drawFixationSpheres() to
        calculate time-weighted alpha on each render cycle.
        
        Args:
            sliderPOS (float): Base alpha for newest fixations (0.0-1.0).
            gradientPOS (float): Gradient steepness controlling fade rate (0.0-1.0).
            playHead (int): Current playback frame index.
        """
        self.useTimeRecencyAlpha = True
        self.timeRecencyBaseAlpha = sliderPOS
        self.timeRecencyGradientValue = gradientPOS
        
        # Force a redraw with current playhead
        if hasattr(self, 'fixationSpheres') and len(self.fixationSpheres) > 0:
            # Trigger drawFixationSpheres to apply the new alpha values
            # This will be called automatically on the next update cycle
            pass
    
    def disableTimeRecencyAlpha(self):
        """
        Disable time-recency alpha gradient for fixation spheres.
        
        Turns off temporal transparency mode, reverting fixation spheres to uniform
        alpha values without time-based fade effects.
        """
        self.useTimeRecencyAlpha = False
            
        
    def heatmapOcclusionCheck(self):
        """
        Perform occlusion culling on heatmap clusters.
        
        Uses ray intersection tests from viewer position to each heatmap cluster fixation
        location. Hides heatmap clusters that are occluded by more than 2 scene objects
        (excluding visualization elements like gaze rays, spheres, and scan paths).
        Improves visual clarity by removing hidden heatmap contributions.
        """
        for index in self.heatmapClusters:
            intersections = viz.intersect(viz.MainView.getPosition(), self.fixationSphereLookupDict[index][0], all = True)
            exclusions = 0
            exclusionList = [[self.gazeRay, self.gazeRayL, self.gazeRayR, self.sceneObjects[GAZE_POINT_OBJECT]], list(self.dwellSpheres.values()), list(self.fixationSphereDict.values()), list(self.scanPath.values())]
            
            for i in intersections:
                for item in exclusionList:
                    if i.object in item:
                        exclusions += 1
                
#            targetAlpha = (sliderPOS * (index + 1)/currIndex) if index <= currIndex else sliderPOS
#            self.heatmapClusters[index].setAlpha(targetAlpha)
                
            if len(intersections) - exclusions > 2:
                self.heatmapClusters[index].setAlpha(0)
#            else:
#                targetAlpha = (sliderPOS * (index + 1)/currIndex) if index <= currIndex else sliderPOS
#                self.heatmapClusters[index].setAlpha(targetAlpha)
               
    def setupRoiTags(self):
        """
        Initialize region-of-interest text labels.
        
        Creates 3D text objects for each ROI in the scene with standardized formatting:
        centered alignment, semi-transparent black backdrop, and consistent scaling.
        Removes any existing tags before creating new ones.
        """
        for tag in self.roiTags:
            self.roiTags[tag].remove()
            
        for item in self.sceneObjects[REGIONS_OF_INTEREST]:
            self.roiTags[item] = viz.addText(item)
    
            self.roiTags[item].alignment(viz.ALIGN_CENTER_BOTTOM)
            self.roiTags[item].setBackdrop(viz.BACKDROP_BOX)
            self.roiTags[item].setBackdropAlpha(0.4)
            self.roiTags[item].resolution(1)
            self.roiTags[item].disable(viz.LIGHTING)
        
            self.roiTags[item].setBackdropColor(viz.BLACK)
            self.roiTags[item].visible(viz.ON)
        
            self.roiTags[item].setScale([0.07, 0.07, 0.07])
            self.roiTags[item].drawOrder(5)
            #self.roiTags[item].setPosition(self.sceneObjects[REGIONS_OF_INTEREST][item].getPosition())
        
    def orientRoiTags(self, visibleFlag):
        """
        Orient ROI text labels to face viewer (billboard effect).
        
        Positions each tag slightly offset from its ROI object toward the viewer,
        then rotates it to face the camera. The 180-degree euler adjustment corrects
        for coordinate system conventions, ensuring readable text orientation.
        
        Args:
            visibleFlag (viz.ON/viz.OFF): Controls tag visibility.
        """
        for item in self.roiTags:
            tagPos = self.sceneObjects[REGIONS_OF_INTEREST][item].getPosition()
            viewerPos = viz.MainView.getPosition()
            
            newPos = vizmat.MoveAlongLine(tagPos, viewerPos, 0.05)
            
            self.roiTags[item].visible(visibleFlag)
            
            self.roiTags[item].setPosition(newPos)
            
            self.roiTags[item].lookAt(viz.MainView.getPosition())
                    
            currEuler = self.roiTags[item].getEuler()
            self.roiTags[item].setEuler(currEuler[0], currEuler[1] + 180, currEuler[2] + 180)
                
    def orientFixationTags(self):
        """
        Orient fixation number labels to face viewer (billboard effect).
        
        Updates each fixation tag to remain viewer-facing by positioning it slightly
        offset from its fixation sphere toward the camera, then applying billboard
        rotation. The 180-degree euler correction ensures proper text readability.
        """
        for sphere in self.fixationTags:
            tagPos = self.fixationSpheres[sphere].getPosition()
            viewerPos = viz.MainView.getPosition()
            
            newPos = vizmat.MoveAlongLine(tagPos, viewerPos, 0.05)
            
            self.fixationTags[sphere].setPosition(newPos)
            
            self.fixationTags[sphere].lookAt(viz.MainView.getPosition())
                    
            currEuler = self.fixationTags[sphere].getEuler()
            self.fixationTags[sphere].setEuler(currEuler[0], currEuler[1] + 180, currEuler[2] + 180)            
        
    def clearHeatmap(self):
        """
        Clear all heatmap visualizations.
        
        Resets all heatmap clusters to empty state, removing the accumulated
        gaussian-blurred fixation intensity overlay from all rendered surfaces.
        """
        for cluster in self.heatmapClusters:
            self.heatmapClusters[cluster].clear()
            
    def setHeatmapAlpha(self, value):
        """
        Set global alpha transparency for all heatmap clusters.
        
        Updates the opacity of all heatmap overlays uniformly. Also toggles the
        heatmap rendering flag on/off based on alpha value.
        
        Args:
            value (float): Alpha transparency (0.0 = invisible, 1.0 = opaque).
        """
        for cluster in self.heatmapClusters:
            self.heatmapClusters[cluster].setAlpha(value)
            
        if value == 0:
            self.heatmapFlag = viz.OFF
        else:
            self.heatmapFlag = viz.ON
            
    def clearTags(self):
        """
        Clear all ROI tag label visualizations.
        
        Hides all region-of-interest text labels by setting their visibility to OFF.
        Tags remain in memory but are not rendered.
        """
        for tag in self.roiTags:
            self.roiTags[tag].visible(viz.OFF) 
                                
    def clearVisualizations(self):
        """
        Clear all replay visualizations at once.
        
        Master clearing method that removes or hides all active visualization elements:
        scan paths, gaze rays, walk paths, fixation spheres, fixation tags, dwell spheres,
        heatmaps, and ROI tags. Used for complete visualization reset.
        """
        self.clearScanPath()
        self.clearGazeRay()
        self.clearWalkPath()
        self.clearFixationSpheres()
        self.clearFixationTags()
        self.clearDwellSpheres()
        self.clearHeatmap()
        self.clearTags()
        
class ReplayEngine:
    """
    Replay data loading and playback engine.
    
    Manages replay session initialization including file discovery, participant selection,
    trial data loading, and scene configuration. Handles both current (.rply JSON format)
    and legacy (SightLab 1.9 text format) replay files. Coordinates scene object creation,
    visualization systems (ReplayVisualisations, ReplayHUD, ReplayGUI), and playback state.
    
    The engine maintains the replay timeline, synchronizes scene objects with recorded data,
    and provides the main update loop for progressive replay rendering.
    """
    def __init__(self, noiseFilter = None, trialNumber = None, sightlab_1_9 = False, dataDirectory = 'data', headlight = None, fastHeatmap = True):
        """
        Initialize replay engine and load session data.
        
        Discovers available replay files, prompts user for session selection, loads trial
        data, and initializes the replay environment. Supports both modern JSON (.rply) and
        legacy SightLab 1.9 text formats.
        
        Args:
            noiseFilter (bool, optional): Enable gaze data noise filtering. Defaults to True
                for VR headsets, False for desktop mode.
            trialNumber (int, optional): Specific trial to load. If None, loads all trials
                from selected session.
            sightlab_1_9 (bool): Load legacy SightLab 1.9 text format instead of JSON.
                Defaults to False.
            dataDirectory (str): Relative path to data folder from script directory.
                Defaults to 'data'.
            headlight (bool, optional): Enable/disable viewer headlight. If None, uses
                default scene lighting.
            fastHeatmap (bool): Enable optimized heatmap rendering mode with reduced
                time bias and update rate. Defaults to True.
        """
        self.transportNode = vizconnect.getTransport('main_transport').getNode3d()
        self.transportNode.setPosition([0,0,-1])
            
        oriTracker = vizconnect.getTracker(name='head_tracker').getNode3d()
        posTracker = viz.addGroup()
        rawTracker = viz.mergeLinkable(posTracker, oriTracker)
        vizconnect.addTracker(rawTracker,'merged', make='Virtual', model='Merged')
           
        self.fastHeatmap = fastHeatmap
        
        if self.fastHeatmap:
            # Apply fast heatmap settings
            if not hasattr(heatmap_config, 'ATTENTION_MAP_MAX_TIME') or heatmap_config.ATTENTION_MAP_MAX_TIME is None:
                heatmap_config.ATTENTION_MAP_MAX_TIME = 30.0
            
            heatmap_config.ATTENTION_MAP_MIN_TIME = 5.0
            heatmap_config.ATTENTION_MAP_GROUP_TIME_BIAS = 0.0
            heatmap_config.ATTENTION_MAP_GROUP_SIZE = 0.05
            heatmap_config.ATTENTION_MAP_UPDATE_RATE = 0.05
        
        if viz.res.isPublished():
            self.scriptDirectory = viz.res.getPublishedPath()
        else:
            stack = inspect.stack()
            caller_frame = stack[3]
            module_path = caller_frame.filename
            self.scriptDirectory = os.path.abspath(os.path.dirname(module_path))
        
        noDateList = []
        dateDict = {}
        sessionList = []
        filePathDict = {}
        
        self.trialNumber = trialNumber
        
        data_directory = os.path.join(self.scriptDirectory, dataDirectory)
        
        self.headlightFlag = headlight
        
        self.participantID = None
        self.replayFileList = {}
        
        if not sightlab_1_9:
#            for root, dirs, files in os.walk(data_directory):
#                for file in files:
#                    if file.endswith('.rply'):
#                        full_path = os.path.join(root, file)
#                        fileSplit = file.split('_')
            
            for file in glob.glob(os.path.join(self.scriptDirectory, '**', "*.rply"), recursive=True):
                fileSplit = os.path.basename(file).split('_')
                
                try:
                    a = datetime.strptime(fileSplit[0], '%m-%d-%Y-%H-%M-%S')
                    if str(a)not in dateDict:
                        filePathDict[str(a) + "_" + fileSplit[1]] = [file]
                    else:
                        filePathDict[str(a) + "_" + fileSplit[1]].append(file)
                        
                    dateDict[str(a)] = fileSplit[1]
                    
                except:
                    noDateList.append(os.path.basename(file)[:-5])
                    
                    if os.path.basename(file)[:-5] not in filePathDict:
                        filePathDict[os.path.basename(file)[:-5]] = [file]
                    else:
                        filePathDict[os.path.basename(file)[:-5]].append(file)
                
            dateList = list(dateDict.keys())
            dateList = sorted(dateList, reverse = True)
            
            for item in dateList:
                sessionList.append(item + "_" + dateDict[item])
                
            sessionList += noDateList
            
        else:
            sightlab_1_9_files = {}
            
            for root, dirs, files in os.walk(data_directory):
                for file in files:
                    if file.endswith('.txt'):
                        full_path = os.path.join(root, file)
                        fileSplit = file.split('_')
                        
                        pid = fileSplit[0]
                        
                        if not pid in sightlab_1_9_files:
                            sightlab_1_9_files[pid] = {}
                            
                        tNo = fileSplit[-1].split('.')[0]
                        
                        if tNo not in sightlab_1_9_files[pid]:
                            sightlab_1_9_files[pid][tNo] = {}
                        
                        if "replay" in file:
                            sightlab_1_9_files[pid][tNo][REPLAY_FILE] = full_path
                        else:
                            sightlab_1_9_files[pid][tNo][TRIAL_FILE] = full_path
                        
            sessionList = list(sightlab_1_9_files.keys())
            
        if len(sessionList) == 0:
            vizinput.message("No Replay (.rply) files found in Project Folder ")
            sys.exit()
            
        choice = vizinput.choose('Select Session', sessionList)
        
        if noiseFilter is None:
            if not VIZCONNECT_CONFIG == "Desktop": 
                noiseFilter = True
            else:
                noiseFilter = False
                
        self.noiseFilter = noiseFilter
        
        self.customFlags = {}
            
        if not sightlab_1_9:
            full_path = filePathDict[sessionList[choice]][0]
            
            # Split the full path into parts
            path_parts = full_path.split(os.sep)

            # Find the folder that contains 'experiment_data'
            index = None
            for part in path_parts:
                if 'experiment_data' in part:
                    index = path_parts.index(part) + 1
                    break

            # Reconstruct the path up to the desired folder, or use parent directory if not found
            if index is not None:
                desired_path = os.sep.join(path_parts[:index])
            else:
                # Fallback: use the directory containing the replay file
                desired_path = os.path.dirname(full_path)
            
            self.dataFolder = desired_path
            
            trialFileList = sorted(filePathDict[sessionList[choice]])
            
            self.participantID = sessionList[choice].split("_")[0]
                    
            for path in trialFileList:
                basename = os.path.basename(path)
                self.replayFileList[basename.split("_")[-1][:-5]] = path
            
            self.replayFileData = {}
            for trial in self.replayFileList:
                replayFile = open(self.replayFileList[trial], "r")
                
                try: 
                    trialData = json.load(replayFile)
                    self.replayFileData[trial] = trialData
                except:
                    print("empty file")
                    
                replayFile.close()
#            self.replayFileData = {}
#            for trial in self.replayFileList:
#                with open(self.replayFileList[trial], "rb") as replayFile:  # Change "r" to "rb"
#                    try: 
#                        trialData = orjson.loads(replayFile.read())  # Use orjson.loads with .read()
#                        self.replayFileData[trial] = trialData
#                    except Exception as e:
#                        print(f"Error loading trial {trial}: {e}")
        else:
            chosenPID = sightlab_1_9_files[sessionList[choice]]
            
            self.participantID = sessionList[choice]
            self.replayFileList = chosenPID
            
            self.replayFileData = {}
            self.trialFileData = {}
            
            for trial in chosenPID:
                replayDataFile = chosenPID[trial][REPLAY_FILE]
                trialDataFile = chosenPID[trial][TRIAL_FILE]
                
                with open(trialDataFile, 'r') as trialFile:
                    trialData = trialFile.readlines()
                    
                filteredTrialData = {}
                for line in trialData:
                    s = re.split('\t|\n',line)
                    s = list(filter(None, s))
                    
                    if len(s) > 0 and "gaze" in s[-1]:
                        filteredTrialData[s[0]] = s[-1]
                
                trialData = filteredTrialData
                
                with open(replayDataFile, 'r') as replayFile:
                    replayData = replayFile.readlines()
                    
                config = replayData[0].strip()
                
                if "360" in os.path.basename(replayDataFile):
                    trialMode = MEDIA_360
                else:
                    trialMode = MODEL_3D
                    
                try:
                    datetime.strptime(pid, "%m-%d-%Y-%H-%M-%S")
                    isGUI = False
                except ValueError:
                    isGUI = True
                
                s = replayData[1].split()
                objectCount = int(s[2])
                gazeCount = int(s[3])
 
                s = re.split('\t|\n',replayData[2])
                s = list(filter(None, s))
                
                environmentFile = os.path.join("resources/environments", os.path.basename(s[0]))
                gazePoint = os.path.join(os.path.dirname(__file__), 'resources/gaze_point', os.path.basename(s[1]))
                avatarHead = os.path.join(os.path.dirname(__file__), 'resources/avatar/head', os.path.basename(s[2]))
                avatarRHand = os.path.join(os.path.dirname(__file__), 'resources/avatar/hands', os.path.basename(s[3]))
                
                if not "desktop" in config:
                    avatarLHand = os.path.join(os.path.dirname(__file__), 'resources/avatar/hands', os.path.basename(s[4]))
                else:
                    avatarLHand = avatarRHand
                    
                resourcesList = s
                    
                gazeObjects = []
                s = re.split('\t|\n',replayData[3])
                gazeObjects = list(filter(None, s))
                
                invisibleObjects = []
                s = re.split('\t|\n',replayData[4])
                invisibleObjects = list(filter(None, s))
                
                builtInObjectCount = 4 if "desktop" in config else 5
                
                customObjectCount = objectCount - builtInObjectCount
                
                customObjects = {}
                if customObjectCount > 0 and len(gazeObjects) > 0:
                    for i in range(0, customObjectCount):
                        customObjects[gazeObjects[gazeCount + i]] = os.path.join(self.scriptDirectory, "resources", os.path.basename(resourcesList[builtInObjectCount + i]))
                
                grabObjects = []
                
                for item in gazeObjects:
                    if item not in customObjects:
                        grabObjects.append(item)
                
                self.replayFileData[trial] = {
                    CONFIGURATION: config.replace("desktop", "Desktop") if "desktop" in config else config,

                    MODE: trialMode,
                    ISGUI: isGUI,
                    
                    ENVIRONMENT_FILE: environmentFile,
                    AVATAR_HEAD_FILE: avatarHead,
                    AVATAR_RIGHT_HAND_FILE: avatarRHand,
                    AVATAR_LEFT_HAND_FILE: avatarLHand,
                    GAZE_POINT_FILE: gazePoint,
                    
                    GAZE_OBJECTS: gazeObjects,
                    GRAB_OBJECTS: grabObjects,
                    INVISIBLE_OBJECTS: invisibleObjects,
                    
                    CUSTOM_OBJECTS: customObjects,
                    AVATAR_OBJECTS: {},
                    
                    OBJECT_TRACKER: {}
                }
                
                for data in replayData[5:]:
                    s = re.split('\t|\n', data)
                    s = list(filter(None, s))
                    
                    timestamp = str(round(float(s[0]), 3))
                    objectTracker = self.replayFileData[trial][OBJECT_TRACKER]
                    objectTracker[timestamp] = {
                        ENVIRONMENT_OBJECT: {},
                        AVATAR_HEAD_OBJECT: {},
                        AVATAR_RIGHT_HAND_OBJECT: {},
                        GAZE_POINT_OBJECT: {},
                    }
                    
                    if not "desktop" in config:
                        objectTracker[timestamp][AVATAR_LEFT_HAND_OBJECT] = {}
                        
                    objectTracker[timestamp][ENVIRONMENT_OBJECT][POSITION] = json.loads(s[1])
                    objectTracker[timestamp][ENVIRONMENT_OBJECT][ORIENTATION] = json.loads(s[2])
                    
                    objectTracker[timestamp][GAZE_POINT_OBJECT][POSITION] = json.loads(s[3])
                    objectTracker[timestamp][GAZE_POINT_OBJECT][ORIENTATION] = json.loads(s[4])
                    
                    objectTracker[timestamp][AVATAR_HEAD_OBJECT][POSITION] = json.loads(s[5])
                    objectTracker[timestamp][AVATAR_HEAD_OBJECT][ORIENTATION] = json.loads(s[6])
                    
                    objectTracker[timestamp][AVATAR_RIGHT_HAND_OBJECT][POSITION] = json.loads(s[7])
                    objectTracker[timestamp][AVATAR_RIGHT_HAND_OBJECT][ORIENTATION] = json.loads(s[8])
                    
                    lastIndex = 9
                    
                    if not "desktop" in config:
                        objectTracker[timestamp][AVATAR_LEFT_HAND_OBJECT][POSITION] = json.loads(s[9])
                        objectTracker[timestamp][AVATAR_LEFT_HAND_OBJECT][ORIENTATION] = json.loads(s[10])
                        
                        lastIndex = 11
                        
                    objectTracker[timestamp][GAZE_TRACKER] = {}
                    objectTracker[timestamp][CUSTOM_OBJECTS] = {}
                    objectTracker[timestamp][AVATAR_OBJECTS] = {}
                    
                    objectTracker[timestamp][GRAB_OBJECTS] = {}
                    
                    count = 0
                    for custom_object in customObjects:
                        objectTracker[timestamp][CUSTOM_OBJECTS][custom_object] = {POSITION: json.loads(s[lastIndex + count]), ORIENTATION: json.loads(s[lastIndex + count + 1])}
                        count += 2
                        
                    lastIndex += 2*customObjectCount
                    
                    if gazeCount > 0:
                        for gaze_item in range(0, (len(gazeObjects)-customObjectCount)*2, 2):
                            objectTracker[timestamp][GAZE_TRACKER][gazeObjects[int(gaze_item/2)]] = {POSITION: json.loads(s[lastIndex + gaze_item]), ORIENTATION: json.loads(s[lastIndex + gaze_item + 1])}
                        
                            objectTracker[timestamp][GAZE_TRACKER][gazeObjects[int(gaze_item/2)]] = {
                                GAZE_STATE: None,
                                GAZE_BOOL: False,
                                DWELL_SPHERE_COUNT: 1,
                                DWELL_TIME: 0.5
                            }
                    else:
                        for item in gazeObjects:
                            objectTracker[timestamp][GAZE_TRACKER][item] = {
                                GAZE_STATE: None,
                                GAZE_BOOL: False,
                                DWELL_SPHERE_COUNT: 1,
                                DWELL_TIME: 0.5
                            }
                        
                    if len(trialData.keys()) > 0 and abs(float(timestamp) - float(list(trialData.keys())[0])) < 0.25:
                        gazeFlag = trialData[list(trialData.keys())[0]]
                        
                        flagSplit = gazeFlag.split(" ")
                        gazeItem = flagSplit[-1]
                        
                        if "fixated" in flagSplit[1]:
                            gazeState = GAZE_FIXATED
                        elif "ended" in flagSplit[1]:
                            gazeState = GAZE_ENDED
                        elif "started" in flagSplit[1]:
                            gazeState = GAZE_STARTED
                            
                        objectTracker[timestamp][GAZE_TRACKER][gazeItem][GAZE_STATE] = gazeState

        keylist = list(self.replayFileData.keys())
        self.currTrial = list(sorted(keylist, key = int))[0]
        
        global PARTICIPANT_ID, REPLAY_FILE_LIST
        
        PARTICIPANT_ID = self.participantID
        REPLAY_FILE_LIST = self.replayFileList
        
        if trialNumber is not None:
            if str(trialNumber) in keylist:
                self.currTrial = str(trialNumber)
            else:
                vizinput.message("Trial Number " + str(trialNumber) + " was not found")
                viz.quit()
        
        self.currentTrialData = self.replayFileData[self.currTrial]
        
        self.clientCount = 0
        
        self.replayGUI = None
        self.replayHUD = None
        self.replayVisualisations = None
        self.mediaLink = None
                
        self.trialMode = self.currentTrialData[MODE]
        self.prevTrialMode = None
        
        if not self.trialMode == MODEL_3D:
            self.trialMode = MEDIA_360
        
        self.clientColors = {}
        
        #self.currentTrialData = self.replayFileData[self.replayGUI.replayButtonLabels[TRIAL_NUMBER].getItem(0)]

        self.playHead = 0
        self.currTime = None
        self.tempTimeBuffer = 0.0
        
        self.sceneUpdate = vizact.onupdate(0, self.updateScene)
        self.timerUpdate = vizact.ontimer(0.1, self.updateTimer)
        
        #self.timerUpdate.setEnabled(viz.ON)
        self.sceneUpdate.setEnabled(viz.OFF)
        self.playState = viz.OFF
        
        self.firstStart = True
        
        self.headLight = viz.MainView.getHeadLight()
        
        self.windowSize = viz.MainWindow.getSize(mode = viz.WINDOW_PIXELS)
        
        #self.timeStampList.sort()
                
        self.playbackSliderPanel = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_BOTTOM, align=vizdlg.ALIGN_LEFT_BOTTOM, background=False,border=False)
        
        self.playbackSlider = self.playbackSliderPanel.addItem(viz.addProgressBar("0.0"), align = viz.ALIGN_LEFT_BOTTOM)
        #self.playbackSlider = viz.addProgressBar("0.0")
        self.playbackSlider.setScale(1.5, 1.5, 1.5)
        self.playbackSlider.setLength(5)
        #self.playbackSlider.alpha(0.9)
        self.playbackSlider.resolution(1)
        self.playbackSliderPanel.setPosition(3, viz.window.getSize()[1]*0.01)
        self.playbackSliderPanel.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)
        
        self.scrubLength = 2.0
        
    def openDataFolder(self):
        if viz.res.isPublished():
            current_directory = viz.res.getPublishedPath('data')
        else:
            current_directory = self.dataFolder
        subprocess.run(['open', current_directory] if os.name == 'posix' else ['explorer', current_directory])

    def windowSizeCheck(self):
        global SCALE_FACTOR, WINDOW_SIZE, proportionFactor

        if viz.window.getSize()[1] < 480:
            viz.window.setSize(viz.window.getSize()[0], 480)

        if not viz.MainWindow.getSize(mode = viz.WINDOW_PIXELS) == self.windowSize:
            WINDOW_SIZE = viz.MainWindow.getSize(mode = viz.WINDOW_PIXELS)

            SCALE_FACTOR = viz.window.getSize()[1]/975
            
            self.replayGUI.replayInfoPanel.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)
            self.replayGUI.instructionsInfoPanel.setScale(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR)
            self.playbackSliderPanel.setScale(viz.window.getSize()[0]/1700, viz.window.getSize()[0]/1700, WINDOW_SIZE[0]/1700)
            #self.playbackSlider.setLength((WINDOW_SIZE[0]/self.windowSize[0])*self.playbackSlider.getLength())
            
            clientCount = max(1, len(self.replayHUD.fixatedText))
            _lh = max(35, int(viz.window.getSize()[1] * 0.05))
            _h = viz.window.getSize()[1]
            self.replayHUD.consoleFixated.setPosition([5, _h - _lh, 0])
            self.replayHUD.consoleEnded.setPosition([5, _h - _lh * (clientCount + 2), 0])

            for i in range(0, clientCount):
                self.replayHUD.fixatedText[i].setPosition([5, _h - _lh * (i + 2), 0])

            for i in range(0, clientCount):
                self.replayHUD.endedText[i].setPosition([5, _h - _lh * (clientCount + i + 3), 0])
            
            self.windowSize = WINDOW_SIZE
            
    def updateTimer(self):
        for client in self.replayVisualisations:
            if self.replayGUI.replaySceneSettings[HEAT_MAP_ALPHA_GRADIENT]:
#                self.replayVisualisations[client].heatmapAlphaGradient(self.replayGUI.replayButtonLabels[HEAT_MAP_SLIDER].get(), self.replayGUI.replayButtonLabels[HEAT_MAP_ALPHA_GRADIENT_SLIDER].get(), self.playHead)
                pass  # Gradient is now handled automatically in drawFixationSpheres via calculateTimeRecencyAlpha
#                self.replayVisualisations[client].heatmapAlphaGradientNew(self.replayGUI.replayButtonLabels[HEAT_MAP_SLIDER].get(), self.replayGUI.replayButtonLabels[HEAT_MAP_ALPHA_GRADIENT_SLIDER].get(), self.playHead)
            
            if self.replayGUI.replaySceneSettings[HEAT_MAP_OCCLUSION]:
                self.replayVisualisations[client].heatmapOcclusionCheck()
                
            self.replayVisualisations[client].orientFixationTags()
            
        if len(self.replayVisualisations) > 0:
            firstClient = next(iter(self.replayVisualisations))
            self.replayVisualisations[firstClient].orientRoiTags(self.replayGUI.replaySceneSettings[ROI_TAG_VISIBLE])
        
        self.windowSizeCheck()
        
        if self.playbackSlider.getFocus():
            self.playbackSlider.alpha(1)
        else:
            self.playbackSlider.alpha(0.8)
            
    def updateAvatars(self, sceneData, client = '1'):
        trackedObjects = [AVATAR_HEAD_OBJECT, AVATAR_RIGHT_HAND_OBJECT, AVATAR_LEFT_HAND_OBJECT, GAZE_POINT_OBJECT]
        keyDict = {
        AVATAR_HEAD_OBJECT: AVATAR_VISIBLE,
        AVATAR_LEFT_HAND_OBJECT: CONTROLLERS_VISIBLE,
        AVATAR_RIGHT_HAND_OBJECT: CONTROLLERS_VISIBLE,
        GAZE_POINT_OBJECT: GAZE_POINT_VISIBLE
        }
        for item in trackedObjects:
            sceneObject = self.sceneObjects[item][client]
                
            if sceneData is None or (item == AVATAR_LEFT_HAND_OBJECT and "Desktop" in self.currentTrialData[CONFIGURATION]):
                sceneObject.visible(viz.OFF)
                continue
            else:
                sceneObject.visible(self.replayGUI.replaySceneSettings[keyDict[item]])
                if VISIBLE in sceneData[item]:
                    sceneObject.visible(sceneData[item][VISIBLE])
#                if COLOR in sceneData[item]:
#                    if not sceneData[item][COLOR] == [1.0, 1.0, 1.0]:
##                        print(item, sceneData[item][COLOR])
#                        sceneObject.color(sceneData[item][COLOR])
        
            sceneObject.setPosition(sceneData[item][POSITION], mode = viz.ABS_GLOBAL)
            sceneObject.setEuler(sceneData[item][ORIENTATION], mode = viz.ABS_GLOBAL)
            
            #sceneObject.setScale(sceneData[item][SCALE])
            
        if EYE_TRACKER in sceneData:
            if LEFT_EYE in sceneData[EYE_TRACKER]:
                if sceneData[EYE_TRACKER][LEFT_EYE][POSITION] is not None and not sceneData[EYE_TRACKER][LEFT_EYE][POSITION] == sceneData[EYE_TRACKER][BOTH_EYES][POSITION]:
                    if GAZE_POINT_OBJECT_L in self.sceneObjects:
                        self.sceneObjects[GAZE_POINT_OBJECT_L][client].setPosition(sceneData[EYE_TRACKER][LEFT_EYE][POSITION], mode = viz.ABS_GLOBAL)
                        self.sceneObjects[GAZE_POINT_OBJECT_L][client].color(viz.BLUE)
                else:
                    self.sceneObjects[GAZE_POINT_OBJECT_L][client].visible(viz.OFF)
            
            if RIGHT_EYE in sceneData[EYE_TRACKER]:
                if sceneData[EYE_TRACKER][RIGHT_EYE][POSITION] is not None and not sceneData[EYE_TRACKER][RIGHT_EYE][POSITION] == sceneData[EYE_TRACKER][BOTH_EYES][POSITION]:
                    if GAZE_POINT_OBJECT_R in self.sceneObjects:
                        self.sceneObjects[GAZE_POINT_OBJECT_R][client].setPosition(sceneData[EYE_TRACKER][RIGHT_EYE][POSITION], mode = viz.ABS_GLOBAL)
                        self.sceneObjects[GAZE_POINT_OBJECT_R][client].color(viz.RED)
                else:
                    self.sceneObjects[GAZE_POINT_OBJECT_R][client].visible(viz.OFF)
    
    def updateVisualisations(self, replayVisualisationsObject):
        replayVisualisationsObject.drawScanPath(self.playHead, visible = self.replayGUI.replaySceneSettings[SCAN_PATH_VISIBLE], scanPathType = self.replayGUI.replaySceneSettings[GAZE_PATH_TYPE], static = self.replayGUI.replaySceneSettings[STATIC_GAZE_PATH])
        replayVisualisationsObject.drawGazeRay(self.playHead, visible = self.replayGUI.replaySceneSettings[GAZE_RAY_VISIBLE])
        
        if self.replayGUI.replayButtonLabels[HEAT_MAP_SLIDER].get() > 0:
            replayVisualisationsObject.drawHeatmap(self.playHead, sliderPOS = self.replayGUI.replayButtonLabels[HEAT_MAP_SLIDER].get(), radius = self.replayGUI.replayButtonLabels[HEAT_MAP_RADIUS].get(), time = self.replayGUI.replayButtonLabels[HEAT_MAP_TIME].get(), static = (self.replayGUI.replayButtonLabels[HEAT_MAP_STATIC].get() == viz.DOWN))
        
        if self.replayGUI.replaySceneSettings[DWELL_SPHERES_VISIBLE]:
            replayVisualisationsObject.drawDwellSpheres(self.playHead)
        
        #if float(self.timeStampList[-1]) < 180 or self.firstStart:
        if self.replayGUI.replaySceneSettings[FIXATION_SPHERES_VISIBLE]:
            replayVisualisationsObject.drawFixationSpheres(self.playHead, static = (self.replayGUI.replayButtonLabels[FIXATION_SPHERES_STATIC].get() == viz.DOWN), firstFixation = self.replayGUI.replaySceneSettings[FIRST_FIXATION_VISIBLE], allFixation = self.replayGUI.replaySceneSettings[ALL_FIXATION_VISIBLE])
            
        replayVisualisationsObject.drawWalkPath(self.playHead, visible = self.replayGUI.replaySceneSettings[WALK_PATH_VISIBLE])
        
    def updateScene(self):
        if not self.playHead < len(self.timeStampList) and self.playState == viz.ON:
            self.togglePlayback()
            self.sceneUpdate.setEnabled(viz.OFF)
            return
        
        if self.playHead >= len(self.timeStampList):
            self.playHead = len(self.timeStampList) - 1
        if self.playHead < 0:
            self.playHead = 0
            
        self.currTime = self.timeStampList[self.playHead]
        
        if self.firstStart:
            self.replayHUD.writeTimerText("Press Spacebar to Start")
        else:
            self.replayHUD.writeTimerText("")
            
            if self.replayVisualisations is not None:
                pupilDiameterText = "PD:"
                for client in self.replayVisualisations:
                    if not self.replayVisualisations[client].pupilDiameterDict == {} and self.currTime in self.replayVisualisations[client].pupilDiameterDict:
                        if self.replayVisualisations[client].pupilDiameterDict[self.currTime] is not None:
                            pupilDiameterText += " client_" + client + ": " + str(round(self.replayVisualisations[client].pupilDiameterDict[self.currTime], 3))
            if pupilDiameterText == "PD:":
                pupilDiameterText = ""
                
            self.replayHUD.writeTimerText(pupilDiameterText)
        
        self.replayGUI.lastPlayHead = self.playHead
        
        try:
            self.playbackSlider.set(float(self.currTime)/float(self.timeStampList[-1]))
        except:
            pass
            
        currTimeStamp = float(self.currTime)
        finalTimeStamp = float(self.timeStampList[-1])
        
        currMilliseconds = int(((currTimeStamp - int(currTimeStamp)) * 1000)/10)
        currMinutes = int(currTimeStamp // 60)
        currSeconds = int(currTimeStamp % 60)
        
        finalMilliseconds = int(((finalTimeStamp - int(finalTimeStamp)) * 1000)/10)
        finalMinutes = int(finalTimeStamp // 60)
        finalSeconds = int(finalTimeStamp % 60)
        
        formattedCurrTime = f"{currMinutes:02d}:{currSeconds:02d}.{currMilliseconds:02d}"
        formattedFinalTime = f"{finalMinutes:02d}:{finalSeconds:02d}.{finalMilliseconds:02d}"
        
        self.playbackSlider.message(formattedCurrTime + " / " + formattedFinalTime)
        #self.playbackSlider.message(self.currTime + "/" + self.timeStampList[-1])
        
        if self.clientCount == 0:
            self.replayHUD.writeToConsole(self.fixatedState[self.currTime], self.endedState[self.currTime], 1)
        else:
            if self.currTime in self.fixatedState:
                for client in self.fixatedState[self.currTime]:
                    self.replayHUD.writeToConsole(self.fixatedState[self.currTime][client], self.endedState[self.currTime][client], int(client))

        if self.replayHUD.getCurrentTimeElapsed() > float(self.currTime) - self.replayHUD.startTimestamp or self.firstStart:
            sceneData = self.currentTrialData[OBJECT_TRACKER][self.currTime]
            if not self.clientCount == 0:
                sceneData = sceneData[next(iter(sceneData))]
                    
            if self.trialMode == MEDIA_360:                
                timeStamp = sceneData[MEDIA_OBJECT][0]
                if abs(self.mediaFile.getTime() - timeStamp) > self.mediaFile.getDuration() - 1:
                    self.mediaFile.setTime(timeStamp)
                
                state = sceneData[MEDIA_OBJECT][1]
                if state == viz.MEDIA_RUNNING and self.playState and self.mediaFile.getState() == viz.MEDIA_PAUSED:
                    self.mediaFile.play()

                elif state == viz.MEDIA_STOPPED:
                    # Treat stopped the same as paused: setTime() above already
                    # positioned the video.  Calling stop() on ExternalVideo sets
                    # _stop_evt which kills the decoder before it can deliver a
                    # frame, leaving the texture permanently black.
                    self.mediaFile.pause()

                elif state == viz.MEDIA_PAUSED:
                    self.mediaFile.pause()
            else:
                self.sceneObjects[ENVIRONMENT_OBJECT].setPosition(sceneData[ENVIRONMENT_OBJECT][POSITION], mode = viz.ABS_GLOBAL)
                self.sceneObjects[ENVIRONMENT_OBJECT].setEuler(sceneData[ENVIRONMENT_OBJECT][ORIENTATION], mode = viz.ABS_GLOBAL)
                
            if self.clientCount == 0:
                self.updateAvatars(sceneData)
            else:
                for client in self.currentTrialData[OBJECT_TRACKER][self.currTime]:
                    self.updateAvatars(self.currentTrialData[OBJECT_TRACKER][self.currTime][client], client)
            
#            for item in self.sceneObjects[GAZE_OBJECTS]:
#                if item in sceneData[GRAB_OBJECTS]:
#                    self.sceneObjects[GRAB_OBJECTS][item].setPosition(sceneData[GRAB_OBJECTS][item][POSITION], mode = viz.ABS_GLOBAL)
#                    self.sceneObjects[GRAB_OBJECTS][item].setEuler(sceneData[GRAB_OBJECTS][item][ORIENTATION], mode = viz.ABS_GLOBAL)
#                    #self.sceneObjects[GRAB_OBJECTS][item].setScale(sceneData[GRAB_OBJECTS][item][SCALE])
#                
#                    if VISIBLE in sceneData[GRAB_OBJECTS][item]:
#                        self.sceneObjects[GRAB_OBJECTS][item].visible(sceneData[GRAB_OBJECTS][item][VISIBLE])
#                
            for item in self.sceneObjects[GRAB_OBJECTS]:
                if item in sceneData[GRAB_OBJECTS]:
                    self.sceneObjects[GRAB_OBJECTS][item].setPosition(sceneData[GRAB_OBJECTS][item][POSITION], mode = viz.ABS_GLOBAL)
                    self.sceneObjects[GRAB_OBJECTS][item].setEuler(sceneData[GRAB_OBJECTS][item][ORIENTATION], mode = viz.ABS_GLOBAL)
                    #self.sceneObjects[GRAB_OBJECTS][item].setScale(sceneData[GRAB_OBJECTS][item][SCALE])
                
                    if VISIBLE in sceneData[GRAB_OBJECTS][item]:
                        self.sceneObjects[GRAB_OBJECTS][item].visible(sceneData[GRAB_OBJECTS][item][VISIBLE])

            # Apply recorded transforms to gaze objects so moving gaze targets play back
#            if GAZE_OBJECTS in sceneData:
#                for item in self.sceneObjects[GAZE_OBJECTS]:
#                    if item in sceneData[GAZE_OBJECTS]:
#                        gazeObj = self.sceneObjects[GAZE_OBJECTS][item]
#                        gazeData = sceneData[GAZE_OBJECTS][item]
#                        gazeObj.setPosition(gazeData[POSITION], mode = viz.ABS_GLOBAL)
#                        gazeObj.setEuler(gazeData[ORIENTATION], mode = viz.ABS_GLOBAL)
#                        if SCALE in gazeData:
#                            gazeObj.setScale(gazeData[SCALE])
#                        if VISIBLE in gazeData:
#                            gazeObj.visible(gazeData[VISIBLE])
#                    if COLOR in sceneData[GRAB_OBJECTS][item]:
#                        if not sceneData[GRAB_OBJECTS][item][COLOR] == [1.0, 1.0, 1.0]:
#                            print(item, sceneData[GRAB_OBJECTS][item][COLOR])
#                            self.sceneObjects[GRAB_OBJECTS][item].color(sceneData[GRAB_OBJECTS][item][COLOR])
                    
            for item in self.sceneObjects[CUSTOM_OBJECTS]:
                if item in sceneData[CUSTOM_OBJECTS]:
                    self.sceneObjects[CUSTOM_OBJECTS][item].setPosition(sceneData[CUSTOM_OBJECTS][item][POSITION], mode = viz.ABS_GLOBAL)
                    self.sceneObjects[CUSTOM_OBJECTS][item].setEuler(sceneData[CUSTOM_OBJECTS][item][ORIENTATION], mode = viz.ABS_GLOBAL)
                    
                    if SCALE in sceneData[CUSTOM_OBJECTS][item]:
                        self.sceneObjects[CUSTOM_OBJECTS][item].setScale(sceneData[CUSTOM_OBJECTS][item][SCALE])
                        
                    if VISIBLE in sceneData[CUSTOM_OBJECTS][item]:
                        self.sceneObjects[CUSTOM_OBJECTS][item].visible(sceneData[CUSTOM_OBJECTS][item][VISIBLE])
                
#                if COLOR in sceneData[CUSTOM_OBJECTS][item]:
#                    if not sceneData[CUSTOM_OBJECTS][item][COLOR] == [1.0, 1.0, 1.0]:
#                        self.sceneObjects[CUSTOM_OBJECTS][item].color(sceneData[CUSTOM_OBJECTS][item][COLOR])
#                
            for item in self.sceneObjects[AVATAR_OBJECTS]:
                if item in sceneData[AVATAR_OBJECTS]:
                    avatarObj = self.sceneObjects[AVATAR_OBJECTS][item]
                    avatarData = sceneData[AVATAR_OBJECTS][item]
                    isChild = avatarData.get('isChild', False)
                    if isChild:
                        avatarObj.setPosition(avatarData[POSITION])
                        avatarObj.setEuler(avatarData[ORIENTATION])
                    else:
                        avatarObj.setPosition(avatarData[POSITION], mode = viz.ABS_GLOBAL)
                        avatarObj.setEuler(avatarData[ORIENTATION], mode = viz.ABS_GLOBAL)
                    #avatarObj.setScale(avatarData[SCALE]) 
                    animState = avatarData[AVATAR_STATE]
                    try:
                        avatarObj.state(animState)
                    except AttributeError:
                        pass
                else:
                    self.sceneObjects[AVATAR_OBJECTS][item].visible(viz.OFF)
                
            if REGIONS_OF_INTEREST in sceneData:
                for item in self.sceneObjects[REGIONS_OF_INTEREST]:
                    self.sceneObjects[REGIONS_OF_INTEREST][item].setPosition(sceneData[REGIONS_OF_INTEREST][item][POSITION], mode = viz.ABS_GLOBAL)
                    self.sceneObjects[REGIONS_OF_INTEREST][item].setEuler(sceneData[REGIONS_OF_INTEREST][item][ORIENTATION], mode = viz.ABS_GLOBAL)
                    # Apply 3-axis scale if available
                    if SCALE in sceneData[REGIONS_OF_INTEREST][item]:
                        self.sceneObjects[REGIONS_OF_INTEREST][item].setScale(sceneData[REGIONS_OF_INTEREST][item][SCALE])
  
            if CUSTOM_FLAGS in sceneData:
                if REPLAY_FLAG in sceneData[CUSTOM_FLAGS]:
                    self.customFlags = sceneData[CUSTOM_FLAGS][REPLAY_FLAG]
                else:
                    self.customFlags = sceneData[CUSTOM_FLAGS]
            else:
                self.customFlags = None  # Or any other appropriate default action
            
            for client in self.replayVisualisations:
                try:
                    if self.clientCount == 0 or self.replayGUI.showClients[client] or self.replayGUI.showClients["All"]:
                        if len(self.replayVisualisations[client].gazePoints) > 0:
                            self.updateVisualisations(self.replayVisualisations[client])
                except:
                        print(client + " not in client list")
                
            self.playHead += 1 
            
            if self.playHead >= len(self.timeStampList):
                self.playHead = len(self.timeStampList)-1
            
            if not self.firstStart:
                while float(self.timeStampList[self.playHead]) - self.replayHUD.startTimestamp < self.replayHUD.getCurrentTimeElapsed():
                    self.playHead += 1
                    
                    if self.playHead >= len(self.timeStampList):
                        break
            
            self.firstStart = False
        
    def scrubForward(self):
        """
        Jump forward in timeline by scrub length interval.
        
        Advances playhead by scrubLength seconds (converted to frame indices), updates
        scene to new timestamp, resets HUD timer, and synchronizes 360 media playback.
        Sends REPLAY_SCRUB event to notify external systems (e.g., AcqKnowledge).
        """
        indexPerSecond = len(self.timeStampList)/float(self.timeStampList[-1])
        increment = self.scrubLength * int(indexPerSecond)
        if self.playHead + increment < len(self.timeStampList):
            self.playHead += increment
        else:
            self.playHead = len(self.timeStampList) - 2
        
        self.playHead = int(self.playHead)
        
        self.replayHUD.resetStartTime(self.timeStampList[self.playHead])
        
        self.updateScene()
        
        if self.playHead >= len(self.timeStampList):
            self.playHead = len(self.timeStampList)-1
        viz.sendEvent(REPLAY_SCRUB, float(self.timeStampList[self.playHead]))
        
        if self.trialMode == MEDIA_360:
            if self.mediaFile.getTime() + self.scrubLength < float(self.timeStampList[-1]) and self.mediaFile.getTime() + self.scrubLength < self.mediaFile.getDuration():
                time = self.mediaFile.getTime() + self.scrubLength
            else:
                time = float(self.timeStampList[-1])
                
            self.mediaFile.setTime(time)
        
    def scrubBackward(self):
        """
        Jump backward in timeline by scrub length interval.
        
        Moves playhead backward by scrubLength seconds (converted to frame indices),
        updates scene to new timestamp, resets HUD timer, and synchronizes 360 media
        playback. Sends REPLAY_SCRUB event for external synchronization.
        """
        indexPerSecond = len(self.timeStampList)/float(self.timeStampList[-1])
        increment = self.scrubLength * int(indexPerSecond)
        if self.playHead - increment >= 0:
            self.playHead -= increment
        else: 
            self.playHead = 0
        
        self.playHead = int(self.playHead)
        
        self.replayHUD.resetStartTime(self.timeStampList[self.playHead])
        
        self.updateScene()
        
        if self.playHead >= len(self.timeStampList):
            self.playHead = len(self.timeStampList)-1
        viz.sendEvent(REPLAY_SCRUB, float(self.timeStampList[self.playHead]))
        
        if self.trialMode == MEDIA_360:
            if self.mediaFile.getTime() - self.scrubLength > 0:
                time = self.mediaFile.getTime() - self.scrubLength
            else:
                time = 0.0
                
            self.mediaFile.setTime(time)
        
    def scrubFrameForward(self):
        """
        Advance timeline by single frame.
        
        Steps playhead forward one data frame, updates scene state, resets HUD timer,
        and advances 360 media by one frame. Useful for precise frame-by-frame inspection.
        Sends REPLAY_SCRUB event.
        """
        increment = 1
        
        if self.playHead + increment < len(self.timeStampList):
            self.playHead += increment
        else:
            self.playHead = len(self.timeStampList) - 1
            
        self.playHead = int(self.playHead)
        
        self.replayHUD.resetStartTime(self.timeStampList[self.playHead])
        
        self.updateScene()
        
        try:
            viz.sendEvent(REPLAY_SCRUB, float(self.timeStampList[self.playHead]))
        except:
            print("trial end limit")
            
        if self.trialMode == MEDIA_360:
            if self.mediaFile.getFrame() + increment < self.mediaFile.getFrameCount():
                self.mediaFile.setFrame(self.mediaFile.getFrame() + increment)
            else:
                self.mediaFile.setFrame(self.mediaFile.getFrameCount())
            
    def scrubFrameBackward(self):
        """
        Move timeline backward by two frames.
        
        Steps playhead backward 2 data frames, updates scene state, resets HUD timer,
        and moves 360 media backward 2 frames. The 2-frame decrement compensates for
        typical frame advance patterns. Sends REPLAY_SCRUB event.
        """
        increment = 2
        
        if self.playHead - increment >= 0:
            self.playHead -= increment
        else:
            self.playHead = 0
        
        self.playHead = int(self.playHead)
        
        self.replayHUD.resetStartTime(self.timeStampList[self.playHead])
        
        self.updateScene()
        
        if self.playHead >= len(self.timeStampList):
                self.playHead = len(self.timeStampList)-1
        viz.sendEvent(REPLAY_SCRUB, float(self.timeStampList[self.playHead]))
        
        if self.trialMode == MEDIA_360:
            if self.mediaFile.getFrame() - increment > 0:
                self.mediaFile.setFrame(self.mediaFile.getFrame() - increment)
            else:
                self.mediaFile.setFrame(0)
        
    def changePlaybackSlider(self, sliderPos):
#            totalTime = float(self.timeStampList[-1])
#            val = sliderPos * totalTime
#            self.playbackSlider.message('%.2f/%.2f'%(val, totalTime))
        
        currTimeStampIndex = int(sliderPos * len(self.timeStampList))
        self.playHead = currTimeStampIndex
        
        if 0 <= self.playHead < len(self.timeStampList):
            viz.sendEvent(REPLAY_SCRUB, float(self.timeStampList[self.playHead]))

        if self.playHead < 0:
            self.playHead = 0
        elif self.playHead >= len(self.timeStampList):
            self.playHead = len(self.timeStampList)-1
        
        self.replayHUD.resetStartTime(self.timeStampList[self.playHead])
        
        if self.trialMode == MEDIA_360:
            #self.mediaFile.setTime(float(self.timeStampList[self.playHead]))
#                timeStamp = self.currentTrialData[OBJECT_TRACKER][self.timeStampList[self.playHead]][MEDIA_OBJECT][0]
#                
#                frameCount = self.mediaFile.getFrameCount()
#                
#                totalDuration = self.mediaFile.getDuration()
#                
#                frame = (timeStamp/totalDuration) * frameCount
#                
#                self.mediaFile.setFrame(frame)
            
                
            currData = self.currentTrialData[OBJECT_TRACKER][self.timeStampList[self.playHead]]
            
            if not self.clientCount == 0:
                currData = currData[next(iter(currData))]
            
            if MEDIA_OBJECT in currData and len(currData[MEDIA_OBJECT]) > 0:
                self.mediaFile.setTime(currData[MEDIA_OBJECT][0])
            
                state = currData[MEDIA_OBJECT][1]
                if state == viz.MEDIA_RUNNING and self.playState:
                    self.mediaFile.play()

                elif state == viz.MEDIA_STOPPED:
                    # Treat stopped the same as paused (see updateScene for rationale).
                    self.mediaFile.pause()

                elif state == viz.MEDIA_PAUSED:
                    self.mediaFile.pause()
                
        self.updateScene()
    
    def togglePlayback(self):
        """
        Toggle between play and pause states.
        
        Enables/disables the scene update loop, manages playback state flag, resets HUD
        timer to current playhead position, and controls 360 media playback. Sends
        REPLAY_PLAYING or REPLAY_PAUSED events to notify external systems.
        """
        if not self.playState:
            self.sceneUpdate.setEnabled(viz.ON)
            self.playState = viz.ON
            viz.sendEvent(REPLAY_PLAYING)
            
            if self.playHead < 0:
                self.replayHUD.resetStartTime(self.timeStampList[0])
            elif self.playHead < len(self.timeStampList):
                self.replayHUD.resetStartTime(self.timeStampList[self.playHead])
            else:
                self.replayHUD.resetStartTime(self.timeStampList[len(self.timeStampList)-1])
            
            if self.trialMode == MEDIA_360:
                # For ExternalVideo (8K), setTime() is required to set _show_once
                # so _pump will upload the first frame. Without it the texture
                # stays black until the decoder independently delivers a frame.
                self.mediaFile.setTime(self.mediaFile.getTime())
                self.mediaFile.play()
        else:
            self.sceneUpdate.setEnabled(viz.OFF)
            self.playState = viz.OFF
            viz.sendEvent(REPLAY_PAUSED)
            
            if self.trialMode == MEDIA_360:
                self.mediaFile.pause()
        
    def resetScene(self):
        """
        Reset replay to beginning and clear all visualizations.
        
        Resets playhead to frame 0, clears firstStart flag, rewinds HUD timer, toggles
        playback off, resets 360 media to start, and clears all visualization layers
        (scan paths, heatmaps, spheres, etc.) across all clients. Sends REPLAY_RESET event.
        """
        self.playHead = 0
        self.firstStart = True
        self.replayHUD.resetStartTime(self.timeStampList[self.playHead])
        
        viz.sendEvent(REPLAY_RESET)

        self.updateScene()
        self.togglePlayback()
        
        if self.trialMode == MEDIA_360:
            self.mediaFile.setTime(0)
            self.mediaFile.play()
            self.mediaFile.pause()
                
        for client in self.replayVisualisations:
            self.replayVisualisations[client].clearVisualizations()
    
    def openDataFolder(self):
        #current_directory = os.path.join(self.scriptDirectory, 'data')
        current_directory = self.dataFolder
        subprocess.run(['open', current_directory] if os.name == 'posix' else ['explorer', current_directory])
        
    def changeClientID(self, e):
        for clientid in self.replayGUI.showClients:
            if clientid == "All":
                client = clientid
            else:
                client = "client_" + clientid
                
            if not client == e.object.getItem(e.newSel):
                self.replayGUI.showClients[clientid] = False
                if clientid in self.replayVisualisations and not e.object.getItem(e.newSel) == "All":
                    self.replayVisualisations[clientid].clearVisualizations()
            else:
                self.replayGUI.showClients[clientid] = True
                self.updateScene()
        
    def changeTrialNumber(self, e, manual = None):
        if manual is not None:
            self.currTrial = manual
        elif not e.object.getItem(e.newSel) == "...":
            self.currTrial = e.object.getItem(e.newSel)
        elif e.object.getItem(e.newSel) == "...":
            self.replayGUI.replayButtonLabels[TRIAL_NUMBER].clearItems()
            
            if e.newSel == 0:
                self.replayGUI.currPage -= 1
            else:
                self.replayGUI.currPage += 1
                
            self.replayGUI.replayButtonLabels[TRIAL_NUMBER].addItems(self.replayGUI.pageDict[self.replayGUI.currPage])
            
            if self.replayGUI.replayButtonLabels[TRIAL_NUMBER].getItems()[0] == "...":
                self.replayGUI.replayButtonLabels[TRIAL_NUMBER].select(1)
            else:
                self.replayGUI.replayButtonLabels[TRIAL_NUMBER].select(0)
                
            self.currTrial = self.replayGUI.replayButtonLabels[TRIAL_NUMBER].getItems()[self.replayGUI.replayButtonLabels[TRIAL_NUMBER].getSelection()]
            
        self.currentTrialData = self.replayFileData[self.currTrial]
                
        self.prevTrialMode = self.trialMode
        
        self.trialMode = self.currentTrialData[MODE]
        if not self.trialMode == MODEL_3D:
            self.trialMode = MEDIA_360
            
        self.deleteScene()
        self.loadScene()
        self.resetScene()
        
    def deleteScene(self):
        if self.replayGUI.headLink is not None:
            self.replayGUI.headLink.remove()
            self.replayGUI.headLink = None
        if self.replayGUI.mediaLink is not None:
            self.replayGUI.mediaLink.remove()
            self.replayGUI.mediaLink = None
        if self.mediaLink is not None:
            self.mediaFile.remove()
            self.mediaLink = None
            
        for object_type in self.sceneObjects:
            if object_type not in [GAZE_OBJECTS, GRAB_OBJECTS, INVISIBLE_OBJECTS]:
                if object_type in [CUSTOM_OBJECTS, AVATAR_OBJECTS, REGIONS_OF_INTEREST]:
                    for item in self.sceneObjects[object_type]:
                        self.sceneObjects[object_type][item].remove()
                else:
                    if isinstance(self.sceneObjects[object_type], dict):
                        for client in self.sceneObjects[object_type]:
                            self.sceneObjects[object_type][client].remove()
                    else:
                        self.sceneObjects[object_type].remove()
        
        for client in self.replayVisualisations:
            self.replayVisualisations[client].clearVisualizations()
            
        self.replayVisualisations = None
        
    def loadScene(self):
        self.playHead = 0
        self.firstStart = True
        self.sceneUpdate.setEnabled(viz.OFF)
        self.playState = viz.OFF
        
        if self.currentTrialData[ISGUI]:
            self.sceneObjects = {
                GAZE_OBJECTS: {},
                GRAB_OBJECTS: {},
                INVISIBLE_OBJECTS: self.currentTrialData[INVISIBLE_OBJECTS],
                REGIONS_OF_INTEREST: {},
                
                CUSTOM_OBJECTS: {},
                AVATAR_OBJECTS: {}
            }
            
            if not isinstance(self.currentTrialData[AVATAR_HEAD_FILE], dict):
                avatarHead = os.path.join(os.path.dirname(__file__), self.currentTrialData[AVATAR_HEAD_FILE]) if "X_Empty.osgb" not in self.currentTrialData[AVATAR_HEAD_FILE] else  r'C:\Program Files\WorldViz\Vizard8\bin\lib\site-packages\sightlab_utils\resources\avatar\head\GlowManBlue.osgb'
#                print("EMPTY HEAD IS",avatarHead)
                avatarRHand = os.path.join(os.path.dirname(__file__), self.currentTrialData[AVATAR_RIGHT_HAND_FILE]) if "empty.osgb" not in self.currentTrialData[AVATAR_RIGHT_HAND_FILE] else  r'C:\Program Files\WorldViz\Vizard8\bin\lib\site-packages\sightlab_utils\resources\avatar\hands\controller1.osgb'
                avatarLHand = os.path.join(os.path.dirname(__file__), self.currentTrialData[AVATAR_LEFT_HAND_FILE]) if "empty.osgb" not in self.currentTrialData[AVATAR_LEFT_HAND_FILE] else  r'C:\Program Files\WorldViz\Vizard8\bin\lib\site-packages\sightlab_utils\resources\avatar\hands\controller2.osgb'
                
                self.sceneObjects.update({
                AVATAR_HEAD_OBJECT: {'1': vizfx.addChild(avatarHead)},
                AVATAR_RIGHT_HAND_OBJECT: {'1': vizfx.addChild(avatarRHand)},
                AVATAR_LEFT_HAND_OBJECT: {'1': vizfx.addChild(avatarLHand)},

                GAZE_POINT_OBJECT: {'1': vizfx.addChild(os.path.join(os.path.dirname(__file__), self.currentTrialData[GAZE_POINT_FILE]))},
                GAZE_POINT_OBJECT_L: {'1': vizfx.addChild(os.path.join(os.path.dirname(__file__), self.currentTrialData[GAZE_POINT_FILE]))},
                GAZE_POINT_OBJECT_R: {'1': vizfx.addChild(os.path.join(os.path.dirname(__file__), self.currentTrialData[GAZE_POINT_FILE]))},

                })
                
            else:
                keyDict = {
                AVATAR_HEAD_OBJECT: AVATAR_HEAD_FILE,
                AVATAR_RIGHT_HAND_OBJECT: AVATAR_RIGHT_HAND_FILE, 
                AVATAR_LEFT_HAND_OBJECT: AVATAR_LEFT_HAND_FILE, 
                GAZE_POINT_OBJECT: GAZE_POINT_FILE,
                GAZE_POINT_OBJECT_L: GAZE_POINT_FILE,
                GAZE_POINT_OBJECT_R: GAZE_POINT_FILE
                }
                
                for item in [AVATAR_HEAD_OBJECT, AVATAR_RIGHT_HAND_OBJECT, AVATAR_LEFT_HAND_OBJECT, GAZE_POINT_OBJECT, GAZE_POINT_OBJECT_L, GAZE_POINT_OBJECT_R]:
                    self.sceneObjects[item] = {}
                    for client in self.currentTrialData[keyDict[item]]:
                        if not item in [GAZE_POINT_OBJECT, GAZE_POINT_OBJECT_L, GAZE_POINT_OBJECT_R]:
                            filename = self.currentTrialData[keyDict[item]][client]
                            if "X_Empty.osgb" in filename and item == AVATAR_HEAD_OBJECT:
                                self.currentTrialData[keyDict[item]][client] = r"C:\Program Files\WorldViz\Vizard8\bin\lib\site-packages\sightlab_utils\resources\avatar\head\GlowManAuto.osgb"
                            if "empty.osgb" in filename and item in AVATAR_RIGHT_HAND_OBJECT:
                                self.currentTrialData[keyDict[item]][client] = r"C:\Program Files\WorldViz\Vizard8\bin\lib\site-packages\sightlab_utils\resources\avatar\hands\controller1.osgb"
                            if "empty.osgb" in filename and item == AVATAR_LEFT_HAND_OBJECT:
                                self.currentTrialData[keyDict[item]][client] = r"C:\Program Files\WorldViz\Vizard8\bin\lib\site-packages\sightlab_utils\resources\avatar\hands\controller2.osgb"
                            
                            self.sceneObjects[item][client] = vizfx.addChild(os.path.join(os.path.dirname(__file__), self.currentTrialData[keyDict[item]][client]))
                        else:
                            self.sceneObjects[item][client] = vizfx.addChild(os.path.join(os.path.dirname(__file__), self.currentTrialData[keyDict[item]][client][0]))
                            
                            if item == GAZE_POINT_OBJECT:
                                self.sceneObjects[item][client].color(self.currentTrialData[keyDict[item]][client][1])
                            elif item == GAZE_POINT_OBJECT_L:
                                self.sceneObjects[item][client].color(viz.BLUE)
                            elif item == GAZE_POINT_OBJECT_R:
                                self.sceneObjects[item][client].color(viz.RED)
                                
                            self.clientColors[client] = self.currentTrialData[keyDict[item]][client][1]
                            
                            if self.currentTrialData[CONFIGURATION] == "Screen Based EyeTracker":
                                self.sceneObjects[item][client].setReferenceFrame(viz.RF_VIEW)
                            
                for client in self.sceneObjects[AVATAR_HEAD_OBJECT]:
                    if "GlowManAuto" in self.currentTrialData[AVATAR_HEAD_FILE][client]:
                        self.sceneObjects[AVATAR_HEAD_OBJECT][client].color(self.clientColors[client])
                
                self.clientCount = len(self.clientColors)
            
            if self.currentTrialData[MODE] == MODEL_3D:
                self.sceneObjects[ENVIRONMENT_OBJECT] = vizfx.addChild(os.path.join(self.scriptDirectory, self.currentTrialData[ENVIRONMENT_FILE]))
                if SIGHTLAB_START_POINT in self.sceneObjects[ENVIRONMENT_OBJECT].getNodeNames():
                    startMarker = self.sceneObjects[ENVIRONMENT_OBJECT].getChild(SIGHTLAB_START_POINT)

                    startMarker.visible(viz.OFF)
                    startMarker.disable(viz.INTERSECTION)
                    self.startPoint = startMarker.getTransform(SIGHTLAB_START_POINT + "_TRANSFORM").getPosition()
                    self.startEuler = startMarker.getTransform(SIGHTLAB_START_POINT + "_TRANSFORM").getEuler()
                    
            else:
                self.mediaFile, _ext = panorama_utils.make_video(os.path.join(self.scriptDirectory, self.currentTrialData[ENVIRONMENT_FILE]))
                
        else:
            self.sceneObjects = {
                AVATAR_HEAD_OBJECT: {'1': vizfx.addChild(self.currentTrialData[AVATAR_HEAD_FILE])},
                AVATAR_RIGHT_HAND_OBJECT: {'1': vizfx.addChild(self.currentTrialData[AVATAR_RIGHT_HAND_FILE])},
                AVATAR_LEFT_HAND_OBJECT: {'1': vizfx.addChild(self.currentTrialData[AVATAR_LEFT_HAND_FILE])},

                GAZE_POINT_OBJECT: {'1': vizfx.addChild(os.path.join(os.path.dirname(__file__), self.currentTrialData[GAZE_POINT_FILE]))},
                GAZE_POINT_OBJECT_L: {'1': vizfx.addChild(os.path.join(os.path.dirname(__file__), self.currentTrialData[GAZE_POINT_FILE]))},
                GAZE_POINT_OBJECT_R: {'1': vizfx.addChild(os.path.join(os.path.dirname(__file__), self.currentTrialData[GAZE_POINT_FILE]))},
                
                GAZE_OBJECTS: {},
                GRAB_OBJECTS: {},
                INVISIBLE_OBJECTS: self.currentTrialData[INVISIBLE_OBJECTS],
                REGIONS_OF_INTEREST: {},
                
                CUSTOM_OBJECTS: {},
                AVATAR_OBJECTS: {}
            }
            
            if GAZE_POINT_OBJECT_L in self.sceneObjects and self.sceneObjects[GAZE_POINT_OBJECT_L] is not None:
                for client in self.sceneObjects[GAZE_POINT_OBJECT_L]:
                    self.sceneObjects[GAZE_POINT_OBJECT_L][client].color(viz.BLUE)
                
            if GAZE_POINT_OBJECT_R in self.sceneObjects and self.sceneObjects[GAZE_POINT_OBJECT_R] is not None:    
                for client in self.sceneObjects[GAZE_POINT_OBJECT_R]:
                    self.sceneObjects[GAZE_POINT_OBJECT_R][client].color(viz.RED)
                                
            if self.currentTrialData[MODE] == MODEL_3D:
                self.sceneObjects[ENVIRONMENT_OBJECT] = vizfx.addChild(self.currentTrialData[ENVIRONMENT_FILE])
            else:
                self.mediaFile, _ext = panorama_utils.make_video(self.currentTrialData[ENVIRONMENT_FILE])
          
        if self.trialMode == MEDIA_360:
            self.headLight.enable()
            self.headLight.intensity(2)
            
            if self.currentTrialData[MODE][2] == "Monoscopic":
                self.sceneObjects[MEDIA_OBJECT] = panorama_utils.MonoSphere(self.currentTrialData[MODE][1])
            elif self.currentTrialData[MODE][2] == "Stereoscopic T/B":
                self.sceneObjects[MEDIA_OBJECT] = panorama_utils.StereoSphere(self.currentTrialData[MODE][1])
            elif self.currentTrialData[MODE][2] == "Stereoscopic L/R":
                self.sceneObjects[MEDIA_OBJECT] = panorama_utils.Stereo180Sphere(self.currentTrialData[MODE][1])

            # Show/hide the 180_dome backdrop so the back hemisphere is occluded
            # for SBS 180 content (mirrors the experiment-side behavior in sightlab.py).
            if not hasattr(self, 'dome180') or self.dome180 is None:
                import os as _os
                self.dome180 = viz.addChild(_os.path.join(_os.path.dirname(__file__), 'resources/objects/180_dome.osgb'))
            self.dome180.visible(viz.ON if self.currentTrialData[MODE][2] == "Stereoscopic L/R" else viz.OFF)

            self.sceneObjects[MEDIA_OBJECT].texture(panorama_utils.get_texture(self.mediaFile))
            
            avatarHead = self.sceneObjects[AVATAR_HEAD_OBJECT]
            avatarHead = avatarHead[next(iter(avatarHead))]
            
            self.transportNode.setPosition(avatarHead.getPosition())

            transportLink = vizconnect.getTransport(name='main_transport')
            transportLink.setEnabled(viz.OFF)
            
            for trackedObject in [AVATAR_HEAD_OBJECT, AVATAR_RIGHT_HAND_OBJECT, AVATAR_LEFT_HAND_OBJECT]:
                for client in self.sceneObjects[trackedObject]:
                    if trackedObject == AVATAR_HEAD_OBJECT:
                        self.sceneObjects[trackedObject][client].alpha(0)
                    if trackedObject in [AVATAR_LEFT_HAND_OBJECT, AVATAR_RIGHT_HAND_OBJECT]:
                        self.sceneObjects[trackedObject][client].disable(viz.INTERSECTION)
                        self.sceneObjects[trackedObject][client].alpha(0)
            
            vizconnect.getDisplay('main_display').setParent(vizconnect.getTracker('merged'))      
            
            self.mediaLink = viz.link(viz.MainView, self.sceneObjects[MEDIA_OBJECT], mask=viz.LINK_POS)
            
            self.mediaFile.play()
            self.mediaFile.setTime(0)
            self.mediaFile.pause()
        else:
            transportLink = vizconnect.getTransport(name='main_transport')
            transportLink.setEnabled(viz.ON)
            
            if self.headlightFlag is None:
                self.headLight.disable()
            else:
                if self.headlightFlag:
                    self.headLight.enable()
                else:
                    self.headLight.disable()
                    
            vizconnect.getDisplay('main_display').setParent(vizconnect.getAvatar('main_avatar').getAttachmentPoint('head'))
            
        sceneObjects = [self.sceneObjects[GRAB_OBJECTS], self.sceneObjects[GAZE_OBJECTS]]
        
        for objectType in sceneObjects:
            for sceneObject in objectType:
                objectType[sceneObject].remove()
                
            objectType = {}
            
        for item in self.sceneObjects[INVISIBLE_OBJECTS]:
            self.sceneObjects[ENVIRONMENT_OBJECT].getChild(item).visible(viz.OFF)
            
        for item in self.currentTrialData[GRAB_OBJECTS]:
            self.sceneObjects[GRAB_OBJECTS][item] = self.sceneObjects[ENVIRONMENT_OBJECT].getChild(item)
                
        for item in self.currentTrialData[CUSTOM_OBJECTS]:
            if not isinstance(self.currentTrialData[CUSTOM_OBJECTS][item], list):
                if not self.currentTrialData[CUSTOM_OBJECTS][item] == "":
                    self.sceneObjects[CUSTOM_OBJECTS][item] = vizfx.addChild(self.currentTrialData[CUSTOM_OBJECTS][item])
                else:
                    self.sceneObjects[CUSTOM_OBJECTS][item] = vizfx.addChild(os.path.join(os.path.dirname(__file__),'resources/objects/Placeholder.osgb'))
            else:
                parentName = self.currentTrialData[CUSTOM_OBJECTS][item][0]
                self.sceneObjects[CUSTOM_OBJECTS][item] = self.sceneObjects[CUSTOM_OBJECTS][parentName].getChild(item)
                
        for item in self.currentTrialData[AVATAR_OBJECTS]:
            avatarPath = self.currentTrialData[AVATAR_OBJECTS][item]
            if avatarPath and avatarPath.startswith('__CHILD__:'):
                childNodeName = avatarPath[len('__CHILD__:'):]
                self.sceneObjects[AVATAR_OBJECTS][item] = self.sceneObjects[ENVIRONMENT_OBJECT].getChild(childNodeName)
            elif avatarPath:
                self.sceneObjects[AVATAR_OBJECTS][item] = vizfx.addAvatar(avatarPath)
            else:
                self.sceneObjects[AVATAR_OBJECTS][item] = self.sceneObjects[ENVIRONMENT_OBJECT].getChild(item)
            
        for item in self.currentTrialData[GAZE_OBJECTS]:
            if item not in self.currentTrialData[CUSTOM_OBJECTS]:
                self.sceneObjects[GAZE_OBJECTS][item] = self.sceneObjects[ENVIRONMENT_OBJECT].getChild(item)
            else:
                self.sceneObjects[GAZE_OBJECTS][item] = self.sceneObjects[CUSTOM_OBJECTS][item]
                
        if REGIONS_OF_INTEREST in self.currentTrialData:
            for item in self.currentTrialData[REGIONS_OF_INTEREST]:
                name = item[4]
                pos = item[0]
                
                radius = item[1]
                #alpha = item[2]
                alpha = 0.5
                color = item[3]
                
                # Get 3-axis scale if available (backward compatible - defaults to [1, 1, 1])
                scaleX = item[5] if len(item) > 5 else 1.0
                scaleY = item[6] if len(item) > 6 else 1.0
                scaleZ = item[7] if len(item) > 7 else 1.0
                
                newROI = vizshape.addSphere(radius = radius, color=color, alpha = alpha)
                newROI.disable(viz.SHADOW_CASTING)
                newROI.disable(viz.SHADOWS)
                newROI.setPosition(pos)
                newROI.setScale([scaleX, scaleY, scaleZ])
            
                self.sceneObjects[REGIONS_OF_INTEREST][name] = newROI
            
        if self.replayHUD is None:
            self.replayHUD = ReplayHUD(self.clientCount)
        
#        if self.replayVisualisations is None:
        if self.clientCount == 0:
            self.replayVisualisations = {'1': ReplayVisualisations(self.currentTrialData, self.sceneObjects, self.noiseFilter, self.clientColors, None, self.fastHeatmap)}
        else:
            clientTrialData = None
            clientSceneObjects = None
            
            self.replayVisualisations = {}
            
            for client in self.clientColors:
                print(client)
                self.replayVisualisations[client] = ReplayVisualisations(self.currentTrialData, self.sceneObjects, self.noiseFilter, self.clientColors, client, self.fastHeatmap)
        
        if self.replayGUI is None:
            self.replayGUI = ReplayGUI(self.sceneObjects, self.replayHUD, self.replayVisualisations, self.trialMode, self.currTrial, self.clientCount)
        else:
            self.replayGUI.sceneObjects = self.sceneObjects
            self.replayGUI.replayHUD = self.replayHUD
            self.replayGUI.replayVisualisations = self.replayVisualisations
            self.replayGUI.trialMode = self.trialMode
        
        self.timeStampList = list(self.currentTrialData[OBJECT_TRACKER].keys())
        
        self.fixatedState = {}
        self.endedState = {}
        
        if self.clientCount == 0:
            for timestamp in self.currentTrialData[OBJECT_TRACKER]:
                self.fixatedState[timestamp] = ""
                self.endedState[timestamp] = ""
                
                if GAZE_TRACKER in self.currentTrialData[OBJECT_TRACKER][timestamp]:
                    for gaze_item in self.currentTrialData[OBJECT_TRACKER][timestamp][GAZE_TRACKER]:
                        if self.currentTrialData[OBJECT_TRACKER][timestamp][GAZE_TRACKER][gaze_item][GAZE_STATE] == GAZE_FIXATED:
                            self.fixatedState[timestamp] = gaze_item
                        elif self.currentTrialData[OBJECT_TRACKER][timestamp][GAZE_TRACKER][gaze_item][GAZE_STATE] == GAZE_ENDED:
                            self.endedState[timestamp] = '{:<15s}: {:.2f} seconds'.format(gaze_item, float(self.currentTrialData[OBJECT_TRACKER][timestamp][GAZE_TRACKER][gaze_item][DWELL_TIME]))
                else:
                    for gaze_item in self.currentTrialData[OBJECT_TRACKER][timestamp][GAZE_OBJECTS]:
                        if self.currentTrialData[OBJECT_TRACKER][timestamp][GAZE_OBJECTS][gaze_item][GAZE_STATE] == GAZE_FIXATED:
                            self.fixatedState[timestamp] = gaze_item
                        elif self.currentTrialData[OBJECT_TRACKER][timestamp][GAZE_OBJECTS][gaze_item][GAZE_STATE] == GAZE_ENDED:
                            self.endedState[timestamp] = '{:<15s}: {:.2f} seconds'.format(gaze_item, float(self.currentTrialData[OBJECT_TRACKER][timestamp][GAZE_OBJECTS][gaze_item][DWELL_TIME]))
        else:
            for timestamp in self.currentTrialData[OBJECT_TRACKER]:
                self.fixatedState[timestamp] = {}
                self.endedState[timestamp] = {}
                
                for client in self.currentTrialData[OBJECT_TRACKER][timestamp]:
                    self.fixatedState[timestamp][client] = ""
                    self.endedState[timestamp][client] = ""
                    if self.currentTrialData[OBJECT_TRACKER][timestamp][client] is not None:
                        if GAZE_TRACKER in self.currentTrialData[OBJECT_TRACKER][timestamp][client]:
                            gazeTracker = GAZE_TRACKER
                        else:
                            gazeTracker = GAZE_OBJECTS
                            
                        for gaze_item in self.currentTrialData[OBJECT_TRACKER][timestamp][client][gazeTracker]:
                            if self.currentTrialData[OBJECT_TRACKER][timestamp][client][gazeTracker][gaze_item][GAZE_STATE] == GAZE_FIXATED:
                                self.fixatedState[timestamp][client] = gaze_item
                            elif self.currentTrialData[OBJECT_TRACKER][timestamp][client][gazeTracker][gaze_item][GAZE_STATE] == GAZE_ENDED:
                                self.endedState[timestamp][client] = '{:<15s}: {:.2f} seconds'.format(gaze_item, self.currentTrialData[OBJECT_TRACKER][timestamp][client][gazeTracker][gaze_item][DWELL_TIME])
                            
        self.updateScene()

        # Each trial starts out of third person, as it does out of follow mode
        self.replayGUI.replaySceneSettings[THIRD_PERSON_MODE] = viz.OFF
        self.replayGUI.replayButtonLabels[THIRD_PERSON_MODE].set(0)

        if self.trialMode == MEDIA_360:
            self.replayGUI.followON()
            self.transportNode.setPosition([0,0,0])
        else:
            self.replayGUI.replayButtonLabels[FOLLOW_MODE].set(0)

            self.replayGUI.avatarON()
            
            if self.prevTrialMode == MEDIA_360:
                avatarHead = self.sceneObjects[AVATAR_HEAD_OBJECT]
                avatarHead = avatarHead[next(iter(avatarHead))]
                    
                pos = avatarHead.getPosition(mode = viz.ABS_GLOBAL)
                offset = vizmat.Distance(viz.MainView.getPosition(mode = viz.ABS_GLOBAL), self.transportNode.getPosition(mode = viz.ABS_GLOBAL))
                
                if not VIZCONNECT_CONFIG == "Desktop":
                    offset = 1.8
                    pos[1] = pos[1] - offset
                    
                pos[2] = pos[2] - 1
                self.transportNode.setPosition(pos, mode = viz.ABS_GLOBAL)
            else:
                pos = self.transportNode.getPosition()
                avatarHead = self.sceneObjects[AVATAR_HEAD_OBJECT]
                avatarHead = avatarHead[next(iter(avatarHead))]
                    
                headPos = avatarHead.getPosition(mode = viz.ABS_GLOBAL)
                
                pos[2] = headPos[2] - 1
                pos[0] = headPos[0]
                
                self.transportNode.setPosition(pos, mode = viz.ABS_GLOBAL)
                
        firstClient = next(iter(self.replayVisualisations))
        self.replayVisualisations[firstClient].setupRoiTags()        
        
        if self.trialNumber is not None:
            self.replayGUI.replayButtonLabels[TRIAL_NUMBER].select(self.replayGUI.replayButtonLabels[TRIAL_NUMBER].getItems().index(str(self.trialNumber)))
            
        viz.sendEvent(TRIAL_LOADED_EVENT)
         
    def getEnvironmentObject(self):
        return self.sceneObjects[ENVIRONMENT_OBJECT]
        
    def setVisualizationRefreshRate(self, refreshRate, mode = "ALL"):
        pass
        
    def screenCapture(self, capture360 = False):
        
        if capture360:
            viztask.schedule(self.screenCapture360)
            return
            
        image_timestamp = datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
        image_filename = f'{image_timestamp}_screenshot.jpg'
        
#        os.makedirs(os.path.join(self.scriptDirectory, 'recordings'), exist_ok=True)
#        path = os.path.join(self.scriptDirectory, 'recordings', image_filename)

        os.makedirs(os.path.join(self.dataFolder, 'screenshots'), exist_ok=True)
        path = os.path.join(self.dataFolder, 'screenshots', image_filename)
        
        viz.window.screenCapture(path)    
        print('Screen captured:', path)
        
    def screenCapture360(self):
        import os, numpy as np, cv2

        def load_face(folder, base, suf):
            # support png/jpg
            for ext in ('.png','.jpg','.jpeg'):
                p = os.path.join(folder, f'{base}{suf}{ext}')
                if os.path.isfile(p):
                    img = cv2.imread(p, cv2.IMREAD_COLOR)
                    if img is None: raise IOError('Failed to read: '+p)
                    return img
            raise IOError('Face not found: ' + suf)

        def cubemap_faces_to_dict(folder, base):
            faces = {}
            for suf in ['_rt','_lf','_up','_dn','_fr','_bk']:
                faces[suf] = load_face(folder, base, suf)
            return faces  # BGR, HxWx3, square
            
#        def cubemap_faces_to_dict(folder, base):
#            faces = {}
#            # load all raw faces first
#            raw = {}
#            for suf in ['_rt','_lf','_up','_dn','_fr','_bk']:
#                raw[suf] = load_face(folder, base, suf)
#
#            
#            min_side = min(min(img.shape[:2]) for img in raw.values())
#            for suf, img in raw.items():
#                faces[suf] = cv2.resize(img, (min_side, min_side), interpolation=cv2.INTER_LINEAR)
#            return faces

        def dir_to_face_uv(x, y, z):
            # pick major axis to choose face, return face key and local u,v in [-1,1]
            ax = np.argmax(np.abs([x,y,z]), axis=0)
            fx = (ax==0); fy = (ax==1); fz = (ax==2)
            sx = np.sign(x); sy = np.sign(y); sz = np.sign(z)

            # init
            face = np.empty(ax.shape, dtype=object)
            u = np.zeros_like(x); v = np.zeros_like(y)

            # +X -> _rt ; -X -> _lf
            m = fx & (sx>0);  face[m] = '_rt'; u[m] = -z[m]/np.abs(x[m]); v[m] = -y[m]/np.abs(x[m])
            m = fx & (sx<0);  face[m] = '_lf'; u[m] =  z[m]/np.abs(x[m]); v[m] = -y[m]/np.abs(x[m])
            # +Y -> _up ; -Y -> _dn
            m = fy & (sy>0);  face[m] = '_up'; u[m] =  x[m]/np.abs(y[m]); v[m] =  z[m]/np.abs(y[m])
            m = fy & (sy<0);  face[m] = '_dn'; u[m] =  x[m]/np.abs(y[m]); v[m] = -z[m]/np.abs(y[m])
            # +Z -> _fr ; -Z -> _bk
            m = fz & (sz>0);  face[m] = '_fr'; u[m] =  x[m]/np.abs(z[m]); v[m] = -y[m]/np.abs(z[m])
            m = fz & (sz<0);  face[m] = '_bk'; u[m] = -x[m]/np.abs(z[m]); v[m] = -y[m]/np.abs(z[m])

            return face, u, v  # u,v in [-1,1]

        def cubemap_to_equirect_py(folder, base, out_path, width=4096):
            faces = cubemap_faces_to_dict(folder, base)
            # assume all faces same size
            Hf, Wf = next(iter(faces.values())).shape[:2]
            # equirect height is width/2
            He = width//2
            # build lon/lat grid
            j = np.linspace(0, He-1, He)
            i = np.linspace(0, width-1, width)
            ii, jj = np.meshgrid(i, j)
            lon = (ii/width)*2*np.pi - np.pi          # [-pi, pi]
            lat = np.pi/2 - (jj/He)*np.pi             # [ +pi/2 .. -pi/2 ] (top->bottom)
            # unit dir
            cx = np.cos(lat)*np.sin(lon)
            cy = np.sin(lat)
            cz = np.cos(lat)*np.cos(lon)

            face, u, v = dir_to_face_uv(cx, cy, cz)
            # map u,v [-1,1] -> pixel coords in face
            uf = ((u+1)*0.5*(Wf-1)).astype(np.float32)
            vf = ((v+1)*0.5*(Hf-1)).astype(np.float32)

            # build output by sampling each face with cv2.remap
            out = np.zeros((He, width, 3), np.uint8)
            for key, img in faces.items():
                mask = (face == key)
                if not np.any(mask): continue
                # remap wants full maps; for speed, remap whole frame per face with masked blend
                mapx = uf.copy(); mapy = vf.copy()
                # irrelevant pixels can stay; we'll mask them out
                sampled = cv2.remap(img, mapx, mapy, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
 
                out[mask] = sampled[mask]

            cv2.imwrite(out_path, out)
            return out_path
            

        image_timestamp = datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
        image_filename = f'{image_timestamp}_360_capture.jpg'

        os.makedirs(os.path.join(self.dataFolder, '360 captures'), exist_ok=True)
        path = os.path.join(self.dataFolder, '360 captures', image_filename)
        
        origWindowSize = viz.window.getSize()
        
        viz.window.setSize(1000, 1000)
        viz.fov(87)
        
        display = vizconnect.getDisplay()
        oriMode = vizconnect.VIEWPOINT_MATCH_DISPLAY
        setPosModes = [viz.ABS_GLOBAL, viz.ABS_LOCAL, viz.ABS_PARENT, viz.REL_GLOBAL, viz.REL_PARENT, viz.REL_LOCAL]
        currMode = setPosModes[0]
#        viz.window.screenCapture(path)
              
        self.replayGUI.consoleOFF()
        self.replayGUI.avatarOFF()
        self.replayGUI.thirdPersonOFF()     # capture from the participant's eyes
        self.replayGUI.followON()
        self.replayGUI.controllersOFF()
        self.playbackSliderPanel.visible(viz.OFF)
        self.replayGUI.replayInfoPanel.visible(viz.OFF)
        self.replayHUD.timerText.visible(viz.OFF)
        self.replayGUI.gazeRayOFF()
        
        faces = [
        ('_rt', ( 90,   0, 0)),  # +X (right)
        ('_lf', (-90,   0, 0)),  # -X (left)
        ('_up', (  0, -90, 0)),  # +Y (up)
        ('_dn', (  0,  90, 0)),  # -Y (down)
        ('_fr', (  0,   0, 0)),  # +Z (forward)
        ('_bk', (180,   0, 0)),  # -Z (back)
        ]
        
        currPos = viz.MainView.getPosition()
        
        if self.trialMode == MODEL_3D:
            currPos[1] -= 1.8
            currPos[2] -= 0.25
        
#        currPos = [0,0,0]
        self.sceneObjects[AVATAR_HEAD_OBJECT][next(iter(self.sceneObjects[AVATAR_HEAD_OBJECT]))].setEuler(0, 0, 0)
        
        vp = vizconnect.addViewpoint(pos=currPos, euler=[0,0,0], oriMode = oriMode)
        vp.add(display)  
        
        vizconnect.resetViewpoints()
        vp.getNode3d().setEuler([0,0,0], mode = currMode)
        vp.getNode3d().setPosition(currPos, mode = currMode)
            
        for suf, euler in faces:
            vp = vizconnect.addViewpoint(pos=currPos, euler=euler, oriMode = oriMode)
            vp.add(display)

            vizconnect.resetViewpoints()
            vp.getNode3d().setEuler(euler, mode = currMode)
            
            if not suf =="_dn":
                vp.getNode3d().setPosition(currPos, mode = currMode)
                viz.fov(87)
            else:
                tempPos = deepcopy(currPos)
                tempPos[2]-= 0.1
                viz.fov(90)
                vp.getNode3d().setPosition(tempPos, mode = currMode)

            image_filename = f'{image_timestamp}_360_capture' + suf + '.jpg'
            path = os.path.join(self.dataFolder, '360 captures', image_filename)

            #            viz.window.screenCapture(path)
            yield viztask.waitTime(0.2)
            yield viz.window.screenCapture(path)
            
        folder = os.path.join(self.dataFolder, '360 captures')
        base   = f'{image_timestamp}_360_capture'
        out_equi = os.path.join(folder, f'{base}_equirect.png')
        cubemap_to_equirect_py(folder, base, out_equi, width=4096)
        print('Equirectangular saved:', out_equi)
        os.startfile(out_equi) 
        
        if self.replayGUI.replayButtonLabels[CONSOLE_VISIBLE].get():
            self.replayGUI.consoleON()
        
        if self.replayGUI.replayButtonLabels[AVATAR_VISIBLE].get():
            self.replayGUI.avatarON()
        
        if self.replayGUI.replayButtonLabels[CONTROLLERS_VISIBLE].get():
            self.replayGUI.controllersON()
        
        if self.replayGUI.replayButtonLabels[GAZE_RAY_VISIBLE].get():
            self.replayGUI.gazeRayON()
            
        if self.replayGUI.replayButtonLabels[FOLLOW_MODE].get():
            self.replayGUI.followOFF()
        
        self.playbackSliderPanel.visible(viz.ON)
        self.replayGUI.replayInfoPanel.visible(viz.ON)
        self.replayHUD.timerText.visible(viz.ON)
        
        viz.window.setSize(origWindowSize[0], origWindowSize[1])
        viz.fov(60)
        
        print('360 Screen captured:', path)
        
class SightLabReplay(ReplayEngine):
    """
    Main public interface for SightLab replay system.
    
    Extends ReplayEngine with keyboard bindings and interactive controls. Provides the
    standard entry point for replay sessions with full GUI control panel, timeline scrubbing,
    playback management, and screen capture. Automatically loads scene and registers input
    handlers for spacebar play/pause, C/V scrubbing, B/N frame stepping, and R reset.
    """
    def __init__(self, noiseFilter = None, trialNumber = None, sightlab_1_9 = False, dataDirectory = 'data', headlight = None, fastHeatmap = True):
        """
        Initialize SightLab replay with keyboard controls.
        
        Calls ReplayEngine.__init__ to load session data, then loads the scene and
        registers keyboard handlers for interactive playback control.
        
        Args:
            noiseFilter (bool, optional): Enable gaze noise filtering (auto-detected).
            trialNumber (int, optional): Specific trial to load, or None for all.
            sightlab_1_9 (bool): Load legacy SightLab 1.9 format. Defaults to False.
            dataDirectory (str): Relative data folder path. Defaults to 'data'.
            headlight (bool, optional): Enable viewer headlight.
            fastHeatmap (bool): Enable optimized heatmap mode. Defaults to True.
        """
        super().__init__(noiseFilter, trialNumber, sightlab_1_9, dataDirectory, headlight, fastHeatmap)
        
        self.loadScene()
        
        if CLIENT_ID in self.replayGUI.replayButtonLabels:
            vizact.onlist(self.replayGUI.replayButtonLabels[CLIENT_ID], self.changeClientID)
        
        vizact.onlist(self.replayGUI.replayButtonLabels[TRIAL_NUMBER], self.changeTrialNumber)
        vizact.onbuttonup(self.replayGUI.replayButtonLabels[DATA_FOLDER], self.openDataFolder)
        
        vizact.onslider(self.playbackSlider, self.changePlaybackSlider)
        
        vizact.onkeydown(' ', self.togglePlayback)
        
        vizact.onkeydown('c', self.scrubBackward)
        vizact.onkeydown('C', self.scrubBackward)
        
        vizact.onkeydown('v', self.scrubForward)
        vizact.onkeydown('V', self.scrubForward)
        
        vizact.onkeydown('b', self.scrubFrameBackward)
        vizact.onkeydown('B', self.scrubFrameBackward)
        
        vizact.onkeydown('n', self.scrubFrameForward)
        vizact.onkeydown('N', self.scrubFrameForward)
        
        vizact.onkeydown('r', self.resetScene)
        vizact.onkeydown('R', self.resetScene)
        
        vizact.onkeydown("/", self.screenCapture)
        vizact.onkeydown("3", self.screenCapture, True)
        vizact.onkeydown("4", self.resetTransportNode)

        if VIZCONNECT_CONFIG == "Desktop":
            vizact.onkeydown(viz.KEY_SHIFT_L, vizconnect.getRawTracker("head_tracker").setEnabled, viz.TOGGLE)

    def resetTransportNode(self):
        """Reset the vizconnect transport node to origin position and default orientation."""
        self.transportNode.setPosition([0, 0, 0], mode=viz.ABS_GLOBAL)
        self.transportNode.setEuler([0, 0, 0], mode=viz.ABS_GLOBAL)

    def setThirdPersonOffset(self, offset = None, pitch = None):
        """
        Set where the third person follow camera sits relative to the participant.

        Example, 4 m behind and 1.5 m above the head, tilted 20 degrees down:
            replay.setThirdPersonOffset([0, 1.5, -4], pitch = 20)

        Args:
            offset (list, optional): [x, y, z] in meters from the participant's head,
                in the direction they face: +y is up and -z is behind them. None keeps
                the current offset (THIRD_PERSON_OFFSET until changed).
            pitch (float, optional): Degrees the camera tilts down toward the
                participant. None keeps the current pitch (THIRD_PERSON_PITCH until changed).
        """
        self.replayGUI.setThirdPersonOffset(offset, pitch)

    def getCurrTime(self):
        """
        Get current replay timestamp.
        
        Returns:
            float: Current playback time in seconds from trial start.
        """
        return self.currTime
        
    def getCurrFlag(self):
        """
        Get custom event flags dictionary.
        
        Returns:
            dict: Custom flags set during replay for experiment logic synchronization.
        """
        return self.customFlags

# AcqKnowledge Integration
# This section automatically sets up AcqKnowledge synchronization when replay.py is imported

try:
    from sightlab_utils.ATCommunicator import ATCommunicator
    from sightlab_utils.ActiveGraphsDialog import ActiveGraphsDialog


    # Global variables to track AcqKnowledge connection state
    _acq_attached_graph_title = None

    def connectToAcqKnowledge():
        """
        Connect to AcqKnowledge software on default port 9090.
        
        Establishes TCP connection to BIOPAC AcqKnowledge for synchronizing replay
        timeline with physiological data recordings. Must be called before attachToGraph.
        
        Returns:
            bool: True if connection successful, False otherwise.
        """
        print("Connecting to AcqKnowledge...")
        try:
            ATCommunicator().connect(9090)
            status = ATCommunicator().getStatus()
            if status != ATCommunicator.Status.NO_CONNECTION:
                print("Successfully connected to AcqKnowledge")
                return True
            else:
                print("Failed to connect to AcqKnowledge. Make sure running and SightLab Communication enabled in Preferences")
                return False
        except Exception as e:
#            print(f"Error connecting to AcqKnowledge: {e}")
            return False

    def disconnectFromAcqKnowledge():
        """
        Disconnect from AcqKnowledge software.
        
        Closes TCP connection to BIOPAC AcqKnowledge and resets attached graph state.
        Call when replay session ends or switching to different data source.
        """
        global _acq_attached_graph_title
        print("Disconnecting from AcqKnowledge...")
        try:
            ATCommunicator().disconnect()
            _acq_attached_graph_title = None
            print("Disconnected from AcqKnowledge")
        except Exception as e:
            print(f"Error disconnecting from AcqKnowledge: {e}")

    def attachToGraph():
        """
        Attach to AcqKnowledge graph for timeline synchronization.
        
        Queries available graphs in AcqKnowledge, auto-selects the first active graph,
        and attaches for synchronized timeline control. Must call connectToAcqKnowledge
        first. Once attached, replay scrubbing will update AcqKnowledge time position.
        
        Returns:
            bool: True if successfully attached, False otherwise.
        """
        global _acq_attached_graph_title
        
        # Check if connected
        if ATCommunicator().getStatus() == ATCommunicator.Status.NO_CONNECTION:
            print("Not connected to AcqKnowledge. Connect first.")
            return False
        
        # Get active graphs
        try:
            graphTitles = ATCommunicator().getActiveGraphs()
            if not graphTitles:
                print("No active graphs found in AcqKnowledge")
                return False
            
            print(f"Available graphs: {graphTitles}")
            
            # Auto-select first graph
            titleOfGraphToAttach = graphTitles[0]
            print(f"Auto-selecting graph: {titleOfGraphToAttach}")
            
            # Attach to selected graph
            if ATCommunicator().attachGraph(titleOfGraphToAttach):
                _acq_attached_graph_title = titleOfGraphToAttach
                print(f"Successfully attached to graph: {titleOfGraphToAttach}")
                return True
            else:
                print(f"Failed to attach to graph: {titleOfGraphToAttach}")
                return False
                
        except Exception as e:
            print(f"Error attaching to graph: {e}")
            return False

    def detachFromGraph():
        """
        Detach from currently attached AcqKnowledge graph.
        
        Stops timeline synchronization with AcqKnowledge but maintains connection.
        Useful for temporarily disabling sync or switching to different graph.
        """
        global _acq_attached_graph_title
        try:
            ATCommunicator().detachGraph()
            if _acq_attached_graph_title:
                print(f"Detached from graph: {_acq_attached_graph_title}")
            _acq_attached_graph_title = None
        except Exception as e:
            print(f"Error detaching from graph: {e}")

    def _on_replay_scrub(t_seconds):
        """
        Handle REPLAY_SCRUB events and synchronize AcqKnowledge timeline.
        
        Internal callback registered to REPLAY_SCRUB event. Converts replay timestamp
        (seconds) to milliseconds and updates AcqKnowledge graph time position when
        attached. Enables synchronized inspection of physiological data alongside
        eye tracking replay.
        
        Args:
            t_seconds (float): Replay timestamp in seconds.
        """
        global _acq_attached_graph_title
        
        # Only send to AcqKnowledge if we have an attached graph
        if _acq_attached_graph_title and ATCommunicator().getStatus() != ATCommunicator.Status.NO_CONNECTION:
            try:
                # Convert seconds to milliseconds for AcqKnowledge
                time_ms = int(float(t_seconds) * 1000.0)
                ATCommunicator().setTimePosition(time_ms)
#                print(f"Synced AcqKnowledge to {time_ms}ms")
            except Exception as e:
                print(f"Failed to scrub AcqKnowledge: {e}")
                # If communication failed, might need to reconnect
                if ATCommunicator().getStatus() == ATCommunicator.Status.NO_CONNECTION:
                    _acq_attached_graph_title = None

    # Set up the callback for REPLAY_SCRUB events
    viz.callback(REPLAY_SCRUB, _on_replay_scrub)

    # Key bindings for AcqKnowledge functions
    vizact.onkeydown('1', connectToAcqKnowledge)      # Press '1' to connect
    vizact.onkeydown('2', attachToGraph)              # Press '2' to attach to graph
    vizact.onkeydown('4', detachFromGraph)            # Press '3' to detach from graph
    vizact.onkeydown('5', disconnectFromAcqKnowledge) # Press '4' to disconnect

    print("AcqKnowledge integration loaded. Key bindings:")
    print("  Press '1' to connect to AcqKnowledge")
    print("  Press '2' to attach to a graph")
#    print("  Press '4' to detach from graph")  
#    print("  Press '5' to disconnect from AcqKnowledge")
    
except ImportError:
    print("ATCommunicator not available - AcqKnowledge integration disabled")
        
if __name__ == '__main__':
    vizconnect.go(VIZCONNECT_PATH)
    
    replay = SightLabReplay()