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
    schema_version: str = "1.0.0"
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
    results: list[FixtureResult]


def load_fixture(path: Path) -> EvaluationFixture:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return EvaluationFixture.model_validate(raw)
