<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Claude Code Adapter

Status: planned for a future version. This directory is the platform boundary for a
Claude Code plugin; it contains no released Claude Code adapter yet.

## Reuse from the canonical core

Generate the Claude Code workflow from `shared/skills/`, reuse the focused references,
Pydantic contracts, Python domain functions, `.ai-architect/` artifact schema, templates,
security policies, and shared evaluations. Architecture reasoning remains host-native
and uses the user's Claude model and plan.

## Host-specific work

Claude Code supports plugins, skills, command hooks, custom subagents, and optional MCP
servers. The adapter should map the three semantic review roles to read-only Claude
subagents while leaving the main session responsible for recommendations and writes.
Hook configuration and payloads must be translated rather than copied from Codex.

Suggested structure:

```text
adapters/claude_code/
├── README.md
├── build_adapter.py
├── templates/
│   ├── plugin.json
│   ├── hooks.json
│   └── agents/
└── validate_adapter.py
```

Prefer short-lived command hooks and the shared one-shot CLI for deterministic work.
Keep the STDIO MCP adapter optional; do not make it a prerequisite unless Claude Code
lifecycle tests prove reliable startup, shutdown, upgrade, and uninstall behavior.

## Implementation gates

1. Recheck the current official plugin, skill, hook, subagent, permission, and MCP
   contracts.
2. Generate one simple public workflow entry from canonical modules.
3. Scope subagents to independent read-only critique and prevent recursive delegation.
4. Translate pre-write validation and response checks to Claude hook events.
5. Run shared fixtures and Claude-specific continuation, permissions, artifact,
   installation, upgrade, and removal tests.
6. Document behavioral differences instead of claiming identical reasoning.

Official starting points:

- https://code.claude.com/docs/en/features-overview
- https://code.claude.com/docs/en/hooks
- https://code.claude.com/docs/en/sub-agents

