# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Typed, single-use continuation state for Codex architecture sessions."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path

try:
    from adapters.codex.control_plane import CodexTurnContext, CodexTurnRoute
except ModuleNotFoundError as exc:
    if exc.name != "adapters":
        raise
    from control_plane import (  # type: ignore[import-not-found, no-redef]
        CodexTurnContext,
        CodexTurnRoute,
    )


class PendingInteraction(StrEnum):
    CLARIFICATION = "clarification"
    DECISION = "decision"


class WorkflowPhase(StrEnum):
    CLARIFY = "clarify"
    APPROVE = "approve"


class ApprovalTransition(StrEnum):
    RESUME_DESIGN = "resume_design"
    RECORD_AND_HANDOFF = "record_and_handoff"


@dataclass(frozen=True)
class SessionContinuation:
    context: CodexTurnContext
    interaction: PendingInteraction
    phase: WorkflowPhase
    approval_transition: ApprovalTransition


class ContinuationManager:
    def __init__(self, plugin_data: Path, *, max_age_seconds: int) -> None:
        self._root = plugin_data / "control-plane"
        self._max_age_seconds = max_age_seconds

    def _path(self, session_id: str) -> Path:
        digest = hashlib.sha256(session_id.encode("utf-8", errors="replace")).hexdigest()
        return self._root / f"continuation-{digest}.json"

    def open(self, session_id: str, continuation: SessionContinuation) -> None:
        path = self._path(session_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(asdict(continuation), sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        temporary.replace(path)

    def consume(self, session_id: str) -> SessionContinuation | None:
        path = self._path(session_id)
        try:
            raw = json.loads(path.read_text("utf-8"))
            if time.time() - path.stat().st_mtime > self._max_age_seconds:
                return None
            context_raw = raw["context"]
            return SessionContinuation(
                context=CodexTurnContext(
                    active=context_raw["active"],
                    route=CodexTurnRoute(context_raw["route"]),
                    reference_paths=tuple(context_raw.get("reference_paths", ())),
                ),
                interaction=PendingInteraction(raw["interaction"]),
                phase=WorkflowPhase(raw["phase"]),
                approval_transition=ApprovalTransition(raw["approval_transition"]),
            )
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None
        finally:
            path.unlink(missing_ok=True)

    def cancel(self, session_id: str) -> None:
        self._path(session_id).unlink(missing_ok=True)
