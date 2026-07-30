# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Reproducibly assemble the Codex Composite skill and plugin package."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
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
RUNTIME_NAME = "ai-architect-runtime.exe"
RUNTIME_DIR_NAME = "ai-architect-runtime"
AUTHORING_BUNDLE_OUTPUT = "assets/artifact-authoring-bundle.md"
AUTHORING_BUNDLE_SOURCES = (
    (
        "ADR authoring rules",
        SKILLS_ROOT / "create-architecture-decisions" / "references" / "adr-authoring.md",
    ),
    (
        "ADR template",
        SKILLS_ROOT / "create-architecture-decisions" / "assets" / "adr-template.md",
    ),
    (
        "Architecture contract example",
        SKILLS_ROOT
        / "create-architecture-decisions"
        / "assets"
        / "architecture-contract.example.yaml",
    ),
    (
        "Implementation plan template",
        SKILLS_ROOT
        / "prepare-coding-handoff"
        / "assets"
        / "implementation-plan-template.md",
    ),
)

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
  Review a current project, suggest and compare suitable design patterns or
  architecture styles, explain patterns with stored examples, obtain approval,
  create ADRs and an architecture contract, prepare coding handoffs, or review
  conformance. Use when the user explicitly invokes the AI Software Architect for
  an architecture task.
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
Codex entry contract: the plugin distributes this capability. The normal composer
entry is `$ai-software-architect`; a substantive request launched from the plugin
page carries Codex's explicit `@` plugin selection and is valid too. A plugin
selection without a request is incomplete. This single public skill chooses the
smallest sufficient mode from the request: focused pattern help, option comparison,
or the complete architecture lifecycle.
Route a definition, implementation example, or named-pattern explanation to focused
help without repository inspection, deterministic tools, or artifacts. Route an open choice among
architectures or patterns to option comparison. Route project analysis, approval,
decision recording, coding handoff, and conformance review to the complete lifecycle.
Architecture advice and repository inspection are read-only. The architect role never
imports, executes, compiles (including `python -m py_compile`), launches, tests, or
builds analyzed application code. Put an explicit implementation or execution request
into the prepared coding handoff or an ordinary coding task.
Before any repository read, artifact discovery, or language detection,
decide whether additional evidence could materially change the next response. When
the user's stated constraints are sufficient for proportionate guidance, use them as
explicit assumptions and do not inspect the active repository.
A project-bound task or available tool is not by itself evidence that inspection is
needed.
If platform or interface statements conflict materially, ask one focused clarification
and end the current turn without a recommendation or repository inspection.
For an open "which pattern" request, compare three to five alternatives for one
decision in the canonical six-column Markdown table, with categorized links and
ordinal `NN/100` fit before recommending. Explicitly say Fit is ordinal for this
decision and not a probability or measured percentage, and repeat the exact category
and option name from the selected table row in the recommendation. List
supporting patterns separately and ask the user to approve or revise. Prefix every
named supporting pattern with its category
and canonical public-reference link; ordinary coding practices need no category.
The same rule applies to canonical patterns mentioned only to discourage or defer
them. Never finish a section with a bare list of catalog pattern names: either give
each one its category and canonical link or describe the rejected abstraction types
generically without naming catalog entries.
Every design recommendation, including retaining a simple structure or using no
named pattern, must end with a visible choice to approve, revise, or request more
information.
The immediate answer to a clarification or decision request remains in this
workflow without another skill invocation. After approval of a project-bound
material decision, do not merely acknowledge approval: enter `record_and_handoff`
and safely create and validate the ADR, architecture contract, context, and coding
handoff. Preserve an explicit no-create/no-modify restriction, explain when a
projectless task cannot persist artifacts, and never treat architecture approval
as authorization to modify application code.
Return only user-facing Markdown. Never emit internal `ai-architect` control
markers or HTML comments because Codex may display them. Clarifications end with
their focused visible question. Open architecture or pattern selections use the
canonical six-section comparison contract. Every recommendation ends with
`## Your decision` and ordinary visible guidance asking the user to approve,
revise, or request more information. For a single recommendation, put the full
recommendation first and keep that final section limited to the user-decision
prompt. Completed recording, handoff, review, or informational work states its
result plainly.
The ordinal Fit disclosure belongs inside `## Decision scope and criteria`, not
under Evidence or Alternatives.
For generic architecture guidance, pattern explanations, or implementation examples,
loading the exact routed bundled reference is a hard gate: do not answer from model
memory, and disclose an unavailable reference instead of inventing an example.
Reproduce the canonical example for a generic request and do not browse merely to
discover or verify deterministic canonical links; use the bundled generated
reference catalog and do not invoke deterministic tools for focused reference help.
The bundled Codex control-plane hooks are defense in depth: they reinforce explicit
activation, blocks repository execution and application-code edits during architect
turns, validates stable visible option-comparison rendering when present, and rejects
leaked internal response markers when the user has trusted it. It does not select a
semantic mode or infer workflow phases from natural-language keywords.
Correctness must not depend on hook availability.
The installed Composite is already active when these instructions are present. Do
not try to rediscover its `SKILL.md` with workspace tools and do not report the skill
unavailable merely because its installation path is not exposed as a workspace file.
For repository evidence in Codex, read only relevant workspace files with native
file tools. Dependency and boundary observations are host-native static analysis;
disclose that dynamic imports, reflection, generated code, and omitted files were
not deterministically verified. Inspect `.ai-architect/` through host-native
read-only tools.
For complete or high-impact workflows, delegate up to three independent read-only
reviews when Codex subagents are available: architecture simplicity and pattern fit;
security and operations; maintainability and testability. Do not delegate focused
help or routine small comparisons. Subagents receive bounded evidence, modify no
files, and return findings with evidence, severity, action, and uncertainty. The main
agent integrates their findings and owns the final recommendation.
During `record_and_handoff`, prepare the ADR, contract, project context, and coding
handoff as one complete bundle before one durable write. Before drafting, load the
single exact bundled `assets/artifact-authoring-bundle.md` resource once; it contains
the canonical ADR template, contract example, ADR-authoring reference, and
implementation-plan template. Use exactly `.ai-architect/project-context.md`,
`.ai-architect/architecture-contract.yaml`, `.ai-architect/implementation-plan.md`,
and `.ai-architect/decisions/ADR-NNN[-slug].md`; do not invent alternate handoff
filenames. Treat the
contract example as authoritative for nested list-item shapes and never infer those shapes
from field names or model memory. `allow-via-interface` requires `via_interface`; `allow`
and `deny` omit it. The trusted `PreToolUse` hook reconstructs proposed
`.ai-architect/` content, validates the complete cross-artifact bundle, and scans
every generated artifact before allowing the write. `PostToolUse` verifies that the
persisted files match the validated bundle.
Never write durable artifacts first and validate them afterward. If deterministic
validation is unavailable or denies the proposal, persist nothing and disclose the limitation.

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


def _write_authoring_bundle(destination: Path) -> dict[str, str]:
    target = destination / AUTHORING_BUNDLE_OUTPUT
    target.parent.mkdir(parents=True, exist_ok=True)
    sections = [
        "<!--\n",
        "SPDX-FileCopyrightText: 2026 Leonardo Muffato "
        "(AUTOSOFT Engineering - www.autosoft-engineering.de)\n",
        "SPDX-License-Identifier: MIT\n",
        "Generated by adapters/codex/build_plugin.py; do not edit this packaged file.\n",
        "-->\n\n",
        "# Artifact Authoring Bundle\n\n",
        "Load this generated resource once during Codex `record_and_handoff`. "
        "The separately maintained canonical sources below remain authoritative.\n\n",
        "## Required output paths\n\n",
        "Submit exactly one complete candidate at each required path:\n\n",
        "- `.ai-architect/project-context.md`\n",
        "- `.ai-architect/architecture-contract.yaml`\n",
        "- `.ai-architect/implementation-plan.md`\n",
        "- `.ai-architect/decisions/ADR-NNN[-slug].md`\n\n",
        "Do not rename `implementation-plan.md` to coding-handoff, handoff, plan, "
        "or any other variant. The host adapter rejects alternate paths.\n",
    ]
    provenance: dict[str, str] = {}
    for heading, source in AUTHORING_BUNDLE_SOURCES:
        sections.extend(
            [
                f"\n---\n\n## {heading}\n\n",
                f"<!-- canonical-source: {_relative(source)} -->\n\n",
                source.read_text(encoding="utf-8").rstrip(),
                "\n",
            ]
        )
        provenance[_relative(source)] = (
            f"skills/ai-software-architect/{AUTHORING_BUNDLE_OUTPUT}"
        )
    target.write_text("".join(sections), encoding="utf-8", newline="\n")
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
        "ai-architect-runtime",
        "--add-data",
        (
            f"{ROOT / 'adapters' / 'codex' / 'reference_catalog.json'}"
            f"{os.pathsep}adapters/codex"
        ),
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
    additional_source_to_output = _write_authoring_bundle(skill_output)
    agents = skill_output / "agents"
    agents.mkdir()
    shutil.copyfile(TEMPLATES / "openai.yaml", agents / "openai.yaml")

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
        "additional_source_to_output": dict(sorted(additional_source_to_output.items())),
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
