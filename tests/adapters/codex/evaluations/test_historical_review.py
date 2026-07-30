# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from adapters.codex.evaluations.historical_review import (
    ExportedTask,
    ExportedTurn,
    HistoricalPhaseReview,
    HistoricalReviewBatch,
    HistoricalTaskExport,
    ReviewConfidence,
    ReviewDecision,
    apply_historical_review,
    build_historical_review_draft,
    fixture_id_from_title,
)
from adapters.codex.evaluations.performance_ledger import load_performance_ledger
from adapters.codex.evaluations.performance_models import PhaseStatus, SpeedMode


def _review(
    *,
    phase: str,
    duration: float,
    decision: ReviewDecision = ReviewDecision.ACCEPTED,
) -> HistoricalPhaseReview:
    started = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)
    return HistoricalPhaseReview(
        source_task_id="thread-1",
        source_task_title="Run14_Exploratory2",
        source_turn_id=f"turn-{phase}",
        campaign_id="Run14",
        fixture_id="architecture-option-comparison",
        fixture_revision="b" * 64,
        workload_fingerprint="c" * 64,
        phase=phase,
        started_at=started,
        completed_at=started + timedelta(seconds=duration),
        duration_seconds=duration,
        decision=decision,
        reason="Completed response with expected decision workflow.",
        confidence=ReviewConfidence.HIGH,
        evidence_sha256="a" * 64,
        model="gpt-5.6-sol",
        reasoning_effort="medium",
        speed=SpeedMode.STANDARD,
        plugin_version="0.1.0",
        codex_version="codex-cli test",
        git_commit="commit-1",
    )


def test_historical_review_applies_accepted_phases_and_keeps_exclusions_out(
    tmp_path: Path,
) -> None:
    batch = HistoricalReviewBatch(
        reviewer_session_id="review-session",
        reviewed_at=datetime.now(UTC),
        phases=[
            _review(phase="initial", duration=10),
            _review(phase="continuation", duration=20),
            _review(
                phase="continuation",
                duration=99,
                decision=ReviewDecision.EXCLUDED,
            ).model_copy(update={"source_turn_id": "turn-aborted"}),
        ],
    )
    ledger = tmp_path / "history.jsonl"

    assert apply_historical_review(batch, ledger) == 1
    record = load_performance_ledger(ledger)[0]
    assert record.timing.measured_phase_seconds == 30
    assert record.phases.continuation.status == PhaseStatus.COMPLETED
    assert apply_historical_review(batch, ledger) == 0


def test_historical_review_preserves_missing_continuation(tmp_path: Path) -> None:
    batch = HistoricalReviewBatch(
        reviewer_session_id="review-session",
        reviewed_at=datetime.now(UTC),
        phases=[_review(phase="initial", duration=10)],
    )
    ledger = tmp_path / "history.jsonl"

    apply_historical_review(batch, ledger)
    record = load_performance_ledger(ledger)[0]
    assert record.phases.continuation.status == PhaseStatus.NOT_RUN
    assert record.phases.continuation.duration_seconds is None


def test_historical_review_aggregates_multiple_continuation_turns(
    tmp_path: Path,
) -> None:
    batch = HistoricalReviewBatch(
        reviewer_session_id="review-session",
        reviewed_at=datetime.now(UTC),
        phases=[
            _review(phase="initial", duration=10),
            _review(phase="continuation", duration=20),
            _review(phase="continuation", duration=5).model_copy(
                update={"source_turn_id": "turn-continuation-2"}
            ),
        ],
    )
    ledger = tmp_path / "history.jsonl"

    apply_historical_review(batch, ledger)
    record = load_performance_ledger(ledger)[0]
    assert record.phases.continuation.duration_seconds == 25
    assert record.timing.measured_phase_seconds == 35


def test_review_draft_maps_names_and_does_not_auto_approve() -> None:
    started = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)
    exported = HistoricalTaskExport(
        exported_at=started,
        archived=True,
        tasks=[
            ExportedTask(
                id="task-1",
                title="Run14_Exploratory2 - Project Pattern Comparison",
                created_at=started,
                updated_at=started + timedelta(seconds=10),
                cwd="C:/project",
                codex_version="codex-cli test",
                turns=[
                    ExportedTurn(
                        id="turn-1",
                        status="completed",
                        started_at=started,
                        completed_at=started + timedelta(seconds=10),
                        duration_seconds=10,
                        user_text="Compare patterns.",
                        agent_text="A complete comparison.",
                        evidence_sha256="a" * 64,
                    )
                ],
            )
        ],
    )

    draft = build_historical_review_draft(
        exported,
        reviewer_session_id="review-session",
        reviewed_at=started,
    )

    assert fixture_id_from_title(
        "Exploratory 4 \N{EN DASH} Abstract Factory examples"
    ) == (
        "abstract-factory-example"
    )
    assert fixture_id_from_title("Run15 - Read-only Architecture Revi…") == (
        "read-only-architecture-review"
    )
    assert draft.phases[0].campaign_id == "Run14"
    assert draft.phases[0].fixture_id == "architecture-option-comparison"
    assert draft.phases[0].decision == ReviewDecision.NEEDS_REVIEW
