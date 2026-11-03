# Experiment brief: gaze dwell with post-trial rating

<!-- Filled example. Two items are marked (assumed): they were not in the researcher's
description and are the kit's defaults. -->

## 1. Purpose
Whether people look longer at the object they later rate as more attractive, in a plain
room with two objects side by side.

## 2. Design
Within subjects. One factor, object pair, with four levels (four pairs). Each pair is one
trial; pair order is randomised per participant. The left/right position of the two objects
in a pair is counterbalanced across participants (assumed: alternate by participant ID parity).

## 3. Stimuli
Environment: `sightlab_resources/environments/whiteroom.osgb`. Each trial shows two shipped
objects from `sightlab_resources/objects/` on stands 1.2 m apart, 2 m in front of the start
point, at eye height (assumed: 1.5 m). Pairs: (vase, lamp), (clock, plant), (mug, bottle),
(book, box).

## 4. Procedure
Instructions → four trials → thank-you. Each trial: a 1 s blank, both objects appear, free
viewing for 8 s, objects disappear, rating scale, next trial on the trigger.

## 5. Participant instructions
Start: "You will see pairs of objects. Look at them however you like. After each pair, rate
how attractive each object was. Press the trigger to begin." Trial: none. End: "Thank you,
the session is complete."

## 6. Responses
Gaze only during viewing. After viewing, two rating questions (1–7) answered with the
controller; on the desktop, with the mouse.

## 7. Independent variables
Object pair (4 levels); within each pair, which object is on the left.

## 8. Dependent variables
Total dwell time and fixation count on each object (summary file: `Total Dwell Time (secs)`,
`Fixation Count`); time to first fixation; the two ratings per trial (custom columns
`Rating_left`, `Rating_right`).

## 9. Data logging
Per-frame gaze (default), per-trial summary with the two rating columns, replay data on.
No BIOPAC. Condition column holds the pair name; a custom column holds the left object name.

## 10. Trials
Four test trials, no practice, one repetition, each 8 s of viewing plus the rating time.
`setTrialCount(4)`.

## 11. Notes
Objects must be registered with `gaze=True` before the trials start; hide them between
trials with `visible(viz.OFF)` rather than removing them, so the summary keeps all eight
object rows every trial. Randomise pair order once per session, not per trial.

## 12. Hardware and setup
Meta Quest Pro with eye tracking (hardware configuration "Meta Quest Pro"); no physiology,
no body tracking; 3 m × 3 m room; SightLab 2.9, Vizard 8. For development and the harness:
`hardwareconfig='Desktop'`.
