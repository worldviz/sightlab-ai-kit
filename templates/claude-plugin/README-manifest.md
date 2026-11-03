# Claude plugin manifest: what was checked

`.claude-plugin/plugin.json` was written against the Claude Code plugin manifest reference,
https://code.claude.com/docs/en/plugins-reference, read on 2026-10-30. Points that matter:

- `name` is the only required field; kebab-case; every component is namespaced under it
  (`/sightlab:new`).
- `version`, `description`, `author` (`name` required; `email`, `url` optional), `homepage`
  (must parse as a URL), `repository`, `license`, `keywords` are recognised metadata.
  Unrecognised top-level keys are stripped with a warning.
- Skills live at `skills/<name>/SKILL.md` and are scanned by default; commands at
  `commands/*.md`. The docs prefer skills over commands for new plugins; the three commands
  here are thin shortcuts into the one skill.
- A `CLAUDE.md` at the plugin root is not loaded and draws a validation warning, so the
  plugin has none (the starter project, which is not a plugin, has one).
- `claude plugin validate <dir>` is the authoritative check; `tools/build_kit.py --validate`
  runs it when the `claude` CLI is present.

This file is not shipped.
