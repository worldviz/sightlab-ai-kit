---
created: 2026-11-03
author: Claude (Fable 5.1)
---

# Releasing the kit

A release is a dated version, a git tag on `main`, and two zips attached to the GitHub
release. Claude Code, claude.ai and Codex users update from the repository; ChatGPT users
get the version once it clears OpenAI's review.

## Steps

1. Edit `src/` (and `templates/` for wrapper files). Keep `docs/CHANGELOG.md` current.
2. Tests, lint, build, validate:
   ```
   .venv/bin/python -m pytest tools/tests -q
   .venv/bin/python tools/lint_kit.py
   .venv/bin/python tools/build_kit.py --version 2026.MM.N
   claude plugin validate ./dist/claude-plugin && claude plugin validate .
   ```
   The build stamps the version into both plugin manifests, both marketplace manifests and
   the templates. Raise it with every release; both ecosystems key updates on it.
3. When the harness or a rule changed, rerun the evals on the VM (`docs/evals/README.md`)
   and add the rows to the month's scoreboard.
4. Commit `src/`, `templates/`, `dist/` and the manifests together; push `main`.
5. Tag and release:
   ```
   git tag v2026.MM.N && git push origin v2026.MM.N
   gh release create v2026.MM.N dist/openai-plugin.zip dist/chat-bundle.zip \
     --title "SightLab 2.x AI Kit 2026.MM.N" --notes-file <notes>
   ```
   `openai-plugin.zip` is what the OpenAI directory submission takes
   (`docs/submission/openai-directory.md`); `chat-bundle.zip` is for a ChatGPT or claude.ai
   Project's files.
6. OpenAI directory: upload the zip as a new version (Sado; see the submission note).
   Claude directory, once listed: nothing to do, it follows `main`.
7. Tell the users in a three-line email: version, what changed, the update command.

## What users do

- Claude Code: `claude plugin update sightlab-2x@worldviz`, or nothing if auto-update is on.
- claude.ai: nothing when **Sync automatically** is on; otherwise **Check for updates**.
- Codex: `codex plugin marketplace upgrade worldviz`, then reinstall from `/plugins`.
- ChatGPT: nothing; the directory serves the approved version.

The report and `REVIEW.md` carry the kit version, so support can see who is behind.
