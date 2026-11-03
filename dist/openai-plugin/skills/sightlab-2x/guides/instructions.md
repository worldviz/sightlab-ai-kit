# Instructions and on-screen text

Sources: help.worldviz.com/sightlab adding-instructions; the earlier assistant's `adding-instructions.md`.

When to read: the study shows the participant text or images at the start, between trials,
or at the end.

## Four ways, from simplest to most flexible

1. **GUI start and end text** (SightLab 2.8+): the researcher types them in the GUI; nothing
   in code. In `gui=True` scripts prefer this.
2. **Trial prompts** on the frame's own calls:
   ```python
   yield sightlab.startTrial(startExperimentText='Look around.\n\nPress the trigger when ready')
   yield sightlab.startTrial(startTrialText='Find the ball.')
   yield sightlab.endTrial(endExperimentText='Thank you.')
   ```
   `startExperimentText` shows once, before the first trial; `startTrialText` before every
   trial; `endExperimentText` only after the last trial. The text waits for
   `textContinueEvent` (default `'triggerPress'`: the controller trigger, or the left mouse
   button on the desktop). No extra `yield` wait is needed for the same purpose.

   `textContinueKey=' '` **replaces** that wait with a wait for the key: SightLab then
   ignores the trigger entirely (`startTrial` does `waitKeyDown(key)` instead of
   `waitEvent(event)`). Use it only for a desktop-only study, and never with on-screen text
   that says "press the trigger": a headset participant would be stuck.
3. **Free-standing instructions** anywhere in the generator:
   ```python
   yield sightlab.showInstructions('Press a to toggle the ball.\n\nPress the trigger to continue', pauseTimer=True)
   yield sightlab.hideInstructions()
   ```
   `pauseTimer=True` stops the trial clock while the text is up. Placed before `startTrial`,
   no `hideInstructions` is needed; the trial start clears it.
4. **Image instructions**: `yield sightlab.showInstructions(image='sightlab_resources/sightlab_controls.jpg')`;
   scale the quad with `sightlab.instructionsImageQuad.setScale([1, 1.5, 1])` before showing.
   Shipped controller diagrams: `sightlab_controls.jpg`, `sightlab_controls_oculus.jpg`,
   `sightlab_controls_presenter.jpg` under `sightlab_resources/`.

## Gotchas

- In GUI mode with `startExperimentText`, set the first trial's start condition to "None"
  in the GUI, or the GUI's own start condition and the text's trigger both wait.
- Several slides: call `showInstructions` several times in a row, each with its own wait.
- If data logging was paused for the instructions, `yield sightlab.setDataLoggingState(1)`
  turns it back on.
- Text is shown on the HUD in front of the view; long paragraphs do not wrap well, use `\n`.

## Shipped examples

`examples/Instructions` (every variant: GUI, multiple slides, images, grabbable image),
`examples/Sample Code`.
