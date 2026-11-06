# E-Learning Lab (overview)

Sources: the E-Learning Lab 1.6.3 folder (`E_Learning_Lab.py`, `e_learning_common.py`, the session
scripts, `global_config/globalConfig.py`, `slide_summary.py`, `headless_create.py`, `lms_bridge.py`);
help.worldviz.com/sightlab e-learning-lab pages (release notes up to 1.6.2), blender-e-learning-lab,
educational-interaction-tool; older 1.4.13 and 1.5.1 copies for comparison; `sightlab_utils` 2.9.3.

When to read: the researcher mentions E-Learning Lab, a VR lesson or presentation, a classroom or
instructor-led session; asks whether to use it or a SightLab script; or wants a lesson, its
quizzes, settings or data explained or changed.

## What it is

A WorldViz application built on SightLab 2 for VR lessons and presentations. An educator builds a
lesson without code in a desktop editor, as a sequence of slides (3D scenes, videos, 360 and 180
media, images, PowerPoint or PDF pages, quizzes), then runs it single-user, instructor-led with
clients in other headsets, or on a projection wall. Optional: an AI tutor avatar, AI generation of
content and whole lessons, proximity sensors, a recorded presenter avatar, eye tracking, SightLab
data saving and BIOPAC sync, face tracking, and an LMS link. It is for educators, trainers and
presenters, and for researchers who study learning with lesson content.

## E-Learning Lab or a SightLab script?

- E-Learning Lab: a sequence the presenter or learner steps through, authored by the researcher
  in the editor; quizzes; a classroom of headsets; an AI tutor.
- A SightLab script: conditions, randomisation, a response or rating per trial, trial-by-trial
  data, custom logic. E-Learning Lab changes slides inside one SightLab trial; per-slide measures
  come from its slide summary (below), not from trials. `examples/Model and Media Viewer` steps
  through models and media in code; lesson slides are model files a script can load.

## How it relates to SightLab 2

- Same installation: it lives in `Documents\Sightlab2\ELearning\E-Learning Lab`, runs in Vizard 8
  and imports the installed `sightlab_utils`; it has no package of its own. The Dashboard's Apps tab
  lists it only when that folder exists; the desktop shortcuts "E-Learning Lab" and "E-Learning Lab
  Client" open `E_Learning_Lab.py` and `E_Learning_Lab_Client.py`.
- Sessions are SightLab sessions. Single User is `sl.SightLab(gui=False)` with a hardware chooser.
  Instructor starts `E_Learning_Lab_Server.py` (a `SightLabServer`) and joins it as a
  `SightLabClient`; clients and the observer are `SightLabClient`s too (`guides/multi-user.md`).
- With Data Saving on it writes SightLab's standard layout (`<date>__experiment_data` with trial
  data, timeline and `.rply`; `guides/replay.md`, `rules/gaze-objects-and-data.md`) plus
  `<date>__slide_summary.csv`, the summary measures per slide visit. `DATA_FOLDER_LOCATION`
  picks the folder: `'ROOT'` (default, the app's `data/`) or `'PROJECT'` (`collections/<Project>/data`).
  `E_Learning_Lab_Replay.py` is SightLab's replay; with `'PROJECT'` it asks which project.
- Avatar replay needs SightLab 2.9.0 or later, SightLab Sync of the `shared` folder 2.9.3.

## Where things are (inside `E-Learning Lab`)

| Path | What it is |
|---|---|
| `E_Learning_Lab.py` | the editor (a Qt desktop app). Run Session writes the project name to `machineChoice.txt` and starts a session script in Vizard |
| `E_Learning_Lab_Single.py`, `_Instructor.py`, `_Server.py`, `_Client.py`, `_Client_Auto_Desktop.py`, `_Client_Auto_VR.py`, `_Client_Controller.py`, `_Observer.py` | the session scripts, one per role |
| `E_Learning_Lab_Replay.py`, `E_Learning_Lab_Single_Publish.py` | session replay; the single-user script used for publishing |
| `e_learning_common.py` | shared runtime (`SightLabManager`, `ELearningCommon`), with helpers `slide_summary.py`, `proximity_triggers.py`, `face_tracking_recorder.py`, `pocket_tts_engine.py` |
| `global_config/globalConfig.py` | app-wide settings; the editor's checkboxes write here |
| `AI_Enabled/AI_Agent/` | the AI tutor; its settings are `configs/AI_Agent_Config_Education.py` |
| `collections/<Project>/` | one folder per lesson |
| `Assets/` | the editor's asset bins (Environments, Objects, Avatars, Videos, 360, Images, Audio, Questions, Prompts, Instructions, Start_Points) |
| `data/`, `Exports/` | session data and quiz results (`'ROOT'`); projects zipped by Export |
| `keys/` | API keys as text files, saved from the Options tab |
| `local_vizconnect_configs/` | custom hardware (projection walls) |
| `shared/`, `E_Learning_Lab_WebXR.py` | lessons synced to other PCs; the Stand Alone (WebXR) runner |
| `headless_create.py`, `lms_bridge.py`, `lms_extension.py` | LMS integration: a lesson built without the GUI from a payload folder (`manifest.json`, `chapter_content.txt`, `quiz.csv`; the project keeps its `manifest.json` and loads its slides sorted), lessons started from `ell://` links |
| `E_Learning_Lab_Launcher.py` | run with the system Python; restarts the editor after a crash or the free Vizard's 5-minute limit |

`E_Learning_Lab - Backup.py`, `- upload-lesson.py` and `E_Learning_Lab_language.py` (a 1.3.9 editor)
are old copies nothing runs; `installer/`, `Utils/`, `controllers/`, `avatars/` hold set-up files and models.

## How a lesson is built

`collections/<Project>/` holds:

- One model per slide at the top level (`.osgb`, `.glb`, `.gltf` or `.fbx`), ordered by a
  two-digit prefix (`01_Heart`, `02_...`); the editor renumbers them when slides are reordered.
- Name suffixes set the slide type: `_360`, `_360_stereo`, `_180_stereo` (360 or 180 media),
  `_Large`, `_Large_stereo` (theatre screen), `_cast` (screen casting), `_Passthrough` (AR).
- Files named after the slide in `Videos/`, `Images/`, `Audio/` (a `.txt` there is read aloud),
  `Questions/`, `Prompts/`, `Knowledge/` and `Replays/` (an avatar replay `.rply` with its `.wav`
  and `.json`). Also `Objects/` (dropped models), `Sounds/` (proximity-sensor sounds),
  `3D_Model_Source_Files/`, and `data/` with `'PROJECT'`.
- Files the editor writes (headed "Auto-generated by E-Learning Lab"), among them
  `environment_objects.py` (per slide: Target, Grabbable, Hidden, Animate, Highlight, Spin, MoveTo,
  avatar state, proximity sensors in `proximity_dict`), `scene_transitions.py` (Key Press, Timer or
  Release Object), `scene_loop_video.py`, `scene_hide_avatar.py`, `project_settings.py` (loop,
  start points, the project's AI toggles).
- A quiz CSV has a header row, the question in the first column, one column per choice and a
  `Correct` column (`Question,Choices,,,Correct`); feedback mode (`QUIZ_FEEDBACK`) needs `Correct`,
  `<br>` breaks a line. A `.txt` quiz shows text pages split at blank lines. New quizzes go in
  `Assets/Questions` (the Questions bin).
- Start points are nodes in the slide model: `START_POINT_SINGLE`, `START_POINT_INSTRUCTOR`,
  `START_POINT_CLIENT`, `START_POINT_AI_AGENT` (markers in `scene_objects/`); a client with a suffix
  uses SightLab's `SIGHTLAB_START_POINT_<suffix>`; Blender scenes use `START_POINT_SINGLE_start`.

| Layer | What | Who |
|---|---|---|
| GUI | projects, slides and their order, placing objects and proximity zones (Scene Editor; Inspector, or Blender in Stand Alone Mode), object checkboxes, AI generation, sharing, Export, Run Session, API keys | the researcher |
| Config | `globalConfig.py` (`SAVE_DATA`, `DATA_FOLDER_LOCATION`, `SAVE_SLIDE_SUMMARY`, `BIOPAC_ON`, `RECORD_MIC_AUDIO`, `RECORD_FACE_TRACKING`, `AUTO_PLAY_VIDEOS`, `STEREO_VIDEO_FORMAT`, `QUIZ_FEEDBACK`, `LESSON_SOURCE`, `LOCAL_VIZCONNECT`, `PROXIMITY_DEBUG`, `USE_LMS_HOOK`); `AI_Agent_Config_Education.py` (`AI_MODEL`, `SPEECH_MODEL`, `IMAGE_PROVIDER`, `POCKET_TTS_VOICE`); quiz, prompt and knowledge files | an agent, with the editor closed |
| Code | the session scripts and `e_learning_common.py` | an agent, as a local change the researcher knows about |

## Features and the page that covers each (in `e-learning-lab/`)

- Placing objects, start points, avatars: `scene-editor.md`. Media and casting: `building-a-new-lesson.md`.
- AI tutor (ChatGPT, Claude, Gemini, Ollama; speech in and out): `ai-intelligent-agent.md`.
- Facts on a pointed-at object: `interactive-object-info.md`. NPC avatars: `adding-npc-avatar-agents.md`.
- AI-generated media, models, avatars: `ai-content-generation.md`. Lesson from a topic: `presentation-lesson-generator.md`.
- AR passthrough: `augmented-reality.md`. Proximity sensors (1.6.1+): `proximity-sensors.md`.
- A recorded presenter replayed as an avatar (1.6.0+): `avatar-replay.md`. Quizzes: `quizzes.md`.
- Multi-user and VPN: `sharing-multi-resources.md`, `connecting-over-separate-networks-using-a-vpn.md`.
- Data logging, replay, microphone, BIOPAC: `data-logging-and-replay.md`. WebXR: `stand-alone-mode-experimental.md`.
- No docs page yet: slide summary, face tracking, LMS link; read `globalConfig.py` and the module headers.

## What an agent can do

- Plan which slides, media and quizzes a brief needs (the researcher builds them), or read a
  project folder and summarise its slides, types, targets, sensors, transitions and quizzes.
- Write or fix quiz CSVs, prompt `.txt` files and `_knowledge` files.
- Change settings in `globalConfig.py` or the AI config while the editor is closed.
- Analyse session data as any SightLab data, per slide from the slide summary
  (`guides/analysis-and-visualization.md`).
- Customise a session script, for example also mark the slide in the trial data's flag column with
  `sightlab.setCustomTrialData(elearning_common.get_environment_name())` after each swap.

Leave to the researcher: the GUI row above, installs (`basic-installation.md`), API keys, sync,
LMS and network set-up, and every test in a headset. AI-generated content is a draft they review.

## Gotchas

- `keys/` holds live API keys: never open, quote, copy or share those files.
- The docs say `mediaConfig.py` for `AUTO_PLAY_VIDEOS` and `STEREO_VIDEO_FORMAT`; the session
  scripts read `global_config/globalConfig.py`. The root `mediaConfig.py` is a leftover.
- The editor rewrites its files. It matches config lines as `KEY = value`; the project files are
  keyed by slide file name, so renaming or renumbering slides by hand breaks them.
- Opening a project copies its AI toggles from `project_settings.py` into
  `AI_Agent_Config_Education.py` (`USE_AI`, `USE_SPEECH_RECOGNITION`, `USE_INTERACTIVE_OBJECT_INFO`,
  `SHOW_OBJECT_LABELS`, `USE_SCENE_AVATAR`, `SCENE_AVATAR_NAME`), overwriting hand edits there.
- The trial data's flag column names the slide only with BIOPAC on; use the slide summary
  (`SAVE_SLIDE_SUMMARY`, needs Data Saving). Quiz results (`<date-time>_<Project>_quiz.csv`) go to
  the data folder even with Data Saving off.
- With `'PROJECT'` data, Export zips the project with its participant data, and deleting the
  project deletes the data.
- Importing `e_learning_common` changes SightLab in that process (it replaces the hardware lists
  and wraps the experiment-summary writer); never import it into an ordinary SightLab script.
- Local Hardware Configs (`LOCAL_VIZCONNECT`) maps fixed names to fixed files in
  `e_learning_common.py`; a new vizconnect file is used only under one of those file names (for
  example as `vizconnect_config_projection.py`), not just by being in the folder.
- Stand Alone Mode (WebXR, hidden unless `ENABLE_STAND_ALONE = True`) serves lessons from the
  system Python, not Vizard; it skips `.osgb` slides and has no AI agent, eye tracking or position
  data. Published builds have no AI agent or speech recognition.
- With `USE_LMS_HOOK` on, `q` no longer ends single-user sessions. A session script run on its own
  reads `machineChoice.txt` or asks for the project.
- Older installs: read `VERSION_NUMBER` in `E_Learning_Lab.py`. A 1.5 install has no proximity
  sensors, avatar replay, Record Microphone, per-project data, slide summary, Pocket TTS or the
  keys `LESSON_SOURCE`, `RECORD_MIC_DEVICE`, `PROXIMITY_DEBUG`.

## Docs map (`sightlab/e-learning-lab/`)

| Need | Pages |
|---|---|
| Start | `index.md`, `basic-installation.md`, `building-a-new-lesson.md`, `release-notes.md` |
| Edit slides | `scene-editor.md`, `inspector-3d-scene-builder.md`, `proximity-sensors.md` |
| Content | `getting-3d-models-and-assets.md`, `sketchfab-integration.md`, `slideshows-powerpoint-and-pdf.md`, `converting-monoscopic-images-to-stereo.md`, `quizzes.md` |
| AI | `ai-intelligent-agent.md`, `interactive-object-info.md`, `setting-the-language.md`, `ai-content-generation.md`, `offline-image-generation.md`, `presentation-lesson-generator.md` |
| Avatars | `included-avatars.md`, `adding-your-own-custom-avatars.md`, `adding-npc-avatar-agents.md`, `avatar-replay.md` |
| Run | `running-a-session-single-user.md`, `running-a-session-as-instructor.md`, `running-a-session-as-a-client.md`, `running-on-a-projection-wall.md`, `controls.md` |
| Multi-user | `sharing-multi-resources.md`, `multi-user-voice-options.md`, `connecting-over-separate-networks-using-a-vpn.md` |
| Data, hardware | `data-logging-and-replay.md`, `custom-hardware-configurations.md`, `augmented-reality.md` |
| Distribute | `publishing-as-an-exe.md`, `stand-alone-mode-experimental.md`, `../blender-e-learning-lab.md` |
| Not E-Learning Lab | `../educational-interaction-tool.md`: the SightLab example `examples/Education_Application_AI` |
