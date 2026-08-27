<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Security Policy

## Supported versions

Security fixes are provided for the latest released minor version.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use [GitHub private vulnerability reporting](https://github.com/leomuf/ai-software-architect/security/advisories/new) and include the affected version, impact, reproduction steps, and any suggested mitigation. Do not include real credentials or confidential repository content.

You should receive an acknowledgement within seven calendar days. Validation, remediation, release timing, and disclosure will be coordinated according to severity and user risk. Please allow a reasonable remediation window before public disclosure.

## Security model

The Codex package uses short-lived local hooks as a defense-in-depth control plane; it does not register a persistent MCP server. Hooks make no model or network calls. They activate only for an explicit AI Software Architect workflow, add bounded workflow context, restrict shell-backed inspection to a small fail-closed static-read allowlist, deny application-code writes, and validate canonical `.ai-architect/` artifacts before and after persistence. Every hook command declares its event explicitly. A PreToolUse parsing, environment, state, or validation failure denies the protected operation; a PostToolUse verification failure stops the workflow. Unrelated turns remain inactive.

Artifact creation requires a trustworthy host-supplied workspace root. ADRs and contracts receive applicable Pydantic validation, generated content is scanned for likely secrets, approved record-and-handoff writes require one consistent ADR/contract/context/implementation-plan bundle, and deletion is not allowed. These checks do not grant filesystem access: Codex sandboxing, permissions, and user approval remain authoritative.

`tools/python-mcp/` is an optional read-only Python STDIO MCP implementation for other hosts and development use; it is not registered by the Codex package. It makes no model or network calls and executes no shell commands. MCP filesystem reads require one host-confirmed workspace root. When a host does not forward MCP roots, bounded source supplied through host-native permissions can be analyzed without filesystem access. Dynamic imports, reflection, generated code, and omitted files are not deterministically covered.

Repository content is untrusted data. These controls reduce impact but do not guarantee that a probabilistic host model cannot be influenced by malicious text, and they are not an operating-system sandbox. Host sandboxing, permissions, and user review remain required.
