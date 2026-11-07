"""The one permitted per-wrapper difference in SKILL.md: the "On this host" section (§6.5).

Inserted where a skill's SKILL.md has `<!-- host-section -->`. Keyed by skill, then by
wrapper: every skill folder under src/ needs all three wrappers here, or the build refuses
it (a skill must never ship with another skill's host text). Keep each short and factual.
`<kit>` in the skill text is the folder that holds SKILL.md; each section says what that is.
"""

HOST = {
    "sightlab-2": {
    "claude-plugin": """## On this host

You are running as the `sightlab-2` skill of the `sightlab` plugin. The
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

What you can run depends on this session's tools and environment, not on the app; check
them first. The static check needs the script, this plugin's folder and a Python 3.8+
interpreter (a sandbox with the files can run it); the Vizard test also needs a Windows
environment where you can run the installed SightLab 2 and Vizard 8. Run whichever you can.
For the rest, give the researcher the commands above to run on the SightLab PC, say which
checks were not performed (in `REVIEW.md` for a build), and never say a check ran when it did
not.
""",
    "openai-plugin": """## On this host

This plugin provides instructions and reference material for SightLab 2, plus the harness
under `harness/` in this skill's folder (`<kit>` is the folder that holds this SKILL.md).
Confirm the generation, then size the request (section 0). What you can run depends on the
tools and environment this session actually has, not on the product's name; check them
first. The two checks need different things:

<!-- openai-review-wording -->
- Static check: access to the script and this skill's folder, and a Python 3.8+
  interpreter. When you have them, run `python "<kit>/harness/check.py" <script>` after
  every edit.
- Vizard test: additionally a Windows environment where you can run the installed programs,
  with SightLab 2 and Vizard 8. When you have it and the researcher's permission, run
  `"C:\\Program Files\\WorldViz\\Vizard8\\bin\\winviz.exe" "<kit>/harness/autopilot.py" "<absolute path to script>"`
  once at the end of a simple build, or at the end of every build step otherwise (in
  PowerShell, prefix the quoted executable with `&`). Say what a run will check; before the
  first launch in a session ask, unless the request already asked for a run or a test.
- For any check you cannot run here: give the researcher the script and the command to run
  on the SightLab PC, or the installed kit (Claude Code:
  `claude plugin install sightlab --marketplace worldviz/sightlab-ai-kit`, then
  `/sightlab:check <script>`; Codex: install SightLab VR Assistant from the Codex app's
  Plugins page, ask it to check the script),
  ask them to paste the results back, and say clearly which checks were not performed.

Generated scripts target the researcher's own licensed SightLab/Vizard installation.
""",
    "chat-bundle": """## On this host

This is the chat bundle: the kit's content without its harness, so `check.py` and the
autopilot are not in these files and cannot be run from them.
Confirm the generation, then size the request (section 0). For a build, write the brief and
the script here. In every
`REVIEW.md` say which checks were not performed and ask the researcher to run them with the
installed kit:

- Claude Code: `claude plugin install sightlab --marketplace worldviz/sightlab-ai-kit`,
  then `/sightlab:check <script>`;
- Codex: install SightLab VR Assistant from the Codex app's Plugins page (search for it),
  then ask it to check the script,

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
