# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Platform-specific paths and commands for the bundled Codex runtime."""

from __future__ import annotations

import os
import platform
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path

RUNTIME_DIRECTORY_NAME = "ai-architect-runtime"


@dataclass(frozen=True)
class RuntimeTarget:
    """One native runtime artifact supported by the Codex plugin package."""

    name: str
    executable_name: str
    archive_suffix: str

    @property
    def executable_relative_path(self) -> Path:
        return (
            Path("runtime")
            / self.name
            / RUNTIME_DIRECTORY_NAME
            / self.executable_name
        )

    @property
    def executable_relative_posix_path(self) -> str:
        return self.executable_relative_path.as_posix()

    def hook_command(self, event: str) -> str:
        return (
            f'"$PLUGIN_ROOT/{self.executable_relative_posix_path}" '
            f"--codex-hook --event {event}"
        )

    def windows_hook_command(self, event: str) -> str:
        windows_path = self.executable_relative_posix_path.replace("/", "\\")
        return (
            f'& "$env:PLUGIN_ROOT\\{windows_path}" '
            f"--codex-hook --event {event}"
        )

    def snapshot_command(self, plugin_root: Path) -> str:
        executable = plugin_root.resolve(strict=False) / self.executable_relative_path
        if self.name == "windows-x86_64":
            return f'& "{executable}" --repository-snapshot --root .'
        return f'{shlex.quote(str(executable))} --repository-snapshot --root .'


RUNTIME_TARGETS: dict[str, RuntimeTarget] = {
    "windows-x86_64": RuntimeTarget(
        name="windows-x86_64",
        executable_name="ai-architect-runtime.exe",
        archive_suffix="windows-x86_64",
    ),
    "aarch64-darwin": RuntimeTarget(
        name="aarch64-darwin",
        executable_name="ai-architect-runtime",
        archive_suffix="aarch64-darwin",
    ),
}


def target_for_name(name: str) -> RuntimeTarget:
    try:
        return RUNTIME_TARGETS[name]
    except KeyError as exc:
        supported = ", ".join(sorted(RUNTIME_TARGETS))
        raise ValueError(f"unsupported runtime target {name!r}; use one of {supported}") from exc


def host_target() -> RuntimeTarget:
    """Return the supported target matching the current build host."""

    machine = platform.machine().casefold()
    if sys.platform == "darwin" and machine in {"arm64", "aarch64"}:
        return RUNTIME_TARGETS["aarch64-darwin"]
    if os.name == "nt" and machine in {"amd64", "x86_64"}:
        return RUNTIME_TARGETS["windows-x86_64"]
    return RUNTIME_TARGETS["windows-x86_64"]


def detect_packaged_target(plugin_root: Path) -> RuntimeTarget:
    """Find the single native runtime contained in a target-specific package."""

    matches = [
        target
        for target in RUNTIME_TARGETS.values()
        if (plugin_root / target.executable_relative_path).is_file()
    ]
    if len(matches) != 1:
        names = ", ".join(target.name for target in matches) or "none"
        raise ValueError(
            "plugin must contain exactly one supported native runtime; found " + names
        )
    return matches[0]
