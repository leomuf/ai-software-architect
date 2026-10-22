# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Visible clarification contract, without classifying natural-language intent."""

from __future__ import annotations

import re

CLARIFICATION_HEADINGS = {
    "en": "## Clarification needed",
    "de": "## Rückfrage",
    "pt-BR": "## Esclarecimento necessário",
    "es": "## Aclaración necesaria",
}
COMPLETION_HEADINGS = {
    "en": "## Result",
    "de": "## Ergebnis",
    "pt-BR": "## Resultado",
    "es": "## Resultado",
}
LEGACY_READ_ONLY_FOOTER = "No files have been created or modified."


def _heading_label(message: str) -> str | None:
    """Read the first ATX heading label, allowing standard heading levels and closers."""

    lines = message.strip().splitlines()
    match = re.fullmatch(r"#{1,6}[ \t]+(.+?)(?:[ \t]+#+)?[ \t]*", lines[0]) if lines else None
    return match[1] if match else None


def declares_clarification(message: str) -> bool:
    """Check an explicit catalog label, without matching natural-language synonyms."""

    return _heading_label(message) in {
        heading.removeprefix("## ") for heading in CLARIFICATION_HEADINGS.values()
    }


def declares_completion(message: str) -> bool:
    """Let a completed explanation contain questions without opening a follow-up."""

    return _heading_label(message) in {
        heading.removeprefix("## ") for heading in COMPLETION_HEADINGS.values()
    }


def clarification_contract_guidance() -> str:
    """Render the same supported declarations used by the parser and correction gate."""

    return " / ".join(
        f"{code}: clarification `{heading}`, completed answer `{COMPLETION_HEADINGS[code]}`"
        for code, heading in CLARIFICATION_HEADINGS.items()
    )


def is_clarification_response(message: str) -> bool:
    """Recognize an explicit heading or the bounded legacy question format.

    A declared clarification may have text after its question. Older responses
    used a final question without a heading; allow their exact, known read-only
    footer too. A question elsewhere in ordinary prose is not an activation signal.
    Code examples and quoted headings do not declare clarification.
    """

    visible = message.strip().replace("\r\n", "\n").replace("\r", "\n")
    lines = visible.splitlines()
    if not lines:
        return False
    if declares_completion(visible):
        return False
    if declares_clarification(visible):
        body = "\n".join(lines[1:]).strip()
        return bool(body) and "?" in body and "```" not in body and "~~~" not in body
    if "```" in visible or "~~~" in visible:
        return False
    paragraphs = visible.rsplit("\n\n", 1)
    if len(paragraphs) == 2 and paragraphs[1].strip() == LEGACY_READ_ONLY_FOOTER:
        visible = paragraphs[0].rstrip()
    return visible.endswith("?")
