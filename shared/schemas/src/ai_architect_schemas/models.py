# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

ADRId = Annotated[str, Field(pattern=r"^ADR-[0-9]{3}$")]
OptionId = Annotated[str, Field(pattern=r"^OPT-[0-9]{3}$")]
ComponentId = Annotated[str, Field(pattern=r"^[a-z][a-z0-9-]*$")]
RunId = Annotated[
    str,
    Field(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"),
]
RelativePathText = Annotated[str, Field(min_length=1, max_length=240)]
ShortText = Annotated[str, Field(min_length=1, max_length=500)]
EvidenceText = Annotated[str, Field(min_length=1, max_length=2_000)]
NarrativeText = Annotated[str, Field(min_length=1, max_length=20_000)]


def _default_languages() -> list[Literal["python"]]:
    return ["python"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)


class WorkflowNode(StrEnum):
    UNDERSTAND = "understand"
    CLARIFY = "clarify"
    DESIGN = "design"
    APPROVE = "approve"
    RECORD_AND_HANDOFF = "record_and_handoff"
    REVIEW = "review"


class WorkflowStatus(StrEnum):
    ACTIVE = "active"
    COMPLETE = "complete"
    BLOCKED = "blocked"
    OUT_OF_SCOPE = "out_of_scope"


class QualityAttribute(StrictModel):
    name: ShortText
    priority: int = Field(ge=1, le=5)
    rationale: EvidenceText
    measurable_signal: EvidenceText | None = None


class ClarificationQuestion(StrictModel):
    id: str = Field(pattern=r"^Q-[0-9]{3}$")
    question: EvidenceText
    decision_impact: EvidenceText
    critical: bool = False
    answer: NarrativeText | None = None


class ArchitectureOption(StrictModel):
    id: OptionId
    name: ShortText
    summary: EvidenceText
    benefits: list[EvidenceText] = Field(default_factory=list, max_length=20)
    drawbacks: list[EvidenceText] = Field(default_factory=list, max_length=20)
    risks: list[EvidenceText] = Field(default_factory=list, max_length=20)
    fit_score: int = Field(ge=0, le=100)
    fit_rationale: EvidenceText


class ArchitectureDecision(StrictModel):
    id: ADRId
    title: ShortText
    status: Literal["proposed", "accepted", "rejected", "superseded"]
    context: NarrativeText
    drivers: list[EvidenceText] = Field(min_length=1, max_length=30)
    considered_option_ids: list[OptionId] = Field(min_length=1, max_length=5)
    selected_option_id: OptionId | None = None
    decision: NarrativeText
    positive_consequences: list[EvidenceText] = Field(default_factory=list, max_length=30)
    negative_consequences: list[EvidenceText] = Field(default_factory=list, max_length=30)
    assumptions: list[EvidenceText] = Field(default_factory=list, max_length=30)
    validation_criteria: list[EvidenceText] = Field(min_length=1, max_length=30)
    supersedes: list[ADRId] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def validate_option_selection(self) -> Self:
        if len(self.considered_option_ids) != len(set(self.considered_option_ids)):
            raise ValueError("considered_option_ids must be unique")
        if self.selected_option_id not in {None, *self.considered_option_ids}:
            raise ValueError("selected_option_id must reference a considered option")
        if self.status == "accepted" and self.selected_option_id is None:
            raise ValueError("accepted decisions require selected_option_id")
        if self.id in self.supersedes:
            raise ValueError("a decision cannot supersede itself")
        return self


class ArchitectureDecisionArtifact(StrictModel):
    schema_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    revision: int = Field(ge=1)
    decision: ArchitectureDecision


class Component(StrictModel):
    id: ComponentId
    responsibility: EvidenceText
    owns_data: list[ShortText] = Field(default_factory=list, max_length=100)
    public_interfaces: list[ShortText] = Field(default_factory=list, max_length=100)


class ExternalBoundary(StrictModel):
    id: ComponentId
    responsibility: EvidenceText


class DependencyRule(StrictModel):
    source: ComponentId
    target: ComponentId
    policy: Literal["allow", "deny", "allow-via-interface"]
    via_interface: ShortText | None = None
    rationale: EvidenceText

    @model_validator(mode="after")
    def validate_interface_policy(self) -> Self:
        if (self.policy == "allow-via-interface") != (self.via_interface is not None):
            raise ValueError("via_interface is required only for allow-via-interface")
        return self


class ArchitectureContract(StrictModel):
    schema_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    revision: int = Field(ge=1)
    scope: ShortText
    architecture_style: ShortText | None = None
    quality_attributes: list[QualityAttribute] = Field(default_factory=list, max_length=20)
    components: list[Component] = Field(default_factory=list, max_length=200)
    external_boundaries: list[ExternalBoundary] = Field(default_factory=list, max_length=100)
    dependency_rules: list[DependencyRule] = Field(default_factory=list, max_length=500)
    required_practices: list[ShortText] = Field(default_factory=list, max_length=200)
    prohibited_practices: list[ShortText] = Field(default_factory=list, max_length=200)
    decision_ids: list[ADRId] = Field(default_factory=list, max_length=200)
    unresolved_questions: list[ClarificationQuestion] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def validate_contract_references(self) -> Self:
        component_ids = [item.id for item in self.components]
        external_ids = [item.id for item in self.external_boundaries]
        node_ids = component_ids + external_ids
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("component and external-boundary ids must be unique")
        if len(self.decision_ids) != len(set(self.decision_ids)):
            raise ValueError("decision_ids must be unique")
        quality_names = [item.name.casefold() for item in self.quality_attributes]
        if len(quality_names) != len(set(quality_names)):
            raise ValueError("quality-attribute names must be unique")
        question_ids = [item.id for item in self.unresolved_questions]
        if len(question_ids) != len(set(question_ids)):
            raise ValueError("unresolved question ids must be unique")
        known_nodes = set(node_ids)
        for rule in self.dependency_rules:
            if rule.source not in known_nodes or rule.target not in known_nodes:
                raise ValueError("dependency rules must reference declared nodes")
        return self


class ArchitectureAnalysisResult(StrictModel):
    status: Literal[
        "needs_clarification",
        "ready_for_approval",
        "approved",
        "complete",
        "blocked",
        "out_of_scope",
    ]
    current_node: WorkflowNode | None
    problem_summary: NarrativeText
    questions: list[ClarificationQuestion] = Field(default_factory=list, max_length=5)
    forces: list[EvidenceText] = Field(default_factory=list, max_length=50)
    quality_attributes: list[QualityAttribute] = Field(default_factory=list, max_length=20)
    options: list[ArchitectureOption] = Field(default_factory=list, max_length=5)
    recommended_option_id: OptionId | None = None
    proposed_decisions: list[ArchitectureDecision] = Field(default_factory=list, max_length=20)
    assumptions: list[EvidenceText] = Field(default_factory=list, max_length=50)
    warnings: list[EvidenceText] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def validate_analysis_references(self) -> Self:
        option_ids = [item.id for item in self.options]
        if len(option_ids) != len(set(option_ids)):
            raise ValueError("option ids must be unique")
        known_options = set(option_ids)
        if self.recommended_option_id not in {None, *known_options}:
            raise ValueError("recommended_option_id must reference an option")
        if self.status in {"ready_for_approval", "approved"}:
            if self.recommended_option_id is None:
                raise ValueError("approval states require a recommended option")
        if self.status == "needs_clarification" and not self.questions:
            raise ValueError("needs_clarification requires at least one question")
        question_ids = [item.id for item in self.questions]
        if len(question_ids) != len(set(question_ids)):
            raise ValueError("question ids must be unique")
        for decision in self.proposed_decisions:
            if not set(decision.considered_option_ids) <= known_options:
                raise ValueError("decision references an unknown option")
        terminal = {"complete", "blocked", "out_of_scope"}
        if (self.status in terminal) != (self.current_node is None):
            raise ValueError("terminal status and current_node are inconsistent")
        return self


class ConformanceFinding(StrictModel):
    id: str = Field(pattern=r"^F-[0-9]{3}$")
    classification: Literal["confirmed-violation", "possible-drift", "acceptable-deviation"]
    severity: Literal["info", "low", "medium", "high", "critical"]
    confidence: Literal["low", "medium", "high"]
    decision_id: ADRId | None = None
    rule: EvidenceText
    evidence: list[EvidenceText] = Field(min_length=1, max_length=50)
    recommendation: EvidenceText


class ConformanceReport(StrictModel):
    scope: ShortText
    findings: list[ConformanceFinding] = Field(default_factory=list, max_length=200)
    files_examined: int = Field(ge=0)
    files_skipped: int = Field(ge=0)
    truncated: bool = False


class ContractValidationInput(StrictModel):
    yaml_content: str = Field(min_length=1, max_length=500_000)


class DecisionListInput(StrictModel):
    statuses: list[Literal["proposed", "accepted", "rejected", "superseded"]] = Field(
        default_factory=list, max_length=4
    )


class RepositoryAnalysisInput(StrictModel):
    relative_roots: list[RelativePathText] = Field(min_length=1, max_length=20)
    languages: list[Literal["python"]] = Field(
        default_factory=_default_languages, min_length=1, max_length=1
    )


class BoundaryCheckInput(RepositoryAnalysisInput):
    contract_yaml: str = Field(min_length=1, max_length=500_000)


class ArtifactSecretScanInput(StrictModel):
    content: str = Field(min_length=1, max_length=500_000)
    artifact_kind: Literal["adr", "contract", "context", "implementation-plan"]


class SecretFinding(StrictModel):
    category: Literal["private-key", "credential", "token"]
    line: int = Field(ge=1)


class ArtifactSecretScanResult(StrictModel):
    safe_to_write: bool
    findings: list[SecretFinding] = Field(default_factory=list, max_length=100)
    truncated: bool = False

    @model_validator(mode="after")
    def validate_safety_result(self) -> Self:
        if self.safe_to_write == bool(self.findings):
            raise ValueError("safe_to_write must be false exactly when findings exist")
        return self


class ContractValidationResult(StrictModel):
    valid: bool
    schema_version: str | None = None
    errors: list[EvidenceText] = Field(default_factory=list, max_length=100)
    warnings: list[EvidenceText] = Field(default_factory=list, max_length=100)
    truncated: bool = False

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        if self.valid == bool(self.errors):
            raise ValueError("valid must be false exactly when errors exist")
        if self.truncated and self.valid:
            raise ValueError("a truncated validation result cannot be valid")
        return self


class ToolError(StrictModel):
    code: Literal[
        "invalid-input",
        "not-found",
        "boundary-violation",
        "protected-path",
        "budget-exhausted",
        "unsupported-format",
        "unsafe-content",
        "workspace-unavailable",
        "internal-error",
    ]
    message: EvidenceText
    relative_path: RelativePathText | None = None
    retryable: bool = False


class DecisionListResult(StrictModel):
    decisions: list[ArchitectureDecision] = Field(default_factory=list, max_length=200)
    invalid_files: list[RelativePathText] = Field(default_factory=list, max_length=200)
    files_examined: int = Field(ge=0)
    files_skipped: int = Field(ge=0)
    truncated: bool = False


class DependencyEdge(StrictModel):
    source: ShortText
    target: ShortText
    evidence: EvidenceText


class DependencyGraphEvidence(StrictModel):
    edges: list[DependencyEdge] = Field(default_factory=list, max_length=5_000)
    files_examined: int = Field(ge=0)
    files_skipped: int = Field(ge=0)
    warnings: list[EvidenceText] = Field(default_factory=list, max_length=100)
    truncated: bool = False


class StrikeEvent(StrictModel):
    reason: Literal[
        "workspace-escape",
        "protected-secret-access",
        "network-attempt",
        "model-call-attempt",
        "shell-execution-attempt",
        "destructive-write-attempt",
        "repeated-off-topic-bypass",
    ]
    denied_operation: EvidenceText
    resulting_count: int = Field(ge=1, le=3)


class WorkflowState(StrictModel):
    run_id: RunId
    status: WorkflowStatus
    current_node: WorkflowNode | None
    clarification_round: int = Field(ge=0, le=3)
    approved_decision_ids: list[ADRId] = Field(default_factory=list, max_length=200)
    pending_decision_ids: list[ADRId] = Field(default_factory=list, max_length=200)
    strikes: list[StrikeEvent] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def validate_state(self) -> Self:
        if (self.status == WorkflowStatus.ACTIVE) != (self.current_node is not None):
            raise ValueError("active status and current_node are inconsistent")
        if set(self.approved_decision_ids) & set(self.pending_decision_ids):
            raise ValueError("decision ids cannot be both approved and pending")
        expected_counts = list(range(1, len(self.strikes) + 1))
        if [event.resulting_count for event in self.strikes] != expected_counts:
            raise ValueError("strike resulting_count values must be sequential")
        return self
