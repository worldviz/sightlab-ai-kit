# Conversational AI agents and avatars

Sources: help.worldviz.com/sightlab ai-agent-overview, ai-intelligent-agent; the earlier assistant's `ai-intelligent-agent.md`; `examples/index.md`.

When to read: the study has an avatar the participant talks to, an interviewer, a
confederate, a shopkeeper, a patient, or several agents in one scene.

## What ships

`examples/AI_Intelligent_Agent` places an avatar that listens (speech recognition or typed
text), answers through a language model, speaks with synthesised voice, and animates (lip
sync, head tracking toward the participant, expressions). Related: `examples/Scripted Avatar Agent`
(fixed lines and animations, no model, fully reproducible), `examples/Adding_NPC` (avatars that
walk and idle), and the `AI_Intelligent_Agent_Per_Trial` demo in the WorldViz demos folder
(a different personality or scenario per trial; ask WorldViz support for it).

Backends: OpenAI and Google models online (API key), or offline models through Ollama.
Voices: Kokoro (offline), OpenAI TTS, ElevenLabs (cloud, voice cloning). Vision: the agent
can be given what the participant sees. Events: the script can react to what is said.

## How a study configures an agent

1. A prompt file: personality, backstory, expertise, conversational style, and the rules of
   the scenario.
2. An avatar config: which model file, voice, animations, where it stands, whether it tracks
   the participant's head.
3. Adding the avatar to the scene in the experiment script, registered with
   `addSceneObject(..., gaze=True)` so gaze on the agent is recorded.
4. Optional knowledge base text the agent can draw on; per-trial prompts for structured
   studies, with context and history reset between trials.

Data: transcripts with timestamps, gaze and dwell on the agent, the usual SightLab files.

## What the agent building the study must not do

- Install packages, download models, or create API keys. The AI Agent example needs extra
  Python packages and keys set as environment variables; that set-up is the researcher's or
  WorldViz support's, following the SightLab documentation page. Say so in `REVIEW.md`.
- Promise latency or reliability of online models in a timed trial; measure it.
- Treat the scripted avatar and the AI agent as interchangeable: for a controlled study the
  scripted one is reproducible, the AI one is not.

## Gotchas

- Microphone and speaker devices are chosen in the config; the desktop autopilot cannot
  speak, so an AI-agent study is at best `smoke-passed` by the harness.
- Head tracking needs the avatar's bone names to match the config; custom avatars from
  Avaturn, ReadyPlayerMe, Mixamo, Rocketbox or Reallusion work when exported as the docs
  describe.
- Multi-agent scenes multiply the model calls and the cost.
