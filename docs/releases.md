---
created: 2026-11-03
author: Claude (Fable 5.1)
---

# Releasing the kit

A release is a dated version, a git tag on `main`, and two zips attached to the GitHub
release. Claude Code and claude.ai users update from the repository; ChatGPT and Codex users
get the version once it clears OpenAI's review. The repository's Codex marketplace
(`.agents/plugins/marketplace.json`) stays for internal testing only: `codex plugin marketplace
add worldviz/sightlab-ai-kit`, then `codex plugin marketplace upgrade worldviz` after each
release. Public instructions point Codex users to the directory.

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
     --title "SightLab AI Kit 2026.MM.N" --notes-file <notes>
   ```
   `openai-plugin.zip` is what the OpenAI directory submission takes
   (`docs/submission/openai-directory.md`); `chat-bundle.zip` is for a ChatGPT or claude.ai
   Project's files.
6. OpenAI directory: upload the zip as a new version (Sado; see the submission note).
   Claude directory, once listed: it follows `main`; each version is scanned and, because of
   the two large reference files, may be held for a reviewer, so check the portal.
7. Tell the users in a three-line email: version, what changed, the update command.

## What users do

- Claude Code: `claude plugin update sightlab@worldviz`, or nothing if auto-update is on.
- claude.ai: nothing when **Sync automatically** is on; otherwise **Check for updates**.
- ChatGPT and Codex: nothing; the directory serves the approved version.

The report and `REVIEW.md` carry the kit version, so support can see who is behind.
