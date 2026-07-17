<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# AI Software Architect

AI Software Architect is an open-source, host-native architecture agent for coding assistants. It helps developers clarify architecture-significant requirements, compare credible options, approve and record decisions, prepare coding handoffs, and review implementation conformance.

The first release target is an installable Codex plugin. Codex supplies the model and reasoning; the plugin supplies progressively disclosed architecture skills plus a bundled, read-only local MCP server for deterministic validation and Python dependency evidence. No separate model API key, hosted backend, telemetry service, or network-listening process is required.

## Development

Prerequisites: `uv 0.11.x` and the Python version recorded in `.python-version`.

```powershell
uv sync --locked --all-packages
uv run pytest
uv run ruff check shared/schemas tools/python-mcp adapters tests
uv run mypy
```

Generate schemas and acceptance criteria:

```powershell
uv run python shared/schemas/generate_schema.py
uv run python shared/evaluations/generate_acceptance.py
```

Build the self-contained Windows x86-64 plugin:

```powershell
uv run python adapters/codex/build_plugin.py --build-runtime
uv run python adapters/codex/smoke_test_runtime.py dist/codex/ai-software-architect/runtime/windows-x86_64/ai-architect-mcp.exe
```

Generated plugin output is written to `dist/codex/ai-software-architect/` and is intentionally excluded from version control.

The approved product and security specification is [specs/AISoftwareArchitect.md](specs/AISoftwareArchitect.md).

## License

MIT License. See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

