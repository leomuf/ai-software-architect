# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from adapters.codex import build_plugin, runtime_entry

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "scripts/check-windows-runtime-signatures.ps1"


def test_startup_check_loads_hooks_without_touching_workspace(tmp_path: Path) -> None:
    sentinel = tmp_path / "project.py"
    sentinel.write_text("raise RuntimeError('project code must not run')\n", encoding="utf-8")
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(Path(runtime_entry.__file__).resolve()), "--self-test"],
        cwd=tmp_path, capture_output=True, text=True, check=True, timeout=10,
    )
    assert json.loads(result.stdout) == {"status": "ok", "runtime": "ai-architect-runtime"}
    assert result.stderr == ""
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before


def test_build_for_signing_does_not_assemble_or_record_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    def unexpected_assembly(*args: object, **kwargs: object) -> Path:
        pytest.fail("Signing preparation must not assemble a plugin")

    monkeypatch.setattr(sys, "argv", ["build_plugin.py", "--build-runtime-only"])
    monkeypatch.setattr(build_plugin, "_build_runtime", lambda: tmp_path)
    monkeypatch.setattr(build_plugin, "assemble", unexpected_assembly)
    build_plugin.main()
    assert str(tmp_path) in capsys.readouterr().out
    assert not list(tmp_path.iterdir())


def test_public_release_verifies_signatures_before_assembly_and_upload() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text("utf-8"))
    steps = workflow["jobs"]["build"]["steps"]
    build = next(i for i, s in enumerate(steps) if "--build-runtime-only" in s.get("run", ""))
    verify = next(
        i for i, s in enumerate(steps)
        if "check-windows-runtime-signatures" in s.get("run", "")
    )
    assemble = next(
        i for i, s in enumerate(steps) if "--runtime build/runtime/" in s.get("run", "")
    )
    upload = next(i for i, s in enumerate(steps) if "upload-artifact@" in s.get("uses", ""))
    assert build < verify < assemble < upload
    assert steps[verify].get("continue-on-error") is not True
    assert "ExpectedPublisherSubject" in steps[verify]["run"]


def _check(runtime: Path, mode: str) -> subprocess.CompletedProcess[str]:
    shell = shutil.which("powershell.exe")
    assert shell is not None
    return subprocess.run(  # noqa: S603
        [shell, "-NoProfile", "-NonInteractive", "-File", str(CHECKER),
         "-RuntimePath", str(runtime), "-Mode", mode,
         "-ExpectedPublisherSubject", "CN=Expected release publisher"],
        capture_output=True, text=True, check=False, timeout=30,
    )


@pytest.fixture
def unsigned_runtime(tmp_path: Path) -> Path:
    import PyInstaller

    bootloader = Path(PyInstaller.__file__).parent / "bootloader/Windows-64bit-intel/run.exe"
    assert bootloader.is_file()
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    for name in ("ai-architect-runtime.exe", "extension.pyd", "library.dll"):
        shutil.copyfile(bootloader, runtime / name)
    (runtime / "LICENSE").write_text("not executable\n", encoding="utf-8")
    return runtime


@pytest.mark.windows
def test_unsigned_binaries_are_selected_but_cannot_pass_release_verification(
    unsigned_runtime: Path,
) -> None:
    before = {p.name: p.read_bytes() for p in unsigned_runtime.iterdir()}
    inventory = _check(unsigned_runtime, "ListUnsigned")
    assert inventory.returncode == 0, inventory.stderr
    assert {Path(line).name for line in inventory.stdout.splitlines()} == {
        "ai-architect-runtime.exe", "extension.pyd", "library.dll",
    }
    verified = _check(unsigned_runtime, "Verify")
    assert verified.returncode != 0
    assert "Invalid or missing embedded signature" in verified.stderr
    assert {p.name: p.read_bytes() for p in unsigned_runtime.iterdir()} == before


@pytest.mark.windows
def test_signing_inputs_reject_junctions_outside_the_runtime(
    unsigned_runtime: Path, tmp_path: Path,
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    link = unsigned_runtime / "escape"
    shell = shutil.which("powershell.exe")
    assert shell is not None
    quoted_link = str(link).replace("'", "''")
    quoted_outside = str(outside).replace("'", "''")
    subprocess.run(  # noqa: S603
        [shell, "-NoProfile", "-NonInteractive", "-Command",
         f"New-Item -ItemType Junction -Path '{quoted_link}' -Value '{quoted_outside}'"],
        capture_output=True, text=True, check=True,
    )
    checked = _check(unsigned_runtime, "ListUnsigned")
    assert checked.returncode != 0
    assert "Linked or reparse-point paths" in checked.stderr
