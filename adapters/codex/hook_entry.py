# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Bounded JSON and state adapter for the Codex control-plane hooks."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

try:
    from adapters.codex.artifact_guard import (
        architecture_artifact_denial_reason,
        proposed_artifact_candidates,
        validate_artifact_bundle_candidates,
    )
    from adapters.codex.continuation import (
        ApprovalTransition,
        CheckpointPhase,
        ContinuationManager,
        PendingInteraction,
        SessionContinuation,
        WorkflowCheckpoint,
        WorkflowCheckpointManager,
        WorkflowPhase,
    )
    from adapters.codex.control_plane import (
        MISSING_INVOCATION_GUIDANCE,
        CodexTurnContext,
        CodexTurnRoute,
        classify_prompt,
        developer_context,
        final_response_violations,
        repository_snapshot_command,
        tool_denial_reason,
        with_reference_hints,
    )
    from adapters.codex.hook_models import HookPayload
    from adapters.codex.response_locales import (
        ComparisonSection,
        contains_comparison_section,
    )
except ModuleNotFoundError as exc:
    if exc.name != "adapters":
        raise
    from artifact_guard import (  # type: ignore[import-not-found, no-redef]
        architecture_artifact_denial_reason,
        proposed_artifact_candidates,
        validate_artifact_bundle_candidates,
    )
    from continuation import (  # type: ignore[import-not-found, no-redef]
        ApprovalTransition,
        CheckpointPhase,
        ContinuationManager,
        PendingInteraction,
        SessionContinuation,
        WorkflowCheckpoint,
        WorkflowCheckpointManager,
        WorkflowPhase,
    )
    from control_plane import (  # type: ignore[import-not-found, no-redef]
        MISSING_INVOCATION_GUIDANCE,
        CodexTurnContext,
        CodexTurnRoute,
        classify_prompt,
        developer_context,
        final_response_violations,
        repository_snapshot_command,
        tool_denial_reason,
        with_reference_hints,
    )
    from hook_models import HookPayload  # type: ignore[import-not-found, no-redef]
    from response_locales import (  # type: ignore[import-not-found, no-redef]
        ComparisonSection,
        contains_comparison_section,
    )

MAX_HOOK_INPUT_BYTES = 1_000_000
MAX_STATE_AGE_SECONDS = 86_400
MAX_CONTINUATION_AGE_SECONDS = 3_600
MAX_STATE_FILES = 512


def _single_bundled_reference_content(
    plugin_root: Path | None,
    context: CodexTurnContext,
) -> str:
    """Read one catalog-routed trusted reference without semantic route inference."""

    if plugin_root is None or len(context.reference_paths) != 1:
        return ""
    skill_root = (
        plugin_root.resolve(strict=False) / "skills" / "ai-software-architect"
    )
    try:
        trusted_root = skill_root.resolve(strict=True)
        reference = (trusted_root / context.reference_paths[0]).resolve(strict=True)
        reference.relative_to(trusted_root)
        if not reference.is_file():
            return ""
        return reference.read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError):
        return ""


def _turn_state_path(payload: dict[str, Any], plugin_data: Path) -> Path:
    session_id = payload.get("session_id")
    turn_id = payload.get("turn_id")
    if not isinstance(session_id, str) or not session_id:
        raise ValueError("hook session_id is unavailable")
    if not isinstance(turn_id, str) or not turn_id:
        raise ValueError("hook turn_id is unavailable")
    identity = f"{session_id}\0{turn_id}"
    digest = hashlib.sha256(identity.encode("utf-8", errors="replace")).hexdigest()
    return plugin_data / "control-plane" / f"turn-{digest}.json"


def _session_id(payload: dict[str, Any]) -> str:
    session_id = payload.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        raise ValueError("hook session_id is unavailable")
    return session_id


def _write_json_context(path: Path, context: CodexTurnContext) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(asdict(context), sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(path)


def _write_context(
    payload: dict[str, Any],
    context: CodexTurnContext,
    plugin_data: Path,
) -> None:
    _write_json_context(_turn_state_path(payload, plugin_data), context)
    _cleanup_stale_contexts(plugin_data)


def _read_context(
    payload: dict[str, Any],
    plugin_data: Path,
) -> CodexTurnContext:
    try:
        raw = json.loads(_turn_state_path(payload, plugin_data).read_text("utf-8"))
        return CodexTurnContext(
            active=raw["active"],
            route=CodexTurnRoute(raw["route"]),
            reference_paths=tuple(raw.get("reference_paths", ())),
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ):
        return CodexTurnContext(active=False, route=CodexTurnRoute.INACTIVE)


def _remove_context(payload: dict[str, Any], plugin_data: Path) -> None:
    try:
        _turn_state_path(payload, plugin_data).unlink(missing_ok=True)
    except (OSError, ValueError):
        pass


def _pending_continuation(
    message: str,
    context: CodexTurnContext,
) -> SessionContinuation | None:
    visible = message.rstrip()
    if contains_comparison_section(visible, ComparisonSection.USER_DECISION):
        return SessionContinuation(
            context=context,
            interaction=PendingInteraction.DECISION,
            phase=WorkflowPhase.APPROVE,
            approval_transition=ApprovalTransition.RECORD_AND_HANDOFF,
        )
    if visible.endswith("?"):
        return SessionContinuation(
            context=context,
            interaction=PendingInteraction.CLARIFICATION,
            phase=WorkflowPhase.CLARIFY,
            approval_transition=ApprovalTransition.RESUME_DESIGN,
        )
    return None


def _continuation_instruction(continuation: SessionContinuation) -> str:
    if continuation.interaction == PendingInteraction.DECISION:
        return (
            "The preceding response requested a decision. Interpret the user's reply "
            "host-natively and in any language. If the user approves, do not merely "
            "acknowledge approval: transition to `record_and_handoff`, safely create "
            "and validate the approved ADR, architecture contract, context, and coding "
            "handoff when this is a project-bound material decision. Architecture "
            "artifact writes under `.ai-architect/` are authorized by approval unless "
            "the original request explicitly prohibited creating or modifying files. "
            "Approval never authorizes application-code changes. If the original turn "
            "was read-only or projectless, preserve that restriction and plainly "
            "explain why artifacts were not persisted. If the user revises or rejects "
            "the proposal, return to design and persist nothing."
        )
    return (
        "The preceding response requested clarification. Interpret this reply as the "
        "answer, retain the clarified constraints, and resume the smallest sufficient "
        "architecture workflow without requiring another skill invocation."
    )


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


def handle_user_prompt_submit(
    payload: dict[str, Any],
    plugin_data: Path,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    prompt = payload.get("prompt")
    prompt_text = prompt if isinstance(prompt, str) else ""
    context = with_reference_hints(classify_prompt(prompt_text), prompt_text)
    continuation: SessionContinuation | None = None
    continuations = ContinuationManager(
        plugin_data,
        max_age_seconds=MAX_CONTINUATION_AGE_SECONDS,
    )
    if not context.active:
        has_other_activation = (
            re.search(r"\$[a-z0-9][a-z0-9-]*", prompt_text, flags=re.IGNORECASE)
            is not None
            or "plugin://" in prompt_text.casefold()
        )
        if has_other_activation:
            continuations.cancel(_session_id(payload))
            return {}
        continuation = continuations.consume(_session_id(payload))
        if continuation is None:
            return {}
        context = continuation.context
    if context.route == CodexTurnRoute.MISSING_SKILL_INVOCATION:
        continuations.cancel(_session_id(payload))
        _cleanup_stale_contexts(plugin_data)
        return {
            "decision": "block",
            "reason": MISSING_INVOCATION_GUIDANCE,
        }
    if continuation is None:
        continuations.cancel(_session_id(payload))
    checkpoints = WorkflowCheckpointManager(plugin_data)
    if continuation is None:
        checkpoint = WorkflowCheckpoint(phase=CheckpointPhase.ACTIVE)
    elif continuation.interaction == PendingInteraction.DECISION:
        checkpoint = WorkflowCheckpoint(
            phase=CheckpointPhase.DECISION_RESPONSE,
            expected_artifacts=["adr", "contract", "context", "implementation-plan"],
        )
    else:
        checkpoint = WorkflowCheckpoint(phase=CheckpointPhase.ACTIVE)
    checkpoints.save(_session_id(payload), checkpoint)
    _write_context(payload, context, plugin_data)
    additional_context = developer_context(
        context,
        continued=continuation is not None,
        continuation_instruction=(
            _continuation_instruction(continuation)
            if continuation is not None
            else ""
        ),
        continuation_interaction=(
            continuation.interaction.value if continuation is not None else None
        ),
        snapshot_command=(
            repository_snapshot_command(plugin_root)
            if plugin_root is not None
            else ""
        ),
        comparison_bundle_path=(
            str(
                plugin_root.resolve(strict=False)
                / "skills"
                / "ai-software-architect"
                / "references"
                / "workflow-evaluate-architecture-options.md"
            )
            if plugin_root is not None
            else ""
        ),
        bundled_reference_content=_single_bundled_reference_content(
            plugin_root,
            context,
        ),
    )
    if (
        plugin_root is not None
        and continuation is not None
        and continuation.interaction == PendingInteraction.DECISION
    ):
        skill_root = plugin_root.resolve(strict=False) / "skills" / "ai-software-architect"
        resource = skill_root / "assets" / "artifact-authoring-bundle.md"
        additional_context += (
            " Exact installed record-and-handoff resource path (authoritative; read "
            "this generated bundle once with a host-native static file tool and do not "
            "search for or separately load its canonical source files): "
            + str(resource)
            + "."
        )
    return {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": additional_context,
        }
    }


def handle_pre_tool_use(
    payload: dict[str, Any],
    plugin_data: Path,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    context = _read_context(payload, plugin_data)
    workspace = (
        Path(payload["cwd"])
        if isinstance(payload.get("cwd"), str) and payload["cwd"]
        else None
    )
    reason = tool_denial_reason(
        context,
        payload.get("tool_name"),
        payload.get("tool_input"),
        workspace=workspace,
        plugin_root=plugin_root,
    )
    if reason is None and context.active:
        local_name = str(payload.get("tool_name", "")).rsplit(".", 1)[-1].casefold()
        if local_name in {"apply_patch", "edit", "write"}:
            if workspace is None:
                reason = (
                    "AI Software Architect denied the architecture artifact write because "
                    "Codex did not provide a trustworthy workspace root."
                )
            else:
                checkpoint = WorkflowCheckpointManager(plugin_data).load(
                    _session_id(payload)
                )
                reason = architecture_artifact_denial_reason(
                    payload.get("tool_input"),
                    workspace,
                    require_complete_bundle=(
                        checkpoint is not None
                        and checkpoint.phase == CheckpointPhase.DECISION_RESPONSE
                    ),
                )
    if reason is None:
        return {}
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def handle_post_tool_use(
    payload: dict[str, Any],
    plugin_data: Path,
) -> dict[str, Any]:
    """Verify the durable postconditions of an approved artifact write."""

    context = _read_context(payload, plugin_data)
    if not context.active:
        return {}
    local_name = str(payload.get("tool_name", "")).rsplit(".", 1)[-1].casefold()
    if local_name not in {"apply_patch", "edit", "write"}:
        return {}
    cwd = payload.get("cwd")
    if not isinstance(cwd, str) or not cwd:
        return {
            "continue": False,
            "stopReason": (
                "AI Software Architect stopped because Codex did not provide a "
                "trustworthy workspace root for post-write verification."
            ),
            "systemMessage": "Architecture artifact post-write verification failed.",
        }
    workspace = Path(cwd)
    try:
        candidates = proposed_artifact_candidates(payload.get("tool_input"), workspace)
        if not candidates:
            raise ValueError("no reconstructable architecture artifact candidate")
        for candidate in candidates:
            persisted = (workspace / candidate.path).read_text("utf-8")
            if persisted != candidate.content:
                raise ValueError(
                    "persisted content differs from validated candidate: "
                    f"{candidate.path.as_posix()}"
                )
        bundle = validate_artifact_bundle_candidates(candidates)
    except (OSError, UnicodeError, ValueError) as exc:
        return {
            "continue": False,
            "stopReason": (
                "AI Software Architect stopped because post-write verification failed: "
                f"{exc}. Review the repository before continuing."
            ),
            "systemMessage": "Architecture artifact post-write verification failed.",
        }
    if bundle is None:
        return {}
    WorkflowCheckpointManager(plugin_data).save(
        _session_id(payload),
        WorkflowCheckpoint(
            phase=CheckpointPhase.COMPLETE,
            expected_artifacts=["adr", "contract", "context", "implementation-plan"],
            artifact_bundle_validated=True,
        ),
    )
    return {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                "The persisted ADR, architecture contract, project context, and coding "
                "handoff exactly match the pre-write validated bundle. State that the "
                "architecture artifacts were recorded and that application source code "
                "was not authorized by this workflow."
            ),
        }
    }


def handle_post_compact(
    payload: dict[str, Any],
    plugin_data: Path,
) -> dict[str, Any]:
    """Restore only the minimal typed workflow checkpoint after compaction."""

    checkpoint = WorkflowCheckpointManager(plugin_data).load(_session_id(payload))
    if checkpoint is None or checkpoint.phase == CheckpointPhase.COMPLETE:
        return {}
    expected = ", ".join(checkpoint.expected_artifacts) or "none"
    return {
        "hookSpecificOutput": {
            "hookEventName": "PostCompact",
            "additionalContext": (
                "AI Software Architect typed workflow checkpoint: phase="
                f"{checkpoint.phase.value}; expected_artifacts={expected}; "
                "artifact_bundle_validated=false. Preserve the current approval and "
                "read-only boundaries; do not reconstruct workflow state from memory."
            ),
        }
    }


def handle_stop(
    payload: dict[str, Any],
    plugin_data: Path,
) -> dict[str, Any]:
    context = _read_context(payload, plugin_data)
    if not context.active:
        return {}
    message = payload.get("last_assistant_message")
    message_text = message if isinstance(message, str) else ""
    continuations = ContinuationManager(
        plugin_data,
        max_age_seconds=MAX_CONTINUATION_AGE_SECONDS,
    )
    if payload.get("stop_hook_active") is True:
        pending = _pending_continuation(message_text, context)
        if pending is not None:
            continuations.open(_session_id(payload), pending)
            WorkflowCheckpointManager(plugin_data).save(
                _session_id(payload),
                WorkflowCheckpoint(
                    phase=(
                        CheckpointPhase.AWAIT_DECISION
                        if pending.interaction == PendingInteraction.DECISION
                        else CheckpointPhase.CLARIFY
                    )
                ),
            )
        else:
            continuations.cancel(_session_id(payload))
        _remove_context(payload, plugin_data)
        return {}
    violations = final_response_violations(
        context,
        message_text,
    )
    if not violations:
        _remove_context(payload, plugin_data)
        pending = _pending_continuation(message_text, context)
        if pending is not None:
            continuations.open(_session_id(payload), pending)
            WorkflowCheckpointManager(plugin_data).save(
                _session_id(payload),
                WorkflowCheckpoint(
                    phase=(
                        CheckpointPhase.AWAIT_DECISION
                        if pending.interaction == PendingInteraction.DECISION
                        else CheckpointPhase.CLARIFY
                    )
                ),
            )
        else:
            continuations.cancel(_session_id(payload))
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
    expected_event: str | None = None,
) -> dict[str, Any]:
    handlers = {
        "UserPromptSubmit": handle_user_prompt_submit,
        "PreToolUse": handle_pre_tool_use,
        "PostToolUse": handle_post_tool_use,
        "PostCompact": handle_post_compact,
        "Stop": handle_stop,
    }
    event = payload.get("hook_event_name")
    if not isinstance(event, str):
        raise ValueError("hook_event_name is unavailable")
    if expected_event is not None and event != expected_event:
        raise ValueError("hook event does not match the invoked hook entry point")
    handler = handlers.get(event)
    HookPayload.model_validate(payload)
    if handler is handle_user_prompt_submit:
        return handler(payload, plugin_data, plugin_root)
    if handler is handle_pre_tool_use:
        return handler(payload, plugin_data, plugin_root)
    return handler(payload, plugin_data) if handler else {}


def _runtime_failure_response(expected_event: str | None, diagnostic: str) -> dict[str, Any]:
    message = (
        "AI Software Architect control-plane validation failed; the protected operation "
        "was not allowed."
        + diagnostic
    )
    if expected_event == "PreToolUse":
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": message,
            },
            "systemMessage": message,
        }
    if expected_event == "PostToolUse":
        return {
            "continue": False,
            "stopReason": message,
            "systemMessage": message,
        }
    return {"systemMessage": message}


def main(expected_event: str | None = None) -> None:
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
        response = handle_hook(
            payload,
            Path(plugin_data_text),
            plugin_root,
            expected_event=expected_event,
        )
    except Exception as exc:
        diagnostic = ""
        if os.environ.get("AI_ARCHITECT_HOOK_DEBUG") == "1":
            diagnostic = f" Diagnostic: {type(exc).__name__}: {exc}"
        response = _runtime_failure_response(expected_event, diagnostic)
    sys.stdout.write(json.dumps(response, separators=(",", ":")))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
