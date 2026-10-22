# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

from pathlib import Path

import pytest

from adapters.codex.clarification import CLARIFICATION_HEADINGS, is_clarification_response
from adapters.codex.continuation import ContinuationManager, PendingInteraction
from adapters.codex.hook_entry import (
    MAX_CONTINUATION_AGE_SECONDS,
    handle_pre_tool_use,
    handle_stop,
    handle_user_prompt_submit,
)
from adapters.codex.inspection import RESOURCE_REQUEST

CAPTURED_INITIAL = (
    "Tkinter creates a native desktop interface, not a browser-based web interface. "
    "Which do you intend: a desktop application using Tkinter, or a web application "
    "using a Python framework such as FastAPI with an HTML/JavaScript frontend?\n\n"
    "No files have been created or modified."
)
CAPTURED_GERMAN = (
    "### Klärung erforderlich\n\n"
    "Tkinter erstellt eine native Desktop-Oberfläche, keine Weboberfläche im Browser. "
    "Welche Variante möchtest du bauen?\n\n"
    "1. **Desktop-Anwendung mit Tkinter**\n"
    "2. **Browserbasierte Webanwendung**, beispielsweise mit FastAPI und einer Web-UI\n\n"
    "Danach kann ich passende Architekturen vergleichen. "
    "Ich werde dabei keine Dateien erstellen oder verändern."
)


def test_legacy_footer_handles_windows_line_endings() -> None:
    assert is_clarification_response(CAPTURED_INITIAL.replace("\n", "\r\n"))


def test_unknown_heading_is_corrected_before_clarification_handoff(tmp_path: Path) -> None:
    base = {"session_id": "german-replay", "turn_id": "initial"}
    handle_user_prompt_submit(
        {**base, "prompt": "$ai-software-architect Kläre die Oberfläche."}, tmp_path
    )
    rejected = handle_stop({**base, "last_assistant_message": CAPTURED_GERMAN}, tmp_path)
    assert rejected["decision"] == "block"
    assert "Rückfrage" in rejected["reason"]
    assert "Result" in rejected["reason"]
    corrected = CAPTURED_GERMAN.replace("### Klärung erforderlich", "### Rückfrage", 1)
    assert (
        handle_stop(
            {
                **base,
                "last_assistant_message": corrected,
                "stop_hook_active": True,
            },
            tmp_path,
        )
        == {}
    )
    resumed = handle_user_prompt_submit(
        {
            **base,
            "turn_id": "followup",
            "prompt": "Eine Desktop-Anwendung mit Tkinter.",
        },
        tmp_path,
    )
    assert "typed clarification continuation" in str(resumed)


@pytest.mark.parametrize("level", range(1, 7))
def test_standard_heading_levels_preserve_portuguese_clarification(level: int) -> None:
    message = "#" * level + " Esclarecimento necessário\n\nDesktop ou navegador?\n\nSem alterações."
    assert is_clarification_response(message)


def test_completed_answer_can_contain_a_question_without_requesting_a_reply(tmp_path: Path) -> None:
    base = {"session_id": "result", "turn_id": "initial"}
    handle_user_prompt_submit({**base, "prompt": "$ai-software-architect Explain this."}, tmp_path)
    assert (
        handle_stop(
            {
                **base,
                "last_assistant_message": "## Result\n\nAn example question is: Is this necessary?",
            },
            tmp_path,
        )
        == {}
    )
    assert (
        handle_user_prompt_submit(
            {
                **base,
                "turn_id": "unrelated",
                "prompt": "Tell me the time.",
            },
            tmp_path,
        )
        == {}
    )


def test_ambiguous_question_is_not_automatically_treated_as_clarification(tmp_path: Path) -> None:
    base = {"session_id": "ambiguous", "turn_id": "initial"}
    handle_user_prompt_submit(
        {**base, "prompt": "$ai-software-architect Explain the tradeoff."}, tmp_path
    )
    text = "Why add an interface? It is useful only when implementations vary."
    assert handle_stop({**base, "last_assistant_message": text}, tmp_path)["decision"] == "block"
    manager = ContinuationManager(tmp_path, max_age_seconds=MAX_CONTINUATION_AGE_SECONDS)
    assert manager.peek("ambiguous") is None
    assert (
        handle_stop(
            {
                **base,
                "last_assistant_message": "## Result\n\n" + text,
                "stop_hook_active": True,
            },
            tmp_path,
        )
        == {}
    )
    assert (
        handle_user_prompt_submit(
            {
                **base,
                "turn_id": "next",
                "prompt": "What time is it?",
            },
            tmp_path,
        )
        == {}
    )


def test_question_marks_in_code_do_not_require_a_response_declaration(tmp_path: Path) -> None:
    base = {"session_id": "code-question", "turn_id": "initial"}
    handle_user_prompt_submit(
        {**base, "prompt": "$ai-software-architect Explain the example."}, tmp_path
    )
    text = "Example:\n\n```python\nlabel = 'Question?'\n```\n\nThis is a string literal."
    assert handle_stop({**base, "last_assistant_message": text}, tmp_path) == {}


@pytest.mark.parametrize("heading", CLARIFICATION_HEADINGS.values())
def test_explicit_clarification_allows_trailing_text(heading: str) -> None:
    assert is_clarification_response(f"{heading}\n\nDesktop or browser?\n\nStatus: read-only.")


@pytest.mark.parametrize(
    "message",
    [
        "Would a server help? The current evidence does not justify one.",
        "> ## Clarification needed\n\nQuoted question?\n\nA quoted example.",
        "```python\nvalue = 'question?'\n```",
        "An example:\n\n```text\n## Clarification needed\nQuestion?\n```",
        "## Clarification needed\n\nNo question was supplied.",
        "",
    ],
)
def test_incidental_or_incomplete_questions_do_not_open_continuation(message: str) -> None:
    assert not is_clarification_response(message)


@pytest.mark.parametrize("corrected_stop", [False, True])
@pytest.mark.parametrize(
    "message", [CAPTURED_INITIAL, f"## Clarification needed\n\n{CAPTURED_INITIAL}"]
)
def test_captured_clarification_keeps_reads_and_validation_active(
    tmp_path: Path,
    message: str,
    corrected_stop: bool,
) -> None:
    data = tmp_path / "data"
    root = tmp_path / "plugin"
    resource = (
        root / "skills/ai-software-architect/references/workflow-evaluate-architecture-options.md"
    )
    resource.parent.mkdir(parents=True)
    resource.write_text("# Trusted workflow\nCompare proportionate options.\n", encoding="utf-8")
    base = {"session_id": "captured-case", "turn_id": "initial"}
    handle_user_prompt_submit(
        {
            **base,
            "prompt": "$ai-software-architect Clarify the interface.",
        },
        data,
        root,
    )
    assert (
        handle_stop(
            {
                **base,
                "last_assistant_message": message,
                "stop_hook_active": corrected_stop,
            },
            data,
        )
        == {}
    )
    pending = ContinuationManager(data, max_age_seconds=MAX_CONTINUATION_AGE_SECONDS).peek(
        "captured-case",
    )
    assert pending is not None and pending.interaction == PendingInteraction.CLARIFICATION

    followup = {**base, "turn_id": "followup"}
    continued = handle_user_prompt_submit(
        {
            **followup,
            "prompt": "Use a local desktop interface with Python Tkinter.",
        },
        data,
        root,
    )
    assert "typed clarification continuation" in str(continued)
    tool = handle_pre_tool_use(
        {
            **followup,
            "tool_name": "exec_command",
            "tool_input": {
                "cmd": RESOURCE_REQUEST + "references/workflow-evaluate-architecture-options.md"
            },
        },
        data,
        root,
    )
    assert tool["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "Trusted workflow" in tool["hookSpecificOutput"]["permissionDecisionReason"]
    unsafe = handle_pre_tool_use(
        {
            **followup,
            "tool_name": "exec_command",
            "tool_input": {"cmd": "python project.py"},
        },
        data,
        root,
    )
    assert unsafe["hookSpecificOutput"]["permissionDecision"] == "deny"
    invalid = handle_stop(
        {
            **followup,
            "last_assistant_message": (
                "Use [Architecture] [Layered Architecture](https://example.invalid/wrong)."
            ),
        },
        data,
    )
    assert invalid["decision"] == "block"
    assert "architecture-layered.md" in invalid["reason"]
    assert (
        handle_stop({**followup, "last_assistant_message": "The review is complete."}, data) == {}
    )
    assert (
        handle_user_prompt_submit(
            {
                **base,
                "turn_id": "unrelated",
                "prompt": "What time is it?",
            },
            data,
        )
        == {}
    )


def test_declared_clarification_without_a_question_is_corrected(tmp_path: Path) -> None:
    base = {"session_id": "session", "turn_id": "turn"}
    handle_user_prompt_submit({**base, "prompt": "$ai-software-architect Clarify this."}, tmp_path)
    result = handle_stop(
        {
            **base,
            "last_assistant_message": "## Clarification needed\n\nI need more information.",
        },
        tmp_path,
    )
    assert result["decision"] == "block"
    assert "visible focused question" in result["reason"]
