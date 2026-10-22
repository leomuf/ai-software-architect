# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Visible clarification contract, without classifying natural-language intent."""

from __future__ import annotations

CLARIFICATION_HEADINGS = {
    "en": "## Clarification needed",
    "de": "## Rückfrage",
    "pt-BR": "## Esclarecimento necessário",
    "es": "## Aclaración necesaria",
}
LEGACY_READ_ONLY_FOOTER = "No files have been created or modified."


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
    if lines[0].rstrip() in CLARIFICATION_HEADINGS.values():
        body = "\n".join(lines[1:]).strip()
        return bool(body) and "?" in body and "```" not in body and "~~~" not in body
    if "```" in visible or "~~~" in visible:
        return False
    paragraphs = visible.rsplit("\n\n", 1)
    if len(paragraphs) == 2 and paragraphs[1].strip() == LEGACY_READ_ONLY_FOOTER:
        visible = paragraphs[0].rstrip()
    return visible.endswith("?")
