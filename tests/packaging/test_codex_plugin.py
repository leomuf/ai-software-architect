# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from adapters.codex.build_plugin import OUTPUT, SKILL_ORDER, assemble


def _snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_codex_plugin_is_reproducible_and_complete(tmp_path: Path) -> None:
    runtime = tmp_path / "ai-architect-mcp.exe"
    runtime.write_bytes(b"reviewed-test-runtime")

    first = assemble(runtime)
    first_snapshot = _snapshot(first)
    second = assemble(runtime)
    assert _snapshot(second) == first_snapshot
    assert second == OUTPUT

    manifest = json.loads((second / ".codex-plugin" / "plugin.json").read_text("utf-8"))
    assert manifest["name"] == "ai-software-architect"
    assert manifest["license"] == "MIT"
    assert manifest["mcpServers"] == "./.mcp.json"
    assert not (second / ".codex-plugin" / ".mcp.json").exists()

    skill = second / "skills" / "ai-software-architect"
    skill_text = (skill / "SKILL.md").read_text("utf-8")
    assert len(skill_text.splitlines()) <= 500
    assert all(f"Canonical module: `{name}`" in skill_text for name in SKILL_ORDER)
    assert len(list((skill / "references").iterdir())) == 51
    assert len(list((skill / "assets").iterdir())) == 3

    metadata = yaml.safe_load((skill / "agents" / "openai.yaml").read_text("utf-8"))
    assert metadata["policy"]["allow_implicit_invocation"] is False
    assert metadata["dependencies"]["tools"][0]["transport"] == "stdio"

    mcp_config = json.loads((second / ".mcp.json").read_text("utf-8"))
    server = mcp_config["mcpServers"]["ai-software-architect-tools"]
    assert server["command"] == "./runtime/windows-x86_64/ai-architect-mcp.exe"
    assert server["args"] == []
    assert (second / server["command"].removeprefix("./")).is_file()

    provenance = json.loads((second / "provenance.json").read_text("utf-8"))
    assert provenance["generator"] == "adapters/codex/build_plugin.py"
    assert len(provenance["source_to_output"]) == 60
    for relative, expected_hash in provenance["output_sha256"].items():
        assert hashlib.sha256((second / relative).read_bytes()).hexdigest() == expected_hash

