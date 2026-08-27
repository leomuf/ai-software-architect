# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Typed contracts for shared exploratory fixtures and Codex run reports."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal, Self

import yaml
from ai_architect_schemas import PatternCategory
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class DirectSkillActivation(StrictModel):
    """Direct skill activation retained for canonical comparison fixtures."""

    type: Literal["direct-skill"]
    skill_invocation: Literal["$ai-software-architect"]

    def render(self) -> str:
        """Preserve the legacy direct-skill syntax used by comparison fixtures."""
        return self.skill_invocation


class StructuredPluginMentionActivation(StrictModel):
    """Picker-selected plugin activation used by the isolated release smoke gate."""

    type: Literal["structured-plugin-mention"]
    mention_label: Literal["ai-software-architect"]
    plugin_name: Literal["ai-software-architect"]
    marketplace: Literal["personal"]

    def render(self) -> str:
        """Render the exact picker-produced mention required by the smoke gate."""
        return (
            f"[@{self.mention_label}]"
            f"(plugin://{self.plugin_name}@{self.marketplace})"
        )


Activation = Annotated[
    DirectSkillActivation | StructuredPluginMentionActivation,
    Field(discriminator="type"),
]


class VerificationPolicy(StrictModel):
    repository_changes: Literal["forbid", "architecture-artifacts-only", "allow"]
    required_repository_changes: list[str] = Field(default_factory=list)
    forbidden_event_types: list[str] = Field(default_factory=list)
    forbidden_response_markers: list[str] = Field(default_factory=list)


class Continuation(StrictModel):
    prompt: str = Field(min_length=1)
    expected: list[str] = Field(min_length=1)
    forbidden_actions: list[str] = Field(default_factory=list)
    verification: VerificationPolicy


class ExpectedDecision(StrictModel):
    selected_category: PatternCategory
    selected_name: str = Field(min_length=1, max_length=120)


class EvaluationFixture(StrictModel):
    schema_version: str
    id: str = Field(min_length=1)
    scenario: str = Field(pattern=r"^[A-Z]+-[0-9]{3}$")
    response_language: str = Field(default="en", pattern=r"^[a-z]{2}(?:-[A-Z]{2})?$")
    activation: Activation
    prompt: str = Field(min_length=1)
    repository: dict[str, str] = Field(default_factory=dict)
    expected: list[str] = Field(min_length=1)
    forbidden_actions: list[str] = Field(default_factory=list)
    verification: VerificationPolicy
    observe_decision: bool = False
    expected_decision: ExpectedDecision | None = None
    continuation: Continuation | None = None

    @field_validator("repository")
    @classmethod
    def repository_paths_are_relative(cls, value: dict[str, str]) -> dict[str, str]:
        for raw_path in value:
            path = Path(raw_path)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError(f"repository path must remain relative: {raw_path}")
        return value

    @model_validator(mode="after")
    def expected_decision_requires_observation(self) -> Self:
        if self.expected_decision is not None and not self.observe_decision:
            raise ValueError("expected_decision requires observe_decision=true")
        return self


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


class DecisionObservation(StrictModel):
    """Privacy-preserving outcome extracted from a validated option comparison."""

    selected_category: str = Field(min_length=1, max_length=40)
    selected_name: str = Field(min_length=1, max_length=120)
    material_assumption_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    material_assumption_word_count: int = Field(ge=1)
    visible_response_word_count: int | None = Field(default=None, ge=1)


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
    decision_observation: DecisionObservation | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )


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
    schema_version: str = "1.4.0"
    run_kind: Literal["exploratory-campaign", "release-gate-smoke"] = (
        "exploratory-campaign"
    )
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
