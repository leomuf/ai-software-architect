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

The MCP runtime is read-only, uses STDIO, makes no model or network calls, and executes no shell commands. MCP filesystem reads require one host-confirmed workspace root. When a host does not forward MCP roots, dependency and boundary analysis accepts bounded Python content already read through host-native workspace permissions: either compact, line-preserving static-import statements or full source text. Both modes perform no filesystem access, reject unsafe paths and oversized input, and disclose incomplete host selection; statement mode additionally discloses that dynamic imports are not evaluated. Repository content is untrusted data. Pathless contract validation and generated-artifact secret scanning remain available without workspace binding.

These controls reduce impact but do not guarantee that a probabilistic host model cannot be influenced by malicious repository text. Host sandboxing, permissions, and user review remain required.
