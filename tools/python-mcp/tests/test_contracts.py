# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

from ai_architect_schemas import ArtifactSecretScanInput, ContractValidationInput
from ai_architect_tools.domain.contracts import (
    scan_generated_artifact,
    validate_architecture_contract,
)

VALID_CONTRACT = """\
schema_version: 1.0.0
revision: 1
scope: notification-subsystem
architecture_style: modular-monolith-with-ports-and-adapters
components:
  - id: domain
    responsibility: Own notification policy
  - id: adapter
    responsibility: Integrate delivery vendors
dependency_rules:
  - source: domain
    target: adapter
    policy: deny
    rationale: Keep vendor details out of the domain
decision_ids: [ADR-001]
"""


def test_valid_contract_is_accepted() -> None:
    result = validate_architecture_contract(ContractValidationInput(yaml_content=VALID_CONTRACT))
    assert result.valid is True
    assert result.schema_version == "1.0.0"


def test_duplicate_yaml_key_is_rejected() -> None:
    result = validate_architecture_contract(
        ContractValidationInput(
            yaml_content="schema_version: 1.0.0\nschema_version: 2.0.0\n"
        )
    )
    assert result.valid is False
    assert "duplicate key" in result.errors[0]


def test_yaml_alias_is_rejected() -> None:
    result = validate_architecture_contract(
        ContractValidationInput(
            yaml_content="schema_version: &version 1.0.0\nrevision: 1\nscope: *version\n"
        )
    )
    assert result.valid is False
    assert "aliases are not allowed" in result.errors[0]


def test_secret_scanner_reports_only_category_and_line() -> None:
    synthetic = "api_key = 'synthetic-secret-value-1234567890'"
    result = scan_generated_artifact(
        ArtifactSecretScanInput(content=synthetic, artifact_kind="contract")
    )
    assert result.safe_to_write is False
    assert result.findings[0].category == "credential"
    assert result.findings[0].line == 1
    assert "synthetic-secret" not in result.model_dump_json()


def test_secret_scanner_allows_documented_placeholder() -> None:
    result = scan_generated_artifact(
        ArtifactSecretScanInput(
            content="api_key: ${AI_ARCHITECT_API_KEY}", artifact_kind="context"
        )
    )
    assert result.safe_to_write is True

