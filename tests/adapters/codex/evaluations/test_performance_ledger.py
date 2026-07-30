# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from adapters.codex.evaluations.historical_review import (
    HistoricalReviewBatch,
    ReviewDecision,
)
from adapters.codex.evaluations.models import PhaseTelemetry
from adapters.codex.evaluations.performance_ledger import (
    append_performance_observations,
    load_performance_ledger,
)
from adapters.codex.evaluations.performance_models import (
    CampaignMetadata,
    EvaluationOutcome,
    ExecutionMode,
    MeasurementQuality,
    ObservationSource,
    PhaseMeasurement,
    PhaseMeasurements,
    PhaseStatus,
    ResultMetadata,
    RuntimeMetadata,
    SpeedMode,
    TimingMetadata,
    build_performance_observation,
)
from adapters.codex.evaluations.performance_models import (
    TestMetadata as PerformanceTestMetadata,
)

HASH = "a" * 64
ROOT = Path(__file__).resolve().parents[4]


def observation(*, continuation: float | None = None, telemetry: bool = False):
    started = datetime(2026, 7, 21, 19, 50, tzinfo=UTC)
    phases = PhaseMeasurements(
        initial=PhaseMeasurement(
            status=PhaseStatus.COMPLETED,
            duration_seconds=12.5,
            telemetry=(
                PhaseTelemetry(
                    first_event_seconds=0.1,
                    first_agent_message_seconds=12.0,
                    last_agent_message_seconds=12.0,
                    agent_message_count=1,
                    tool_call_count=0,
                    input_tokens=100,
                    output_tokens=20,
                )
                if telemetry
                else None
            ),
        ),
        continuation=(
            PhaseMeasurement(status=PhaseStatus.COMPLETED, duration_seconds=continuation)
            if continuation is not None
            else PhaseMeasurement(status=PhaseStatus.NOT_RUN)
        ),
    )
    return build_performance_observation(
        campaign=CampaignMetadata(
            id="Run15",
            execution_mode=ExecutionMode.PARALLEL_CODEX_TASKS,
            started_at=started,
            completed_at=started + timedelta(seconds=20),
            wall_clock_seconds=20,
        ),
        test=PerformanceTestMetadata(
            fixture_id="architecture-option-comparison",
            fixture_revision=HASH,
            workload_fingerprint=HASH,
            task_name="Run15_Exploratory2",
            task_id="thread-123",
        ),
        runtime=RuntimeMetadata(
            model="gpt-5.6-sol",
            reasoning_effort="medium",
            speed=SpeedMode.STANDARD,
            codex_version="codex-cli test",
            plugin_version="0.1.0",
            plugin_provenance=HASH,
            git_commit="ded61ae",
            host="windows-x86_64",
        ),
        phases=phases,
        timing=TimingMetadata(
            measured_phase_seconds=12.5 + (continuation or 0.0)
        ),
        result=ResultMetadata(
            outcome=EvaluationOutcome.MANUAL_REVIEW,
            source=ObservationSource.CODEX_TASK_HISTORY,
            measurement_quality=MeasurementQuality.MEASURED,
        ),
    )


def test_missing_continuation_is_null_and_does_not_change_total() -> None:
    record = observation()
    serialized = record.model_dump(mode="json")

    assert serialized["phases"]["continuation"] == {
        "status": "not-run",
        "duration_seconds": None,
    }
    assert serialized["timing"]["measured_phase_seconds"] == 12.5


def test_completed_phase_requires_a_duration() -> None:
    with pytest.raises(ValidationError, match="requires duration_seconds"):
        PhaseMeasurement(status=PhaseStatus.COMPLETED)


def test_observation_rejects_an_inconsistent_phase_total() -> None:
    valid = observation()
    raw = valid.model_dump(mode="json")
    raw["timing"]["measured_phase_seconds"] = 99.0

    with pytest.raises(ValidationError, match="must equal the sum"):
        type(valid).model_validate_json(json.dumps(raw))


def test_record_id_is_stable_and_content_addressed() -> None:
    first = observation()
    second = observation()
    changed = observation(continuation=1.0)

    assert first.record_id == second.record_id
    assert changed.record_id != first.record_id


def test_telemetry_uses_new_schema_without_changing_legacy_serialization() -> None:
    legacy = observation()
    instrumented = observation(telemetry=True)

    assert legacy.schema_version == "1.0.0"
    assert "telemetry" not in legacy.model_dump(mode="json")["phases"]["initial"]
    assert instrumented.schema_version == "1.1.0"
    assert instrumented.phases.initial.telemetry is not None
    assert instrumented.record_id != legacy.record_id


def test_ledger_append_is_atomic_and_idempotent(tmp_path: Path) -> None:
    ledger = tmp_path / "history.jsonl"
    record = observation()

    assert append_performance_observations(ledger, [record]) == 1
    assert append_performance_observations(ledger, [record]) == 0
    assert load_performance_ledger(ledger) == [record]
    assert not ledger.with_suffix(".jsonl.lock").exists()


def test_instrumented_append_preserves_legacy_record_identity(tmp_path: Path) -> None:
    ledger = tmp_path / "history.jsonl"
    legacy = observation()
    instrumented = observation(telemetry=True)

    assert append_performance_observations(ledger, [legacy]) == 1
    assert append_performance_observations(ledger, [instrumented]) == 1

    loaded = load_performance_ledger(ledger)
    assert [record.schema_version for record in loaded] == ["1.0.0", "1.1.0"]
    assert loaded[0].record_id == legacy.record_id
    assert loaded[1].phases.initial.telemetry is not None


def test_ledger_rejects_duplicate_lines(tmp_path: Path) -> None:
    ledger = tmp_path / "history.jsonl"
    record = observation()
    ledger.write_text(
        record.model_dump_json() + "\n" + record.model_dump_json() + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate performance record ID"):
        load_performance_ledger(ledger)


def test_versioned_performance_history_validates() -> None:
    records = load_performance_ledger(
        ROOT / "evaluation-data" / "exploratory-runs.jsonl"
    )

    assert records
    assert len({record.record_id for record in records}) == len(records)


def test_versioned_import_evidence_does_not_expose_absolute_windows_paths() -> None:
    imports = ROOT / "evaluation-data" / "imports"

    for path in imports.glob("*.json"):
        assert "C:\\\\" not in path.read_text(encoding="utf-8")


def test_historical_review_links_accepted_phases_to_canonical_records() -> None:
    review = HistoricalReviewBatch.model_validate_json(
        (
            ROOT
            / "evaluation-data"
            / "imports"
            / "codex-desktop-history-review.json"
        ).read_text(encoding="utf-8")
    )
    records = load_performance_ledger(
        ROOT / "evaluation-data" / "exploratory-runs.jsonl"
    )
    record_ids = {record.record_id for record in records}

    accepted = [
        phase for phase in review.phases if phase.decision == ReviewDecision.ACCEPTED
    ]
    assert accepted
    assert all(phase.canonical_record_id in record_ids for phase in accepted)
