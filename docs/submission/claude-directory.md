---
created: 2026-11-03
author: Claude (Fable 5.1)
---

# Submitting to the Claude directory

Source read 2026-11-03: claude.com/docs/directory/publish, /docs/plugins/submit,
/docs/plugins/pre-submission-checklist. The directory lists plugins from a GitHub repository
and follows a branch; after the first review, new commits become new versions without a
resubmission. Listing is for discovery; our users can install from the marketplace without it.

## Who and where

- Portal: https://claude.ai/directory/manage, signed in to the WorldViz claude.ai
  organization on a paid plan (Pro, Max, Team or Enterprise). On Team/Enterprise an Owner
  submits. The first organization to submit a repository folder owns the listing.
- The GitHub account connected to that claude.ai organization must be able to push to
  `worldviz/sightlab-ai-kit`. The repository must be public before the listing goes live.

## What to enter

| Field | Value |
|---|---|
| Submission type | Plugin bundle |
| Repository | `worldviz/sightlab-ai-kit` |
| Plugin path | `dist/claude-plugin` |
| Branch or tag | `main` (every release lands there; a tag would need changing per release) |
| Listing name, description | read from `plugin.json` (`sightlab`, "Build, check and test WorldViz SightLab (Vizard) experiments from a research brief. Carries one skill per SightLab generation; SightLab 2 today.") and the plugin's `README.md` |
| Data handling | reads no personal data; stores nothing; sends nothing to any service; keeps nothing; not for under-18s |
| Compliance | contact email (support@ or Andy), four acknowledgements |
| New versions | GitHub push webhook (needs repo admin to install) or scheduled check |
| Auto-publish | on, once the reviewer allows it |

## What validation will say about this plugin

- `claude plugin validate ./dist/claude-plugin` passes (2026-11-03).
- README (≥ 40 words) and LICENSE are in the plugin folder. Both are generated from
  `templates/claude-plugin/`.
- **Expected hold:** `reference/sightlab.py` (635 KB) and `reference/viz.py` (371 KB) exceed
  the 256 KiB per-file limit, so the version is "held for a reviewer" with "Files or
  downloads the validator couldn't inspect". The README explains what they are. A reviewer
  clears it; it is not a rejection. Every later version raises the same hold until a
  reviewer stops applying it, so expect a delay per release unless auto-publish is granted.
- The listing icon is `dist/claude-plugin/.claude-plugin/icon.png` (512×512, the SightLab VR
  Assistant icon). The directory takes it from the first save or submission only and never
  changes it afterwards, so make sure it is the wanted one before the first **Validate**.
- No hooks, no MCP servers, no executables, no package launchers, no credentials.
- The skill tells Claude to run `python .../check.py` and `winviz.exe .../autopilot.py`; a
  script that SKILL.md only tells Claude to run is not part of the automated check. The
  README's "What it runs, sends and fetches" section is written for the security scan.

## Steps

1. Submit new > Plugin bundle > Source: repository, path, branch > **Validate**; fix any
   blocking finding in the repo, push, **Re-validate**.
2. Check the listing details (from `plugin.json` and the README).
3. Data handling, compliance, review and submit.
4. Watch **Submissions**; when the version passes or is cleared, **Publish**.
5. After listing: releases are commits to `main`; the portal's Versions tab shows each scan.

## Open for Andy

- Which claude.ai organization and account submit (listing ownership is permanent).
- The LICENSE wording in `templates/claude-plugin/LICENSE` is a draft, not legal review.
