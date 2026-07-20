# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Validate the repository's Codex plugin package without mutable external tooling."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import yaml

SEMVER = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


def validate(root: Path) -> None:
    root = root.resolve(strict=True)
    manifest_path = root / ".codex-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    required = {"name", "version", "description", "author", "license", "skills", "interface"}
    missing = required - manifest.keys()
    if missing:
        raise ValueError(f"manifest fields missing: {sorted(missing)}")
    if manifest["name"] != root.name or not SEMVER.fullmatch(manifest["version"]):
        raise ValueError("plugin name or version is invalid")
    if manifest["mcpServers"] != "./.mcp.json" or not (root / ".mcp.json").is_file():
        raise ValueError("MCP companion file is missing")
    if set(path.name for path in (root / ".codex-plugin").iterdir()) != {"plugin.json"}:
        raise ValueError("only plugin.json may exist inside .codex-plugin")
    for field in ("composerIcon", "logo"):
        asset = manifest["interface"].get(field)
        if asset and not (root / asset.removeprefix("./")).is_file():
            raise ValueError(f"manifest asset is missing: {asset}")
    default_prompts = manifest["interface"].get("defaultPrompt", [])
    if not default_prompts or not all(
        isinstance(prompt, str)
        and prompt.strip()
        and "$ai-software-architect" not in prompt
        and "plugin://ai-software-architect" not in prompt
        for prompt in default_prompts
    ):
        raise ValueError("plugin default prompts must contain task text without activation markers")
    if not any(
        "design pattern" in prompt.casefold() and "project" in prompt.casefold()
        for prompt in default_prompts
    ):
        raise ValueError("plugin default prompts must include project-fit design-pattern guidance")
    skill_root = root / "skills" / "ai-software-architect"
    packaged_skills = {path.name for path in (root / "skills").iterdir() if path.is_dir()}
    if packaged_skills != {"ai-software-architect"}:
        raise ValueError("the Codex package must expose exactly one user-facing skill")
    skill_text = (skill_root / "SKILL.md").read_text("utf-8")
    _, frontmatter, _ = skill_text.split("---", 2)
    metadata = yaml.safe_load(frontmatter)
    if metadata["name"] != "ai-software-architect" or metadata["license"] != "MIT":
        raise ValueError("generated skill metadata is invalid")
    forbidden_response_markers = (
        "ai-architect-outcome:",
        "ai-architect-decision-shape:",
        "ai-architect-actions:",
    )
    if any(marker in skill_text for marker in forbidden_response_markers):
        raise ValueError("generated skill must not expose internal response markers")
    for phrase in (
        "Return only user-facing Markdown",
        "Every recommendation ends with",
        "Do not emit internal control markers",
    ):
        if phrase not in skill_text:
            raise ValueError("generated skill visible-response contract is incomplete")
    openai = yaml.safe_load((skill_root / "agents" / "openai.yaml").read_text("utf-8"))
    if openai["policy"]["allow_implicit_invocation"] is not False:
        raise ValueError("implicit invocation must remain disabled")
    mcp = json.loads((root / ".mcp.json").read_text("utf-8"))
    server = mcp["mcpServers"]["ai-software-architect-mcp"]
    expected_args = [
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "./scripts/start-mcp.ps1",
    ]
    if (
        set(server) != {"command", "args", "cwd"}
        or server["command"] != "powershell.exe"
        or server["args"] != expected_args
        or server["cwd"] != "."
    ):
        raise ValueError(
            "MCP startup must use the reviewed cache-safe PowerShell launcher"
        )
    launcher = root / "scripts" / "start-mcp.ps1"
    executable = root / "runtime/windows-x86_64/ai-architect-mcp/ai-architect-mcp.exe"
    if not launcher.is_file() or not executable.is_file():
        raise ValueError("bundled MCP executable is missing")
    hooks_path = root / "hooks" / "hooks.json"
    if not hooks_path.is_file():
        raise ValueError("the default Codex control-plane hook file is missing")
    hooks = json.loads(hooks_path.read_text("utf-8"))
    if set(hooks["hooks"]) != {"UserPromptSubmit", "PreToolUse", "Stop"}:
        raise ValueError("the Codex control-plane hook events are incomplete")
    for groups in hooks["hooks"].values():
        for group in groups:
            for hook in group["hooks"]:
                if hook["type"] != "command" or hook["timeout"] > 5:
                    raise ValueError("control-plane hooks must be bounded command hooks")
                if "--codex-hook" not in hook["commandWindows"]:
                    raise ValueError("Windows control-plane hook entry is invalid")
                windows_command = hook["commandWindows"]
                if "$env:PLUGIN_ROOT" not in windows_command:
                    raise ValueError(
                        "Windows control-plane hooks must use PowerShell plugin-root "
                        "environment syntax"
                    )
                if "%PLUGIN_ROOT%" in windows_command:
                    raise ValueError("cmd.exe environment syntax is invalid in a PowerShell hook")
    text_files = (
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.casefold() in {".md", ".yaml", ".json"}
    )
    if "TODO" in "\n".join(path.read_text("utf-8", errors="ignore") for path in text_files):
        raise ValueError("plugin contains an unresolved TODO")
    provenance_path = root / "provenance.json"
    provenance = json.loads(provenance_path.read_text("utf-8"))
    if provenance.get("plugin_version") != manifest["version"]:
        raise ValueError("provenance plugin version does not match the manifest")
    expected_hashes = provenance.get("output_sha256")
    if not isinstance(expected_hashes, dict):
        raise ValueError("provenance output hashes are missing")
    packaged_files = {
        path.relative_to(root).as_posix(): path
        for path in root.rglob("*")
        if path.is_file() and path != provenance_path
    }
    if set(expected_hashes) != set(packaged_files):
        raise ValueError("provenance file inventory does not match the plugin package")
    for relative_path, path in packaged_files.items():
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if expected_hashes[relative_path] != actual:
            raise ValueError(f"provenance hash mismatch: {relative_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("plugin", type=Path)
    args = parser.parse_args()
    validate(args.plugin)
    print(f"Plugin validation passed: {args.plugin.resolve()}")


if __name__ == "__main__":
    main()
