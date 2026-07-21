<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# GitHub Copilot Adapter

Status: planned for a future version. This directory is the platform boundary for
packaging AI Software Architect for GitHub Copilot; it contains no released Copilot
adapter yet.

## Reuse from the canonical core

The adapter should generate its workflow from `shared/skills/`, copy only routed
references and assets, use the Pydantic contracts from `shared/schemas/`, call the
Python domain functions in `tools/python-mcp/src/ai_architect_tools/domain/`, preserve
the `.ai-architect/` artifact format, and run the shared Gherkin evaluations.

## Host-specific work

Copilot currently supports Agent Skills, custom agents, repository and personal
hooks, and optional MCP servers. The first adapter should prefer Agent Skills plus
short-lived hooks or a one-shot CLI. MCP may be enabled later only when install,
restart, idle-process, and removal behavior passes lifecycle tests.

Suggested structure:

```text
adapters/github_copilot/
├── README.md
├── build_adapter.py
├── templates/
│   ├── agent-profile.md
│   └── hooks.json
└── validate_adapter.py
```

The generated package should expose one obvious public entry point. Semantic review
roles—architecture critic, security/operations reviewer, and maintainability/testability
reviewer—may map to Copilot custom agents, but the canonical workflow must still work
sequentially when subagent delegation is unavailable.

## Implementation gates

1. Verify the current official Copilot customization, Agent Skills, custom-agent,
   hooks, and MCP documentation.
2. Create a deterministic generator rather than maintaining copied skill text.
3. Translate hook events into the shared activation, write-boundary, contract, and
   secret-scan policies.
4. Prove that focused help does not inspect repositories or start tools.
5. Run shared conformance fixtures plus Copilot-specific installation, permission,
   continuation, artifact-write, and removal tests.
6. Document limitations before marking the adapter implemented.

Official starting points:

- https://docs.github.com/en/copilot/reference/customization-cheat-sheet
- https://docs.github.com/en/copilot/concepts/agents/hooks

