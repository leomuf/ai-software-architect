# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Deterministic user-facing renderers for validated architecture models."""

from __future__ import annotations

import yaml
from ai_architect_schemas import ArchitectureContract, ArchitectureOptionComparison


def render_architecture_contract(contract: ArchitectureContract) -> str:
    """Render a validated contract without allowing model-invented YAML shapes."""

    return yaml.safe_dump(
        contract.model_dump(mode="json", exclude_none=True),
        allow_unicode=True,
        sort_keys=False,
    )


def _option_cell(category: str, name: str, reference: str | None) -> str:
    if reference is None:
        return f"[{category}] {name}"
    return f"[{category}] [{name}]({reference})"


def render_option_comparison(comparison: ArchitectureOptionComparison) -> str:
    """Render the stable comparison contract from one validated source object."""

    by_id = {option.id: option for option in comparison.alternatives}
    selected = by_id[comparison.recommended_option_id]
    lines = [
        "## Decision scope and criteria",
        "",
        comparison.decision_scope,
        "",
        "Fit is an ordinal `NN/100` score for this decision, not a probability "
        "or measured percentage.",
        "",
        *[f"- {criterion}" for criterion in comparison.scoring_criteria],
        "",
        "## Evidence and assumptions",
        "",
        *[f"- **{claim.kind}:** {claim.claim}" for claim in comparison.evidence_and_assumptions],
        "",
        "## Alternatives",
        "",
        "| Option | Fit | Rationale | Main benefit | Main liability | Material assumption |",
        "| --- | ---: | --- | --- | --- | --- |",
    ]
    for option in comparison.alternatives:
        lines.append(
            "| "
            + " | ".join(
                (
                    _option_cell(option.category, option.name, option.canonical_reference),
                    f"{option.fit_score}/100",
                    option.fit_rationale,
                    option.main_benefit,
                    option.main_liability,
                    option.material_assumption,
                )
            )
            + " |"
        )
    lines.extend(
        (
            "",
            "## Recommendation",
            "",
            "Choose **"
            + _option_cell(selected.category, selected.name, selected.canonical_reference)
            + "**.",
            "",
            comparison.recommendation_rationale,
            "",
            "## Supporting patterns",
            "",
        )
    )
    lines.extend(
        "- "
        + _option_cell(pattern.category, pattern.name, pattern.canonical_reference)
        + f" — {pattern.role}"
        for pattern in comparison.supporting_patterns
    )
    if not comparison.supporting_patterns:
        lines.append("No supporting patterns are required.")
    lines.extend(("", "## Your decision", "", comparison.user_decision_prompt, ""))
    return "\n".join(lines)
