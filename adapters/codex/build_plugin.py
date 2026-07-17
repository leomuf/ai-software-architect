# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Reproducibly assemble the Codex Composite skill and plugin package."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = ROOT / "shared" / "skills"
TEMPLATES = ROOT / "adapters" / "codex" / "templates"
OUTPUT = ROOT / "dist" / "codex" / "ai-software-architect"
BUILD = ROOT / "build"
RUNTIME_NAME = "ai-architect-mcp.exe"

SKILL_ORDER = (
    "orchestrate-architecture-workflow",
    "conduct-architecture-interview",
    "evaluate-architecture-options",
    "create-architecture-decisions",
    "prepare-coding-handoff",
    "review-architecture-conformance",
)

GENERATED_FRONTMATTER = """---
name: ai-software-architect
description: >-
  Perform architecture-first analysis, compare credible options, obtain approval,
  create ADRs and an architecture contract, prepare coding handoffs, or review
  conformance. Use only when the user explicitly invokes the AI Software Architect
  for an architecture task.
license: MIT
---
<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# AI Software Architect

Use the user's Codex model for all reasoning. Never request a separate model API key.
Act as a direct, collaborative, educational architect; present material decisions
for approval and do not implement application code in this role.

"""


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _skill_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"skill frontmatter missing: {_relative(path)}")
    _, _, body = text.split("---\n", 2)
    body = body.lstrip()
    if body.startswith("<!--"):
        _, separator, body = body.partition("-->")
        if not separator:
            raise ValueError(f"SPDX comment is not closed: {_relative(path)}")
        body = body.lstrip()
    if "TODO" in body:
        raise ValueError(f"unresolved placeholder: {_relative(path)}")
    return body.rstrip() + "\n"


def _copy_resources(destination: Path) -> dict[str, str]:
    provenance: dict[str, str] = {}
    seen: set[str] = set()
    for skill_name in SKILL_ORDER:
        skill_root = SKILLS_ROOT / skill_name
        skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        for resource_kind in ("references", "assets"):
            resource_root = skill_root / resource_kind
            if not resource_root.exists():
                continue
            for source in sorted(path for path in resource_root.iterdir() if path.is_file()):
                if source.name in seen:
                    raise ValueError(f"duplicate generated resource name: {source.name}")
                if f"({resource_kind}/{source.name})" not in skill_text:
                    raise ValueError(f"resource is not directly linked: {_relative(source)}")
                seen.add(source.name)
                target = destination / resource_kind / source.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                provenance[_relative(source)] = target.relative_to(OUTPUT).as_posix()
    return provenance


def _build_runtime() -> Path:
    runtime_dist = BUILD / "runtime"
    runtime_work = BUILD / "pyinstaller"
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        "ai-architect-mcp",
        "--distpath",
        str(runtime_dist),
        "--workpath",
        str(runtime_work),
        "--specpath",
        str(BUILD),
        str(ROOT / "adapters" / "codex" / "runtime_entry.py"),
    ]
    subprocess.run(command, cwd=ROOT, check=True)  # noqa: S603
    executable = runtime_dist / RUNTIME_NAME
    if not executable.is_file():
        raise FileNotFoundError(f"runtime build did not create {executable}")
    return executable


def assemble(runtime: Path) -> Path:
    output_resolved = OUTPUT.resolve()
    expected_parent = (ROOT / "dist" / "codex").resolve()
    if output_resolved.parent != expected_parent or output_resolved.name != "ai-software-architect":
        raise ValueError("refusing to replace an unexpected output directory")
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)

    skill_output = OUTPUT / "skills" / "ai-software-architect"
    skill_output.mkdir(parents=True)
    sections = [GENERATED_FRONTMATTER]
    source_to_output: dict[str, str] = {}
    for name in SKILL_ORDER:
        source = SKILLS_ROOT / name / "SKILL.md"
        sections.append(f"\n---\n\n## Canonical module: `{name}`\n\n")
        sections.append(_skill_body(source))
        source_to_output[_relative(source)] = "skills/ai-software-architect/SKILL.md"
    generated_skill = skill_output / "SKILL.md"
    generated_skill.write_text("".join(sections), encoding="utf-8", newline="\n")
    if len(generated_skill.read_text(encoding="utf-8").splitlines()) > 500:
        raise ValueError("generated Composite SKILL.md exceeds 500 lines")

    source_to_output.update(_copy_resources(skill_output))
    agents = skill_output / "agents"
    agents.mkdir()
    shutil.copyfile(TEMPLATES / "openai.yaml", agents / "openai.yaml")

    manifest = OUTPUT / ".codex-plugin" / "plugin.json"
    manifest.parent.mkdir(parents=True)
    shutil.copyfile(TEMPLATES / "plugin.json", manifest)
    shutil.copyfile(TEMPLATES / "mcp.json", OUTPUT / ".mcp.json")
    shutil.copyfile(ROOT / "LICENSE", OUTPUT / "LICENSE")
    shutil.copyfile(ROOT / "NOTICE", OUTPUT / "NOTICE")
    shutil.copyfile(ROOT / "THIRD_PARTY_NOTICES.md", OUTPUT / "THIRD_PARTY_NOTICES.md")
    assets = OUTPUT / "assets"
    assets.mkdir()
    shutil.copyfile(ROOT / "assets" / "AISoftwareArchitect.png", assets / "logo.png")

    runtime_target = OUTPUT / "runtime" / "windows-x86_64" / RUNTIME_NAME
    runtime_target.parent.mkdir(parents=True)
    shutil.copyfile(runtime, runtime_target)

    generated_files = sorted(path for path in OUTPUT.rglob("*") if path.is_file())
    provenance = {
        "schema_version": "1.0.0",
        "generator": "adapters/codex/build_plugin.py",
        "source_to_output": dict(sorted(source_to_output.items())),
        "output_sha256": {
            path.relative_to(OUTPUT).as_posix(): _hash(path) for path in generated_files
        },
    }
    (OUTPUT / "provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    return OUTPUT


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path)
    parser.add_argument("--build-runtime", action="store_true")
    args = parser.parse_args()
    if args.runtime and args.build_runtime:
        parser.error("use either --runtime or --build-runtime")
    runtime = _build_runtime() if args.build_runtime else args.runtime
    if runtime is None or not runtime.resolve().is_file():
        parser.error("provide --runtime <reviewed executable> or --build-runtime")
    print(assemble(runtime.resolve()))


if __name__ == "__main__":
    main()
