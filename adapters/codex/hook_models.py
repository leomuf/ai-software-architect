# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Typed boundary models for short-lived Codex hook events."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class HookPayload(BaseModel):
    """Validate stable common fields while preserving event-specific extensions."""

    model_config = ConfigDict(extra="allow", strict=True)

    hook_event_name: Literal[
        "UserPromptSubmit",
        "PreToolUse",
        "PostToolUse",
        "PostCompact",
        "Stop",
    ]
    session_id: str
    turn_id: str | None = None
    cwd: str | None = None
    tool_name: str | None = None
    tool_input: Any = None
