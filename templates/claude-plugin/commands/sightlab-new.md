---
description: Start a new SightLab 2.x experiment from a description, a paper, or a Fit Check brief
---

Use the `sightlab-2x` skill. The researcher's description follows this command (or ask for
it if empty): $ARGUMENTS

1. Run the scope guard against `register/cannot.md` and say which list the request is in.
2. Find the installed SightLab (`Find the install`) and report its version.
3. Assemble `brief/<study-name>.md` from `brief/TEMPLATE.md`; ask only the consequential
   questions; mark defaults `(assumed)`.
4. When design, procedure, responses, trials and hardware are settled, build the skeleton,
   run `"${CLAUDE_PLUGIN_ROOT}/skills/sightlab-2x/harness/check.py"` on it, and stop at the first
   headset checkpoint with `REVIEW.md`.
