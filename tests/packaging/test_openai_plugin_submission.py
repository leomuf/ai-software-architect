# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "adapters" / "codex" / "templates" / "plugin.json"
SUBMISSION_ROOT = ROOT / "docs" / "openai-plugin-submission"
PACKAGE_SCRIPT = ROOT / "scripts" / "package-openai-plugin-submission.ps1"


def test_manifest_identifies_company_publisher_and_public_policies() -> None:
    manifest = json.loads(MANIFEST.read_text("utf-8"))

    assert manifest["version"] == "0.2.2"
    assert manifest["author"]["name"] == (
        "AUTOSOFT Engineering (a brand of XAVIER MUFFATO LTDA)"
    )
    assert manifest["interface"]["developerName"] == "AUTOSOFT Engineering"
    assert manifest["interface"]["category"] == "Developer Tools"
    assert "eligible exploratory observations" not in (
        manifest["interface"]["longDescription"]
    )
    for field in ("websiteURL", "privacyPolicyURL", "termsOfServiceURL"):
        assert manifest["interface"][field].startswith("https://")


def test_submission_listing_has_three_realistic_starter_prompts() -> None:
    listing = yaml.safe_load((SUBMISSION_ROOT / "listing.yaml").read_text("utf-8"))

    assert listing["publisher"]["display_name"] == "AUTOSOFT Engineering"
    assert (
        listing["publisher"]["developer_identity_to_verify_and_select"]
        == "XAVIER MUFFATO LTDA"
    )
    assert listing["plugin"]["portal_submission_type"] == "Skills only"
    assert listing["plugin"]["category_preference"] == "Developer Tools"
    assert "more than 350 eligible exploratory observations" in (
        listing["plugin"]["description"]
    )
    assert len(listing["starter_prompts"]) == 3
    assert all(prompt.strip() for prompt in listing["starter_prompts"])


def test_submission_has_required_positive_and_negative_cases() -> None:
    cases = yaml.safe_load((SUBMISSION_ROOT / "test-cases.yaml").read_text("utf-8"))

    assert len(cases["positive_cases"]) == 5
    assert len(cases["negative_cases"]) == 3
    assert all(case["success_indicators"] for case in cases["positive_cases"])
    assert all(case["success_indicators"] for case in cases["negative_cases"])
    assert all(case["why_not_complete"] for case in cases["negative_cases"])


def test_openai_package_script_preserves_plugin_root() -> None:
    script = PACKAGE_SCRIPT.read_text("utf-8-sig")

    assert "IO.Compression.ZipArchive" in script
    assert "Security.Cryptography.SHA256" in script
    assert 'Replace("\\", "/")' in script
    assert "Get-FileHash" not in script
    assert "tar.exe" not in script
    assert '".codex-plugin/plugin.json"' in script
    assert '".agents/plugins/marketplace.json"' in script
    assert "validate_plugin.py" in script


def test_openai_package_has_windows_explorer_compatible_member_paths(
    tmp_path: Path,
) -> None:
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if powershell is None:
        return

    plugin = tmp_path / "plugin"
    required_files = {
        ".codex-plugin/plugin.json": json.dumps(
            {"name": "ai-software-architect", "version": "0.2.2"}
        ),
        "skills/ai-software-architect/SKILL.md": "# Test skill\n",
        "hooks/hooks.json": "{}\n",
        "provenance.json": "{}\n",
        "PRIVACY.md": "# Privacy\n",
        "TERMS.md": "# Terms\n",
        "SUPPORT.md": "# Support\n",
    }
    for relative_path, content in required_files.items():
        path = plugin / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_uv = fake_bin / "uv.cmd"
    fake_uv.write_text("@exit /b 0\n", encoding="ascii")
    output = tmp_path / "output"
    environment = os.environ.copy()
    path_key = next(key for key in environment if key.casefold() == "path")
    environment[path_key] = f"{fake_bin}{os.pathsep}{environment[path_key]}"

    result = subprocess.run(  # noqa: S603 - fixed local PowerShell executable
        [
            powershell,
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
            "0.2.2",
        ],
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"

    archive_path = output / "ai-software-architect-v0.2.2-openai-plugin.zip"
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.namelist()

    assert len(members) == len(required_files)
    assert ".codex-plugin/plugin.json" in members
    assert all(not member.startswith("./") for member in members)
    assert all("\\" not in member for member in members)
