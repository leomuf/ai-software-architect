# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

from ai_architect_tools.mcp_server import INSTRUCTIONS, mcp


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
