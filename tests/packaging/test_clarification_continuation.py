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


def test_legacy_footer_handles_windows_line_endings() -> None:
    assert is_clarification_response(CAPTURED_INITIAL.replace("\n", "\r\n"))


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
