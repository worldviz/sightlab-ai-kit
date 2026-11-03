# Experiment brief: object recognition with two exposure conditions

## 1. Purpose
<!-- id: purpose -->
Whether longer exposure to a set of objects improves later recognition, in a simple
study-then-test design.

## 2. Design
<!-- id: design -->
Within subjects, one factor, exposure, with two levels: short (2 s) and long (6 s). Four
trials, two per level, order shuffled once per participant with both levels in each half
(assumed: a balanced shuffle of `["short", "short", "long", "long"]`).

## 3. Stimuli
<!-- id: stimuli -->
Environment `sightlab_resources/environments/whiteroom.osgb`. Each trial studies three
shipped objects from `sightlab_resources/objects/` on a table 1.5 m ahead, then shows one
probe object: on half the trials one of that trial's three (old), on the others an object
that was not among that trial's three (new). "New" means new to this trial; an object may
appear in another trial's study set (assumed: eight distinct objects in all, for example
`basketball.osgb`, `Baseball.osgb`, `Plant.osgb`, `box.osgb`, `chair.osgb`, `crate.osgb`,
`guitar.osgb`, `flashlight.osgb`, assignment fixed per session).

## 4. Procedure
<!-- id: procedure -->
Instructions, then four trials. Each trial: study phase (three objects for 2 s or 6 s), a
1 s blank, probe appears, the participant answers "seen before?" yes or no, next trial.

## 5. Participant instructions
<!-- id: instructions -->
Start: "You will see three objects, then one object. Say whether that object was among the
three. Press the trigger to begin." Probe: "Was this object among the three?" End: "Thank you."

## 6. Responses
<!-- id: responses -->
A two-option rating scale (`Yes`, `No`) after the probe, chosen with the trigger (mouse on
the desktop).

## 7. Independent variables
<!-- id: ivs -->
Exposure (short / long); probe type (old / new).

## 8. Dependent variables
<!-- id: dvs -->
The response and whether it was correct, in custom summary columns `Response` (Yes/No) and
`Correct` (1/0); the condition in `Condition` (short/long) and the probe type in `Probe`
(old/new).

## 9. Data logging
<!-- id: data-logging -->
Standard files; the three study objects and the probe registered with `gaze=True` so dwell
data exists; summary columns `Condition`, `Probe`, `Response`, `Correct`.

## 10. Trials
<!-- id: trials -->
Four trials: `setTrialCount(4)`.

## 11. Notes
<!-- id: notes -->
Shuffle the condition list once before the loop. Label each trial with its condition via
`trialLabel=` so the standard `Label` column also carries it. Hide objects with
`visible(viz.OFF)` between phases rather than removing them.

## 12. Hardware and setup
<!-- id: hardware -->
Any headset (hardware configuration "Meta Quest 3" assumed); no physiology; SightLab 2.9,
Vizard 8. Development and the harness use `hardwareconfig='Desktop'`.
