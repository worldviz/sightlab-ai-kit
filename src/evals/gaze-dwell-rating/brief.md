# Experiment brief: gaze dwell with post-trial rating

## 1. Purpose
<!-- id: purpose -->
Whether people look longer at the object they later rate as more attractive, in a plain
room with two objects side by side.

## 2. Design
<!-- id: design -->
Within subjects. One factor, object pair, with four levels (four pairs). Each pair is one
trial; pair order is randomised once per participant. Left/right position within a pair is
counterbalanced across participants (assumed: alternate by participant ID parity).

## 3. Stimuli
<!-- id: stimuli -->
Environment `sightlab_resources/environments/whiteroom.osgb`. Each trial shows two shipped
objects from `sightlab_resources/objects/` on stands 1.2 m apart, 2 m in front of the start
point, at eye height (assumed: 1.5 m). Pairs, all shipped files: (`Plant.osgb`,
`guitar.osgb`), (`chair.osgb`, `crate.osgb`), (`flashlight.osgb`, `computer_monitor.osgb`),
(`pigeon.osgb`, `chick.osgb`). Shipped models load at their own scale; scale any that look
wrong so each is roughly 0.3 m tall (assumed).

## 4. Procedure
<!-- id: procedure -->
Instructions, then four trials, then a thank-you. Each trial: a 1 s blank, both objects
appear, free viewing for 8 s, objects disappear, two rating questions, next trial.

## 5. Participant instructions
<!-- id: instructions -->
Start: "You will see pairs of objects. Look at them however you like. After each pair, rate
how attractive each object was. Press the trigger to begin." (The trigger, so no
`textContinueKey`.) End: "Thank you, the session is complete."

## 6. Responses
<!-- id: responses -->
Gaze only during viewing. After viewing, two rating questions (1 to 7), left object then
right object, answered with the controller trigger (mouse on the desktop).

## 7. Independent variables
<!-- id: ivs -->
Object pair (4 levels); which object is on the left.

## 8. Dependent variables
<!-- id: dvs -->
Total dwell time and fixation count on each object (standard summary columns); the two
ratings per trial in custom summary columns `Rating_left` and `Rating_right`.

## 9. Data logging
<!-- id: data-logging -->
Per-frame gaze (default), per-trial summary with `Rating_left`, `Rating_right`, `Pair` and
`Left object` columns, replay data on. No BIOPAC.

## 10. Trials
<!-- id: trials -->
Four test trials, no practice, one repetition, 8 s of viewing each plus rating time:
`setTrialCount(4)`.

## 11. Notes
<!-- id: notes -->
Register all eight objects with `gaze=True` before the trials; hide the ones not in use
with `visible(viz.OFF)` rather than removing them. Randomise pair order once per session.

## 12. Hardware and setup
<!-- id: hardware -->
Meta Quest Pro with eye tracking (hardware configuration "Meta Quest Pro"); no physiology or
body tracking; SightLab 2.9, Vizard 8. Development and the harness use
`hardwareconfig='Desktop'`.
