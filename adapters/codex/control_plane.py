# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Deterministic routing and rendering checks for explicitly activated Codex turns."""

from __future__ import annotations

import re
from collections.abc import Collection
from dataclasses import dataclass
from enum import StrEnum

from ai_architect_schemas import ComparedArchitectureOption
from pydantic import ValidationError

MAIN_SKILL_MARKER = "$ai-software-architect"
OPTIONS_SKILL_MARKER = "$evaluate-architecture-options"
PLUGIN_SELECTION_MARKER = "plugin://ai-software-architect"
CANONICAL_REFERENCE_BASE = (
    "https://github.com/leomuf/ai-software-architect/blob/main/"
    "shared/skills/evaluate-architecture-options/references/"
)
REFERENCE_CATEGORY_PREFIXES = (
    "architecture-",
    "data-",
    "dependency-",
    "gof-",
    "integration-",
    "modernization-",
    "presentation-",
    "resilience-",
)
MISSING_INVOCATION_GUIDANCE = (
    "AI Software Architect was selected, but no architect workflow was invoked. "
    "Please resend with `$ai-software-architect` for the complete workflow or "
    "`$evaluate-architecture-options` for a focused pattern comparison, "
    "explanation, or stored example."
)
PLUGIN_MCP_TOOLS = {
    "validate_complete_architecture_contract",
    "scan_generated_architecture_artifact",
    "analyze_python_dependencies",
    "check_python_architecture_boundaries",
}
SHELL_TOOL_NAMES = {"bash", "exec_command", "shell_command"}
PATCH_TOOL_NAMES = {"apply_patch", "edit", "write"}
OPTION_COMPARISON_DISALLOWED_TOOLS = {
    "validate_complete_architecture_contract",
    "scan_generated_architecture_artifact",
    "check_python_architecture_boundaries",
}
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
DECISION_ACTION_MARKER = (
    "<!-- ai-architect-actions: approve, revise, more-information -->"
)
COMPARISON_DECISION_SHAPE_MARKER = (
    "<!-- ai-architect-decision-shape: comparison -->"
)
SINGLE_DECISION_SHAPE_MARKER = "<!-- ai-architect-decision-shape: single -->"
DECISION_SHAPES = ("comparison", "single")
DECISION_SHAPE_PATTERN = re.compile(
    r"<!--\s*ai-architect-decision-shape:\s*([^<>]*?)\s*-->",
)
WORKFLOW_OUTCOMES = ("clarify", "recommendation", "complete")
WORKFLOW_OUTCOME_PATTERN = re.compile(
    r"<!--\s*ai-architect-outcome:\s*([^<>]*?)\s*-->",
)


class CodexTurnRoute(StrEnum):
    INACTIVE = "inactive"
    MISSING_SKILL_INVOCATION = "missing_skill_invocation"
    FOCUSED_WORKFLOW = "focused_workflow"
    OPTION_COMPARISON = "option_comparison"
    PATTERN_REFERENCE = "pattern_reference"
    ARCHITECTURE_WORKFLOW = "architecture_workflow"


@dataclass(frozen=True)
class CodexTurnContext:
    active: bool
    route: CodexTurnRoute
    reference_slug: str | None = None


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
    offered_actions: tuple[str, ...]


def _reference_aliases(slug: str) -> set[str]:
    readable = slug
    for prefix in REFERENCE_CATEGORY_PREFIXES:
        if readable.startswith(prefix):
            readable = readable.removeprefix(prefix)
            break
    readable = readable.replace("-", " ")
    aliases = {readable}
    words = readable.split()
    if len(words) >= 3:
        aliases.add("".join(word[0] for word in words))
    return aliases


def _contains_alias(prompt: str, alias: str) -> bool:
    return re.search(
        rf"(?<![\w-]){re.escape(alias)}(?![\w-])",
        prompt,
        flags=re.IGNORECASE,
    ) is not None


def _requested_reference_slugs(
    prompt: str,
    available_reference_slugs: Collection[str],
) -> tuple[str, ...]:
    matches = {
        slug
        for slug in available_reference_slugs
        if any(_contains_alias(prompt, alias) for alias in _reference_aliases(slug))
    }
    return tuple(sorted(matches))


def classify_prompt(
    prompt: str,
    available_reference_slugs: Collection[str] = (),
) -> CodexTurnContext:
    """Route only from explicit host markers and the bundled reference catalog."""

    lowered = prompt.casefold()
    has_main_skill = MAIN_SKILL_MARKER in lowered
    has_options_skill = OPTIONS_SKILL_MARKER in lowered
    if (
        PLUGIN_SELECTION_MARKER in lowered
        and not has_main_skill
        and not has_options_skill
    ):
        return CodexTurnContext(
            active=True,
            route=CodexTurnRoute.MISSING_SKILL_INVOCATION,
        )
    if not has_main_skill and not has_options_skill:
        return CodexTurnContext(active=False, route=CodexTurnRoute.INACTIVE)
    if has_options_skill:
        reference_slugs = _requested_reference_slugs(
            prompt,
            available_reference_slugs,
        )
        if len(reference_slugs) == 1:
            return CodexTurnContext(
                active=True,
                route=CodexTurnRoute.PATTERN_REFERENCE,
                reference_slug=reference_slugs[0],
            )
        if len(reference_slugs) > 1:
            return CodexTurnContext(
                active=True,
                route=CodexTurnRoute.OPTION_COMPARISON,
            )
        return CodexTurnContext(
            active=True,
            route=CodexTurnRoute.FOCUSED_WORKFLOW,
        )
    return CodexTurnContext(
        active=True,
        route=CodexTurnRoute.ARCHITECTURE_WORKFLOW,
    )


def developer_context(context: CodexTurnContext) -> str:
    base = (
        "AI Software Architect Codex control plane is active because an architect "
        "skill was explicitly invoked. Treat the plugin as the distribution bundle "
        "and follow the invoked skill as the semantic workflow. The hook does not "
        "infer architecture intent from natural-language keywords."
    )
    if context.route == CodexTurnRoute.PATTERN_REFERENCE:
        return base + _pattern_reference_context(context)
    if context.route == CodexTurnRoute.OPTION_COMPARISON:
        return (
            base
            + " Route: focused option comparison. Use the six stable section "
            "headings in skill order and include this language-neutral action marker "
            f"inside the final section: {DECISION_ACTION_MARKER} Compare two to five "
            "genuine alternatives for one decision, normally three to five when that "
            "many are credible. Use linked category labels and ordinal NN/100 fit. "
            "Contract validation, artifact scanning, and boundary checking are not "
            "part of this focused comparison route."
        )
    if context.route == CodexTurnRoute.FOCUSED_WORKFLOW:
        return (
            base
            + " Route: focused option-evaluation workflow. Let the focused skill and "
            "selected model determine whether to clarify, explain, or compare. "
            "Contract validation, artifact scanning, and boundary checking are not "
            "part of this focused skill."
        )
    return (
        base
        + " Route: complete architecture workflow. Let the invoked skill and selected "
        "model determine whether to understand, clarify, design, approve, record and "
        "handoff, or review. Never treat a recommendation as approved. Use MCP only "
        "for bounded repository evidence or artifact validation that the current "
        "workflow phase actually requires. Apply the clarification gate before "
        "selecting a decision shape: materially conflicting platform or interface "
        "statements require one focused clarification, no repository inspection, no "
        "MCP call, and no recommendation in that turn. Only after that gate passes, "
        "choose the recommendation's decision shape using host-native reasoning. "
        "An open request to choose "
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
        "alternatives for one decision, and "
        f"include {COMPARISON_DECISION_SHAPE_MARKER}. Use "
        f"{SINGLE_DECISION_SHAPE_MARKER} only when the user explicitly requests one "
        "highest-leverage improvement or supplied constraints make one proportionate "
        "simplicity decision sufficient; never use `single` to present a stack of "
        "recommended patterns. For `single`, put all recommendation content first, "
        "then place the shape and action markers immediately before one final visible "
        "decision prompt that offers approval, revision, and more information; no "
        "heading or recommendation content follows those markers. Named supporting "
        "patterns use `[Category] [Name](canonical public reference)`; ordinary coding "
        "practices may remain plain bullets. Place exactly one decision-shape marker "
        "immediately before the action marker in every recommendation. End every final response "
        "with exactly one "
        "language-neutral outcome marker: `<!-- ai-architect-outcome: clarify -->` "
        "when material input is required, `<!-- ai-architect-outcome: recommendation "
        "-->` when an architecture decision awaits the user, or `<!-- "
        "ai-architect-outcome: complete -->` when no architecture decision is "
        "pending. A recommendation must place this action marker immediately before "
        f"visible decision guidance, followed by its outcome marker: "
        f"{DECISION_ACTION_MARKER}"
    )


def _pattern_reference_context(context: CodexTurnContext) -> str:
    if context.reference_slug is None:
        raise ValueError("pattern-reference route requires one bundled reference")
    public_reference = f"{CANONICAL_REFERENCE_BASE}{context.reference_slug}.md"
    return (
        " Route: focused canonical reference. The matching bundled Markdown is "
        "provided below by the hook. Use it as the single source of truth; do not "
        "fetch another copy from the web, inspect the repository, or call an MCP "
        f"tool. Link {public_reference} in the user-facing answer. If the user asks "
        "for an implementation example and the reference contains one, reuse that "
        "stored example and explain how its participants map to the pattern."
    )


def _canonical_tool_name(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    return next((name for name in PLUGIN_MCP_TOOLS if name in value), None)


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
    if REPOSITORY_EXECUTION_PATTERN.search(
        command
    ) or DIRECT_EXECUTABLE_PATTERN.search(command):
        return (
            "AI Software Architect analysis treats repository code as untrusted "
            "data and does not run interpreters, test runners, package runners, or "
            "build tools. Use host-native static reads and the bounded AST tools."
        )
    if REPOSITORY_MUTATION_PATTERN.search(command) or GIT_MUTATION_PATTERN.search(
        command
    ):
        return (
            "AI Software Architect shell inspection is read-only and cannot mutate "
            "repository files or Git state. Approved architecture artifacts must be "
            "written through a reviewable patch limited to .ai-architect/."
        )
    return None


def _patch_text_from_tool_input(value: object) -> str | None:
    if isinstance(value, str):
        return value
    if not isinstance(value, dict):
        return None
    for key in ("patch", "input"):
        patch = value.get(key)
        if isinstance(patch, str):
            return patch
    return None


def _patch_is_limited_to_architecture_artifacts(tool_input: object) -> bool:
    patch = _patch_text_from_tool_input(tool_input)
    if patch is None:
        return False
    targets = tuple(
        (match.group(1) or match.group(2)).strip().replace("\\", "/")
        for match in PATCH_FILE_PATTERN.finditer(patch)
    )
    return bool(targets) and all(
        target.startswith(".ai-architect/")
        and not target.startswith("/")
        and ".." not in target.split("/")
        for target in targets
    )


def tool_denial_reason(
    context: CodexTurnContext,
    tool_name_value: object,
    tool_input: object = None,
) -> str | None:
    if not context.active:
        return None
    local_tool_name = _normalized_local_tool_name(tool_name_value)
    if local_tool_name in SHELL_TOOL_NAMES:
        reason = _shell_denial_reason(tool_input)
        if reason is not None:
            return reason
    if local_tool_name in PATCH_TOOL_NAMES:
        if context.route in {
            CodexTurnRoute.FOCUSED_WORKFLOW,
            CodexTurnRoute.OPTION_COMPARISON,
            CodexTurnRoute.PATTERN_REFERENCE,
        }:
            return (
                "The focused architecture-options workflow is explanatory and "
                "read-only; it cannot edit repository files."
            )
        if not _patch_is_limited_to_architecture_artifacts(tool_input):
            return (
                "The AI Software Architect never writes application code. Its patch "
                "surface is limited to approved files under .ai-architect/."
            )
    tool_name = _canonical_tool_name(tool_name_value)
    if tool_name is None:
        return None
    if context.route == CodexTurnRoute.PATTERN_REFERENCE:
        return (
            "The focused reference is already bundled into this turn; an AI Software "
            "Architect MCP call would add no relevant evidence."
        )
    if (
        context.route
        in {CodexTurnRoute.FOCUSED_WORKFLOW, CodexTurnRoute.OPTION_COMPARISON}
        and tool_name in OPTION_COMPARISON_DISALLOWED_TOOLS
    ):
        return (
            f"{tool_name} is outside the focused option-evaluation skill. "
            "Compare the alternatives first; validate artifacts only in the complete "
            "workflow phase that owns that operation."
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


def parse_option_comparison_markdown(message: str) -> ParsedOptionComparison:
    """Parse only the user-facing fields that are deterministically represented."""

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
        score_text = score_match.group(
            "plain_score"
        ) or score_match.group("emphasized_score")
        if score_text is None:
            continue
        matched = option_pattern.fullmatch(cells[0])
        if matched is None:
            continue
        category = matched.group("category")
        name = matched.group("linked_name") or matched.group("plain_name")
        option_id = f"OPT-{len(rows) + 1:03d}"
        option = ComparedArchitectureOption.model_validate(
            {
                "id": option_id,
                "category": category,
                "name": name,
                "canonical_reference": (
                    None if category == "No pattern" else matched.group("link")
                ),
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

    decision_prompt = _section_text(message, "## Your decision", None)
    if DECISION_ACTION_MARKER not in decision_prompt:
        raise ValueError("language-neutral decision action marker is missing")
    visible_decision_prompt = decision_prompt.replace(DECISION_ACTION_MARKER, "").strip()
    visible_decision_prompt = DECISION_SHAPE_PATTERN.sub(
        "",
        visible_decision_prompt,
    ).strip()
    visible_decision_prompt = re.sub(
        r"<!--.*?-->",
        "",
        visible_decision_prompt,
        flags=re.DOTALL,
    ).strip()
    if not visible_decision_prompt:
        raise ValueError("user decision prompt must contain visible guidance")

    parsed = ParsedOptionComparison(
        decision_scope_and_criteria=_section_text(
            message,
            "## Decision scope and criteria",
            "## Evidence and assumptions",
        ),
        evidence_and_assumptions=_section_text(
            message,
            "## Evidence and assumptions",
            "## Alternatives",
        ),
        alternatives=tuple(rows),
        recommended_option_id=mentioned[0][1],
        recommendation=recommendation,
        supporting_patterns=_section_text(
            message,
            "## Supporting patterns",
            "## Your decision",
        ),
        user_decision_prompt=visible_decision_prompt,
        offered_actions=("approve", "revise", "more-information"),
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
            "`NN/100`. The Recommendation must name one table "
            "option; Supporting patterns must remain separate; Your decision must "
            "contain the action marker followed by visible guidance. Validation "
            f"detail: {exc}"
        ]
    return []


def _architecture_workflow_violations(message: str) -> list[str]:
    marker_matches = tuple(WORKFLOW_OUTCOME_PATTERN.finditer(message))
    if len(marker_matches) != 1:
        return [
            "include exactly one workflow outcome marker using clarify, "
            "recommendation, or complete"
        ]
    outcome_match = marker_matches[0]
    outcome = outcome_match.group(1).strip()
    if outcome not in WORKFLOW_OUTCOMES:
        return [
            "workflow outcome must be exactly clarify, recommendation, or complete"
        ]
    action_marker_count = message.count(DECISION_ACTION_MARKER)
    decision_shape_matches = tuple(DECISION_SHAPE_PATTERN.finditer(message))
    if outcome == "recommendation" and action_marker_count != 1:
        return [
            "a recommendation outcome must include exactly one language-neutral "
            "approve, revise, more-information action marker plus visible decision "
            "guidance"
        ]
    if outcome == "recommendation":
        if len(decision_shape_matches) != 1:
            return [
                "a recommendation outcome must declare exactly one decision shape "
                "using comparison or single"
            ]
        decision_shape = decision_shape_matches[0].group(1).strip()
        if decision_shape not in DECISION_SHAPES:
            return [
                "recommendation decision shape must be exactly comparison or single"
            ]
        shape_marker_end = decision_shape_matches[0].end()
        action_marker_start = message.find(DECISION_ACTION_MARKER)
        if (
            action_marker_start < shape_marker_end
            or message[shape_marker_end:action_marker_start].strip()
        ):
            return [
                "place the decision-shape marker immediately before the decision "
                "action marker"
            ]
        action_marker_end = message.find(DECISION_ACTION_MARKER) + len(
            DECISION_ACTION_MARKER
        )
        visible_guidance = message[action_marker_end : outcome_match.start()]
        visible_guidance = re.sub(
            r"<!--.*?-->",
            "",
            visible_guidance,
            flags=re.DOTALL,
        ).strip()
        if not visible_guidance:
            return [
                "place visible localized decision guidance between the action marker "
                "and the recommendation outcome marker"
            ]
        if decision_shape == "single" and re.search(
            r"(?m)^#{1,6}\s+",
            visible_guidance,
        ):
            return [
                "for a single recommendation, put all recommendation headings and "
                "content before the decision-shape and action markers; after the "
                "markers include only one final visible decision prompt offering "
                "approval, revision, and more information"
            ]
        if decision_shape == "comparison":
            comparison_violations = _option_comparison_violations(message)
            if comparison_violations:
                return comparison_violations
    if outcome != "recommendation" and action_marker_count:
        return [
            "the decision action marker is reserved for a recommendation outcome"
        ]
    if outcome != "recommendation" and decision_shape_matches:
        return [
            "the decision-shape marker is reserved for a recommendation outcome"
        ]
    return []


def final_response_violations(
    context: CodexTurnContext,
    message: str,
) -> list[str]:
    if context.route == CodexTurnRoute.OPTION_COMPARISON:
        return _option_comparison_violations(message)
    if context.route == CodexTurnRoute.ARCHITECTURE_WORKFLOW:
        return _architecture_workflow_violations(message)
    return []
