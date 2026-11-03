# Experiment brief: object 1-back with BIOPAC markers

## 1. Purpose
<!-- id: purpose -->
A working-memory load task in VR whose events are visible in a BIOPAC physiology recording,
so heart-rate changes can be aligned with task events.

## 2. Design
<!-- id: design -->
Within subjects, one condition. Two blocks (trials) of eight items each. In each block three
items are repeats of the previous item (1-back targets); the sequence is fixed per block
(assumed: generated once per session with exactly three targets, never two in a row).

## 3. Stimuli
<!-- id: stimuli -->
Environment `sightlab_resources/environments/lab_empty.osgb`. Three shipped objects
(assumed: basketball, soccerball and a vizshape cube) shown one at a time on a stand 1.5 m
ahead at eye height, each for 1.5 s with a 0.5 s blank between items.

## 4. Procedure
<!-- id: procedure -->
Instructions, block 1 (eight items, about 16 s), a 5 s rest, block 2, thank-you. Items run
on a timer; nothing waits for the participant except the start.

## 5. Participant instructions
<!-- id: instructions -->
Start: "Objects will appear one after another. Press the trigger whenever the object is the
same as the one just before it. Press the trigger to begin." End: "Thank you."

## 6. Responses
<!-- id: responses -->
A trigger press (space bar on the desktop) within the item's 2 s window. A press on a
repeat item is a hit; a press on any other item is a false alarm; a repeat with no press is
a miss.

## 7. Independent variables
<!-- id: ivs -->
None manipulated; item type (repeat / non-repeat) is the within-block factor.

## 8. Dependent variables
<!-- id: dvs -->
Per block: `Hits`, `False alarms`, `Misses`, mean reaction time on hits `RT hits (s)`, as
custom summary columns.

## 9. Data logging
<!-- id: data-logging -->
BIOPAC on (`biopac=True`): SightLab's automatic trial start/end markers, plus one marker per
item onset named by the item and whether it is a repeat (`sightlab.acqServer.insertGlobalEvent`).
Standard per-frame data on; no gaze objects needed beyond the stand (assumed: the stand is
registered with `gaze=True` so dwell data exists).

## 10. Trials
<!-- id: trials -->
Two blocks: `setTrialCount(2)`. Each block ends by timer after its eighth item.

## 11. Notes
<!-- id: notes -->
Item timing from `viztask.waitTime`; responses from a `viz.KEYDOWN_EVENT` / trigger callback
that records the time against the current item. Markers must be sent at onset, not at the
end of the item. The marker name must include the item name.

## 12. Hardware and setup
<!-- id: hardware -->
Any headset (hardware configuration "SteamVR" assumed), BIOPAC MP160 with AcqKnowledge and
the NDT link on the same network; SightLab 2.9, Vizard 8. Development and the harness use
`hardwareconfig='Desktop'`; the harness counts marker calls but cannot confirm delivery.
