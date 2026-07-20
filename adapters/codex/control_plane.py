# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Deterministic routing and rendering checks for explicitly activated Codex turns."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from ai_architect_schemas import ComparedArchitectureOption
from pydantic import ValidationError

try:
    from adapters.codex.reference_catalog import REFERENCE_CATALOG, ReferenceSpec
except ModuleNotFoundError as exc:
    if exc.name != "adapters":
        raise
    from reference_catalog import (  # type: ignore[import-not-found, no-redef]
        REFERENCE_CATALOG,
        ReferenceSpec,
    )

MAIN_SKILL_MARKER = "$ai-software-architect"
PLUGIN_SELECTION_MARKER = "plugin://ai-software-architect"
PLUGIN_MARKDOWN_SELECTION_PATTERN = re.compile(
    r"\[[^\]\r\n]*\]\(\s*plugin://ai-software-architect[^)\r\n]*\)",
    flags=re.IGNORECASE,
)
PLUGIN_URI_PATTERN = re.compile(
    r"plugin://ai-software-architect(?:@[0-9a-z._-]+)?",
    flags=re.IGNORECASE,
)
CANONICAL_REFERENCE_BASE = (
    "https://github.com/leomuf/ai-software-architect/blob/main/"
    "shared/skills/evaluate-architecture-options/references/"
)
# Compatibility view for conformance checks; the source of truth is generated JSON.
REFERENCE_SPECS: dict[str, tuple[str, str]] = {
    entry.name.casefold(): (entry.category, entry.filename)
    for entry in REFERENCE_CATALOG.entries
}
MISSING_INVOCATION_GUIDANCE = (
    "AI Software Architect was selected without a request. Add your architecture "
    "question after the plugin selection, or invoke `$ai-software-architect` "
    "directly; the architect will choose focused pattern help or the complete "
    "architecture workflow from your request."
)
SHELL_TOOL_NAMES = {"bash", "exec_command", "shell_command"}
PATCH_TOOL_NAMES = {"apply_patch", "edit", "write"}
WEB_LOOKUP_TOOL_NAMES = {"websearch", "web_search", "search_query", "web__run"}
REPOSITORY_EXECUTION_PATTERN = re.compile(
    r"""(?ix)
    (?:^|[;&|{(=]\s*)(?:&\s*)?(?:["'][^"'\r\n]*[\\/])?
    (?:
        python(?:3(?:\.\d+)*)? | py | pytest | tox | nox | coverage |
        uv | pip(?:3)? | node | npm | npx | pnpm | yarn | bun | deno |
        ruby | bundle | php | java | javac | gradle | mvn | dotnet |
        cargo | rustc | go | cmd | powershell | pwsh | wsl | bash | sh |
        zsh | start-process | invoke-expression | iex | import-module
    )
    (?:\.exe)?(?=\s|$|["'])
    """
)
DIRECT_EXECUTABLE_PATTERN = re.compile(
    r"""(?ix)
    (?:^|[;&|{(=]\s*)(?:&\s*)?
    (?:"[^"\r\n]+"|'[^'\r\n]+'|[^\s;&|{}()=]+)
    \.(?:exe|bat|cmd|ps1|sh|py)
    (?=\s|$)
    """
)
REPOSITORY_MUTATION_PATTERN = re.compile(
    r"""(?ix)
    (?:^|[;&|{(]\s*)
    (?:
        remove-item | set-content | add-content | out-file | new-item |
        copy-item | move-item | rename-item | clear-content |
        del | erase | copy | move | mkdir | rmdir
    )
    (?=\s|$)
    """
)
GIT_MUTATION_PATTERN = re.compile(
    r"""(?ix)
    (?:^|[;&|{(]\s*)git(?:\.exe)?\s+
    (?:
        add | commit | checkout | switch | restore | reset | clean | merge |
        rebase | cherry-pick | revert | pull | push | tag | stash | rm | mv
    )
    (?=\s|$)
    """
)
PATCH_FILE_PATTERN = re.compile(
    r"^\*\*\* (?:Add|Update|Delete) File: (.+)$|^\*\*\* Move to: (.+)$",
    flags=re.MULTILINE,
)
REQUIRED_COMPARISON_SECTIONS = (
    "## Decision scope and criteria",
    "## Evidence and assumptions",
    "## Alternatives",
    "## Recommendation",
    "## Supporting patterns",
    "## Your decision",
)
HIDDEN_HTML_COMMENT_PATTERN = re.compile(
    r"<!--.*?-->",
    flags=re.DOTALL,
)


class CodexTurnRoute(StrEnum):
    INACTIVE = "inactive"
    MISSING_SKILL_INVOCATION = "missing_skill_invocation"
    ARCHITECTURE_WORKFLOW = "architecture_workflow"


@dataclass(frozen=True)
class CodexTurnContext:
    active: bool
    route: CodexTurnRoute
    reference_paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class ParsedOptionComparison:
    """The exact rendering fields the Stop hook can verify without semantic inference."""

    decision_scope_and_criteria: str
    evidence_and_assumptions: str
    alternatives: tuple[ComparedArchitectureOption, ...]
    recommended_option_id: str
    recommendation: str
    supporting_patterns: str
    user_decision_prompt: str


def classify_prompt(prompt: str) -> CodexTurnContext:
    """Activate only from explicit host markers; leave semantic routing to the model."""

    lowered = prompt.casefold()
    has_main_skill = MAIN_SKILL_MARKER in lowered
    has_plugin_selection = PLUGIN_SELECTION_MARKER in lowered
    if has_plugin_selection and not has_main_skill:
        without_selection = PLUGIN_MARKDOWN_SELECTION_PATTERN.sub(" ", prompt)
        without_selection = PLUGIN_URI_PATTERN.sub(" ", without_selection)
        if not re.search(r"\w", without_selection, flags=re.UNICODE):
            return CodexTurnContext(
                active=True,
                route=CodexTurnRoute.MISSING_SKILL_INVOCATION,
            )
        return CodexTurnContext(
            active=True,
            route=CodexTurnRoute.ARCHITECTURE_WORKFLOW,
        )
    if not has_main_skill:
        return CodexTurnContext(active=False, route=CodexTurnRoute.INACTIVE)
    return CodexTurnContext(
        active=True,
        route=CodexTurnRoute.ARCHITECTURE_WORKFLOW,
    )


def _explicit_reference_paths(prompt: str) -> tuple[str, ...]:
    """Resolve only explicit canonical names; do not choose a semantic workflow mode."""

    return tuple(
        f"references/{entry.filename}"
        for entry in REFERENCE_CATALOG.explicitly_named(prompt)
    )


def with_reference_hints(
    context: CodexTurnContext,
    prompt: str,
) -> CodexTurnContext:
    paths = _explicit_reference_paths(prompt)
    if not paths:
        return context
    return CodexTurnContext(
        active=context.active,
        route=context.route,
        reference_paths=paths,
    )


def developer_context(
    context: CodexTurnContext,
    *,
    continued: bool = False,
    continuation_instruction: str = "",
) -> str:
    base = (
        "AI Software Architect Codex control plane is active because an architect "
        "workflow was explicitly selected or invoked. The single user-facing "
        "Composite chooses "
        "focused pattern help or the complete architecture lifecycle from the user's "
        "request. The installed Composite is already active; do not try to rediscover "
        "its SKILL.md with workspace tools and do not report the skill unavailable "
        "merely because its installation path is not exposed as a workspace file. "
        "The hook does not infer architecture intent from natural-language keywords."
    )
    continuation = (
        " This is a bounded continuation of the immediately preceding AI Software "
        "Architect clarification or decision request; preserve that workflow context. "
        + continuation_instruction
        if continued
        else ""
    )
    reference_hint = ""
    if context.reference_paths:
        rendered_paths = ", ".join(
            f"`{path}` with canonical public URL "
            f"`{CANONICAL_REFERENCE_BASE}{Path(path).name}`"
            for path in context.reference_paths
        )
        reference_hint = (
            " Exact bundled reference hint from explicitly named architecture terms: "
            f"{rendered_paths}. This hint does not choose the semantic workflow mode. "
            "Before explaining or showing an implementation of a hinted pattern, load "
            "that exact bundled reference. For a generic example, reproduce its "
            "canonical Python example and participant mapping; do not answer from "
            "memory, synthesize another variant, or browse the public repository. If "
            "the bundled reference cannot be loaded, disclose that limitation instead "
            "of inventing an example."
        )
    catalog_index = REFERENCE_CATALOG.compact_index()
    return (
        base + " Route: model-selected workflow. First choose the smallest sufficient mode: "
        "focused explanation or example, option comparison, or complete architecture "
        "lifecycle. Focused help does not inspect the repository, call MCP, or create "
        "artifacts unless the request explicitly requires project evidence. The "
        "complete lifecycle may understand, clarify, design, approve, record and "
        "handoff, or review. Never treat a recommendation as approved. Use MCP only "
        "for bounded repository evidence or artifact validation that the current "
        "workflow phase actually requires. `analyze_python_dependencies` accepts "
        "bounded `dependency_statements` only; never send complete `source_files` to "
        "that tool. Reserve full source for an approved architecture-boundary check "
        "when contract verification truly requires it. Apply the clarification gate before "
        "drafting a recommendation: materially conflicting platform or interface "
        "statements require one focused clarification, no repository inspection, no "
        "MCP call, and no recommendation in that turn. Only after that gate passes "
        "may host-native reasoning choose the response structure. An open request to "
        "choose "
        "architecture or design-pattern options is `comparison`: use the six stable "
        "comparison headings exactly and in order—"
        + ", ".join(REQUIRED_COMPARISON_SECTIONS)
        + "—and render Alternatives as a Markdown table with exactly these columns: "
        "Option, Fit, Rationale, Main benefit, Main liability, Material assumption. "
        "Allowed category labels are GoF, Architecture, Presentation, Dependency, "
        "Data, Integration, Resilience, Modernization, and No pattern. Example Option "
        "cells are `[No pattern] Keep the script simple` and `[GoF] "
        f"[Strategy]({CANONICAL_REFERENCE_BASE}gof-strategy.md)`. Named options link "
        "their bundled public reference, and Fit is ordinal NN/100. Compare genuine "
        "alternatives for one decision. When the user explicitly requests one "
        "highest-leverage improvement or supplied constraints make one proportionate "
        "simplicity decision sufficient, present one recommendation rather than a "
        "comparison; never use a single recommendation to present a stack of patterns. "
        "Put all single-recommendation content first, then end with `## Your decision` "
        "and one visible prompt that offers approval, revision, and more information. "
        "Named supporting "
        "patterns use `[Category] [Name](canonical public reference)`; ordinary coding "
        "practices may remain plain bullets. Clarifications end with the focused "
        "visible question, and completed work states its result plainly. Never emit "
        "internal `ai-architect` response markers or HTML comments; Codex may display "
        "them to the user. The Stop hook validates only stable visible structures and "
        "does not classify the semantic workflow outcome. Canonical reference index "
        f"(metadata only; load bodies progressively): {catalog_index}. This complete "
        "index is authoritative for reference names, categories, filenames, and public "
        "links. Never browse the web or public repository to discover a canonical "
        "reference path. During `record_and_handoff`, resolve these bundled paths "
        "under the installed public skill root `skills/ai-software-architect/`: "
        "`assets/adr-template.md`, `assets/architecture-contract.example.yaml`, "
        "`references/adr-authoring.md`, and `assets/implementation-plan-template.md`. "
        "Do not resolve them from the plugin root or search for artifact schemas or "
        "examples."
        " During `record_and_handoff`, create every complete candidate in memory before "
        "any durable artifact patch. Validate the contract with exactly "
        "`request: {yaml_content: <complete YAML>, validation_scope: "
        "complete-candidate-contract}` and inspect `result.valid`. Scan each complete "
        "candidate with exactly `request: {content: <complete content>, artifact_kind: "
        "<adr|contract|context|implementation-plan>}` and inspect `result.safe_to_write`. "
        "Do not use `contract`, `validation_scope: complete`, or any other artifact-kind "
        "literal. Only after all required results pass may one reviewable patch persist "
        "the approved set under `.ai-architect/`; never patch durable artifacts first and "
        "validate the persisted files afterward."
        + continuation
        + reference_hint
    )


def _normalized_local_tool_name(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    return value.rsplit(".", 1)[-1].casefold()


def _command_from_tool_input(value: object) -> str | None:
    if isinstance(value, str):
        return value
    if not isinstance(value, dict):
        return None
    command = value.get("command")
    return command if isinstance(command, str) else None


def _shell_denial_reason(tool_input: object) -> str | None:
    command = _command_from_tool_input(tool_input)
    if command is None:
        return (
            "The AI Software Architect could not verify this shell command's "
            "arguments, so it was denied. Use host-native static reads instead."
        )
    if REPOSITORY_EXECUTION_PATTERN.search(command) or DIRECT_EXECUTABLE_PATTERN.search(command):
        return (
            "AI Software Architect analysis treats repository code as untrusted "
            "data and does not run interpreters, test runners, package runners, or "
            "build tools. Use host-native static reads and the bounded AST tools."
        )
    if REPOSITORY_MUTATION_PATTERN.search(command) or GIT_MUTATION_PATTERN.search(command):
        return (
            "AI Software Architect shell inspection is read-only and cannot mutate "
            "repository files or Git state. Approved architecture artifacts must be "
            "written through a reviewable patch limited to .ai-architect/."
        )
    return None


def _patch_text_from_tool_input(value: object) -> str | None:
    if isinstance(value, str):
        return value if "*** Begin Patch" in value else None
    candidates: list[str] = []

    def collect(current: object, depth: int = 0) -> None:
        if depth > 4:
            return
        if isinstance(current, str):
            if "*** Begin Patch" in current and "*** End Patch" in current:
                candidates.append(current)
            return
        if isinstance(current, dict):
            for nested in current.values():
                collect(nested, depth + 1)
        elif isinstance(current, list):
            for nested in current:
                collect(nested, depth + 1)

    collect(value)
    return candidates[0] if len(candidates) == 1 else None


def _patch_target_is_architecture_artifact(target: str, workspace: Path | None) -> bool:
    normalized = target.strip().replace("\\", "/")
    if not normalized or ".." in normalized.split("/"):
        return False
    candidate = Path(target.strip())
    if candidate.is_absolute():
        if workspace is None:
            return False
        try:
            relative = candidate.resolve(strict=False).relative_to(
                workspace.resolve(strict=False)
            )
        except (OSError, ValueError):
            return False
        normalized = relative.as_posix()
    return normalized.startswith(".ai-architect/")


def _patch_is_limited_to_architecture_artifacts(
    tool_input: object,
    workspace: Path | None = None,
) -> bool:
    patch = _patch_text_from_tool_input(tool_input)
    if patch is None:
        return False
    targets = tuple(
        (match.group(1) or match.group(2)).strip().replace("\\", "/")
        for match in PATCH_FILE_PATTERN.finditer(patch)
    )
    return bool(targets) and all(
        _patch_target_is_architecture_artifact(target, workspace)
        for target in targets
    )


def tool_denial_reason(
    context: CodexTurnContext,
    tool_name_value: object,
    tool_input: object = None,
    workspace: Path | None = None,
) -> str | None:
    if not context.active:
        return None
    local_tool_name = _normalized_local_tool_name(tool_name_value)
    if local_tool_name in WEB_LOOKUP_TOOL_NAMES:
        return (
            "AI Software Architect canonical references are bundled with the plugin; "
            "web lookup is disabled during the architecture workflow. Use the "
            "reference paths supplied by the active skill context."
        )
    if local_tool_name in SHELL_TOOL_NAMES:
        reason = _shell_denial_reason(tool_input)
        if reason is not None:
            return reason
    if local_tool_name in PATCH_TOOL_NAMES:
        if not _patch_is_limited_to_architecture_artifacts(tool_input, workspace):
            return (
                "The AI Software Architect never writes application code. Its patch "
                "surface is limited to approved files under .ai-architect/."
            )
    return None


def _sections_are_ordered(message: str) -> bool:
    positions = [message.find(section) for section in REQUIRED_COMPARISON_SECTIONS]
    return all(position >= 0 for position in positions) and positions == sorted(positions)


def _section_text(message: str, heading: str, next_heading: str | None) -> str:
    start = message.find(heading)
    if start < 0:
        return ""
    start += len(heading)
    end = message.find(next_heading, start) if next_heading else len(message)
    return message[start:end].strip() if end >= 0 else ""


def _reference_spec_for_name(name: str) -> ReferenceSpec | None:
    return REFERENCE_CATALOG.named(name)


def _validate_canonical_reference(
    *,
    category: str,
    name: str,
    link: str | None,
) -> None:
    if category == "No pattern":
        return
    if link is None or not link.startswith(CANONICAL_REFERENCE_BASE):
        raise ValueError(f"{name} must link to the canonical public reference")
    expected = _reference_spec_for_name(name)
    if expected is None:
        return
    if category != expected.category:
        raise ValueError(f"{name} must use the {expected.category} category")
    if link != CANONICAL_REFERENCE_BASE + expected.filename:
        raise ValueError(f"{name} must link to {expected.filename}")


def _validate_supporting_patterns(text: str) -> None:
    linked_name = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    for line in text.splitlines():
        linked_specs = tuple(
            (REFERENCE_CATALOG.named(name), link)
            for name, link in linked_name.findall(line)
        )
        for spec, link in linked_specs:
            if spec is None:
                continue
            if f"[{spec.category}]" not in line or link != CANONICAL_REFERENCE_BASE + spec.filename:
                raise ValueError(
                    f"the first supporting-pattern mention of {spec.name} must use "
                    f"[{spec.category}] and its canonical public reference"
                )
        for spec in REFERENCE_CATALOG.explicitly_named(line):
            expected_link = CANONICAL_REFERENCE_BASE + spec.filename
            if f"[{spec.category}]" not in line or expected_link not in line:
                raise ValueError(
                    f"the first supporting-pattern mention of {spec.name} must use "
                    f"[{spec.category}] and its canonical public reference"
                )


def parse_option_comparison_markdown(message: str) -> ParsedOptionComparison:
    """Parse only the user-facing fields that are deterministically represented."""

    if HIDDEN_HTML_COMMENT_PATTERN.search(message):
        raise ValueError("internal control markers and HTML comments must not be rendered")
    if not _sections_are_ordered(message):
        raise ValueError("required comparison sections are missing or out of order")

    alternatives_text = _section_text(
        message,
        "## Alternatives",
        "## Recommendation",
    )
    rows: list[ComparedArchitectureOption] = []
    option_names: dict[str, str] = {}
    option_pattern = re.compile(
        r"^\[(?P<category>GoF|Architecture|Presentation|Dependency|Data|Integration|"
        r"Resilience|Modernization|No pattern)\]\s+"
        r"(?:\[(?P<linked_name>[^\]]+)\]\((?P<link>[^)]+)\)|(?P<plain_name>.+))$"
    )
    for line in alternatives_text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 6:
            continue
        score_match = re.fullmatch(
            r"(?P<plain_score>(?:100|[1-9]?[0-9])/100)|"
            r"(?P<emphasis>\*\*|__)"
            r"(?P<emphasized_score>(?:100|[1-9]?[0-9])/100)"
            r"(?P=emphasis)",
            cells[1],
        )
        if score_match is None:
            continue
        score_text = score_match.group("plain_score") or score_match.group("emphasized_score")
        if score_text is None:
            continue
        matched = option_pattern.fullmatch(cells[0])
        if matched is None:
            continue
        category = matched.group("category")
        name = matched.group("linked_name") or matched.group("plain_name")
        option_id = f"OPT-{len(rows) + 1:03d}"
        link = None if category == "No pattern" else matched.group("link")
        _validate_canonical_reference(
            category=category,
            name=name,
            link=link,
        )
        option = ComparedArchitectureOption.model_validate(
            {
                "id": option_id,
                "category": category,
                "name": name,
                "canonical_reference": link,
                "fit_score": int(score_text.removesuffix("/100")),
                "fit_rationale": cells[2],
                "main_benefit": cells[3],
                "main_liability": cells[4],
                "material_assumption": cells[5],
            }
        )
        rows.append(option)
        option_names[option.name.casefold()] = option.id
    if not 2 <= len(rows) <= 5:
        raise ValueError("comparison must contain two to five valid alternative rows")

    recommendation = _section_text(
        message,
        "## Recommendation",
        "## Supporting patterns",
    )
    lowered_recommendation = recommendation.casefold()
    mentioned = sorted(
        (lowered_recommendation.find(name), option_id)
        for name, option_id in option_names.items()
        if name in lowered_recommendation
    )
    if not mentioned:
        raise ValueError("recommendation must name a compared alternative")

    decision_scope = _section_text(
        message,
        "## Decision scope and criteria",
        "## Evidence and assumptions",
    )
    if "ordinal" not in decision_scope.casefold():
        raise ValueError("decision criteria must describe Fit as an ordinal score")

    supporting_patterns = _section_text(
        message,
        "## Supporting patterns",
        "## Your decision",
    )
    _validate_supporting_patterns(supporting_patterns)

    decision_prompt = _section_text(message, "## Your decision", None)
    visible_decision_prompt = re.sub(
        r"<!--.*?-->",
        "",
        decision_prompt,
        flags=re.DOTALL,
    ).strip()
    if not visible_decision_prompt:
        raise ValueError("user decision prompt must contain visible guidance")

    parsed = ParsedOptionComparison(
        decision_scope_and_criteria=decision_scope,
        evidence_and_assumptions=_section_text(
            message,
            "## Evidence and assumptions",
            "## Alternatives",
        ),
        alternatives=tuple(rows),
        recommended_option_id=mentioned[0][1],
        recommendation=recommendation,
        supporting_patterns=supporting_patterns,
        user_decision_prompt=visible_decision_prompt,
    )
    if not all(
        (
            parsed.decision_scope_and_criteria,
            parsed.evidence_and_assumptions,
            parsed.recommendation,
            parsed.supporting_patterns,
        )
    ):
        raise ValueError("comparison sections must contain visible content")
    return parsed


def _option_comparison_violations(message: str) -> list[str]:
    try:
        parse_option_comparison_markdown(message)
    except (ValidationError, ValueError) as exc:
        return [
            "render one complete replacement with these exact ordered headings: "
            + ", ".join(REQUIRED_COMPARISON_SECTIONS)
            + ". Under `## Alternatives`, use exactly this six-column header: "
            "`| Option | Fit | Rationale | Main benefit | Main liability | "
            "Material assumption |`. Provide two to five genuine rows (normally "
            "three to five). Allowed category labels are `GoF`, `Architecture`, "
            "`Presentation`, `Dependency`, `Data`, `Integration`, `Resilience`, "
            "`Modernization`, and `No pattern`. Example Option cells: `[No pattern] "
            "Keep the script simple`; `[GoF] "
            f"[Strategy]({CANONICAL_REFERENCE_BASE}gof-strategy.md)`. Each named "
            "option links its canonical public reference, and each Fit is ordinal "
            "`NN/100`; Decision scope and criteria must explicitly call Fit ordinal. "
            "The Recommendation must name one table option. Supporting patterns must "
            "remain separate, and the first mention of every named supporting pattern "
            "must include its category and canonical public link. Your decision must "
            "contain visible guidance offering approval, revision, or more "
            "information. Do not include internal control markers or HTML comments. "
            "Validation "
            f"detail: {exc}"
        ]
    return []


def _architecture_workflow_violations(message: str) -> list[str]:
    if HIDDEN_HTML_COMMENT_PATTERN.search(message):
        return [
            "remove internal control markers or HTML comments and return only user-facing content"
        ]
    if "## Alternatives" in message:
        return _option_comparison_violations(message)
    if "## Your decision" in message:
        visible_guidance = re.sub(
            r"<!--.*?-->",
            "",
            _section_text(message, "## Your decision", None),
            flags=re.DOTALL,
        ).strip()
        if not visible_guidance:
            return ["place visible decision guidance under `## Your decision`"]
        if re.search(
            r"(?m)^#{1,6}\s+",
            visible_guidance,
        ):
            return [
                "put all recommendation headings and content before `## Your "
                "decision`; keep that final section limited to visible decision "
                "guidance"
            ]
    return []


def final_response_violations(
    context: CodexTurnContext,
    message: str,
) -> list[str]:
    if context.route == CodexTurnRoute.ARCHITECTURE_WORKFLOW:
        return _architecture_workflow_violations(message)
    return []
