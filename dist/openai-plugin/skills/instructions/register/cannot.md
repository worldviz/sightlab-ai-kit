---
status: draft for Alex and Sado to review
---

# What SightLab 2 cannot do, what needs custom work, and what needs hardware

Read this before building anything. Classify the request, say which list it falls in, and
say so to the researcher in plain words. Over-promising costs more than a frank "not in 2.x".

## Not possible in SightLab 2 (say so, offer the nearest thing)

- Running in a web browser or on a headset without a Windows PC: SightLab 2 is a Vizard
  application. (SightLab 3 Standalone is the WorldViz product for that.)
- macOS or Linux: Vizard is Windows only.
- Eye tracking without an eye-tracking headset or a screen-based tracker: on the Desktop
  configuration the "gaze" is the view direction, which is fine for development and for
  head-direction studies only.
- Physically accurate physics simulation (soft bodies, fluids, destructible worlds): Vizard's
  physics covers rigid bodies, collisions and grabbing; see `examples/Physics`.
- Photoreal, AAA-quality rendering: fine for research; not a game-engine look.
- Native hand tracking on every headset: available where the headset and its vizconnect
  configuration provide it (Quest, Focus Vision); not on headsets without it.
- Sub-millisecond event timing guarantees: trial events are logged at frame rate (typically
  72–90 Hz); synchronisation with physiology uses BIOPAC markers, not a shared clock.

## Possible, but custom work (say what it takes before starting)

- Animated or conversational avatars beyond the shipped agents: `examples/AI_Intelligent_Agent`
  and `examples/Scripted Avatar Agent` are starting points; new animations, lip-sync and
  gestures are modelling and scripting work.
- Large generated worlds (a city, a forest with thousands of plants): possible with external
  tools (Blender, generated assets) and Vizard's loaders, with performance work; not a
  one-shot request.
- Multi-user studies: supported (`SightLabServer`/`SightLabClient`; the scripts live in the
  `Multi User ExamplesScripts` folder beside `ExampleScripts`) but each setup needs network
  configuration and a test on the real machines.
- Driving, locomotion rigs, treadmills, motion platforms: shipped examples exist
  (`examples/Driving`); hardware integration is per device.
- Custom analysis beyond the shipped tools: the data files are CSV; `examples/AI_Data_Analysis`
  and `examples/VisualizationTools` show the pattern; anything specific is scripting work.
- Anything that changes `sightlab_utils` itself: refer to WorldViz support.

## Needs hardware you may not have (build it; say what cannot be tested without the device)

- Real eye-tracking data: an eye-tracking headset (Vive Pro Eye, Vive Focus Vision, Meta
  Quest Pro, HP Omnicept, Varjo, Pupil Labs Neon…) or a screen-based tracker. The harness
  verifies the pipeline in desktop mode only.
- BIOPAC markers and physiology: a BIOPAC MP160/MP36 with AcqKnowledge and the NDT network
  link; the script can be checked for the marker calls, not for delivery.
- Full-body or hand tracking: Vive trackers, OptiTrack, Mocopi, Manus gloves, or a headset
  with hand tracking.
- LSL, fNIRS, EEG streams: the device and its software (`examples/LSL_Sample`, `examples/cobiFNIR`).
- Passthrough and mixed reality: a headset with colour passthrough (`examples/MixedReality`).
- 8K or stereo 360 video playback: a GPU and the extra codec installer.

## Nearest-thing table (for the "not possible" answers)

| Asked for | Offer instead |
|---|---|
| browser-based delivery | SightLab 3 Standalone, or a packaged Vizard executable (`examples/PublishExe`) |
| eye tracking on a plain headset | head-direction dwell on the Desktop/SteamVR configuration, labelled as such |
| fluid or soft-body physics | rigid-body physics with pre-made animations |
| guaranteed sub-ms sync | BIOPAC markers at trial events plus frame timestamps |
