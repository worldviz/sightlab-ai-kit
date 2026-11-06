"""The one permitted per-wrapper difference in SKILL.md: the "On this host" section (§6.5).

Inserted where a skill's SKILL.md has `<!-- host-section -->`. Keyed by skill, then by
wrapper: every skill folder under src/ needs all three wrappers here, or the build refuses
it (a skill must never ship with another skill's host text). Keep each short and factual.
`<kit>` in the skill text is the folder that holds SKILL.md; each section says what that is.
"""

HOST = {
    "sightlab-2": {
    "claude-plugin": """## On this host

You are running as the `sightlab-2` skill of the `sightlab` Claude Code plugin, with file and command access. The
kit's files live under the plugin root, not in the researcher's project: `<kit>` is
`${CLAUDE_PLUGIN_ROOT}/skills/sightlab-2`. Confirm the generation, then size the request (section 0); for a build
the checks are expected, not optional:

- `python "${CLAUDE_PLUGIN_ROOT}/skills/sightlab-2/harness/check.py" <script> --sightlab-utils "<installed package dir>"`
  after every edit (the package dir is in "Find the install"; any Python 3.8+ runs the
  checker, Vizard is not needed for it);
- `"C:\\Program Files\\WorldViz\\Vizard8\\bin\\winviz.exe" "${CLAUDE_PLUGIN_ROOT}/skills/sightlab-2/harness/autopilot.py" "<absolute path to script>"`
  once at the end of a simple build, or at the end of every build step otherwise (section 4);
  read `autopilot-report.json` in the run folder it names;
- `/sightlab:new`, `/sightlab:check` and `/sightlab:review`
  are shortcuts for the brief, the checks and the review note.

If you cannot run Windows programs here (claude.ai chat, Cowork, any non-Windows sandbox),
this is a chat: answer questions from the files, write the brief and the script, list the
checks you could not run, and give the researcher the two commands above to run on the
SightLab PC. Never say a check ran when it did not.
""",
    "openai-plugin": """## On this host

This plugin provides instructions and reference material for SightLab 2, plus the harness
under `harness/` in this skill's folder (`<kit>` is the folder that holds this SKILL.md).
Confirm the generation, then size the request (section 0). Whether this host may run the checks depends on the
product you are using and its permissions:

<!-- openai-review-wording -->
- in ChatGPT (no local files): you cannot run the checks; say so, and for a build ask the
  researcher to run them on the SightLab PC with the installed kit (Claude Code:
  `claude plugin install sightlab --marketplace worldviz/sightlab-ai-kit`, then
  `/sightlab:check <script>`; Codex: `codex plugin marketplace add
  worldviz/sightlab-ai-kit`, install the SightLab VR Assistant, ask it to check the script)
  and paste the results back;
- in Codex with command access and the researcher's permission: run the checks as the skill
  describes, from this skill's folder: `python "<kit>/harness/check.py" <script>` after every
  edit, and `"C:\\Program Files\\WorldViz\\Vizard8\\bin\\winviz.exe" "<kit>/harness/autopilot.py" "<absolute path to script>"`
  once at the end of a simple build, or at the end of every build step otherwise (in
  PowerShell, Codex's shell on Windows, prefix the quoted
  executable with `&`). Say what a run will check; before the first launch in a session ask, as a
  plain chat question, unless the request already asked for a run or a test.

Generated scripts target the researcher's own licensed SightLab/Vizard installation.
""",
    "chat-bundle": """## On this host

You are in a chat without access to the researcher's files or commands. Confirm the generation, then size the request
(section 0). For a build, write the brief and the script here; you cannot run
`check.py` or the experiment. In every `REVIEW.md` list the checks you could not run and ask
the researcher to run them with the installed kit:

- Claude Code: `claude plugin install sightlab --marketplace worldviz/sightlab-ai-kit`,
  then `/sightlab:check <script>`;
- Codex: `codex plugin marketplace add worldviz/sightlab-ai-kit`, install the SightLab VR
  Assistant from `/plugins`, then ask it to check the script,

and to paste the output back so you can fix what they find.
""",
    },
}


def host_section(skill: str, wrapper: str) -> str:
    """The "On this host" text for one skill on one wrapper; KeyError names the skill when it has none."""
    try:
        return HOST[skill][wrapper]
    except KeyError:
        raise KeyError(f"no host section for skill {skill!r} on {wrapper}") from None
