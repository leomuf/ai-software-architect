# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Observe real hook continuation state without consuming it or retaining user text."""

from __future__ import annotations

import hashlib
from pathlib import Path

from adapters.codex.continuation import (
    ContinuationManager,
    PendingInteraction,
    WorkflowCheckpointManager,
)
from adapters.codex.evaluations.models import AssertionStatus, DeterministicAssertion
from adapters.codex.hook_entry import MAX_CONTINUATION_AGE_SECONDS


def observe_pending_continuation(
    data_root: Path,
    session_id: str | None,
    expected: str,
) -> tuple[Path | None, DeterministicAssertion]:
    """Locate this fresh session's pending record across host-managed plugin data.

    Only direct plugin-data children are searched. No prompt/response is read, and
    no filename convention for marketplace names is assumed. Ambiguity fails.
    """

    digest = hashlib.sha256((session_id or "").encode()).hexdigest()
    try:
        matches = list(data_root.glob(f"*/control-plane/continuation-{digest}.json"))
        plugin_data = matches[0].parent.parent if len(matches) == 1 and session_id else None
        pending = (
            ContinuationManager(plugin_data, max_age_seconds=MAX_CONTINUATION_AGE_SECONDS).peek(
                session_id or "",
            )
            if plugin_data
            else None
        )
        valid = (
            pending is not None
            and pending.context.active
            and pending.interaction == PendingInteraction(expected)
        )
    except (OSError, ValueError):
        plugin_data, valid = None, False
    return plugin_data, DeterministicAssertion(
        name="architect-continuation-pending",
        status=AssertionStatus.PASS if valid else AssertionStatus.FAIL,
        evidence=(
            f"Observed an unexpired {expected} continuation in actual hook state."
            if valid
            else "Expected pending architect context was missing or unusable."
        ),
    )


def observe_resumed_continuation(
    plugin_data: Path | None,
    session_id: str,
    expected: str,
) -> DeterministicAssertion:
    """Require the follow-up hook to have consumed the expected interaction."""

    checkpoint = WorkflowCheckpointManager(plugin_data).load(session_id) if plugin_data else None
    valid = checkpoint is not None and checkpoint.resumed_interaction == PendingInteraction(
        expected
    )
    return DeterministicAssertion(
        name="architect-continuation-resumed",
        status=AssertionStatus.PASS if valid else AssertionStatus.FAIL,
        evidence=(
            f"The follow-up hook resumed the {expected} context."
            if valid
            else "No hook checkpoint confirms resumption of architect context."
        ),
    )
