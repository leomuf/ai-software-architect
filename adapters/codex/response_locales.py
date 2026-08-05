# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Declarative user-facing comparison labels for the Codex control plane."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ComparisonSection(StrEnum):
    DECISION_SCOPE = "decision_scope"
    EVIDENCE = "evidence"
    ALTERNATIVES = "alternatives"
    RECOMMENDATION = "recommendation"
    SUPPORTING_PATTERNS = "supporting_patterns"
    USER_DECISION = "user_decision"


SECTION_ORDER = tuple(ComparisonSection)


@dataclass(frozen=True)
class ComparisonLocale:
    """One complete visible label set; adding a locale requires no parser changes."""

    code: str
    headings: tuple[str, ...]
    table_headers: tuple[str, ...]
    fit_disclosure: str
    choose_prefix: str
    no_supporting_patterns: str

    def heading(self, section: ComparisonSection) -> str:
        return self.headings[SECTION_ORDER.index(section)]


COMPARISON_LOCALES = (
    ComparisonLocale(
        code="en",
        headings=(
            "## Decision scope and criteria",
            "## Evidence and assumptions",
            "## Alternatives",
            "## Recommendation",
            "## Supporting patterns",
            "## Your decision",
        ),
        table_headers=(
            "Option",
            "Fit",
            "Rationale",
            "Main benefit",
            "Main liability",
            "Material assumption",
        ),
        fit_disclosure=(
            "Fit is an ordinal `NN/100` score for this decision, not a probability "
            "or measured percentage."
        ),
        choose_prefix="Choose",
        no_supporting_patterns="No supporting patterns are required.",
    ),
    ComparisonLocale(
        code="de",
        headings=(
            "## Entscheidungsumfang und Kriterien",
            "## Evidenz und Annahmen",
            "## Alternativen",
            "## Empfehlung",
            "## Unterstützende Patterns",
            "## Deine Entscheidung",
        ),
        table_headers=(
            "Option",
            "Fit",
            "Begründung",
            "Hauptvorteil",
            "Hauptnachteil",
            "Wesentliche Annahme",
        ),
        fit_disclosure=(
            "Fit ist ein ordinaler `NN/100`-Wert für diese Entscheidung, keine "
            "Wahrscheinlichkeit und kein gemessener Prozentsatz."
        ),
        choose_prefix="Wähle",
        no_supporting_patterns="Es sind keine unterstützenden Patterns erforderlich.",
    ),
)


def comparison_locale(code: str) -> ComparisonLocale:
    normalized = code.casefold()
    for locale in COMPARISON_LOCALES:
        if locale.code.casefold() == normalized:
            return locale
    raise ValueError(f"unsupported comparison response locale: {code}")


def matching_comparison_locale(message: str) -> ComparisonLocale:
    matches = []
    for locale in COMPARISON_LOCALES:
        positions = [message.find(heading) for heading in locale.headings]
        if all(position >= 0 for position in positions) and positions == sorted(positions):
            matches.append(locale)
    if len(matches) != 1:
        raise ValueError("comparison must use exactly one complete localized heading set")
    return matches[0]


def contains_comparison_section(message: str, section: ComparisonSection) -> bool:
    return any(locale.heading(section) in message for locale in COMPARISON_LOCALES)


def locale_containing_section(
    message: str,
    section: ComparisonSection,
) -> ComparisonLocale:
    matches = [
        locale for locale in COMPARISON_LOCALES if locale.heading(section) in message
    ]
    if len(matches) != 1:
        raise ValueError("response must use one unambiguous localized section heading")
    return matches[0]


def comparison_contract_guidance() -> str:
    rendered = []
    for locale in COMPARISON_LOCALES:
        headings = ", ".join(f"`{heading}`" for heading in locale.headings)
        headers = " | ".join(locale.table_headers)
        rendered.append(f"{locale.code}: {headings}; table `{headers}`")
    return " Choose exactly one complete label set matching the user's language: " + " / ".join(
        rendered
    )
