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
    runtime = tmp_path / "ai-architect-runtime"
    runtime.mkdir()
    (runtime / "ai-architect-runtime.exe").write_bytes(b"reviewed-test-runtime")
    (runtime / "python313.dll").write_bytes(b"reviewed-test-library")

    first = build_plugin.assemble(runtime)
    first_snapshot = _snapshot(first)
    second = build_plugin.assemble(runtime)
    assert _snapshot(second) == first_snapshot
    assert second == output

    manifest = json.loads((second / ".codex-plugin" / "plugin.json").read_text("utf-8"))
    assert manifest["name"] == "ai-software-architect"
    default_prompts = manifest["interface"]["defaultPrompt"]
    assert all("$ai-software-architect" not in prompt for prompt in default_prompts)
    assert all("plugin://ai-software-architect" not in prompt for prompt in default_prompts)
    assert "Suggest suitable design patterns for my current project." in default_prompts
    warning = (
        "⚠️ IMPORTANT: BEFORE FIRST USE, ACTIVATE ALL FIVE BUNDLED HOOKS IN THE "
        "HOOKS SECTION BELOW."
    )
    hook_explanation = (
        "All five are required for reliable routing, continuation, safety checks, "
        "artifact validation, and complete responses."
    )
    assert manifest["interface"]["longDescription"].endswith(
        f"\n\n{warning} {hook_explanation}"
    )
    assert manifest["license"] == "MIT"
    assert "mcpServers" not in manifest
    assert not (second / ".mcp.json").exists()
    assert not (second / ".codex-plugin" / ".mcp.json").exists()
    assert not (second / ".codex").exists()
    assert not (second / "agents").exists()

    skill = second / "skills" / "ai-software-architect"
    skill_text = (skill / "SKILL.md").read_text("utf-8")
    assert len(skill_text.splitlines()) <= 500
    assert all(
        build_plugin.WORKFLOW_REFERENCE_OUTPUTS[name] in skill_text
        for name in build_plugin.SKILL_ORDER
    )
    assert "Return only user-facing Markdown" in skill_text
    assert "Every recommendation ends with" in skill_text
    for marker in (
        "ai-architect-outcome:",
        "ai-architect-decision-shape:",
        "ai-architect-actions:",
    ):
        assert marker not in skill_text
    assert len(list((skill / "references").iterdir())) == 57
    assert len(list((skill / "assets").iterdir())) == 4
    assert {path.name for path in (second / "skills").iterdir() if path.is_dir()} == {
        "ai-software-architect"
    }
    assert (skill / "references" / "gof-abstract-factory.md").is_file()
    for name, relative_path in build_plugin.WORKFLOW_REFERENCE_OUTPUTS.items():
        workflow = skill / relative_path
        assert workflow.is_file()
        workflow_text = workflow.read_text("utf-8")
        assert f"Canonical source: shared/skills/{name}/SKILL.md" in workflow_text
        assert "](references/" not in workflow_text
        assert "](assets/" not in workflow_text
        if name == "evaluate-architecture-options":
            assert "Codex progressive-disclosure boundary" in workflow_text
            assert "Load at most one focused reference" in workflow_text
            assert "## Compact canonical reference catalog" in workflow_text
            assert "| GoF | Strategy | `gof-strategy.md` |" in workflow_text
            assert build_plugin.CANONICAL_REFERENCE_BASE in workflow_text
            assert "Bundled path rule: `references/<File>`" in workflow_text
            assert "## Direct reference routing" not in workflow_text
            assert len(workflow_text.encode("utf-8")) < 15_000
    authoring_bundle = skill / "assets" / "artifact-authoring-bundle.md"
    assert authoring_bundle.is_file()
    bundle_text = authoring_bundle.read_text("utf-8")
    for heading, source in build_plugin.AUTHORING_BUNDLE_SOURCES:
        assert f"## {heading}" in bundle_text
        assert build_plugin._relative(source) in bundle_text
    for required_path in (
        ".ai-architect/project-context.md",
        ".ai-architect/architecture-contract.yaml",
        ".ai-architect/implementation-plan.md",
        ".ai-architect/decisions/ADR-NNN[-slug].md",
    ):
        assert required_path in bundle_text
    assert "Do not rename `implementation-plan.md`" in bundle_text
    assert not (skill / "assets" / "reference-catalog.md").exists()
    assert "12,000 combined" in bundle_text
    assert "plain `OPT-NNN` identifiers" in bundle_text

    metadata = yaml.safe_load((skill / "agents" / "openai.yaml").read_text("utf-8"))
    assert metadata["interface"]["short_description"] == (
        "Choose best design patterns"
    )
    assert metadata["policy"]["allow_implicit_invocation"] is False
    assert metadata["interface"]["default_prompt"] == (
        "Suggest project-fit patterns or guide a complete architecture workflow."
    )
    assert "dependencies" not in metadata
    assert not (second / "scripts" / "start-mcp.ps1").exists()
    assert (
        second
        / "runtime"
        / "windows-x86_64"
        / "ai-architect-runtime"
        / "ai-architect-runtime.exe"
    ).is_file()
    hooks = json.loads((second / "hooks" / "hooks.json").read_text("utf-8"))
    assert hooks["description"].startswith("Five required local hooks")
    assert set(hooks["hooks"]) == {
        "UserPromptSubmit",
        "PreToolUse",
        "PostToolUse",
        "PostCompact",
        "Stop",
    }
    assert sum(
        len(group["hooks"])
        for groups in hooks["hooks"].values()
        for group in groups
    ) == 5
    assert "--codex-hook" in str(hooks)
    pre_tool_matcher = hooks["hooks"]["PreToolUse"][0]["matcher"]
    assert "Bash" in pre_tool_matcher
    assert "apply_patch" in pre_tool_matcher

    provenance = json.loads((second / "provenance.json").read_text("utf-8"))
    assert provenance["generator"] == "adapters/codex/build_plugin.py"
    assert len(provenance["source_to_output"]) == 60
    assert len(provenance["additional_source_to_output"]) == 5
    assert set(provenance["additional_source_to_output"].values()) == {
        "skills/ai-software-architect/assets/artifact-authoring-bundle.md",
        "skills/ai-software-architect/references/workflow-evaluate-architecture-options.md",
    }
    for relative, expected_hash in provenance["output_sha256"].items():
        assert hashlib.sha256((second / relative).read_bytes()).hexdigest() == expected_hash

    versioned = build_plugin.assemble(
        runtime,
        plugin_version="0.1.0+codex.test-cachebuster",
    )
    versioned_manifest_path = versioned / ".codex-plugin" / "plugin.json"
    versioned_manifest = json.loads(versioned_manifest_path.read_text("utf-8"))
    assert versioned_manifest["version"] == "0.1.0+codex.test-cachebuster"
    versioned_provenance = json.loads((versioned / "provenance.json").read_text("utf-8"))
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
