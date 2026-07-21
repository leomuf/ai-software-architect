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

Google's current Antigravity getting-started material documents Rules, Workflows,
Skills, and MCP customization. It does not establish that Codex-style plugin
packaging or equivalent lifecycle hooks are available. The adapter format and
control-plane mapping must therefore be designed only after the target Antigravity
version's official contracts have been verified. Any agent or parallel-review
mechanism must be capability-detected; the workflow must remain valid as a
sequential single-agent flow.

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

Prefer Skills and the smallest supported deterministic execution boundary. Retain
MCP as an optional transport around the same Python core, enabled only after
lifecycle and permission tests pass on supported Antigravity versions.

## Implementation gates

1. Verify the current official skill, rule, workflow, agent, permission, packaging,
   lifecycle-hook, and MCP documentation; do not assume a Codex-equivalent plugin
   surface.
2. Generate rather than duplicate canonical workflow and knowledge files.
3. Translate activation, read-only inspection, architecture-artifact writes, contract
   validation, and secret scanning into native controls.
4. Test progressive disclosure and explicit invocation with representative models.
5. Run shared fixtures and Antigravity-specific installation, permissions, artifact,
   upgrade, process-lifecycle, and removal tests.
6. Publish limitations and supported versions before claiming implementation.

Official starting points:

- [Getting Started with Antigravity IDE](https://codelabs.developers.google.com/getting-started-agy-ide)
