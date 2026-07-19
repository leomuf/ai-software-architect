# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from typing import TextIO, cast

import pytest
from ai_architect_schemas import (
    DependencyGraphEvidence,
    DependencyStatementInput,
    InlineRepositoryAnalysisInput,
    SourceFileInput,
)
from ai_architect_tools.mcp_server import (
    DEFAULT_IDLE_SECONDS,
    INSTRUCTIONS,
    _configured_idle_seconds,
    _idle_expired,
    _parent_is_alive,
    _tool_activity,
    analyze_repository_dependencies,
    mcp,
)
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def test_security_instructions_are_self_contained_and_bounded() -> None:
    prefix = INSTRUCTIONS[:512]
    assert len(INSTRUCTIONS) <= 512
    for required in ("Read-only", "No network", "untrusted", "root", "bounded"):
        assert required in prefix


def test_mcp_exposes_only_the_four_codex_safe_tools() -> None:
    assert set(mcp._tool_manager._tools) == {
        "validate_complete_architecture_contract",
        "analyze_python_dependencies",
        "check_python_architecture_boundaries",
        "scan_generated_architecture_artifact",
    }


def test_codex_tool_schemas_expose_no_workspace_root_or_adr_listing() -> None:
    serialized = str({name: tool.parameters for name, tool in mcp._tool_manager._tools.items()})
    assert "relative_roots" not in serialized
    assert "list_architecture_decisions" not in serialized
    validation = mcp._tool_manager._tools["validate_complete_architecture_contract"].parameters
    assert "complete-candidate-contract" in str(validation)


@pytest.mark.asyncio
async def test_inline_analysis_does_not_require_mcp_roots() -> None:
    result = await analyze_repository_dependencies(
        InlineRepositoryAnalysisInput(
            source_files=[SourceFileInput(relative_path="budget.py", content="import decimal\n")]
        )
    )
    assert isinstance(result, DependencyGraphEvidence)
    assert [(edge.source, edge.target) for edge in result.edges] == [("budget", "decimal")]


@pytest.mark.asyncio
async def test_fast_statement_analysis_does_not_require_mcp_roots() -> None:
    result = await analyze_repository_dependencies(
        InlineRepositoryAnalysisInput(
            dependency_statements=[
                DependencyStatementInput(
                    relative_path="budget.py",
                    start_line=17,
                    statement="import decimal",
                )
            ]
        )
    )
    assert isinstance(result, DependencyGraphEvidence)
    assert [(edge.source, edge.target, edge.evidence) for edge in result.edges] == [
        ("budget", "decimal", "budget.py:17")
    ]


def test_idle_timeout_configuration_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_ARCHITECT_MCP_IDLE_SECONDS", "30")
    assert _configured_idle_seconds() == 30
    monkeypatch.setenv("AI_ARCHITECT_MCP_IDLE_SECONDS", "1")
    assert _configured_idle_seconds() == DEFAULT_IDLE_SECONDS
    monkeypatch.setenv("AI_ARCHITECT_MCP_IDLE_SECONDS", "not-a-number")
    assert _configured_idle_seconds() == DEFAULT_IDLE_SECONDS


def test_parent_probe_is_read_only_and_detects_current_parent() -> None:
    assert _parent_is_alive(os.getppid())
    assert not _parent_is_alive(0)


def test_active_tool_call_prevents_idle_termination(monkeypatch: pytest.MonkeyPatch) -> None:
    import ai_architect_tools.mcp_server as server

    monkeypatch.setattr(server, "_last_activity", 10.0)
    assert _idle_expired(20.0, 5.0)
    with _tool_activity():
        assert not _idle_expired(1_000.0, 5.0)


@pytest.mark.asyncio
async def test_source_stdio_process_exits_after_client_closes_input() -> None:
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "ai_architect_tools.mcp_server"],
    )
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as errlog:
        async with asyncio.timeout(10):
            async with stdio_client(parameters, errlog=cast(TextIO, errlog)) as (
                read_stream,
                write_stream,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    assert len(tools.tools) == 4
        errlog.seek(0)
        assert "Traceback" not in errlog.read()
