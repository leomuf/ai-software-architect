# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Shell-specific quoting for one trusted reader; no project-command parsing."""

from __future__ import annotations

import os
import shlex
import sys
from pathlib import Path


def snapshot_shells() -> dict[str, str]:
    """Use host installation locations, never a project-controlled PATH lookup."""
    if sys.platform == "win32":
        system_root = Path(os.environ.get("SystemRoot", "C:/Windows"))
        program_files = Path(os.environ.get("ProgramFiles", "C:/Program Files"))
        candidates = {
            system_root / "System32/WindowsPowerShell/v1.0/powershell.exe": "powershell",
            program_files / "PowerShell/7/pwsh.exe": "powershell",
            program_files / "Git/bin/bash.exe": "bash",
        }
    else:
        # Launcher support is separate from availability of a native runtime package.
        candidates = {Path("/bin/bash"): "bash"}
    return {
        str(path): kind for path, kind in candidates.items()
        if path.is_absolute() and path.is_file()
        and not (kind == "bash" and (os.environ.get("BASH_ENV") or os.environ.get("ENV")))
    }


def default_snapshot_shell() -> str:
    shells = snapshot_shells()
    if not shells:
        raise ValueError("no trusted snapshot shell is available; use native file tools")
    return next(iter(shells))


def quote_snapshot_command(executable: Path, shell: str) -> str:
    """Quote a trusted executable as a literal under a known interpreter."""
    kind = snapshot_shells().get(shell)
    if kind is None:
        raise ValueError("snapshot shell must be an exact trusted absolute path")
    if kind == "powershell":
        literal = str(executable)
        # PowerShell also recognizes typographic single quotes as delimiters.
        for quote in ("'", "\u2018", "\u2019"):
            literal = literal.replace(quote, quote * 2)
        return f"& '{literal}' --repository-snapshot --root ."
    return f"{shlex.quote(executable.as_posix())} --repository-snapshot --root ."
