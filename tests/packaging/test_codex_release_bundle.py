# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MARKETPLACE_TEMPLATE = ROOT / "adapters" / "codex" / "templates" / "marketplace.json"
INSTALL_GUIDE = ROOT / "docs" / "INSTALL_CODEX_PLUGIN.md"
PACKAGE_SCRIPT = ROOT / "scripts" / "package-codex-release.ps1"


def test_release_marketplace_points_to_bundled_plugin() -> None:
    marketplace = json.loads(MARKETPLACE_TEMPLATE.read_text("utf-8"))

    assert marketplace["name"] == "ai-software-architect-release"
    assert marketplace["interface"]["displayName"] == "AI Software Architect Release"
    assert marketplace["plugins"] == [
        {
            "name": "ai-software-architect",
            "source": {
                "source": "local",
                "path": "./plugins/ai-software-architect",
            },
            "policy": {
                "installation": "AVAILABLE",
                "authentication": "ON_INSTALL",
            },
            "category": "Productivity",
        }
    ]


def test_install_guide_requires_no_development_runtime() -> None:
    guide = INSTALL_GUIDE.read_text("utf-8")

    assert "without Python, `uv`" in guide
    assert ".agents/plugins/marketplace.json" in guide
    assert "$ai-software-architect" in guide
    assert "@AI Software Architect` plugin selector as a substitute" in guide


@pytest.mark.skipif(
    shutil.which("powershell.exe") is None and shutil.which("pwsh") is None,
    reason="PowerShell is required for the Windows release-bundle integration test",
)
def test_release_script_builds_installable_marketplace_bundle(tmp_path: Path) -> None:
    shell = shutil.which("powershell.exe") or shutil.which("pwsh")
    assert shell is not None

    plugin = tmp_path / "assembled-plugin"
    manifest = plugin / ".codex-plugin" / "plugin.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps({"name": "ai-software-architect", "version": "0.1.0"}),
        encoding="utf-8",
    )
    (plugin / "runtime-marker.txt").write_text("self-contained-runtime", encoding="utf-8")
    output = tmp_path / "release"

    subprocess.run(  # noqa: S603
        [
            shell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(PACKAGE_SCRIPT),
            "-PluginPath",
            str(plugin),
            "-OutputDirectory",
            str(output),
            "-PluginVersion",
            "0.1.0",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    bundle_name = "ai-software-architect-v0.1.0-windows-x86_64"
    bundle = output / bundle_name
    archive = output / f"{bundle_name}.zip"
    checksum = output / "SHA256SUMS.txt"
    assert (bundle / ".agents" / "plugins" / "marketplace.json").is_file()
    assert (
        bundle
        / "plugins"
        / "ai-software-architect"
        / ".codex-plugin"
        / "plugin.json"
    ).is_file()
    assert (bundle / "plugins" / "ai-software-architect" / "runtime-marker.txt").is_file()
    assert "$ai-software-architect" in (bundle / "INSTALL.md").read_text("utf-8-sig")
    assert (bundle / "VERSION.txt").read_text("ascii").strip() == "0.1.0"
    assert archive.is_file()

    expected_checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    assert checksum.read_text("ascii").strip() == f"{expected_checksum}  {archive.name}"
    with zipfile.ZipFile(archive) as release_zip:
        members = {name.replace("\\", "/") for name in release_zip.namelist()}
    assert f"{bundle_name}/.agents/plugins/marketplace.json" in members
    assert (
        f"{bundle_name}/plugins/ai-software-architect/.codex-plugin/plugin.json" in members
    )
    assert f"{bundle_name}/INSTALL.md" in members
