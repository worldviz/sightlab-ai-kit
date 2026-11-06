# Guides

Topic guides trimmed for an agent from the SightLab 2 documentation (help.worldviz.com/sightlab)
and the references the earlier assistant bundled. Each says when to read it, the calls
involved, the shipped examples, and the gotchas. None contains install steps: anything that
needs extra packages or keys is a WorldViz support conversation, not an agent action.

| Guide | Read it when |
|---|---|
| `first-project.md` | a new user makes a first project in the GUI, step by step (or the agent does it with computer use) |
| `instructions.md` | the study shows text or images to the participant at any point |
| `hardware.md` | the study names a headset, eye tracker or controller; the script picks the hardware; the data needs pupil size |
| `multi-user.md` | two or more participants share a scene; server and client scripts; shared state and events |
| `object-detection.md` | gaze on objects found automatically by AI detection rather than registered by hand |
| `inspector.md` | a 3D scene needs editing: gaze-object groups, regions of interest, the starting point, lighting, textures |
| `replay.md` | the researcher wants to see a session again, heatmaps, or custom flags in the replay |
| `dashboard.md` | the project must appear in, or be launched from, the SightLab Dashboard |
| `virtual-screen.md` | stimuli are 2D videos or images on a screen inside VR |
| `360-moving-regions.md` | a 360 video needs gaze data on something that moves; tracing, writing or fixing a region file |
| `driving.md` | the study is a driving task or uses the driving example as a base |
| `data-recorder.md` | the participant uses an external application (SteamVR, Unreal, a desktop app, a standalone headset app), not a SightLab scene; External Data Recorder 2.0 |
| `e-learning-lab.md` | E-Learning Lab: VR lessons and presentations built on SightLab; whether to use it or a SightLab script |
| `ai-agents.md` | a conversational avatar or AI character is part of the study |
| `analysis-and-visualization.md` | the researcher asks for charts, summaries, or analysis of the data files |

The data files themselves are described in `rules/gaze-objects-and-data.md`.
