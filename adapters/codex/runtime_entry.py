# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""PyInstaller entry point for the short-lived Codex control-plane runtime."""

from __future__ import annotations

import sys


def main() -> None:
    if sys.argv[1:] == ["--codex-hook"]:
        try:
            from adapters.codex.hook_entry import main as hook_main
        except ModuleNotFoundError as exc:
            if exc.name != "adapters":
                raise
            from hook_entry import main as hook_main  # type: ignore[import-not-found, no-redef]

        hook_main()
        return

    raise SystemExit("use --codex-hook; this runtime does not start a persistent server")

if __name__ == "__main__":
    main()
