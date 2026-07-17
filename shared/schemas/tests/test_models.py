# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pytest
from ai_architect_schemas import (
    ArchitectureContract,
    ArchitectureDecision,
    ArtifactSecretScanResult,
    WorkflowNode,
    WorkflowState,
    WorkflowStatus,
)
from pydantic import ValidationError


def test_contract_rejects_coerced_priority_and_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ArchitectureContract.model_validate(
            {
                "schema_version": "1.0.0",
                "revision": 1,
                "scope": "sample",
                "quality_attributes": [
                    {"name": "Security", "priority": "5", "rationale": "Required"}
                ],
                "unexpected": True,
            }
        )


def test_contract_rejects_dependency_to_unknown_component() -> None:
    with pytest.raises(ValidationError, match="declared nodes"):
        ArchitectureContract.model_validate(
            {
                "schema_version": "1.0.0",
                "revision": 1,
                "scope": "sample",
                "components": [{"id": "domain", "responsibility": "Business rules"}],
                "dependency_rules": [
                    {
                        "source": "domain",
                        "target": "vendor",
                        "policy": "deny",
                        "rationale": "Keep the domain portable",
                    }
                ],
            }
        )


def test_accepted_decision_requires_selected_considered_option() -> None:
    with pytest.raises(ValidationError, match="selected_option_id"):
        ArchitectureDecision(
            id="ADR-001",
            title="Choose style",
            status="accepted",
            context="A style is required.",
            drivers=["Maintainability"],
            considered_option_ids=["OPT-001"],
            decision="Use the selected style.",
            validation_criteria=["Dependencies conform"],
        )


def test_workflow_state_requires_node_only_while_active() -> None:
    with pytest.raises(ValidationError, match="active status"):
        WorkflowState(
            run_id="123e4567-e89b-42d3-a456-426614174000",
            status=WorkflowStatus.COMPLETE,
            current_node=WorkflowNode.REVIEW,
            clarification_round=0,
        )


def test_secret_scan_result_flags_are_consistent() -> None:
    with pytest.raises(ValidationError, match="safe_to_write"):
        ArtifactSecretScanResult(safe_to_write=False, findings=[])
