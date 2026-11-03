"""What each public wrapper may contain, as globs relative to a skill folder under src/ (design §6.7).

A file not matched here does not ship, whatever else is in src/. Add a glob deliberately.
"""

# Content every wrapper carries: the skill and everything it points at.
CONTENT = [
    "SKILL.md",
    "rules/*.md",
    "patterns/*.md",
    "brief/*.md",
    "register/*.md",
    "guides/*.md",
    "api/sightlab-api.md",
    "api/sightlab-api.json",
    "api/undocumented.md",
    "api/resources.json",
    "api/resources.md",
    "examples/index.md",
    "examples/index.json",
    "examples/curated/*.py",
    "evals/README.md",
    "evals/*/brief.md",
    "evals/*/autopilot-assertions.json",
    "evals/*/acceptance.md",
    "reference/README.md",
    "reference/sightlab.py",
    "reference/viz.py",
    "reference/replay.py",
]

# The static checker, for hosts that can run commands. Never the fixtures or the spike.
HARNESS = [
    "harness/check.py",
    "harness/autopilot.py",
    "harness/autopilot_core.py",
    "harness/README.md",
]

ALLOW = {
    "claude-plugin": CONTENT + HARNESS,
    "openai-plugin": CONTENT + HARNESS + ["agents/openai.yaml"],  # Codex users install this one; the harness runs from its skill folder; openai.yaml is its UI metadata
    "starter-project": [],               # a project template: the kit is the installed plugin, never a copy
    "chat-bundle": CONTENT,
}

# Shape rules for content the kit writes itself (reference/ is the real source and is exempt).
MAX_FENCED_LINES = 200  # a "pattern" longer than this is a script dump, not a pattern
MAX_PY_LINES = 400      # a curated example longer than this is not curated (largest curated: ~140)
PY_HEADER = "# Source: ExampleScripts/"  # every curated example must start with this (tools/curate_examples.py writes it)
