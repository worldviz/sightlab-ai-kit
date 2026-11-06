# Conversational AI agents and avatars

Sources: the `AI_Intelligent_Agent` example (`AI_Agent.py`, `AI_Agent_GUI.py`,
`AI_Agent_Avatar.py`, `Config_Global.py`, `configs/`, `AI_Agents.py`) and `Scripted Avatar
Agent`, with SightLab 2.9.3; help.worldviz.com/sightlab ai-intelligent-agent,
ai-intelligent-agent-overview, ai-agent-overview. Where they differ, this follows the code.

When to read: the study has an avatar the participant talks to: an interviewer, a
confederate, a patient, a shopkeeper, or several agents in one scene. For avatars that only
stand, walk or play fixed animations, read `guides/avatar-agents.md`.

## What ships

`examples/AI_Intelligent_Agent`: an avatar that listens (speech recognition or typed text),
answers through a language model, speaks with a synthesised voice, and animates (talk and
idle states, mouth, head turned to the participant, expressions). `AI_Agent.py` (code mode)
and `AI_Agent_GUI.py` run one trial per conversation; the agent is `AI_Agent_Avatar.py`,
set by `Config_Global.py`, `configs/` (one per character) and `prompts/`.

## Wiring it into a SightLab script

Importing `AI_Agent_Avatar` does the set-up: it shows the startup dialogs, loads the avatar
config and the avatar, prepares the model, voice, microphone and keys, and schedules the
chat loop. The experiment registers the avatar and runs trials. `AI_Agent.py`, cut down:

```python
import sightlab_utils.sightlab as sl
from sightlab_utils.settings import *
from Config_Global import *
import AI_Agent_Avatar

sightlab = sl.SightLab(gui=False, pid=False)
sightlab.setTrialCount(TRIAL_COUNT)
sightlab.setEnvironment(vizfx.addChild(ENVIRONMENT_MODEL))
avatar = AI_Agent_Avatar.avatar          # code-loaded (USE_SCENE_AVATAR off)
sightlab.addSceneObject('avatar', avatar, gaze=True, avatar=True)

def sightLabExperiment():
    for i in range(TRIAL_COUNT):
        yield viztask.waitKeyDown(SET_CONTINUE_KEY)
        if USE_PER_TRIAL_PROMPTS:
            AI_Agent_Avatar._load_trial_prompt(sightlab.getTrialNumber())
        yield sightlab.startTrial()
        yield viztask.waitKeyDown(SET_CONTINUE_KEY)
        yield sightlab.endTrial()
        AI_Agent_Avatar.reset_speech_state()   # idle again if cut off mid-reply

viztask.schedule(sightlab.runExperiment)
viztask.schedule(sightLabExperiment)
```

- The shipped scripts pass `avatar=True` only (the avatar appears in the replay). Gaze and
  dwell on the agent need `gaze=True` as well, as in the `Scripted Avatar Agent` rating
  scripts (in GUI mode, or its gaze box ticked in the GUI).
- With `USE_SCENE_AVATAR`, the avatar is one placed in the environment in Inspector, found
  by `SCENE_AVATAR_NAME` after `startTrial` with
  `AI_Agent_Avatar.resolve_scene_avatar(sightlab, env)` (register what it returns; it falls
  back to `AVATAR_MODEL`). `AI_Agent_GUI.py` takes the first avatar in the GUI scene. An
  `avatarStandin` node in the environment places a code-loaded avatar (`avatarPlacer`).
- Talking: hold `START_SPEAKING_KEY` (`'c'`), or the button behind the vizconnect events
  `triggerDown`/`triggerUp`. With `HOLD_KEY_TO_SPEAK` off, `'c'` toggles listening and a
  pause of `SILENCE_THRESHOLD` ends the turn. In typed chat, `'c'` opens a text box and `q`
  closes it. `'h'` sends a screenshot to the model; `AI_Agent.py` binds it.
- Events: every finished audio clip sends `viz.getEventID('SpeechDone')`, and a reply is
  several clips; hook it with `vizact.addCallback`. `yield
  AI_Agent_Avatar.wait_for_interaction_limit()` waits for the exchange limit (below) and the
  end of the last reply.

## Configuration: `Config_Global.py`

By default every start asks, in dialogs, for the avatar config, speech recognition, prompt,
model, language and voice engine (`USE_AVATAR_CHOOSER`, `USE_DROPDOWN_OPTIONS`,
`USE_LANGUAGE_DROPDOWN`, `USE_TTS_DROPDOWN`, all True; last picks in `.last_choices.json`).
For a study turn them off and set the values here: the avatar is then `DEFAULT_AVATAR` and
the prompt `CHATGPT_PROMPT_FILE`, used for every model despite its name.

| Setting | Default | Notes |
|---|---|---|
| `AI_MODEL` | `'OFFLINE_OLLAMA'` | or `'CHAT_GPT'`, `'CLAUDE'`, `'Gemini'` (that spelling) |
| `OPEN_AI_MODEL`, `ANTHROPIC_MODEL`, `GEMINI_MODEL`, `OFFLINE_MODEL` | in the file | model names change; read them there. The Ollama model must already be pulled |
| `MAX_TOKENS`, `MAX_HISTORY_EXCHANGES` | 4096, 30 | Claude's reply cap; exchanges remembered |
| `SPEECH_MODEL` | `'Edge TTS'` | online, no key. Offline: `'Piper'`, `'Kokoro'`, `'Pocket TTS'`. Key: `'Open AI TTS'`, `'GPT Realtime'`, `'Eleven Labs'` |
| `USE_SPEECH_RECOGNITION`, `HOLD_KEY_TO_SPEAK`, `INTERRUPT_AI` | True | talking over the agent stops it |
| `SILENCE_THRESHOLD`, `MAX_SPEECH_DURATION` | 0.8, 12.0 | seconds |
| `WHISPER_MODEL`, `WHISPER_LANGUAGE` | `"base"`, `"en"` | local faster-whisper if installed, else Google's online recogniser (`GOOGLE_STT_LANGUAGE`) |
| `DEFAULT_LANGUAGE` | `'English'` | sets recognition, voices and a "respond only in" rule; Piper and Pocket TTS switch to Edge TTS |
| `TRIAL_COUNT`, `END_TEXT` | 1, `"Done. Thank you!"` | `AI_Agent.py`; the GUI sets its own |

Keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `ELEVENLABS_API_KEY`, read
from the environment, else from a key file in a `keys/` folder. Without one the single agent
quits; `AI_Agents.py` reads the environment only and falls back to Ollama. Edge TTS needs
the internet, no key. Ollama with Piper, Kokoro or Pocket TTS and faster-whisper is offline.

## Avatar configs

`configs/<Name>.py` is run into `AI_Agent_Avatar` at start and can override any global (the
shipped RocketBox configs set `USE_SCENE_AVATAR = False`). Copy `Template_Male.py` or
`Template_Female.py` and set `AVATAR_MODEL`, `AVATAR_POSITION`, `AVATAR_EULER`;
`IDLE_ANIMATION` and `TALK_ANIMATION` (state numbers from Inspector; for a scene avatar the
idle state must match the GUI's); `NECK_BONE`, `HEAD_BONE`, `SPINE_BONE` (head turning);
`MOUTH_OPEN_ID`, `SMILE_MORPH_ID`, `SAD_MORPH_ID`, `BLINK_ID` (`find_morph_indices.py`
lists an avatar's morphs); and the voices `EDGE_TTS_VOICE`, `PIPER_VOICE`, `KOKORO_VOICE`,
`POCKET_TTS_VOICE`, `OPEN_AI_VOICE`, `REALTIME_VOICE`, `ELEVEN_LABS_VOICE` (a voice in the
researcher's ElevenLabs account). A config named with a language (`RocketBoxFemale -
Greek`) speaks and listens in it. Swap the character by choosing another config; there is
one agent per session.

## Prompts, knowledge and events

`prompts/*.txt` is UTF-8 text; one file serves every model. Write it to the character ("You
are Tom, in his home office..."): the scene, what the character knows, the rules of the
scenario, and short spoken answers with no stage directions. The agent appends to any
prompt, including one swapped in mid-session: the event list (`Resources/event_info.py`,
`USE_BUILT_IN_EVENTS_AUTOMATICALLY`), every `.txt` and `.pdf` in `Knowledge/`
(`USE_KNOWLEDGE`), and the tone and language rules when they apply. A new prompt need not
list the events.

The model writes `event: smile` (or `sad`, `neutral`, `nod`, `shake`, `wave`, `screenshot`);
the agent runs it and strips the tag before speaking. `wave` only prints. A study's own
event is a function registered from the experiment script,
`AI_Agent_Avatar.EVENT_REGISTRY.register('lamp_off', lampOff)`, and described in the prompt.

## Structured trials

- `USE_PER_TRIAL_PROMPTS` with `TRIAL_PROMPTS = {2: "prompts/X.txt"}`: that trial starts
  with the new prompt and an empty history; trials without an entry keep both.
- `SCRIPT_CONDITIONS`: one condition drawn per session (`FORCE_CONDITION` pins it); it labels
  the trials and goes into the summary as `TrialCondition`. `CONTEXTUAL_PROMPT` with
  `CONTEXTUAL_PROMPT_FILES` picks the prompt by condition.
- `SCRIPTED_RESPONSES` with `SCRIPTED_RESPONSE_FILES` (trial to file, or to
  `{condition: file}`): no model call; each turn speaks the next line (blank and `#` lines
  skipped, the last repeats), events and tone tags still work. The reproducible option.
- `SET_NUMBER_OF_INTERACTIONS` with `NUMBER_OF_INTERACTIONS` (5) ends the trial after that
  many exchanges, once the reply is spoken; `SET_LAST_MESSAGE` adds `LAST_MESSAGE` first.

## Data

- The usual SightLab files, with gaze and dwell on the agent only if it is a gaze object.
- `SAVE_TRANSCRIPT = True` (default False) writes `[time] User:`, `Agent:` and `System:` lines
  to `Transcripts/transcript_<start>.txt` beside the script: one file per run, not per trial,
  not in the data folder. Match it to trials by time.
- `LOG_LATENCIES = True` writes model and voice timings to `TTS_Metrics/`; screenshots for the
  model go to `recordings/`. The multi-agent scripts write no transcript.

## Several agents; multi-user

`multi_agent_interaction.py` builds each agent with `AIAgent(config_path=..., name=...,
prompt_path=...)` and registers it with `addSceneObject`. The agents discuss
`LEADING_QUESTION` or speak a fixed `dialogue`; `'c'` and `'v'` address Agent1 and Agent2,
`'r'` restarts, `stop_conversation(agents)` resets them at trial end. Each config sets its
own `AI_MODEL` and voices; the engine is `'Open AI TTS'`, `'Edge TTS'`, `'Piper'` or
`'Pocket TTS'` (`MULTI_AGENT_SPEECH_MODEL`). Every agent adds model calls and cost.

No multi-user version ships (none among the multi-user examples): treat it as single-user.

## What the agent building the study must not do

- Install packages, download models or voices, pull Ollama models, run the Pocket TTS
  installer, or create API keys. That set-up is the researcher's or WorldViz support's,
  following the SightLab documentation page "AI Agent" (ai-intelligent-agent). Name in
  `REVIEW.md` what the study needs: provider and key, Ollama model, voice engine,
  faster-whisper.
- Open, print, copy or write anything in a `keys/` folder; leave it out of any copy.
- Promise latency or reliability of online models in a timed trial; measure it
  (`LOG_LATENCIES`).
- Treat the AI agent and a scripted one as interchangeable: only scripted lines give the same
  wording every session (`SCRIPTED_RESPONSES`, or `examples/Scripted Avatar Agent`, whose
  lines are voiced by OpenAI TTS by default).

## Gotchas

- The chat loop starts at import, not with a trial: the participant can talk before the first
  trial and between trials, and the history carries over unless the trial swaps the prompt.
- Dialog choices and avatar-config overrides live in `AI_Agent_Avatar`; read
  `AI_Agent_Avatar.USE_SCENE_AVATAR` and the like, not the `Config_Global` import.
- Under the autopilot each dialog takes its first option and the run is at best
  `smoke-passed`; it cannot talk or type to the agent and skips `keys/`. Say the
  conversation was not tested.
- Microphone and speakers are the Windows defaults, not set in the config. The talk button's
  `triggerDown`/`triggerUp` are in only some vizconnect files (`guides/hardware.md`).
- Bone names and morph indices must match the avatar; a wrong morph index silently moves
  another morph or none.
- Without Pocket TTS installed, the agent says so in the console and uses Edge TTS.
- `AI_Agent_GUI.py` sets every trial's start and end condition to none so Space does not race
  the script; keep that when adapting it.

## Shipped examples

`examples/AI_Intelligent_Agent`, `examples/Scripted Avatar Agent` (fixed lines, ratings,
STIM file), `examples/Adding_NPC` (avatars with no language model).
