# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Strict contracts for exploratory-evaluation performance observations."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from adapters.codex.evaluations.models import PhaseTelemetry, StrictModel

PerformanceSchemaVersion = Literal["1.0.0", "1.1.0", "1.2.0"]
PERFORMANCE_SCHEMA_VERSION: PerformanceSchemaVersion = "1.2.0"


class ExecutionMode(StrEnum):
    SEQUENTIAL_CODEX_CLI = "sequential-codex-cli"
    PARALLEL_CODEX_TASKS = "parallel-codex-tasks"
    INTERACTIVE_CODEX_TASK = "interactive-codex-task"


class SpeedMode(StrEnum):
    STANDARD = "standard"
    FAST = "fast"
    UNKNOWN = "unknown"


class PhaseStatus(StrEnum):
    COMPLETED = "completed"
    NOT_RUN = "not-run"


class MeasurementQuality(StrEnum):
    MEASURED = "measured"
    RECONSTRUCTED = "reconstructed"
    INFERRED = "inferred"


class ObservationSource(StrEnum):
    CODEX_CLI_RUNNER = "codex-cli-runner"
    CODEX_TASK_HISTORY = "codex-task-history"
    REPORT_IMPORT = "report-import"


class EvaluationOutcome(StrEnum):
    MANUAL_REVIEW = "manual-review"
    PASSED = "passed"
    DETERMINISTIC_FAILURE = "deterministic-failure"


class CampaignMetadata(StrictModel):
    id: str = Field(min_length=1, max_length=160)
    execution_mode: ExecutionMode
    started_at: datetime
    completed_at: datetime
    wall_clock_seconds: float = Field(ge=0)

    @field_validator("started_at", "completed_at")
    @classmethod
    def timestamps_are_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("campaign timestamps must include a timezone")
        return value

    @model_validator(mode="after")
    def completion_follows_start(self) -> CampaignMetadata:
        if self.completed_at < self.started_at:
            raise ValueError("campaign completed_at must not precede started_at")
        return self


class TestMetadata(StrictModel):
    fixture_id: str = Field(min_length=1, max_length=160)
    fixture_revision: str = Field(pattern=r"^[a-f0-9]{64}$")
    workload_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    task_name: str | None = Field(default=None, max_length=240)
    task_id: str | None = Field(default=None, max_length=160)


class RuntimeMetadata(StrictModel):
    model: str = Field(min_length=1, max_length=160)
    reasoning_effort: str = Field(min_length=1, max_length=40)
    speed: SpeedMode
    codex_version: str = Field(min_length=1, max_length=240)
    plugin_version: str = Field(min_length=1, max_length=160)
    plugin_provenance: str | None = Field(
        default=None,
        pattern=r"^(sha256:)?[a-f0-9]{64}$",
    )
    git_commit: str = Field(min_length=1, max_length=160)
    host: str = Field(default="unknown", min_length=1, max_length=160)


class PhaseMeasurement(StrictModel):
    status: PhaseStatus
    duration_seconds: float | None = Field(default=None, ge=0)
    telemetry: PhaseTelemetry | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )

    @model_validator(mode="after")
    def duration_matches_status(self) -> PhaseMeasurement:
        if self.status == PhaseStatus.COMPLETED and self.duration_seconds is None:
            raise ValueError("a completed phase requires duration_seconds")
        if self.status == PhaseStatus.NOT_RUN and self.duration_seconds is not None:
            raise ValueError("a not-run phase must use a null duration_seconds")
        return self


class PhaseMeasurements(StrictModel):
    initial: PhaseMeasurement
    continuation: PhaseMeasurement = Field(
        default_factory=lambda: PhaseMeasurement(status=PhaseStatus.NOT_RUN)
    )


class TimingMetadata(StrictModel):
    measured_phase_seconds: float = Field(ge=0)


class ResultMetadata(StrictModel):
    outcome: EvaluationOutcome
    source: ObservationSource
    measurement_quality: MeasurementQuality
    notes: str | None = Field(default=None, max_length=2_000)


class PerformanceObservation(StrictModel):
    schema_version: PerformanceSchemaVersion = PERFORMANCE_SCHEMA_VERSION
    record_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    campaign: CampaignMetadata
    test: TestMetadata
    runtime: RuntimeMetadata
    phases: PhaseMeasurements
    timing: TimingMetadata
    result: ResultMetadata

    @model_validator(mode="after")
    def totals_and_identity_are_consistent(self) -> PerformanceObservation:
        measured = sum(
            phase.duration_seconds or 0.0
            for phase in (self.phases.initial, self.phases.continuation)
            if phase.status == PhaseStatus.COMPLETED
        )
        if round(measured, 3) != round(self.timing.measured_phase_seconds, 3):
            raise ValueError(
                "timing.measured_phase_seconds must equal the sum of completed phases"
            )
        if self.schema_version == "1.0.0" and any(
            phase.telemetry is not None
            for phase in (self.phases.initial, self.phases.continuation)
        ):
            raise ValueError("schema version 1.0.0 cannot contain phase telemetry")
        if self.schema_version == "1.1.0" and any(
            phase.telemetry is not None and phase.telemetry.tool_events
            for phase in (self.phases.initial, self.phases.continuation)
        ):
            raise ValueError("schema version 1.1.0 cannot contain tool timeline events")
        expected = performance_record_id(_identity_payload(self))
        if self.record_id != expected:
            raise ValueError("record_id does not match the canonical observation identity")
        return self


def performance_record_id(observation_without_id: dict[str, Any]) -> str:
    """Return a deterministic identifier for a complete canonical observation."""

    payload = json.dumps(
        observation_without_id,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _identity_payload(observation: PerformanceObservation) -> dict[str, Any]:
    payload = observation.model_dump(mode="json", exclude={"record_id"})
    if observation.schema_version == "1.0.0":
        for phase in payload["phases"].values():
            phase.pop("telemetry", None)
    elif observation.schema_version == "1.1.0":
        for phase in payload["phases"].values():
            telemetry = phase.get("telemetry")
            if telemetry is not None:
                telemetry.pop("tool_events", None)
    return payload


def build_performance_observation(**fields: Any) -> PerformanceObservation:
    """Build an observation and derive its content-addressed record ID."""

    phases = fields.get("phases")
    has_telemetry = isinstance(phases, PhaseMeasurements) and any(
        phase.telemetry is not None for phase in (phases.initial, phases.continuation)
    )
    has_tool_events = isinstance(phases, PhaseMeasurements) and any(
        phase.telemetry is not None and phase.telemetry.tool_events
        for phase in (phases.initial, phases.continuation)
    )
    schema_version: PerformanceSchemaVersion
    if has_tool_events:
        schema_version = PERFORMANCE_SCHEMA_VERSION
    elif has_telemetry:
        schema_version = "1.1.0"
    else:
        schema_version = "1.0.0"
    unvalidated = PerformanceObservation.model_construct(
        schema_version=schema_version,
        record_id="0" * 64,
        **fields,
    )
    raw = _identity_payload(unvalidated)
    return PerformanceObservation.model_validate(
        {
            "schema_version": schema_version,
            "record_id": performance_record_id(raw),
            **fields,
        }
    )
