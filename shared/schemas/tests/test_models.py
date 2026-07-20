# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pytest
from ai_architect_schemas import (
    ArchitectureContract,
    ArchitectureDecision,
    ArchitectureOptionComparison,
    ArtifactSecretScanResult,
    DependencyAnalysisInput,
    DependencyStatementInput,
    EvidenceClaim,
    RepositoryAnalysisInput,
    SourceFileInput,
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


def test_evidence_claim_requires_observation_for_asserted_fact() -> None:
    with pytest.raises(ValidationError, match="requires at least one evidence"):
        EvidenceClaim(kind="confirmed-fact", claim="The dependency is installed.")
    assumption = EvidenceClaim(
        kind="assumption",
        claim="The application will run on one workstation.",
    )
    assert assumption.evidence == []


def test_repository_analysis_requires_exactly_one_input_mode() -> None:
    with pytest.raises(ValidationError, match="exactly one"):
        RepositoryAnalysisInput()
    with pytest.raises(ValidationError, match="exactly one"):
        RepositoryAnalysisInput(
            relative_roots=["."],
            source_files=[SourceFileInput(relative_path="app.py", content="import json\n")],
        )
    with pytest.raises(ValidationError, match="exactly one"):
        RepositoryAnalysisInput(
            source_files=[SourceFileInput(relative_path="app.py", content="import json\n")],
            dependency_statements=[
                DependencyStatementInput(
                    relative_path="app.py",
                    start_line=1,
                    statement="import json",
                )
            ],
        )


def test_inline_source_contract_preserves_content_and_rejects_duplicate_paths() -> None:
    source = SourceFileInput(relative_path=" app.py ", content="  import json\n")
    assert source.relative_path == "app.py"
    assert source.content == "  import json\n"
    with pytest.raises(ValidationError, match="unique"):
        RepositoryAnalysisInput(
            source_files=[
                SourceFileInput(relative_path="pkg\\module.py", content="import json\n"),
                SourceFileInput(relative_path="pkg/module.py", content="import pathlib\n"),
            ]
        )


def test_dependency_statement_contract_preserves_text_and_rejects_duplicate_lines() -> None:
    statement = DependencyStatementInput(
        relative_path=" app.py ",
        start_line=7,
        statement="import json as data\n",
    )
    assert statement.relative_path == "app.py"
    assert statement.statement == "import json as data\n"
    with pytest.raises(ValidationError, match="unique"):
        RepositoryAnalysisInput(
            dependency_statements=[
                statement,
                DependencyStatementInput(
                    relative_path="app.py",
                    start_line=7,
                    statement="import pathlib",
                ),
            ]
        )


def test_codex_dependency_analysis_accepts_statements_and_rejects_source_files() -> None:
    request = DependencyAnalysisInput(
        dependency_statements=[
            DependencyStatementInput(
                relative_path="app.py",
                start_line=3,
                statement="import json",
            )
        ]
    )
    assert request.to_domain_input().source_files == []
    with pytest.raises(ValidationError, match="Extra inputs"):
        DependencyAnalysisInput.model_validate(
            {
                "dependency_statements": [
                    {
                        "relative_path": "app.py",
                        "start_line": 3,
                        "statement": "import json",
                    }
                ],
                "source_files": [
                    {"relative_path": "app.py", "content": "import json\n"}
                ],
            }
        )


def test_dependency_statement_rejects_blank_null_and_mixed_code() -> None:
    with pytest.raises(ValidationError, match="blank"):
        DependencyStatementInput(
            relative_path="app.py",
            start_line=1,
            statement="   ",
        )
    with pytest.raises(ValidationError, match="null"):
        DependencyStatementInput(
            relative_path="app.py",
            start_line=1,
            statement="import os\x00",
        )


def test_option_comparison_enforces_user_facing_contract() -> None:
    comparison = ArchitectureOptionComparison.model_validate(
        {
            "decision_scope": "Choose the application boundary style.",
            "scoring_criteria": ["Testability", "Change cost"],
            "alternatives": [
                {
                    "id": "OPT-001",
                    "category": "Architecture",
                    "name": "Hexagonal Architecture",
                    "canonical_reference": "references/architecture-hexagonal.md",
                    "fit_score": 86,
                    "fit_rationale": "Strong isolation for volatile adapters.",
                    "main_benefit": "Keeps domain policy independent.",
                    "main_liability": "Introduces ports and mapping code.",
                    "material_assumption": "External integrations will change.",
                },
                {
                    "id": "OPT-002",
                    "category": "Architecture",
                    "name": "Layered Architecture",
                    "canonical_reference": "references/architecture-layered.md",
                    "fit_score": 72,
                    "fit_rationale": "Simple and familiar for the current scope.",
                    "main_benefit": "Low learning cost.",
                    "main_liability": "Layer boundaries can erode.",
                    "material_assumption": "Deployment remains simple.",
                },
                {
                    "id": "OPT-003",
                    "category": "No pattern",
                    "name": "Keep functions",
                    "canonical_reference": None,
                    "fit_score": 48,
                    "fit_rationale": "Low ceremony but weak isolation.",
                    "main_benefit": "Minimal refactoring.",
                    "main_liability": "Volatile responsibilities stay coupled.",
                    "material_assumption": "The application will remain small.",
                },
            ],
            "recommended_option_id": "OPT-001",
            "recommendation_rationale": "The adapter volatility justifies the boundary.",
            "user_decision_prompt": (
                "Please approve, revise, or request more information before I continue."
            ),
            "offered_actions": ["approve", "revise", "more-information"],
        }
    )
    assert comparison.recommended_option_id == "OPT-001"


def test_option_comparison_rejects_incomplete_choice_contract() -> None:
    with pytest.raises(ValidationError, match="fewer_than_three_rationale"):
        ArchitectureOptionComparison.model_validate(
            {
                "decision_scope": "Choose one structure.",
                "scoring_criteria": ["Simplicity"],
                "alternatives": [
                    {
                        "id": "OPT-001",
                        "category": "Architecture",
                        "name": "Layered",
                        "canonical_reference": "references/architecture-layered.md",
                        "fit_score": 70,
                        "fit_rationale": "Familiar.",
                        "main_benefit": "Simple.",
                        "main_liability": "Can couple layers.",
                        "material_assumption": "Small team.",
                    },
                    {
                        "id": "OPT-002",
                        "category": "No pattern",
                        "name": "No pattern",
                        "canonical_reference": None,
                        "fit_score": 50,
                        "fit_rationale": "Few moving parts.",
                        "main_benefit": "No ceremony.",
                        "main_liability": "No explicit boundary.",
                        "material_assumption": "Scope stays tiny.",
                    },
                ],
                "recommended_option_id": "OPT-001",
                "recommendation_rationale": "A small boundary is justified.",
                "user_decision_prompt": (
                    "Please approve, revise, or request more information."
                ),
                "offered_actions": ["approve", "revise", "more-information"],
            }
        )


def test_option_comparison_actions_are_language_independent() -> None:
    payload = {
        "decision_scope": "Choose one structure.",
        "scoring_criteria": ["Simplicity"],
        "alternatives": [
            {
                "id": "OPT-001",
                "category": "Architecture",
                "name": "Layered",
                "canonical_reference": "references/architecture-layered.md",
                "fit_score": 70,
                "fit_rationale": "Familiar.",
                "main_benefit": "Simple.",
                "main_liability": "Can couple layers.",
                "material_assumption": "Small team.",
            },
            {
                "id": "OPT-002",
                "category": "No pattern",
                "name": "No pattern",
                "canonical_reference": None,
                "fit_score": 50,
                "fit_rationale": "Few moving parts.",
                "main_benefit": "No ceremony.",
                "main_liability": "No explicit boundary.",
                "material_assumption": "Scope stays tiny.",
            },
        ],
        "fewer_than_three_rationale": "Only two alternatives address this decision.",
        "recommended_option_id": "OPT-001",
        "recommendation_rationale": "A small boundary is justified.",
        "user_decision_prompt": (
            "Bitte bestätigen, überarbeiten oder weitere Informationen anfordern."
        ),
        "offered_actions": ["approve", "revise", "more-information"],
    }
    comparison = ArchitectureOptionComparison.model_validate(payload)
    assert comparison.user_decision_prompt.startswith("Bitte")
