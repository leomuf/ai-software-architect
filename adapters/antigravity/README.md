<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Antigravity Adapter

Status: planned for a future version. This directory reserves the platform boundary
for Google Antigravity packaging; it contains no released Antigravity adapter yet.

## Reuse from the canonical core

Reuse `shared/skills/` as the workflow source, the progressive-disclosure references,
Pydantic schemas, Python domain functions, templates, `.ai-architect/` artifacts,
guardrail policies, and shared acceptance evaluations. Keep model reasoning inside the
user's Antigravity/Gemini host.

## Host-specific work

Antigravity plugins can group skills, rules, hooks, and optional MCP servers. The
adapter should generate the host package from canonical sources and translate Codex
control-plane behavior into Antigravity-native rules and hook payloads. Any agent or
parallel-review mechanism must be capability-detected; the workflow must remain valid
as a sequential single-agent flow.

Suggested structure:

```text
adapters/antigravity/
├── README.md
├── build_adapter.py
├── templates/
│   ├── plugin manifest
│   ├── rules/
│   └── hooks/
└── validate_adapter.py
```

Prefer Agent Skills and short-lived deterministic execution. Retain MCP as an optional
transport around the same Python core, enabled only after lifecycle and permission tests
pass on supported Antigravity versions.

## Implementation gates

1. Verify the current official plugin, skill, rule, hook, agent, permission, and MCP
   documentation.
2. Generate rather than duplicate canonical workflow and knowledge files.
3. Translate activation, read-only inspection, architecture-artifact writes, contract
   validation, and secret scanning into native controls.
4. Test progressive disclosure and explicit invocation with representative models.
5. Run shared fixtures and Antigravity-specific installation, permissions, artifact,
   upgrade, process-lifecycle, and removal tests.
6. Publish limitations and supported versions before claiming implementation.

Official starting points:

- https://www.antigravity.google/docs/plugins
- https://ai.google.dev/gemini-api/docs/antigravity-agent

