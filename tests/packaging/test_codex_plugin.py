# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml
from pytest import MonkeyPatch, raises

from adapters.codex import build_plugin, validate_plugin


def _snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_codex_plugin_is_reproducible_and_complete(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    output_parent = tmp_path / "dist" / "codex"
    output = output_parent / "ai-software-architect"
    monkeypatch.setattr(build_plugin, "OUTPUT_PARENT", output_parent)
    monkeypatch.setattr(build_plugin, "OUTPUT", output)
    runtime = tmp_path / "ai-architect-mcp"
    runtime.mkdir()
    (runtime / "ai-architect-mcp.exe").write_bytes(b"reviewed-test-runtime")
    (runtime / "python313.dll").write_bytes(b"reviewed-test-library")

    first = build_plugin.assemble(runtime)
    first_snapshot = _snapshot(first)
    second = build_plugin.assemble(runtime)
    assert _snapshot(second) == first_snapshot
    assert second == output

    manifest = json.loads((second / ".codex-plugin" / "plugin.json").read_text("utf-8"))
    assert manifest["name"] == "ai-software-architect"
    assert all(
        "$ai-software-architect" in prompt
        for prompt in manifest["interface"]["defaultPrompt"]
    )
    assert manifest["license"] == "MIT"
    assert manifest["mcpServers"] == "./.mcp.json"
    assert not (second / ".codex-plugin" / ".mcp.json").exists()
    assert not (second / ".codex").exists()
    assert not (second / "agents").exists()

    skill = second / "skills" / "ai-software-architect"
    skill_text = (skill / "SKILL.md").read_text("utf-8")
    assert len(skill_text.splitlines()) <= 500
    assert all(f"Canonical module: `{name}`" in skill_text for name in build_plugin.SKILL_ORDER)
    assert "<!-- ai-architect-outcome: clarify -->" in skill_text
    assert "<!-- ai-architect-outcome: recommendation -->" in skill_text
    assert "<!-- ai-architect-outcome: complete -->" in skill_text
    assert "<!-- ai-architect-actions: approve, revise, more-information -->" in skill_text
    assert len(list((skill / "references").iterdir())) == 51
    assert len(list((skill / "assets").iterdir())) == 3
    focused = second / "skills" / "evaluate-architecture-options"
    assert (focused / "SKILL.md").is_file()
    assert (focused / "references" / "gof-abstract-factory.md").is_file()
    focused_metadata = yaml.safe_load((focused / "agents" / "openai.yaml").read_text("utf-8"))
    assert focused_metadata["policy"]["allow_implicit_invocation"] is False

    metadata = yaml.safe_load((skill / "agents" / "openai.yaml").read_text("utf-8"))
    assert metadata["policy"]["allow_implicit_invocation"] is False
    assert metadata["dependencies"]["tools"][0]["transport"] == "stdio"

    mcp_config = json.loads((second / ".mcp.json").read_text("utf-8"))
    server = mcp_config["mcpServers"]["ai-software-architect-tools"]
    assert server["command"] == ("./runtime/windows-x86_64/ai-architect-mcp/ai-architect-mcp.exe")
    assert server["args"] == []
    assert server["cwd"] == "."
    assert (second / server["command"].removeprefix("./")).is_file()
    hooks = json.loads((second / "hooks" / "hooks.json").read_text("utf-8"))
    assert set(hooks["hooks"]) == {"UserPromptSubmit", "PreToolUse", "Stop"}
    assert "--codex-hook" in str(hooks)
    pre_tool_matcher = hooks["hooks"]["PreToolUse"][0]["matcher"]
    assert "Bash" in pre_tool_matcher
    assert "apply_patch" in pre_tool_matcher

    provenance = json.loads((second / "provenance.json").read_text("utf-8"))
    assert provenance["generator"] == "adapters/codex/build_plugin.py"
    assert len(provenance["source_to_output"]) == 60
    assert (
        "shared/skills/evaluate-architecture-options/SKILL.md"
        in (provenance["additional_source_to_output"])
    )
    for relative, expected_hash in provenance["output_sha256"].items():
        assert hashlib.sha256((second / relative).read_bytes()).hexdigest() == expected_hash

    versioned = build_plugin.assemble(
        runtime,
        plugin_version="0.1.0+codex.test-cachebuster",
    )
    versioned_manifest_path = versioned / ".codex-plugin" / "plugin.json"
    versioned_manifest = json.loads(versioned_manifest_path.read_text("utf-8"))
    assert versioned_manifest["version"] == "0.1.0+codex.test-cachebuster"
    versioned_provenance = json.loads(
        (versioned / "provenance.json").read_text("utf-8")
    )
    assert versioned_provenance["plugin_version"] == versioned_manifest["version"]
    assert (
        versioned_provenance["output_sha256"][".codex-plugin/plugin.json"]
        == hashlib.sha256(versioned_manifest_path.read_bytes()).hexdigest()
    )
    validate_plugin.validate(versioned)

    notice = versioned / "NOTICE"
    notice.write_text(notice.read_text("utf-8") + "post-build mutation\n", encoding="utf-8")
    with raises(ValueError, match="provenance hash mismatch"):
        validate_plugin.validate(versioned)
