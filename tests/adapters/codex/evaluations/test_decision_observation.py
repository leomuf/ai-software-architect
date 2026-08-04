# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import hashlib

from adapters.codex.evaluations.decision_observation import extract_decision_observation

REFERENCE_BASE = (
    "https://github.com/leomuf/ai-software-architect/blob/main/"
    "shared/skills/evaluate-architecture-options/references/"
)


def _comparison(*, selected: str, assumption: str) -> str:
    layered = (
        f"| [Architecture] [Layered Architecture]"
        f"({REFERENCE_BASE}architecture-layered.md) | 80/100 | Cohesion | "
        f"Simple seams | Erosion | {assumption} |"
    )
    strategy = (
        f"| [GoF] [Strategy]({REFERENCE_BASE}gof-strategy.md) | 70/100 | "
        "Policy change | Substitution | Indirection | Policies will vary |"
    )
    no_pattern = (
        "| [No pattern] Keep budget_book.py simple | 60/100 | Small scope | "
        "Low ceremony | Coupling | Scope stays tiny |"
    )
    return f"""## Decision scope and criteria
Choose one boundary; Fit is an ordinal score.

## Evidence and assumptions
Static evidence and explicit assumptions are separated.

## Alternatives
| Option | Fit | Rationale | Main benefit | Main liability | Material assumption |
| --- | ---: | --- | --- | --- | --- |
{layered}
{strategy}
{no_pattern}

## Recommendation
Choose {selected} with moderate uncertainty.

## Supporting patterns
- [Dependency] [Dependency injection]({REFERENCE_BASE}dependency-injection.md) — supplies adapters.

## Your decision
Approve, revise, or request more evidence.
"""


def test_extracts_public_selection_and_hashes_normalized_assumption() -> None:
    selected = (
        f"[Architecture] [Layered Architecture]"
        f"({REFERENCE_BASE}architecture-layered.md)"
    )
    observation = extract_decision_observation(
        _comparison(selected=selected, assumption="  Integrations   Will Grow ")
    )

    assert observation.selected_category == "Architecture"
    assert observation.selected_name == "Layered Architecture"
    assert observation.material_assumption_sha256 == hashlib.sha256(
        b"integrations will grow"
    ).hexdigest()
    assert observation.material_assumption_word_count == 3
    assert observation.visible_response_word_count is not None
    assert observation.visible_response_word_count > 100
    assert "Integrations" not in observation.model_dump_json()


def test_free_form_no_pattern_name_is_not_retained() -> None:
    observation = extract_decision_observation(
        _comparison(
            selected="[No pattern] Keep budget_book.py simple",
            assumption="Scope stays tiny",
        )
    )

    assert observation.selected_category == "No pattern"
    assert observation.selected_name == "No pattern"
    assert "budget_book" not in observation.model_dump_json()
