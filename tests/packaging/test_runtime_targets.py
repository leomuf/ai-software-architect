# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import json
import shlex
import sys
from pathlib import Path

import pytest

from adapters.codex import build_plugin, control_plane, runtime_targets, validate_plugin
from adapters.codex.snapshot_launch import default_snapshot_shell


@pytest.mark.parametrize(("system", "machine", "expected"), [
    ("win32", "AMD64", "windows-x86_64"),
    ("win32", "x86_64", "windows-x86_64"),
    ("darwin", "arm64", "aarch64-darwin"),
    ("darwin", "aarch64", "aarch64-darwin"),
    ("linux", "x86_64", None),
    ("darwin", "x86_64", None),
])
def test_native_build_host_is_explicit(
    monkeypatch: pytest.MonkeyPatch, system: str, machine: str, expected: str | None,
) -> None:
    monkeypatch.setattr(runtime_targets.sys, "platform", system)
    monkeypatch.setattr(runtime_targets.platform, "machine", lambda: machine)
    if expected is None:
        with pytest.raises(ValueError, match="unsupported native build host"):
            runtime_targets.host_target()
    else:
        assert runtime_targets.host_target().name == expected


def test_build_rejects_cross_compilation_before_launching_pyinstaller(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        build_plugin, "host_target", lambda: runtime_targets.target_for_name("aarch64-darwin"),
    )
    with pytest.raises(ValueError, match="does not match this host"):
        build_plugin._build_runtime(runtime_targets.target_for_name("windows-x86_64"))


def test_windows_hook_commands_remain_identical_to_upstream_template() -> None:
    template = json.loads((build_plugin.TEMPLATES / "hooks.json").read_text("utf-8"))
    target = runtime_targets.target_for_name("windows-x86_64")
    for event, groups in template["hooks"].items():
        for group in groups:
            for hook in group["hooks"]:
                assert target.hook_command(event) == hook["command"]
                assert target.windows_hook_command(event) == hook["commandWindows"]


def test_package_detection_rejects_missing_or_ambiguous_runtimes(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="found none"):
        runtime_targets.detect_packaged_target(tmp_path)
    for target in runtime_targets.RUNTIME_TARGETS.values():
        executable = tmp_path / target.executable_relative_path
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b"fixture")
    with pytest.raises(ValueError, match="exactly one"):
        runtime_targets.detect_packaged_target(tmp_path)
    with pytest.raises(ValueError, match="exactly one"):
        validate_plugin.validate(tmp_path, target=runtime_targets.target_for_name("windows-x86_64"))


@pytest.mark.skipif(sys.platform != "darwin", reason="requires native macOS paths")
def test_macos_snapshot_launcher_keeps_literal_path_and_shell_interface(tmp_path: Path) -> None:
    plugin = tmp_path / "installed plugin's files"
    target = runtime_targets.target_for_name("aarch64-darwin")
    executable = plugin / target.executable_relative_path
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"fixture")
    command = control_plane.repository_snapshot_command(plugin, shell=default_snapshot_shell())
    assert shlex.split(command) == [str(executable), "--repository-snapshot", "--root", "."]
    with pytest.raises(ValueError, match="exact trusted absolute path"):
        control_plane.repository_snapshot_command(  # noqa: S604 -- tests rejection only
            plugin, shell="./project-shell",
        )
