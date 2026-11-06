---
description: Start a new SightLab 2 experiment from a description, a paper, or a Fit Check brief
---

Use the SightLab skill for this project's generation (today `sightlab-2`; its first section says how to tell). The researcher's description follows this command (or ask for
it if empty): $ARGUMENTS

1. When platform or integration constraints matter, consult `register/capabilities-and-custom-development.md`; explain relevant constraints and continue with feasible implementation work.
2. Find the installed SightLab (`Find the install`) and report its version.
3. Assemble `brief/<study-name>.md` from `brief/TEMPLATE.md`; ask only the consequential
   questions; mark defaults `(assumed)`.
4. When design, procedure, responses, trials and hardware are settled, build the skeleton,
   run `python "${CLAUDE_PLUGIN_ROOT}/skills/sightlab-2/harness/check.py" <script>` on it, and stop at the first
   headset checkpoint with `REVIEW.md`.
