# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Validate the repository's Codex plugin package without mutable external tooling."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
from pathlib import Path

import yaml

try:
    from adapters.codex.runtime_targets import (
        RUNTIME_TARGETS,
        RuntimeTarget,
        detect_packaged_target,
        target_for_name,
    )
except ModuleNotFoundError as exc:
    if exc.name != "adapters":
        raise
    from runtime_targets import (  # type: ignore[import-not-found, no-redef]
        RUNTIME_TARGETS,
        RuntimeTarget,
        detect_packaged_target,
        target_for_name,
    )

SEMVER = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


def validate(
    root: Path,
    *,
    target: RuntimeTarget | None = None,
) -> None:
    root = root.resolve(strict=True)
    target = target or detect_packaged_target(root)
    manifest_path = root / ".codex-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    required = {"name", "version", "description", "author", "license", "skills", "interface"}
    missing = required - manifest.keys()
    if missing:
        raise ValueError(f"manifest fields missing: {sorted(missing)}")
    if manifest["name"] != root.name or not SEMVER.fullmatch(manifest["version"]):
        raise ValueError("plugin name or version is invalid")
    if "mcpServers" in manifest or (root / ".mcp.json").exists():
        raise ValueError("the Codex package must not register a persistent MCP server")
    if manifest.get("hooks") != "./hooks/hooks.json":
        raise ValueError(
            "the manifest must explicitly declare the bundled hook configuration"
        )
    expected_author = "AUTOSOFT Engineering (a brand of XAVIER MUFFATO LTDA)"
    if manifest["author"].get("name") != expected_author:
        raise ValueError("the manifest author must identify the brand and legal publisher")
    interface = manifest["interface"]
    if interface.get("developerName") != "AUTOSOFT Engineering":
        raise ValueError("the interface publisher must be AUTOSOFT Engineering")
    for field in ("websiteURL", "privacyPolicyURL", "termsOfServiceURL"):
        value = interface.get(field)
        if not isinstance(value, str) or not value.startswith("https://"):
            raise ValueError(f"manifest {field} must be an absolute HTTPS URL")
    if set(path.name for path in (root / ".codex-plugin").iterdir()) != {"plugin.json"}:
        raise ValueError("only plugin.json may exist inside .codex-plugin")
    for field in ("composerIcon", "logo"):
        asset = manifest["interface"].get(field)
        if asset and not (root / asset.removeprefix("./")).is_file():
            raise ValueError(f"manifest asset is missing: {asset}")
    for legal_file in ("PRIVACY.md", "TERMS.md", "SUPPORT.md"):
        if not (root / legal_file).is_file():
            raise ValueError(f"packaged public document is missing: {legal_file}")
    default_prompts = manifest["interface"].get("defaultPrompt", [])
    long_description = manifest["interface"].get("longDescription", "")
    warning = (
        "⚠️ IMPORTANT: BEFORE FIRST USE, ACTIVATE ALL FIVE BUNDLED HOOKS IN THE "
        "HOOKS SECTION BELOW."
    )
    hook_explanation = (
        "All five are required for reliable routing, continuation, safety checks, "
        "artifact validation, and complete responses."
    )
    onboarding_suffix = f"\n\n{warning} {hook_explanation}"
    if not isinstance(long_description, str) or not long_description.endswith(
        onboarding_suffix
    ):
        raise ValueError(
            "plugin long description must end with the separated five-hook onboarding block"
        )
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
    executable = root / target.executable_relative_path
    if not executable.is_file():
        raise ValueError("bundled short-lived Codex runtime is missing")
    if target.name != "windows-x86_64" and not executable.stat().st_mode & stat.S_IXUSR:
        raise ValueError("native runtime executable is not user-executable")
    if (root / "scripts" / "start-mcp.ps1").exists():
        raise ValueError("legacy persistent MCP launcher must not be packaged")
    hooks_path = root / "hooks" / "hooks.json"
    if not hooks_path.is_file():
        raise ValueError("the default Codex control-plane hook file is missing")
    hooks = json.loads(hooks_path.read_text("utf-8"))
    if sum(
        len(group["hooks"])
        for groups in hooks["hooks"].values()
        for group in groups
    ) != 5:
        raise ValueError("Codex package must define exactly five command hooks")
    if set(hooks["hooks"]) != {
        "UserPromptSubmit",
        "PreToolUse",
        "PostToolUse",
        "PostCompact",
        "Stop",
    }:
        raise ValueError("the Codex control-plane hook events are incomplete")
    for event, groups in hooks["hooks"].items():
        for group in groups:
            for hook in group["hooks"]:
                if hook["type"] != "command" or hook["timeout"] > 5:
                    raise ValueError("control-plane hooks must be bounded command hooks")
                expected_suffix = f"--codex-hook --event {event}"
                if hook.get("command") != target.hook_command(event):
                    raise ValueError(
                        f"{event} hook must declare the exact {target.name} runtime command"
                    )
                if expected_suffix not in hook["command"]:
                    raise ValueError(f"{event} hook event arguments are invalid")
                if target.name == "windows-x86_64":
                    windows_command = hook.get("commandWindows")
                    if windows_command != target.windows_hook_command(event):
                        raise ValueError("Windows control-plane hook entry is invalid")
                elif "commandWindows" in hook:
                    raise ValueError(
                        "macOS control-plane hooks must not declare a Windows override"
                    )
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
    parser.add_argument("--target", choices=sorted(RUNTIME_TARGETS))
    args = parser.parse_args()
    validate(
        args.plugin,
        target=target_for_name(args.target) if args.target else None,
    )
    print(f"Plugin validation passed: {args.plugin.resolve()}")


if __name__ == "__main__":
    main()
