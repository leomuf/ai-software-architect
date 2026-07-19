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
OPTION_COMPARISON_DISALLOWED_TOOLS = {
    "validate_complete_architecture_contract",
    "scan_generated_architecture_artifact",
    "check_python_architecture_boundaries",
}
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
        "workflow phase actually requires. End every final response with exactly one "
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


def tool_denial_reason(
    context: CodexTurnContext,
    tool_name_value: object,
) -> str | None:
    tool_name = _canonical_tool_name(tool_name_value)
    if not context.active or tool_name is None:
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
        if len(cells) != 6 or not re.fullmatch(r"(?:100|[1-9]?[0-9])/100", cells[1]):
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
                "fit_score": int(cells[1].removesuffix("/100")),
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
        return [str(exc)]
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
    if outcome == "recommendation" and action_marker_count != 1:
        return [
            "a recommendation outcome must include exactly one language-neutral "
            "approve, revise, more-information action marker plus visible decision "
            "guidance"
        ]
    if outcome == "recommendation":
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
    if outcome != "recommendation" and action_marker_count:
        return [
            "the decision action marker is reserved for a recommendation outcome"
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
