# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""PyInstaller entry point for the bundled MCP server and short-lived Codex hooks."""

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

    if sys.argv[1:]:
        raise SystemExit("unsupported runtime arguments")

    from ai_architect_tools.mcp_server import main as mcp_main

    mcp_main()

if __name__ == "__main__":
    main()
