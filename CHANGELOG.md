<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Changelog

All notable user-facing changes to AI Software Architect are documented here.
The project follows [Semantic Versioning](https://semver.org/).

## Unreleased

### Added

- Host-native, architecture-first workflow for Codex.
- Modular Agent Skills with progressive disclosure.
- Credible architecture-option comparisons and explicit human approval.
- Architecture Decision Record, contract, context, handoff, and conformance workflows.
- Focused references for architecture styles, all 23 GoF patterns, dependencies,
  data, integration, resilience, and complexity control.
- Compact Python examples for every GoF pattern.
- Deterministic hook-based Codex control plane.
- Read-only local Windows x86-64 STDIO MCP tools.
- Reproducible `uv` workspace, validation suite, package provenance, and security
  guardrails.

### Known Limitations

- The packaged MCP runtime currently supports Windows x86-64 only.
- GitHub Copilot, Claude Code, Google Antigravity, and other adapters are planned
  but not yet implemented.
- The five model-based exploratory fixtures are currently executed manually for
  release candidates.
- Public GitHub marketplace packaging and release publication are still release
  work; the personal marketplace is for development testing.

[Unreleased]: https://github.com/leomuf/ai-software-architect/commits/main
