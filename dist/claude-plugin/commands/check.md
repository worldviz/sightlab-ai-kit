---
description: Run the SightLab 2.x static checks (and the autopilot when available) on a script
---

Use the SightLab skill for this project's generation (today `sightlab-2x`; its first section says how to tell). Target script: $ARGUMENTS (default: the experiment script in
this project).

1. Run `python "${CLAUDE_PLUGIN_ROOT}/skills/sightlab-2x/harness/check.py" <script> --sightlab-utils "<installed package dir>"`
   and show the findings; fix every error; answer every warning from the brief.
2. If Vizard is installed, and neither the researcher nor a `NO_AUTOPILOT` file in the project
   folder says otherwise, say what the run will check, ask once before the first launch in
   this session, then run
   `"C:\Program Files\WorldViz\Vizard8\bin\winviz.exe" "${CLAUDE_PLUGIN_ROOT}/skills/sightlab-2x/harness/autopilot.py" "<absolute path to script>"`
   and summarise `autopilot-report.json`: verdict, interventions, assertions, `needs_human`.
3. Do not call the experiment working on a `smoke-passed` verdict; say what the harness had
   to do.
