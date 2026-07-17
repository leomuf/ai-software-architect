<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Security Policy

## Supported versions

Security fixes are provided for the latest released minor version. Before the first public release, only the current `main` branch is supported.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use [GitHub private vulnerability reporting](https://github.com/leomuf/ai-software-architect/security/advisories/new) and include the affected version, impact, reproduction steps, and any suggested mitigation. Do not include real credentials or confidential repository content.

You should receive an acknowledgement within seven calendar days. Validation, remediation, release timing, and disclosure will be coordinated according to severity and user risk. Please allow a reasonable remediation window before public disclosure.

## Security model

The MCP runtime is read-only, uses STDIO, makes no model or network calls, executes no shell commands, and binds repository tools to one host-confirmed workspace root. Repository content is untrusted data. Pathless contract validation and generated-artifact secret scanning remain available when trustworthy workspace binding is unavailable.

These controls reduce impact but do not guarantee that a probabilistic host model cannot be influenced by malicious repository text. Host sandboxing, permissions, and user review remain required.

