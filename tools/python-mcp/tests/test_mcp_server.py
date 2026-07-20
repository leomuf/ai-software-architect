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
    DependencyAnalysisInput,
    DependencyGraphEvidence,
    DependencyStatementInput,
)
from ai_architect_tools.mcp_server import (
    IDLE_SELF_REAP_SECONDS,
    INSTRUCTIONS,
    _parent_is_alive,
    _should_self_reap,
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
    assert mcp.name == "ai-software-architect-mcp"
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
    dependency_analysis = mcp._tool_manager._tools["analyze_python_dependencies"].parameters
    assert "dependency_statements" in str(dependency_analysis)
    assert "source_files" not in str(dependency_analysis)
    validation = mcp._tool_manager._tools["validate_complete_architecture_contract"].parameters
    assert "complete-candidate-contract" in str(validation)


@pytest.mark.asyncio
async def test_fast_statement_analysis_does_not_require_mcp_roots() -> None:
    result = await analyze_repository_dependencies(
        DependencyAnalysisInput(
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


def test_parent_probe_is_read_only_and_detects_current_parent() -> None:
    assert _parent_is_alive(os.getppid())
    assert not _parent_is_alive(0)


def test_idle_self_reap_interval_is_short_and_bounded() -> None:
    assert 5 <= IDLE_SELF_REAP_SECONDS <= 30
    expired = IDLE_SELF_REAP_SECONDS + 1
    assert _should_self_reap(
        active_calls=0,
        last_activity=0,
        now=expired,
    )
    assert not _should_self_reap(
        active_calls=1,
        last_activity=0,
        now=expired,
    )
    assert not _should_self_reap(
        active_calls=0,
        last_activity=0,
        now=IDLE_SELF_REAP_SECONDS - 0.001,
    )


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


@pytest.mark.asyncio
async def test_source_stdio_process_self_reaps_when_started_but_unused() -> None:
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "ai_architect_tools.mcp_server",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        await asyncio.wait_for(process.wait(), timeout=IDLE_SELF_REAP_SECONDS + 5)
        assert process.returncode == 0
        assert process.stderr is not None
        assert b"Traceback" not in await process.stderr.read()
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()
