# Experiment brief: visual search driven by a STIM file

## 1. Purpose
<!-- id: purpose -->
How quickly people find a target object among distractors, as a function of where it is
and how many distractors there are; the trial list must be editable without touching code.

## 2. Design
<!-- id: design -->
Within subjects. Each row of a STIM file is one trial: target name, target position
(left / centre / right) and distractor count (2 or 4). Four rows, run in file order
(assumed: no shuffling, so the researcher controls the order from the file).

## 3. Stimuli
<!-- id: stimuli -->
Environment `sightlab_resources/environments/dojo.osgb`. Target: `basketball.osgb` or
`soccerball.osgb` from `sightlab_resources/objects/`. Distractors: vizshape cubes (assumed:
0.25 m, grey) placed on a 2 m arc around the target's row at eye height.

## 4. Procedure
<!-- id: procedure -->
Instructions, then four trials. Each trial: prompt, objects appear, the participant finds
the target; the trial ends when gaze has rested on the target for 1 s, or after 20 s.

## 5. Participant instructions
<!-- id: instructions -->
Start: "Find the ball and look at it until it changes colour. Press the trigger to begin."
Per trial: "Find the <target>." End: "Thank you."

## 6. Responses
<!-- id: responses -->
Gaze dwell on the target (SightLab `GAZE_TIME_EVENT` with the dwell threshold set to 1 s)
ends the trial; no key press.

## 7. Independent variables
<!-- id: ivs -->
Target position (3 levels) and distractor count (2 levels), from the STIM file.

## 8. Dependent variables
<!-- id: dvs -->
Time to find the target in seconds, from trial start to the dwell event, in a custom
summary column `Time to find (s)`; whether the trial timed out, `Timed out` (yes/no).

## 9. Data logging
<!-- id: data-logging -->
Standard files plus summary columns `Target`, `Position`, `Distractors`, `Time to find (s)`
and `Timed out`, one row per trial. The target is the only registered gaze object.

## 10. Trials
<!-- id: trials -->
Four trials, one per STIM row: `setTrialCount(4)` from the number of rows read.

## 11. Notes
<!-- id: notes -->
The STIM file is `stim/search.csv` beside the script with header
`target,position,distractors` and four rows. Use `sightlab_utils.stim_reader`. The target
turns green on the dwell event, then the trial ends; do not call `endTrial` from inside the
gaze callback directly.

## 12. Hardware and setup
<!-- id: hardware -->
An eye-tracking headset (hardware configuration "Vive Pro Eye" assumed); SightLab 2.9,
Vizard 8. Development and the harness use `hardwareconfig='Desktop'`, where the harness
looks at the target to trigger the dwell.
