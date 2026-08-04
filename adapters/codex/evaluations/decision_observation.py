# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Extract bounded comparison outcomes without retaining free-form response text."""

from __future__ import annotations

import hashlib
import re

from adapters.codex.control_plane import parse_option_comparison_markdown
from adapters.codex.evaluations.models import DecisionObservation


def _normalized_assumption(value: str) -> str:
    """Normalize presentation-only differences before deriving a private fingerprint."""

    return " ".join(value.casefold().split())


def extract_decision_observation(response: str) -> DecisionObservation:
    """Extract one validated selection and hash, rather than store, its assumption."""

    comparison = parse_option_comparison_markdown(response)
    selected = next(
        option
        for option in comparison.alternatives
        if option.id == comparison.recommended_option_id
    )
    assumption = _normalized_assumption(selected.material_assumption)
    if not assumption:
        raise ValueError("selected alternative has no material assumption")

    # Catalog-backed names are public product metadata. A free-form no-pattern label
    # may contain project details, so reduce it to the stable category name.
    selected_name = "No pattern" if selected.category == "No pattern" else selected.name
    return DecisionObservation(
        selected_category=selected.category,
        selected_name=selected_name,
        material_assumption_sha256=hashlib.sha256(assumption.encode("utf-8")).hexdigest(),
        material_assumption_word_count=len(re.findall(r"\b\w+\b", assumption)),
        visible_response_word_count=len(re.findall(r"\b[\w-]+\b", response)),
    )
