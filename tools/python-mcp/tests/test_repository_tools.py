# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

from pathlib import Path

import pytest
from ai_architect_schemas import (
    BoundaryCheckInput,
    DecisionListInput,
    DependencyStatementInput,
    RepositoryAnalysisInput,
    SourceFileInput,
)
from ai_architect_tools.domain.boundaries import check_architecture_boundaries
from ai_architect_tools.domain.decisions import list_architecture_decisions
from ai_architect_tools.domain.dependencies import analyze_repository_dependencies
from ai_architect_tools.domain.workspace import (
    InlineSourceReader,
    WorkspaceAccessError,
    WorkspaceReader,
)

from .test_contracts import VALID_CONTRACT


def test_workspace_rejects_traversal_and_protected_files(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("SECRET=value", encoding="utf-8")
    reader = WorkspaceReader(tmp_path)
    with pytest.raises(WorkspaceAccessError, match="workspace-relative"):
        reader.read_text("../outside.py", {".py"})
    with pytest.raises(WorkspaceAccessError, match="protected"):
        reader.read_text(".env", {".env"})


def test_dependency_analysis_uses_ast_and_discloses_dynamic_imports(tmp_path: Path) -> None:
    package = tmp_path / "domain"
    package.mkdir()
    (package / "service.py").write_text(
        '"import ignored.comment"\nimport json\nfrom adapter import vendor\n'
        '__import__("dynamic_module")\n',
        encoding="utf-8",
    )
    result = analyze_repository_dependencies(
        WorkspaceReader(tmp_path), RepositoryAnalysisInput(relative_roots=["domain"])
    )
    assert {(edge.source, edge.target) for edge in result.edges} == {
        ("domain.service", "json"),
        ("domain.service", "adapter"),
    }
    assert result.warnings == ["Dynamic import at domain/service.py:4 was not resolved"]


def test_boundary_check_reports_denied_dependency(tmp_path: Path) -> None:
    domain = tmp_path / "domain"
    domain.mkdir()
    (domain / "service.py").write_text("from adapter import vendor\n", encoding="utf-8")
    result = check_architecture_boundaries(
        WorkspaceReader(tmp_path),
        BoundaryCheckInput(relative_roots=["domain"], contract_yaml=VALID_CONTRACT),
    )
    assert len(result.findings) == 1
    assert result.findings[0].classification == "confirmed-violation"
    assert result.findings[0].evidence == ["domain/service.py:1"]


def test_inline_dependency_analysis_uses_only_supplied_sources() -> None:
    sources = [
        SourceFileInput(
            relative_path="domain/service.py",
            content="import json\nfrom adapter import vendor\n",
        )
    ]
    request = RepositoryAnalysisInput(source_files=sources)
    result = analyze_repository_dependencies(InlineSourceReader(sources), request)
    assert {(edge.source, edge.target) for edge in result.edges} == {
        ("domain.service", "json"),
        ("domain.service", "adapter"),
    }
    assert result.warnings == [
        "Inline source mode analyzes only host-supplied files; coverage may be incomplete"
    ]


def test_inline_boundary_check_reports_denied_dependency() -> None:
    sources = [
        SourceFileInput(
            relative_path="domain/service.py", content="from adapter import vendor\n"
        )
    ]
    result = check_architecture_boundaries(
        InlineSourceReader(sources),
        BoundaryCheckInput(source_files=sources, contract_yaml=VALID_CONTRACT),
    )
    assert len(result.findings) == 1
    assert result.findings[0].evidence == ["domain/service.py:1"]


def test_fast_statement_analysis_preserves_original_evidence_lines() -> None:
    request = RepositoryAnalysisInput(
        dependency_statements=[
            DependencyStatementInput(
                relative_path="budget_book.py",
                start_line=12,
                statement="import pandas as pd",
            ),
            DependencyStatementInput(
                relative_path="budget_book.py",
                start_line=20,
                statement="from matplotlib import (\n    pyplot,\n)",
            ),
        ]
    )
    result = analyze_repository_dependencies(None, request)
    assert [(edge.source, edge.target, edge.evidence) for edge in result.edges] == [
        ("budget_book", "pandas", "budget_book.py:12"),
        ("budget_book", "matplotlib", "budget_book.py:20"),
    ]
    assert result.files_examined == 1
    assert result.files_skipped == 0
    assert result.warnings == [
        "Fast statement mode analyzes only host-supplied static imports; "
        "dynamic imports and omitted statements are not evaluated"
    ]


def test_fast_statement_boundary_check_reports_denied_dependency() -> None:
    statements = [
        DependencyStatementInput(
            relative_path="domain/service.py",
            start_line=41,
            statement="from adapter import vendor",
        )
    ]
    result = check_architecture_boundaries(
        None,
        BoundaryCheckInput(
            dependency_statements=statements,
            contract_yaml=VALID_CONTRACT,
        ),
    )
    assert len(result.findings) == 1
    assert result.findings[0].evidence == ["domain/service.py:41"]
    assert result.warnings == [
        "Fast statement mode analyzes only host-supplied static imports; "
        "dynamic imports and omitted statements are not evaluated"
    ]


def test_fast_statement_mode_rejects_non_import_code_and_untrusted_paths() -> None:
    with pytest.raises(WorkspaceAccessError, match="exactly one static import"):
        analyze_repository_dependencies(
            None,
            RepositoryAnalysisInput(
                dependency_statements=[
                    DependencyStatementInput(
                        relative_path="app.py",
                        start_line=1,
                        statement="print('not an import')",
                    )
                ]
            ),
        )
    with pytest.raises(WorkspaceAccessError, match="workspace-relative"):
        analyze_repository_dependencies(
            None,
            RepositoryAnalysisInput(
                dependency_statements=[
                    DependencyStatementInput(
                        relative_path="../outside.py",
                        start_line=1,
                        statement="import os",
                    )
                ]
            ),
        )


def test_inline_source_reader_rejects_untrusted_paths_and_formats() -> None:
    with pytest.raises(WorkspaceAccessError, match="workspace-relative"):
        InlineSourceReader(
            [SourceFileInput(relative_path="../outside.py", content="import os\n")]
        )
    with pytest.raises(WorkspaceAccessError, match="workspace-relative"):
        InlineSourceReader(
            [SourceFileInput(relative_path="C:\\outside.py", content="import os\n")]
        )
    with pytest.raises(WorkspaceAccessError, match="hidden"):
        InlineSourceReader(
            [SourceFileInput(relative_path=".venv/injected.py", content="import os\n")]
        )
    with pytest.raises(WorkspaceAccessError, match="not supported"):
        InlineSourceReader(
            [SourceFileInput(relative_path="notes.txt", content="import os\n")]
        )
    with pytest.raises(WorkspaceAccessError, match="single-file budget"):
        InlineSourceReader(
            [SourceFileInput(relative_path="large.py", content="é" * 300_000)]
        )


def test_decision_listing_validates_frontmatter_and_filename(tmp_path: Path) -> None:
    directory = tmp_path / ".ai-architect" / "decisions"
    directory.mkdir(parents=True)
    (directory / "ADR-001-style.md").write_text(
        """---
schema_version: 1.0.0
revision: 1
decision:
  id: ADR-001
  title: Choose architecture style
  status: accepted
  context: The subsystem needs a stable structure.
  drivers: [Maintainability]
  considered_option_ids: [OPT-001]
  selected_option_id: OPT-001
  decision: Use ports and adapters.
  validation_criteria: [Domain does not depend on adapters]
---

# Choose architecture style
""",
        encoding="utf-8",
    )
    result = list_architecture_decisions(WorkspaceReader(tmp_path), DecisionListInput())
    assert [decision.id for decision in result.decisions] == ["ADR-001"]
    assert result.invalid_files == []
