# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pytest
from ai_architect_schemas import (
    DependencyGraphEvidence,
    DependencyStatementInput,
    RepositoryAnalysisInput,
    SourceFileInput,
)
from ai_architect_tools.mcp_server import (
    INSTRUCTIONS,
    analyze_repository_dependencies,
    mcp,
)


def test_security_instructions_are_self_contained_and_bounded() -> None:
    prefix = INSTRUCTIONS[:512]
    assert len(INSTRUCTIONS) <= 512
    for required in ("Read-only", "No network", "untrusted", "root", "bounded"):
        assert required in prefix


def test_mcp_exposes_only_the_five_approved_tools() -> None:
    assert set(mcp._tool_manager._tools) == {
        "validate_architecture_contract",
        "list_architecture_decisions",
        "analyze_repository_dependencies",
        "check_architecture_boundaries",
        "scan_generated_artifact",
    }


@pytest.mark.asyncio
async def test_inline_analysis_does_not_require_mcp_roots() -> None:
    result = await analyze_repository_dependencies(
        RepositoryAnalysisInput(
            source_files=[
                SourceFileInput(relative_path="budget.py", content="import decimal\n")
            ]
        ),
        None,  # type: ignore[arg-type]
    )
    assert isinstance(result, DependencyGraphEvidence)
    assert [(edge.source, edge.target) for edge in result.edges] == [
        ("budget", "decimal")
    ]


@pytest.mark.asyncio
async def test_fast_statement_analysis_does_not_require_mcp_roots() -> None:
    result = await analyze_repository_dependencies(
        RepositoryAnalysisInput(
            dependency_statements=[
                DependencyStatementInput(
                    relative_path="budget.py",
                    start_line=17,
                    statement="import decimal",
                )
            ]
        ),
        None,  # type: ignore[arg-type]
    )
    assert isinstance(result, DependencyGraphEvidence)
    assert [(edge.source, edge.target, edge.evidence) for edge in result.edges] == [
        ("budget", "decimal", "budget.py:17")
    ]
