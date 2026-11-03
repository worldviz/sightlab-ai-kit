#!/usr/bin/env python3
"""Build the public wrappers from src/ (design §6.7) and the repo's two marketplace manifests.

  dist/claude-plugin/     Claude Code / claude.ai plugin: manifest, commands, README, LICENSE, skills/sightlab-2x/
  dist/openai-plugin/     the SightLab VR Assistant (ChatGPT/Codex) layout, next version; harness included
  dist/openai-plugin.zip  the same folder zipped, as the OpenAI directory submission wants it
  dist/starter-project/   a project template: CLAUDE.md, AGENTS.md, README, brief/; no copy of the kit
  dist/chat-bundle.zip    the content only, for claude.ai Projects and ChatGPT Projects
  dist/BUILD.json         version, date, sightlab_utils version, every file with its sha256
  <repo>/.claude-plugin/marketplace.json and <repo>/.agents/plugins/marketplace.json
                          the marketplaces Claude Code, claude.ai and Codex install from (github: worldviz/sightlab-ai-kit)

Rules enforced here: outputs are built from allowlists (tools/allowlists.py), never by
copying a folder; a secrets scan runs over every output; a fenced block longer than
MAX_FENCED_LINES fails the build; every wrapper's
skill text equals src/SKILL.md apart from the front matter and the generated "On this
host" section (tools/host_sections.py).

Usage: build_kit.py --version 2026.11.0 [--out dist]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import zipfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from allowlists import ALLOW, MAX_FENCED_LINES, MAX_PY_LINES, PY_HEADER  # noqa: E402
from host_sections import HOST  # noqa: E402

KIT = Path(__file__).resolve().parents[1]
HOST_MARKER = "<!-- host-section -->"
FRONT_RE = re.compile(r"^---\n(.*?)\n---\n?", re.S)
HOST_SECTION_RE = re.compile(r"^## On this host\n.*?(?=^## |\Z)", re.S | re.M)
FENCE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.S)
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\b(api[_-]?key|secret|token)\s*[:=]\s*['\"][^'\"]{12,}['\"]"),
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),
]
TEXT_SUFFIXES = {".md", ".json", ".py", ".yaml", ".yml", ".txt", ".csv", ".cfg", ".ini"}


class BuildError(Exception):
    pass


class SecretsFound(BuildError):
    pass


class ContentShape(BuildError):
    pass


# ----------------------------------------------------------------------------- skill text

def _lf(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def skill_body(text: str) -> str:
    """The comparable part of a SKILL.md: no front matter, no host section, no marker, LF only."""
    t = _lf(text)
    t = FRONT_RE.sub("", t, count=1)
    t = HOST_SECTION_RE.sub("", t)
    t = t.replace(HOST_MARKER, "")
    return re.sub(r"\n{3,}", "\n\n", t).strip() + "\n"


def substitute(text: str, info: dict) -> str:
    return text.replace("{{SIGHTLAB_VERSION}}", info["sightlab_utils_version"]).replace("{{KIT_DATE}}", info["date"])


def render_skill(src_text: str, wrapper: str, skill_name: str, info: dict) -> str:
    t = substitute(_lf(src_text), info)
    m = FRONT_RE.match(t)
    if not m:
        raise BuildError("src/SKILL.md has no front matter")
    front = re.sub(r"^name:.*$", f"name: {skill_name}", m.group(1), flags=re.M)
    body = t[m.end():]
    if body.count(HOST_MARKER) != 1:
        raise BuildError("src/SKILL.md must contain exactly one host-section marker")
    body = body.replace(HOST_MARKER, HOST[wrapper].strip() + "\n")
    return f"---\n{front}\n---\n{body}"


# ----------------------------------------------------------------------------- selection

def _allowed_files(src: Path, wrapper: str) -> list[Path]:
    files: list[Path] = []
    for pattern in ALLOW[wrapper]:
        files += [p for p in sorted(src.glob(pattern)) if p.is_file()]
    return files


def _guard_shape(path: Path, text: str) -> None:
    """Content the kit writes must keep its shape; reference/ carries the real source and is exempt."""
    if "reference" in path.parts:
        return
    for block in FENCE_RE.findall(text):
        if block.count("\n") > MAX_FENCED_LINES:
            raise ContentShape(f"{path}: fenced block of {block.count(chr(10))} lines exceeds {MAX_FENCED_LINES}; that is a script dump, not a pattern")
    if path.suffix == ".py" and "harness" not in path.parts:
        # Shipped scripts are curated copies of examples: short, and headed with their source.
        if not text.startswith(PY_HEADER):
            raise ContentShape(f"{path}: curated .py files must start with '{PY_HEADER}' (use tools/curate_examples.py)")
        if text.count("\n") > MAX_PY_LINES:
            raise ContentShape(f"{path}: {text.count(chr(10))} lines exceeds {MAX_PY_LINES}; a curated example is short")


def _scan_secrets(path: Path, text: str) -> None:
    for pat in SECRET_PATTERNS:
        m = pat.search(text)
        if m:
            raise SecretsFound(f"{path}: looks like a secret ({pat.pattern[:30]}…)")


def _copy_content(src: Path, dest_root: Path, wrapper: str, skill_name: str, info: dict) -> list[Path]:
    written: list[Path] = []
    for path in _allowed_files(src, wrapper):
        rel = path.relative_to(src)
        out = dest_root / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
            _guard_shape(path, text)
            if rel.as_posix() == "SKILL.md":
                text = render_skill(text, wrapper, skill_name, info)
            else:
                text = substitute(_lf(text), info)
            _scan_secrets(out, text)
            out.write_text(text, encoding="utf-8", newline="\n")
        else:
            shutil.copyfile(path, out)
        written.append(out)
    return written


def _copy_template(templates: Path, name: str, dest: Path, info: dict) -> list[Path]:
    written: list[Path] = []
    root = templates / name
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.name != "README-manifest.md"):
        out = dest / path.relative_to(root)
        out.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix in TEXT_SUFFIXES or path.name in (".gitignore",):
            text = substitute(_lf(path.read_text(encoding="utf-8")), info).replace("{{VERSION}}", info["version"])
            _scan_secrets(out, text)
            out.write_text(text, encoding="utf-8", newline="\n")
        else:
            shutil.copyfile(path, out)
        written.append(out)
    return written


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


MARKETPLACE_NAME = "worldviz"
MARKETPLACE_REPO = "worldviz/sightlab-ai-kit"


def write_marketplaces(root: Path, dist_name: str, version: str, openai_name: str, openai_display: str) -> None:
    """The repo root is a marketplace for both ecosystems (read 2026-11-03 from code.claude.com/docs/en/plugins/
    marketplace-reference and learn.chatgpt.com/docs/plugins): Claude Code, claude.ai and Codex each add
    `worldviz/sightlab-ai-kit` once and install from it."""
    claude = {
        "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
        "name": MARKETPLACE_NAME,
        "description": "WorldViz plugins: the SightLab 2.x AI Kit for building and testing SightLab (Vizard) experiments.",
        "owner": {"name": "WorldViz", "url": "https://www.worldviz.com"},
        "plugins": [{
            "name": "sightlab-2x",
            "source": f"./{dist_name}/claude-plugin",
            "description": "Build, check and test WorldViz SightLab 2.x (Vizard) eye-tracking experiments from a research brief.",
            "version": version,
            "category": "Science",
            "tags": ["sightlab", "vizard", "vr", "eye-tracking", "experiment"],
        }],
    }
    codex = {
        "name": MARKETPLACE_NAME,
        "interface": {"displayName": "WorldViz"},
        "plugins": [{
            "name": openai_name,
            "source": {"source": "local", "path": f"./{dist_name}/openai-plugin"},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Developer Tools",
            "interface": {"displayName": openai_display},
            "version": version,
        }],
    }
    for rel, data in ((".claude-plugin/marketplace.json", claude), (".agents/plugins/marketplace.json", codex)):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")


# ----------------------------------------------------------------------------- build

def build(src: Path, templates: Path, out: Path, version: str, base_plugin: Path) -> dict:
    src, templates, out, base_plugin = Path(src), Path(templates), Path(out), Path(base_plugin)
    api = json.loads((src / "api" / "sightlab-api.json").read_text(encoding="utf-8"))
    info = {"version": version, "date": date.today().isoformat(), "sightlab_utils_version": api["sightlab_utils_version"]}
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    files: dict[str, dict[str, str]] = {}

    # claude-plugin
    cp = out / "claude-plugin"
    _copy_template(templates, "claude-plugin", cp, info)
    _copy_content(src, cp / "skills" / "sightlab-2x", "claude-plugin", "sightlab-2x", info)

    # openai-plugin: the existing listing's manifest and display files, next version
    op = out / "openai-plugin"
    manifest = json.loads((base_plugin / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    manifest["version"] = version
    manifest.setdefault("extensions", {}).setdefault("com.openai", {})["publication"] = {
        "release_notes": f"Kit {version}: skill, rules, patterns, API map, reference source and the test harness, generated from sightlab_utils {info['sightlab_utils_version']}."
    }
    (op / ".codex-plugin").mkdir(parents=True)
    (op / ".codex-plugin" / "plugin.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    for rel in ("assets/gpt-icon.png", "skills/instructions/agents/openai.yaml"):
        srcf = base_plugin / rel
        if srcf.is_file():
            (op / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(srcf, op / rel)
    _copy_template(templates, "openai-plugin", op, info)
    _copy_content(src, op / "skills" / "instructions", "openai-plugin", "instructions", info)
    with zipfile.ZipFile(out / "openai-plugin.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(op.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(op).as_posix())

    # starter-project: a template only; the kit is the installed plugin
    sp = out / "starter-project"
    _copy_template(templates, "starter-project", sp, info)
    for name in ("TEMPLATE.md", "EXAMPLE-gaze-dwell.md"):
        (sp / "brief").mkdir(parents=True, exist_ok=True)
        text = substitute(_lf((src / "brief" / name).read_text(encoding="utf-8-sig")), info)
        (sp / "brief" / name).write_text(text, encoding="utf-8", newline="\n")

    write_marketplaces(out.parent, out.name, version, manifest["name"], manifest["interface"]["displayName"])

    # chat-bundle.zip
    cb = out / "_chat-bundle"
    _copy_content(src, cb / "sightlab-2x", "chat-bundle", "sightlab-2x", info)
    with zipfile.ZipFile(out / "chat-bundle.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(cb.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(cb).as_posix())
    shutil.rmtree(cb)

    # identity check across wrappers
    bodies = {
        "claude-plugin": skill_body((cp / "skills" / "sightlab-2x" / "SKILL.md").read_text(encoding="utf-8")),
        "openai-plugin": skill_body((op / "skills" / "instructions" / "SKILL.md").read_text(encoding="utf-8")),
    }
    with zipfile.ZipFile(out / "chat-bundle.zip") as z:
        bodies["chat-bundle"] = skill_body(z.read("sightlab-2x/SKILL.md").decode("utf-8"))
    expected = skill_body(substitute(_lf((src / "SKILL.md").read_text(encoding="utf-8-sig")), info))
    for name, body in bodies.items():
        if body != expected:
            raise BuildError(f"{name}: skill text differs from src/SKILL.md beyond the host section")

    for wrapper in ("claude-plugin", "openai-plugin", "starter-project"):
        root = out / wrapper
        files[wrapper] = {p.relative_to(root).as_posix(): _sha(p) for p in sorted(root.rglob("*")) if p.is_file()}
    with zipfile.ZipFile(out / "chat-bundle.zip") as z:
        files["chat-bundle"] = {n: hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}
    result = {**info, "skill_body_sha256": hashlib.sha256(expected.encode("utf-8")).hexdigest(), "files": files}
    (out / "BUILD.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8", newline="\n")
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--version", required=True)
    p.add_argument("--src", type=Path, default=KIT / "src")
    p.add_argument("--templates", type=Path, default=KIT / "templates")
    p.add_argument("--out", type=Path, default=KIT / "dist")
    p.add_argument("--base-plugin", type=Path, default=KIT / "SightLab-VR-Assistant-0.80.6")
    a = p.parse_args(argv)
    try:
        info = build(a.src, a.templates, a.out, a.version, a.base_plugin)
    except BuildError as e:
        print(f"BUILD FAILED: {e}", file=sys.stderr)
        return 1
    n = sum(len(v) for v in info["files"].values())
    print(f"kit {info['version']} from sightlab_utils {info['sightlab_utils_version']}: {n} files across the wrappers -> {a.out}; marketplaces in {a.out.parent}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
