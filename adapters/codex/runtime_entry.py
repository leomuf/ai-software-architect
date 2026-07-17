# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""PyInstaller entry point for the bundled Windows STDIO MCP executable."""

from __future__ import annotations

from ai_architect_tools.mcp_server import main

if __name__ == "__main__":
    main()
