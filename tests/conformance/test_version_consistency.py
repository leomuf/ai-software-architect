# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Keep the public plugin and bundled Python package versions aligned."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from ai_architect_tools import __version__ as tools_runtime_version

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "adapters" / "codex" / "templates" / "plugin.json"
PROJECTS = {
    "ai-software-architect-workspace": ROOT / "pyproject.toml",
    "ai-architect-schemas": ROOT / "shared" / "schemas" / "pyproject.toml",
    "ai-architect-tools": ROOT / "tools" / "python-mcp" / "pyproject.toml",
}


def _project_version(path: Path) -> str:
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    return str(payload["project"]["version"])


def test_product_and_bundled_package_versions_are_aligned() -> None:
    plugin_version = str(json.loads(MANIFEST.read_text("utf-8"))["version"])

    assert {name: _project_version(path) for name, path in PROJECTS.items()} == {
        name: plugin_version for name in PROJECTS
    }
    assert tools_runtime_version == plugin_version


def test_lockfile_records_the_aligned_workspace_versions() -> None:
    plugin_version = str(json.loads(MANIFEST.read_text("utf-8"))["version"])
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    locked_versions = {
        str(package["name"]): str(package["version"])
        for package in lock["package"]
        if package["name"] in PROJECTS
    }

    assert locked_versions == {name: plugin_version for name in PROJECTS}
