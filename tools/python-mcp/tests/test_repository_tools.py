# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

from pathlib import Path

import pytest
from ai_architect_schemas import BoundaryCheckInput, DecisionListInput, RepositoryAnalysisInput
from ai_architect_tools.domain.boundaries import check_architecture_boundaries
from ai_architect_tools.domain.decisions import list_architecture_decisions
from ai_architect_tools.domain.dependencies import analyze_repository_dependencies
from ai_architect_tools.domain.workspace import WorkspaceAccessError, WorkspaceReader

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

