# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Validate the repository's Codex plugin package without mutable external tooling."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


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
    skill_root = root / "skills" / "ai-software-architect"
    skill_text = (skill_root / "SKILL.md").read_text("utf-8")
    _, frontmatter, _ = skill_text.split("---", 2)
    metadata = yaml.safe_load(frontmatter)
    if metadata["name"] != "ai-software-architect" or metadata["license"] != "MIT":
        raise ValueError("generated skill metadata is invalid")
    openai = yaml.safe_load((skill_root / "agents" / "openai.yaml").read_text("utf-8"))
    if openai["policy"]["allow_implicit_invocation"] is not False:
        raise ValueError("implicit invocation must remain disabled")
    mcp = json.loads((root / ".mcp.json").read_text("utf-8"))
    server = mcp["mcpServers"]["ai-software-architect-tools"]
    if (
        set(server) != {"command", "args", "cwd"}
        or server["args"] != []
        or server["cwd"] != "."
    ):
        raise ValueError(
            "MCP startup must use a fixed executable from the plugin-root working directory"
        )
    executable = root / server["command"].removeprefix("./")
    if not executable.is_file() or executable.suffix.casefold() != ".exe":
        raise ValueError("bundled MCP executable is missing")
    text_files = (
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.casefold() in {".md", ".yaml", ".json"}
    )
    if "TODO" in "\n".join(
        path.read_text("utf-8", errors="ignore") for path in text_files
    ):
        raise ValueError("plugin contains an unresolved TODO")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("plugin", type=Path)
    args = parser.parse_args()
    validate(args.plugin)
    print(f"Plugin validation passed: {args.plugin.resolve()}")


if __name__ == "__main__":
    main()
