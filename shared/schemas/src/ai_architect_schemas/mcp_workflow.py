# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Anonymous stateless MCP wire contracts and a separate client-local checkpoint."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import ConfigDict, Field

from .models import ArchitectureOptionComparison, StrictModel

CONTRACT_VERSION: Literal["0.1.0"] = "0.1.0"
ARTIFACT_VERSION = "1.0.0"
Text = Annotated[str, Field(min_length=1, max_length=2000)]


class EmptyRequest(StrictModel):
    pass


class ResourceRequest(StrictModel):
    resource_id: str = Field(min_length=1, max_length=160)
    reference_version: str = Field(min_length=1, max_length=80)


class ArtifactFile(StrictModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=False)
    path: str = Field(min_length=1, max_length=160)
    content: str = Field(min_length=1, max_length=65536)


class PrepareRequest(StrictModel):
    """A self-contained validation/export request, with no workflow or identity fields."""

    contract_version: Literal["0.1.0"] = CONTRACT_VERSION
    files: list[ArtifactFile] = Field(min_length=4, max_length=8)


class WorkflowError(StrictModel):
    code: str = ""
    retryable: bool = False
    repair_hint: str = ""


class WorkflowResponse(StrictModel):
    ok: bool
    data: dict[str, object] = Field(default_factory=dict)
    error: WorkflowError = Field(default_factory=WorkflowError)


class WorkflowWireContracts(StrictModel):
    capabilities: EmptyRequest
    resource: ResourceRequest
    prepare: PrepareRequest
    response: WorkflowResponse


class LocalWorkflowCheckpoint(StrictModel):
    """Client-owned state only. Never accepted as an MCP request or approval authority."""

    contract_version: Literal["0.1.0"] = CONTRACT_VERSION
    local_review_id: str = Field(pattern=r"^[0-9a-f-]{36}$")
    revision: int = Field(ge=1)
    phase: Literal["active", "clarification", "analysis", "prepared", "exported", "cancelled"]
    reference_version: str = Field(pattern=r"^[a-f0-9]{64}$")
    scope: Text
    constraints: list[Text] = Field(default_factory=list, max_length=20)
    context: str = Field(default="", max_length=2000)
    question_rounds: int = Field(default=0, ge=0, le=3)
    unresolved_questions: list[Text] = Field(default_factory=list, max_length=5)
    evidence_provenance: list[Text] = Field(default_factory=list, max_length=20)
    evidence_limits: list[Text] = Field(min_length=1, max_length=20)
    comparison: ArchitectureOptionComparison | None = None
    candidate_digest: str = Field(default="", pattern=r"^(?:[a-f0-9]{64})?$")
    acceptance: Literal["unverified"] = "unverified"
    local_persistence: Literal["host-managed-unverified"] = "host-managed-unverified"
