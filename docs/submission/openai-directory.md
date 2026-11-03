---
created: 2026-11-03
author: Claude (Fable 5.1)
---

# Submitting to the OpenAI plugin directory (ChatGPT and Codex)

Source read 2026-11-03: developers.openai.com/plugins/deploy/submission and
learn.chatgpt.com/docs/plugins. The listing is a ZIP uploaded per version; every version is
reviewed; one review can be active per plugin; the existing SightLab VR Assistant listing
(0.80.x, Sado) is updated by uploading the new ZIP under the same plugin name.

## Who

- Organization owners on the OpenAI platform, or members with **Apps Management Write**.
  Individual or business verification must be complete to publish under the WorldViz name.
  Sado submitted 0.80.x, so his account already has what is needed.

## The package

`dist/openai-plugin.zip` from the release. It is `dist/openai-plugin/` zipped: the
`.codex-plugin/plugin.json` manifest, `skills/sightlab-2/` (the kit, including `harness/`
and `reference/`), `assets/gpt-icon.png`, `README.md`, `LICENSE`.

Manifest facts (from `.codex-plugin/plugin.json`, carried over from 0.80.6 and re-stamped):

| Field | Value | Limit |
|---|---|---|
| `name` | `gpt-8fac8a955f2dc675005d97a73ee481f2` | the listing's stable id; do not change it |
| `version` | `2026.11.1` | explicit, raised per release |
| `interface.displayName` | SightLab VR Assistant | ≤ 30 |
| `interface.shortDescription` | Build SightLab VR experiments | ≤ 30 |
| `interface.longDescription` | from 0.80.6 | ≤ 4000; **revise**: it still says the plugin only provides instructions and reference files, and the kit now includes the harness |
| `interface.developerName` | Worldviz | ≤ 80 |
| `interface.category` | Developer Tools | from the dashboard's list |
| `interface.capabilities` | `["skills"]` | Codex, ≤ 20 |
| `interface.composerIcon`, `logo` | `./assets/gpt-icon.png` | square, ≥ 48 px |
| `websiteURL`, `supportURL`, `privacyPolicyURL`, `termsOfServiceURL` | help.worldviz.com / worldviz.com pages from 0.80.6 | all HTTPS |
| `extensions.com.openai.publication.release_notes` | written by the build | |

Skills-only plugins need no review test cases and no demo recording. No MCP server, no
hooks (lifecycle hooks are not eligible for the directory), no `.app.json`.

`skills/sightlab-2/agents/openai.yaml` (Codex UI metadata; `skills/instructions/` until 2026.11.2) carried a truncated
`short_description` from 0.80.6; it is fixed in this build ("Build SightLab VR experiments").

## What the reviewer will read

The execution wording. The skill's host section (`tools/host_sections.py`, marker
`<!-- openai-review-wording -->`) says that in ChatGPT the assistant cannot run anything and
asks the researcher to run the checks, and that in Codex, with command access and the
researcher's permission, it runs `check.py` and `winviz.exe ... autopilot.py` from the
plugin's skill folder and says what a run will check before launching. Sado owns the final
wording; the 0.80.x listing forbade execution outright, and this is the first version that
does not.

## Steps

1. Platform dashboard > the SightLab VR Assistant plugin > **Upload plugin to make changes**
   > `openai-plugin.zip`. Fix validation errors (the build already keeps the manifest valid).
2. Resolve **Metadata & Skills** findings; let the skill scans finish.
3. **Submit for review**; complete the policy attestations.
4. Watch **Review status**; feedback arrives by email. If rejected, fix, rebuild, upload again.
5. After approval, **Publish plugin**. Publishing an update replaces the previous version.

Community reports (2026) put review at days to weeks with no published timeline and no
expediting, so submit a version only when the content changed in a way web users need.

## Open for Sado and Andy

- The execution wording above.
- The long description text (4000 chars max) and whether the icon stays.
- `publication.countries` is unset (inherits the current listing's); set it if the dashboard asks.
