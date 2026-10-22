# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from adapters.codex.evaluations.continuation_observation import (
    observe_pending_continuation,
    observe_resumed_continuation,
)
from adapters.codex.evaluations.models import AssertionStatus
from adapters.codex.hook_entry import handle_stop, handle_user_prompt_submit


def _open(data: Path, session: str = "test-session") -> None:
    base = {"session_id": session, "turn_id": "initial"}
    handle_user_prompt_submit({**base, "prompt": "$ai-software-architect Clarify this."}, data)
    handle_stop({**base, "last_assistant_message": "Desktop or browser?"}, data)


def test_decision_resumption_survives_a_completed_stop(tmp_path: Path) -> None:
    data = tmp_path / "plugin"
    base = {"session_id": "decision-session", "turn_id": "initial"}
    handle_user_prompt_submit(
        {**base, "prompt": "$ai-software-architect Recommend one option."}, data
    )
    handle_stop(
        {
            **base,
            "last_assistant_message": "## Your decision\n\nApprove, revise, or ask for details.",
        },
        data,
    )
    found, pending = observe_pending_continuation(tmp_path, "decision-session", "decision")
    assert found == data and pending.status == AssertionStatus.PASS
    followup = {**base, "turn_id": "followup"}
    handle_user_prompt_submit({**followup, "prompt": "Revise the recommendation."}, data)
    handle_stop({**followup, "last_assistant_message": "The review is complete."}, data)
    observed = observe_resumed_continuation(data, "decision-session", "decision")
    assert observed.status == AssertionStatus.PASS


def test_observation_requires_actual_pending_and_consumed_hook_state(tmp_path: Path) -> None:
    data = tmp_path / "marketplace-independent-name"
    _open(data)
    found, assertion = observe_pending_continuation(tmp_path, "test-session", "clarification")
    assert found == data
    assert assertion.status == AssertionStatus.PASS
    assert (
        observe_resumed_continuation(data, "test-session", "clarification").status
        == AssertionStatus.FAIL
    )
    followup = {"session_id": "test-session", "turn_id": "followup"}
    handle_user_prompt_submit({**followup, "prompt": "Desktop."}, data)
    # Stop may renew the pending interaction, but must preserve proof of resumption.
    handle_stop(
        {**followup, "last_assistant_message": "## Clarification needed\n\nWhich OS?"}, data
    )
    assert (
        observe_resumed_continuation(data, "test-session", "clarification").status
        == AssertionStatus.PASS
    )
    assert (
        observe_resumed_continuation(data, "test-session", "decision").status
        == AssertionStatus.FAIL
    )


@pytest.mark.parametrize("condition", ["absent", "wrong-kind", "expired", "ambiguous", "malformed"])
def test_missing_or_unusable_state_fails_observation(tmp_path: Path, condition: str) -> None:
    if condition != "absent":
        _open(tmp_path / "one")
        record = next(tmp_path.glob("*/control-plane/continuation-*.json"))
        if condition == "expired":
            os.utime(record, (time.time() - 7200, time.time() - 7200))
        if condition == "ambiguous":
            _open(tmp_path / "two")
        if condition == "malformed":
            record.write_text("not-json", encoding="utf-8")
    _, assertion = observe_pending_continuation(
        tmp_path,
        "test-session",
        "decision" if condition == "wrong-kind" else "clarification",
    )
    assert assertion.status == AssertionStatus.FAIL
