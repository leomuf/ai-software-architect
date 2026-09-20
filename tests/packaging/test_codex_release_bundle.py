# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

from adapters.codex import build_plugin
from adapters.codex.runtime_targets import target_for_name
from scripts.package_codex_release import package_release

ROOT = Path(__file__).resolve().parents[2]
MARKETPLACE_TEMPLATE = ROOT / "adapters" / "codex" / "templates" / "marketplace.json"
INSTALL_GUIDE = ROOT / "docs" / "INSTALL_CODEX_PLUGIN.md"
PACKAGE_SCRIPT = ROOT / "scripts" / "package-codex-release.ps1"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


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
            "category": "Developer Tools",
        }
    ]


def test_install_guide_requires_no_development_runtime() -> None:
    guide = INSTALL_GUIDE.read_text("utf-8")

    assert "without Python, `uv`" in guide
    assert ".agents/plugins/marketplace.json" in guide
    assert "$ai-software-architect" in guide
    assert "selecting\n**AI Software Architect** from the picker" in guide
    assert "Do not merely type the literal display name" in guide
    assert "All five hooks are required" in guide
    assert "aarch64-darwin" in guide
    assert "shasum -a 256" in guide


def test_ci_packages_the_version_from_the_built_manifest() -> None:
    workflow = CI_WORKFLOW.read_text("utf-8")

    assert "dist/codex/ai-software-architect/.codex-plugin/plugin.json" in workflow
    assert "-PluginVersion $manifest.version" in workflow
    assert "package-codex-release.ps1 -PluginVersion 0.1.0" not in workflow
    assert "macos-aarch64-package:" in workflow
    assert "--target aarch64-darwin" in workflow


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

    system_root = os.environ.get("SystemRoot")
    if system_root is None:
        pytest.skip("Windows SystemRoot is required for the duplicate tar.exe regression test")
    system_tar = Path(system_root) / "System32" / "tar.exe"
    if not system_tar.is_file():
        pytest.skip("Windows system tar.exe is required for the release-bundle test")
    tar_directories = (tmp_path / "tar-one", tmp_path / "tar-two")
    for directory in tar_directories:
        directory.mkdir()
        shutil.copy2(system_tar, directory / "tar.exe")
    environment = os.environ.copy()
    environment["PATH"] = os.pathsep.join(
        [*(str(directory) for directory in tar_directories), environment.get("PATH", "")]
    )
    tar_probe = subprocess.run(  # noqa: S603
        [
            shell,
            "-NoProfile",
            "-Command",
            "@(Get-Command tar.exe -CommandType Application).Count",
        ],
        check=True,
        capture_output=True,
        env=environment,
        text=True,
    )
    assert int(tar_probe.stdout.strip()) >= 2

    result = subprocess.run(  # noqa: S603
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
        check=False,
        capture_output=True,
        env=environment,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(
            "release packaging script failed "
            f"with exit code {result.returncode}\n"
            f"--- stdout ---\n{result.stdout.strip()}\n"
            f"--- stderr ---\n{result.stderr.strip()}",
            pytrace=False,
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


def test_macos_release_bundle_is_targeted_and_reproducible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output_parent = tmp_path / "dist" / "codex"
    plugin_output = output_parent / "ai-software-architect"
    monkeypatch.setattr(build_plugin, "OUTPUT_PARENT", output_parent)
    monkeypatch.setattr(build_plugin, "OUTPUT", plugin_output)
    runtime = tmp_path / "ai-architect-runtime"
    runtime.mkdir()
    executable = runtime / "ai-architect-runtime"
    executable.write_bytes(b"reviewed-macos-release-runtime")
    executable.chmod(0o755)

    target = target_for_name("aarch64-darwin")
    plugin = build_plugin.assemble(
        runtime,
        plugin_version="0.2.3+darwin.test",
        target=target,
    )
    release = tmp_path / "release"
    archive, checksum = package_release(plugin, release, target=target)
    first_archive_bytes = archive.read_bytes()
    bundle_name = "ai-software-architect-v0.2.3+darwin.test-aarch64-darwin"
    assert archive.name == f"{bundle_name}.zip"
    assert checksum.read_text("ascii").strip() == (
        f"{hashlib.sha256(first_archive_bytes).hexdigest()}  {archive.name}"
    )
    with zipfile.ZipFile(archive) as release_zip:
        members = set(release_zip.namelist())
    assert (
        f"{bundle_name}/plugins/ai-software-architect/runtime/"
        "aarch64-darwin/ai-architect-runtime/ai-architect-runtime"
    ) in members
    install_guide = (
        release / bundle_name / "INSTALL.md"
    ).read_text("utf-8")
    assert "Get-FileHash" not in install_guide
    assert "shasum -a 256" in install_guide
    package_release(plugin, release, target=target)
    assert archive.read_bytes() == first_archive_bytes
