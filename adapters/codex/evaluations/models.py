# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Typed contracts for shared exploratory fixtures and Codex run reports."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Activation(StrictModel):
    skill_invocation: str = Field(min_length=1)


class VerificationPolicy(StrictModel):
    repository_changes: Literal["forbid", "architecture-artifacts-only", "allow"]
    forbidden_event_types: list[str] = Field(default_factory=list)
    forbidden_response_markers: list[str] = Field(default_factory=list)


class Continuation(StrictModel):
    prompt: str = Field(min_length=1)
    expected: list[str] = Field(min_length=1)
    forbidden_actions: list[str] = Field(default_factory=list)
    verification: VerificationPolicy


class EvaluationFixture(StrictModel):
    schema_version: str
    id: str = Field(min_length=1)
    scenario: str = Field(pattern=r"^[A-Z]+-[0-9]{3}$")
    activation: Activation
    prompt: str = Field(min_length=1)
    repository: dict[str, str] = Field(default_factory=dict)
    expected: list[str] = Field(min_length=1)
    forbidden_actions: list[str] = Field(default_factory=list)
    verification: VerificationPolicy
    continuation: Continuation | None = None

    @field_validator("repository")
    @classmethod
    def repository_paths_are_relative(cls, value: dict[str, str]) -> dict[str, str]:
        for raw_path in value:
            path = Path(raw_path)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError(f"repository path must remain relative: {raw_path}")
        return value


class AssertionStatus(StrEnum):
    PASS = "pass"  # noqa: S105 - evaluation status, not a credential
    FAIL = "fail"


class DeterministicAssertion(StrictModel):
    name: str
    status: AssertionStatus
    evidence: str


class ToolTimelineEvent(StrictModel):
    """Privacy-preserving timing for one runner-observed Codex tool item."""

    ordinal: int = Field(ge=1)
    tool_type: str = Field(min_length=1, max_length=80)
    started_seconds: float = Field(ge=0)
    completed_seconds: float = Field(ge=0)
    duration_seconds: float = Field(ge=0)
    gap_from_previous_tool_seconds: float | None = Field(default=None, ge=0)
    status: str = Field(min_length=1, max_length=40)


class PhaseTelemetry(StrictModel):
    """Runner-observed Codex event timing and usage; never inferred."""

    first_event_seconds: float | None = Field(default=None, ge=0)
    first_agent_message_seconds: float | None = Field(default=None, ge=0)
    last_agent_message_seconds: float | None = Field(default=None, ge=0)
    agent_message_count: int = Field(default=0, ge=0)
    tool_call_count: int = Field(default=0, ge=0)
    item_counts: dict[str, int] = Field(default_factory=dict)
    input_tokens: int | None = Field(default=None, ge=0)
    cached_input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    tool_events: list[ToolTimelineEvent] = Field(
        default_factory=list,
        exclude_if=lambda value: not value,
    )
    unavailable_metrics: list[str] = Field(default_factory=list)


class PhaseResult(StrictModel):
    name: Literal["initial", "continuation"]
    exit_code: int
    duration_seconds: float = Field(ge=0)
    thread_id: str | None = None
    final_response_file: str | None = None
    event_log_file: str
    stderr_file: str
    event_types: list[str]
    repository_changes: list[str]
    assertions: list[DeterministicAssertion]
    manual_review: list[str]
    telemetry: PhaseTelemetry | None = None


class EvaluationStatus(StrEnum):
    DETERMINISTIC_FAILURE = "deterministic-failure"
    INFRASTRUCTURE_ERROR = "infrastructure-error"
    MANUAL_REVIEW = "manual-review"
    PLANNED = "planned"


class FixtureResult(StrictModel):
    fixture_id: str
    scenario: str
    status: EvaluationStatus
    workspace: str
    phases: list[PhaseResult]
    error: str | None = None


class CampaignReport(StrictModel):
    schema_version: str = "1.2.0"
    started_at: datetime
    completed_at: datetime
    codex_command: str
    codex_version: str
    installed_plugin_id: str | None = None
    installed_plugin_marketplace: str | None = None
    installed_plugin_version: str | None = None
    installed_plugin_provenance_sha256: str | None = None
    expected_plugin_version: str | None = None
    model: str
    reasoning_effort: str
    speed: Literal["standard", "fast", "unknown"] = "unknown"
    campaign_wall_clock_seconds: float | None = Field(default=None, ge=0)
    git_commit: str = "unknown"
    results: list[FixtureResult]


def load_fixture(path: Path) -> EvaluationFixture:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return EvaluationFixture.model_validate(raw)
