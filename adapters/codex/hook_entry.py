# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Bounded JSON and state adapter for the Codex control-plane hooks."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

try:
    from adapters.codex.control_plane import (
        MISSING_INVOCATION_GUIDANCE,
        CodexTurnContext,
        CodexTurnRoute,
        classify_prompt,
        developer_context,
        final_response_violations,
        tool_denial_reason,
    )
except ModuleNotFoundError as exc:
    if exc.name != "adapters":
        raise
    from control_plane import (  # type: ignore[import-not-found, no-redef]
        MISSING_INVOCATION_GUIDANCE,
        CodexTurnContext,
        CodexTurnRoute,
        classify_prompt,
        developer_context,
        final_response_violations,
        tool_denial_reason,
    )

MAX_HOOK_INPUT_BYTES = 1_000_000
MAX_BUNDLED_REFERENCE_BYTES = 200_000
MAX_STATE_AGE_SECONDS = 86_400
MAX_STATE_FILES = 512


def _reference_root(plugin_root: Path) -> Path:
    return (
        plugin_root
        / "skills"
        / "evaluate-architecture-options"
        / "references"
    ).resolve()


def _available_reference_slugs(plugin_root: Path | None) -> tuple[str, ...]:
    if plugin_root is None:
        return ()
    reference_root = _reference_root(plugin_root)
    try:
        return tuple(
            sorted(
                path.stem
                for path in reference_root.glob("*.md")
                if path.is_file() and path.resolve().parent == reference_root
            )
        )
    except OSError:
        return ()


def _state_path(payload: dict[str, Any], plugin_data: Path) -> Path:
    session_id = payload.get("session_id")
    turn_id = payload.get("turn_id")
    if not isinstance(session_id, str) or not session_id:
        raise ValueError("hook session_id is unavailable")
    if not isinstance(turn_id, str) or not turn_id:
        raise ValueError("hook turn_id is unavailable")
    identity = f"{session_id}\0{turn_id}"
    digest = hashlib.sha256(identity.encode("utf-8", errors="replace")).hexdigest()
    return plugin_data / "control-plane" / f"{digest}.json"


def _write_context(
    payload: dict[str, Any],
    context: CodexTurnContext,
    plugin_data: Path,
) -> None:
    path = _state_path(payload, plugin_data)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(asdict(context), sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(path)
    _cleanup_stale_contexts(plugin_data)


def _read_context(
    payload: dict[str, Any],
    plugin_data: Path,
) -> CodexTurnContext:
    try:
        raw = json.loads(_state_path(payload, plugin_data).read_text("utf-8"))
        return CodexTurnContext(
            active=raw["active"],
            route=CodexTurnRoute(raw["route"]),
            reference_slug=raw.get("reference_slug"),
        )
    except (FileNotFoundError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return CodexTurnContext(active=False, route=CodexTurnRoute.INACTIVE)


def _remove_context(payload: dict[str, Any], plugin_data: Path) -> None:
    try:
        _state_path(payload, plugin_data).unlink(missing_ok=True)
    except (OSError, ValueError):
        pass


def _cleanup_stale_contexts(
    plugin_data: Path,
    *,
    now: float | None = None,
) -> None:
    state_root = plugin_data / "control-plane"
    try:
        candidates = [
            (path.stat().st_mtime, path)
            for path in state_root.glob("*.json")
            if path.is_file()
        ]
    except OSError:
        return
    current_time = time.time() if now is None else now
    candidates.sort(reverse=True)
    for index, (modified, path) in enumerate(candidates):
        if index >= MAX_STATE_FILES or current_time - modified > MAX_STATE_AGE_SECONDS:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass


def _bundled_reference_context(
    context: CodexTurnContext,
    plugin_root: Path | None,
) -> str:
    if context.reference_slug is None or plugin_root is None:
        return ""
    reference_root = _reference_root(plugin_root)
    reference_path = (reference_root / f"{context.reference_slug}.md").resolve()
    if reference_path.parent != reference_root:
        raise ValueError("bundled reference escaped its reference directory")
    raw = reference_path.read_bytes()
    if len(raw) > MAX_BUNDLED_REFERENCE_BYTES:
        raise ValueError("bundled reference exceeds the bounded context size")
    reference_text = raw.decode("utf-8")
    return (
        "\n\nThe trusted bundled canonical reference is included below. Use its "
        "Python example verbatim when the user's generic request does not require "
        "domain adaptation. Do not fetch another copy from the web.\n"
        "<bundled-canonical-reference>\n"
        + reference_text
        + "\n</bundled-canonical-reference>"
    )


def handle_user_prompt_submit(
    payload: dict[str, Any],
    plugin_data: Path,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    prompt = payload.get("prompt")
    context = classify_prompt(
        prompt if isinstance(prompt, str) else "",
        _available_reference_slugs(plugin_root),
    )
    if not context.active:
        return {}
    if context.route == CodexTurnRoute.MISSING_SKILL_INVOCATION:
        _cleanup_stale_contexts(plugin_data)
        return {
            "decision": "block",
            "reason": MISSING_INVOCATION_GUIDANCE,
        }
    _write_context(payload, context, plugin_data)
    return {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": (
                developer_context(context)
                + _bundled_reference_context(context, plugin_root)
            ),
        }
    }


def handle_pre_tool_use(
    payload: dict[str, Any],
    plugin_data: Path,
) -> dict[str, Any]:
    context = _read_context(payload, plugin_data)
    reason = tool_denial_reason(context, payload.get("tool_name"))
    if reason is None:
        return {}
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def handle_stop(
    payload: dict[str, Any],
    plugin_data: Path,
) -> dict[str, Any]:
    context = _read_context(payload, plugin_data)
    if not context.active:
        return {}
    if payload.get("stop_hook_active") is True:
        _remove_context(payload, plugin_data)
        return {}
    message = payload.get("last_assistant_message")
    violations = final_response_violations(
        context,
        message if isinstance(message, str) else "",
    )
    _remove_context(payload, plugin_data)
    if not violations:
        return {}
    return {
        "decision": "block",
        "reason": (
            "The AI Software Architect response did not pass its deterministic "
            "user-facing contract. Return a complete standalone replacement response "
            "that preserves all already-valid content; do not return an addendum or "
            "only the missing sentence. Correct these issues: "
            + "; ".join(violations)
            + "."
        ),
    }


def handle_hook(
    payload: dict[str, Any],
    plugin_data: Path,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    handlers = {
        "UserPromptSubmit": handle_user_prompt_submit,
        "PreToolUse": handle_pre_tool_use,
        "Stop": handle_stop,
    }
    event = payload.get("hook_event_name")
    if not isinstance(event, str):
        return {}
    handler = handlers.get(event)
    if handler is handle_user_prompt_submit:
        return handler(payload, plugin_data, plugin_root)
    return handler(payload, plugin_data) if handler else {}


def main() -> None:
    """Read one bounded hook event from stdin and emit one JSON response."""

    try:
        raw = sys.stdin.buffer.read(MAX_HOOK_INPUT_BYTES + 1)
        if len(raw) > MAX_HOOK_INPUT_BYTES:
            raise ValueError("hook input exceeds the bounded input size")
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise TypeError("hook input must be a JSON object")
        plugin_data_text = os.environ.get("PLUGIN_DATA")
        if not plugin_data_text:
            raise ValueError("PLUGIN_DATA is unavailable")
        plugin_root_text = os.environ.get("PLUGIN_ROOT")
        plugin_root = Path(plugin_root_text) if plugin_root_text else None
        response = handle_hook(payload, Path(plugin_data_text), plugin_root)
    except Exception:
        response = {
            "systemMessage": (
                "AI Software Architect control-plane hook failed open; deterministic "
                "turn validation was unavailable."
            )
        }
    sys.stdout.write(json.dumps(response, separators=(",", ":")))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
