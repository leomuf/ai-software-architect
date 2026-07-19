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
OUTPUT_PARENT = ROOT / "dist" / "codex"
OUTPUT = OUTPUT_PARENT / "ai-software-architect"
BUILD = ROOT / "build"
RUNTIME_NAME = "ai-architect-mcp.exe"
RUNTIME_DIR_NAME = "ai-architect-mcp"

SKILL_ORDER = (
    "orchestrate-architecture-workflow",
    "conduct-architecture-interview",
    "evaluate-architecture-options",
    "create-architecture-decisions",
    "prepare-coding-handoff",
    "review-architecture-conformance",
)
FOCUSED_SKILL_NAMES = ("evaluate-architecture-options",)

FOCUSED_OPTIONS_OPENAI_YAML = """interface:
  display_name: "Evaluate Architecture Options"
  short_description: "Compare architecture and design-pattern choices"
  default_prompt: >-
    Use $evaluate-architecture-options to compare credible options and ask me
    to choose.

policy:
  allow_implicit_invocation: false

dependencies:
  tools:
    - type: "mcp"
      value: "ai-software-architect-tools"
      description: "Read-only local contract and Python evidence tools"
      transport: "stdio"
"""

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
Codex entry contract: the plugin distributes this capability, but the workflow runs
only when the user explicitly invokes `$ai-software-architect`. A plugin `@` mention
does not replace the `$` skill invocation. For a direct pattern explanation or
implementation example, the user may instead invoke `$evaluate-architecture-options`.
Architecture advice and repository inspection are read-only by default. Unless the
user explicitly requests execution or modification, never import, execute, compile
(including `python -m py_compile`), launch, test, or build analyzed repository code.
Before any repository read, artifact discovery, language detection, or MCP call,
decide whether additional evidence could materially change the next response. When
the user's stated constraints are sufficient for proportionate guidance, use them as
explicit assumptions and do not inspect the active repository or call an MCP tool.
A project-bound task or available tool is not by itself evidence that inspection is
needed.
For an open "which pattern" request, compare three to five alternatives for one
decision with categorized links and ordinal `NN/100` fit before recommending; list
supporting patterns separately and ask the user to approve or revise.
Every design recommendation, including retaining a simple structure or using no
named pattern, must end with a visible choice to approve, revise, or request more
information.
End every `$ai-software-architect` final response with exactly one hidden outcome
marker: `<!-- ai-architect-outcome: clarify -->` when material input is needed,
`<!-- ai-architect-outcome: recommendation -->` when a decision awaits the user,
or `<!-- ai-architect-outcome: complete -->` when no architecture decision is
pending. A recommendation must also include exactly one
`<!-- ai-architect-actions: approve, revise, more-information -->` marker
immediately before visible, localized decision guidance, followed by its outcome
marker. The other outcomes must not include the action marker.
For generic architecture guidance, pattern explanations, or implementation examples,
use the routed skill reference directly and do not call MCP tools. Call MCP tools only
when the requested task actually requires repository evidence or artifact validation.
If platform or interface statements conflict materially, ask one focused clarification
and end the current turn without a recommendation or MCP call.
The bundled Codex control-plane hook is defense in depth: it reinforces explicit
routing, injects one explicitly matched bundled reference, blocks MCP operations that
are structurally outside a focused skill route, validates the focused option-
comparison rendering, and checks the complete workflow's stable outcome/action
markers once when the user has trusted it. It does not infer semantic workflow phases
from natural-language keywords. Correctness must not depend on hook availability.
For deterministic Python evidence in Codex, read only relevant workspace files with
native file tools. Prefer bounded `dependency_statements` for routine static import
scans; use `source_files` when full AST context or higher assurance matters. The Codex
MCP surface accepts no workspace root and exposes no ADR-listing tool. Inspect
`.ai-architect/` through host-native read-only tools.
Call `validate_complete_architecture_contract` only for a complete candidate, set
`validation_scope` to `complete-candidate-contract`, and inspect `result.valid` before
claiming validation succeeded.

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
        "--onedir",
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
    runtime = runtime_dist / RUNTIME_DIR_NAME
    executable = runtime / RUNTIME_NAME
    if not executable.is_file():
        raise FileNotFoundError(f"runtime build did not create {executable}")
    return runtime


def _copy_focused_skills() -> dict[str, str]:
    additional_sources: dict[str, str] = {}
    for name in FOCUSED_SKILL_NAMES:
        source = SKILLS_ROOT / name
        target = OUTPUT / "skills" / name
        shutil.copytree(source, target)
        agents = target / "agents"
        agents.mkdir(exist_ok=True)
        (agents / "openai.yaml").write_text(
            FOCUSED_OPTIONS_OPENAI_YAML,
            encoding="utf-8",
            newline="\n",
        )
        for path in sorted(source.rglob("*")):
            if path.is_file():
                additional_sources[_relative(path)] = (
                    target / path.relative_to(source)
                ).relative_to(OUTPUT).as_posix()
    return additional_sources


def assemble(runtime: Path, *, plugin_version: str | None = None) -> Path:
    output_resolved = OUTPUT.resolve()
    expected_parent = OUTPUT_PARENT.resolve()
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
    additional_sources = _copy_focused_skills()

    manifest = OUTPUT / ".codex-plugin" / "plugin.json"
    manifest.parent.mkdir(parents=True)
    shutil.copyfile(TEMPLATES / "plugin.json", manifest)
    manifest_payload = json.loads(manifest.read_text("utf-8"))
    if plugin_version is not None:
        manifest_payload["version"] = plugin_version
    manifest.write_text(
        json.dumps(manifest_payload, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    shutil.copyfile(TEMPLATES / "mcp.json", OUTPUT / ".mcp.json")
    hooks = OUTPUT / "hooks"
    hooks.mkdir()
    shutil.copyfile(TEMPLATES / "hooks.json", hooks / "hooks.json")
    shutil.copyfile(ROOT / "LICENSE", OUTPUT / "LICENSE")
    shutil.copyfile(ROOT / "NOTICE", OUTPUT / "NOTICE")
    shutil.copyfile(ROOT / "THIRD_PARTY_NOTICES.md", OUTPUT / "THIRD_PARTY_NOTICES.md")
    assets = OUTPUT / "assets"
    assets.mkdir()
    shutil.copyfile(ROOT / "assets" / "codex-plugin-icon.png", assets / "logo.png")

    runtime_target = OUTPUT / "runtime" / "windows-x86_64" / RUNTIME_DIR_NAME
    runtime_target.parent.mkdir(parents=True)
    shutil.copytree(runtime, runtime_target)

    generated_files = sorted(path for path in OUTPUT.rglob("*") if path.is_file())
    provenance = {
        "schema_version": "1.0.0",
        "generator": "adapters/codex/build_plugin.py",
        "plugin_version": manifest_payload["version"],
        "source_to_output": dict(sorted(source_to_output.items())),
        "additional_source_to_output": dict(sorted(additional_sources.items())),
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
    parser.add_argument("--plugin-version")
    args = parser.parse_args()
    selected_modes = sum((args.runtime is not None, args.build_runtime))
    if selected_modes != 1:
        parser.error("use exactly one of --runtime or --build-runtime")
    runtime = _build_runtime() if args.build_runtime else args.runtime
    if runtime is None or not runtime.resolve().is_dir():
        parser.error("provide --runtime <reviewed one-directory runtime> or --build-runtime")
    print(
        assemble(
            runtime.resolve(),
            plugin_version=args.plugin_version,
        )
    )


if __name__ == "__main__":
    main()
