# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Compare deterministic dependency evidence with declared dependency rules."""

from __future__ import annotations

from ai_architect_schemas import (
    ArchitectureContract,
    BoundaryCheckInput,
    ConformanceFinding,
    ConformanceReport,
    ContractValidationInput,
    RepositoryAnalysisInput,
)

from .contracts import load_safe_yaml, validate_architecture_contract
from .dependencies import analyze_repository_dependencies
from .workspace import SourceReader


def _matches_component(module: str, component: str) -> bool:
    normalized = component.replace("-", "_")
    parts = module.lstrip(".").split(".")
    return normalized in parts or module.lstrip(".").startswith(normalized + ".")


def check_architecture_boundaries(
    reader: SourceReader | None, request: BoundaryCheckInput
) -> ConformanceReport:
    validation = validate_architecture_contract(
        ContractValidationInput(yaml_content=request.contract_yaml)
    )
    if not validation.valid:
        return ConformanceReport(
            scope="invalid-contract",
            findings=[
                ConformanceFinding(
                    id="F-001",
                    classification="possible-drift",
                    severity="high",
                    confidence="high",
                    rule="The architecture contract must be valid before boundaries are checked.",
                    evidence=validation.errors[:10],
                    recommendation=(
                        "Correct and validate the architecture contract, then rerun the check."
                    ),
                )
            ],
            files_examined=0,
            files_skipped=0,
        )
    contract = ArchitectureContract.model_validate(load_safe_yaml(request.contract_yaml))
    graph = analyze_repository_dependencies(
        reader,
        RepositoryAnalysisInput(
            relative_roots=request.relative_roots,
            source_files=request.source_files,
            dependency_statements=request.dependency_statements,
            languages=request.languages,
        ),
    )
    findings: list[ConformanceFinding] = []
    for rule in contract.dependency_rules:
        if rule.policy != "deny":
            continue
        evidence = [
            edge.evidence
            for edge in graph.edges
            if _matches_component(edge.source, rule.source)
            and _matches_component(edge.target, rule.target)
        ]
        if evidence:
            findings.append(
                ConformanceFinding(
                    id=f"F-{len(findings) + 1:03d}",
                    classification="confirmed-violation",
                    severity="high",
                    confidence="high",
                    rule=(
                        f"Dependency from {rule.source} to {rule.target} is denied: "
                        f"{rule.rationale}"
                    ),
                    evidence=evidence[:50],
                    recommendation=(
                        "Remove the dependency or revise the accepted architecture decision."
                    ),
                )
            )
        if len(findings) >= 200:
            break
    return ConformanceReport(
        scope=contract.scope,
        findings=findings,
        files_examined=graph.files_examined,
        files_skipped=graph.files_skipped,
        warnings=graph.warnings,
        truncated=graph.truncated or len(findings) >= 200,
    )
