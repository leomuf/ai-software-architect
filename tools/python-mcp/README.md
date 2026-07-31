<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# AI Software Architect MCP Server

This package contains `ai-software-architect-mcp`, an optional local Python STDIO
Model Context Protocol (MCP) adapter for AI Software Architect, plus related
command-line tools. It can give a compatible coding assistant bounded, deterministic
architecture evidence and validation while the assistant's selected model
remains responsible for architectural reasoning.

The server is a supporting component, not an autonomous agent. It does not
select design patterns, recommend an architecture, call a model, or implement
application code. Keeping these responsibilities separate makes deterministic
results testable and lets every supported coding assistant use its own model,
credits, tools, permissions, and reasoning behavior.

## Current Codex Packaging Decision

The Python MCP adapter remains versioned and tested, but it is no longer registered
or shipped as a persistent server in the Codex plugin. Codex now packages only a
short-lived deterministic runtime for `UserPromptSubmit`, `PreToolUse`,
`PostToolUse`, `PostCompact`, and `Stop` hooks. Each hook process handles one
bounded event and exits.

Exploratory testing established an incompatible lifecycle trade-off in Codex Desktop
for Windows:

1. Codex can initialize and retain STDIO MCP transports even when a task never calls
   a tool.
2. Codex can refuse plugin uninstall while those transports or processes remain active,
   even when the executable was copied outside the plugin cache.
3. A short idle self-reaper makes uninstall reliable, but Codex does not reliably
   relaunch that transport for a later tool call, producing `Transport closed` errors.

Therefore the Codex release prioritizes reliable installation, upgrade, and removal.
Complete proposed `.ai-architect/` writes are reconstructed and checked by the
short-lived `PreToolUse` hook: contracts are validated with the same Pydantic/domain
functions and generated artifacts are secret-scanned before the write. Repository
dependency and boundary observations use host-native static inspection with disclosed
limitations. Small Codex reviews may invoke the packaged runtime once as a bounded
repository snapshot helper; it supplies static text evidence to the host model and
does not expose an MCP transport or claim parser-verified architecture analysis.

This is an adapter decision, not deletion of MCP support. The STDIO server continues
to wrap the shared Python domain functions and may be used by GitHub Copilot, Claude
Code, Antigravity, other compatible hosts, or a future Codex version when lifecycle
tests prove reliable startup, relaunch, shutdown, upgrade, and uninstall behavior.

## Why the MCP Server Exists

Language models can inspect code and reason about architecture, but factual
operations such as parsing imports or validating a structured contract are more
reliable when implemented as ordinary deterministic code. The MCP server
therefore supplies evidence and validation results that the host model can cite
and interpret.

Compatible hosts communicate with it over STDIO only: the process does not start a
network listener or install a background service.

## Historical Codex Launch Architecture

The tagged `pre-release-mcp-server` Windows Codex package used Codex as the MCP
process host and invoked a
reviewed PowerShell launcher instead of executing the server binary directly
from the versioned plugin cache. These are complementary layers, not competing
launch modes:

```text
Codex
  -> packaged PowerShell launcher
    -> private runtime copy under %LOCALAPPDATA%
      -> Python STDIO MCP server
```

The direct-executable approach used by earlier development packages was
simpler, but a running Windows executable could keep the versioned plugin cache
locked and prevent clean uninstall. The launcher instead copies only the
packaged, validated runtime to a random per-session directory, changes its
working directory out of the plugin cache, preserves inherited STDIO, and
removes the private copy after the server exits.

That historical design was retained alongside the server's bounded idle self-reaping
because the two controls address different failure modes: the launcher prevents
Windows file and working-directory locks in the plugin cache, while self-reaping
releases MCP sessions that Codex may otherwise keep alive. The launcher uses
Windows PowerShell with `-NoProfile`, `-NonInteractive`, and a process-scoped
`-ExecutionPolicy Bypass`; it does not modify the user's execution policy.

### Observed Codex uninstall constraint

Integration testing on Codex Desktop for Windows established that moving the
server executable out of the plugin cache is necessary but not sufficient for
reliable removal. Codex rejected an uninstall while MCP processes belonging to
the installed plugin were still running, even though every executable and its
working directory were already under `%LOCALAPPDATA%` rather than the plugin
cache. The same uninstall completed promptly after those MCP processes exited.

This distinguishes two independent lifecycle constraints:

1. **Windows cache locking:** a process launched directly from the plugin cache
   can keep files or its working directory locked. The PowerShell launcher and
   private runtime copy prevent this.
2. **Codex active-session retention:** Codex can refuse to uninstall a plugin
   while its MCP processes or transports are still active, regardless of where
   their executable files reside. The bounded idle self-reaper releases these
   retained sessions—including initialized transports that never receive a tool
   call—without requiring users to terminate processes manually.

Release testing must therefore verify both that no process owns a plugin-cache
path and that all inactive MCP processes exit before the first uninstall
attempt. A successful cache deletion alone is not sufficient lifecycle proof.

## MCP Tool Surface

The optional MCP adapter exposes four read-only tools:

| Tool | Purpose |
|---|---|
| `validate_complete_architecture_contract` | Validates one complete candidate architecture contract against the shared Pydantic schema and semantic rules. Callers must inspect `result.valid` before claiming success. |
| `scan_generated_architecture_artifact` | Checks a complete generated ADR, contract, project context, or implementation plan for secret-like content without returning suspected secret values. |
| `analyze_python_dependencies` | Extracts static Python import relationships from bounded, line-preserving import statements already selected and supplied by the host. It does not accept complete source files. |
| `check_python_architecture_boundaries` | Compares bounded Python dependency evidence with the allowed dependencies in a complete architecture contract and reports conformance findings. |

MCP outputs contain structured evidence and stable errors, not architectural
recommendations. Generic pattern explanations and stored examples do not need
an MCP call.

## Evidence Modes

The tools use two filesystem-free evidence representations:

- **Fast statement mode:** receives line-preserving static `import` and
  `from ... import ...` statements. It minimizes payload size for routine
  dependency orientation and is the only mode accepted by
  `analyze_python_dependencies`, but cannot evaluate omitted or dynamic imports.
- **Full-source mode:** receives bounded Python source files when full AST
  context is required for `check_python_architecture_boundaries` against an
  approved contract. A compatible host may request interactive approval for
  this larger local data transfer.

In both modes, the enabling host first reads the selected content through its
native workspace permissions. The MCP tool accepts no workspace root and opens
no repository path. It parses the supplied text with Python's Abstract Syntax
Tree (AST) support without importing or executing the analyzed application.

The architecture workflow and pattern knowledge are language-neutral. The
current deterministic dependency and boundary analyzers are Python-specific.
Other languages may still be reviewed by the host model, but they do not yet
receive an MCP-verified dependency graph.

## Safety and Privacy

The server is intentionally narrow:

- read-only, with no application or architecture-artifact writes;
- no model or network calls, telemetry, shell commands, or subprocesses;
- no execution, import, compilation, or testing of analyzed repository code;
- repository content is treated as untrusted data, never as instructions;
- bounded inputs, files, statements, edges, execution time, and process calls;
- protected, absolute, traversal, duplicate, oversized, and unsupported inputs
  are rejected with sanitized structured errors;
- suspected secret values are never included in scan results;
- standard output is reserved exclusively for MCP protocol messages.

The tagged historical Codex package started the server through a small packaged PowerShell launcher. For each
session, the launcher copies the reviewed, versioned runtime into a random
directory below `%LOCALAPPDATA%/AI Software Architect/plugin-runtime/`, changes
its own current directory out of the versioned plugin cache, and removes the
session copy after the server exits. The long-lived processes therefore keep no
plugin-cache path open during uninstall. The launcher's execution-policy bypass
is process-scoped and does not change user or machine policy. The server exits
when its STDIO connection closes or its parent process disappears. It also
self-reaps after 15 seconds without an active call, including when Codex
initialized the transport but never sent a tool call. It never interrupts an
active call, and architecture decisions or continuation state are not stored in
MCP process memory.

These controls complement, but do not replace, the coding assistant's sandbox,
permissions, native tools, or user approval flow.

## Package Structure

```text
tools/python-mcp/
├── pyproject.toml
├── README.md
├── src/ai_architect_tools/
│   ├── mcp_server.py       # STDIO MCP transport and process lifecycle
│   ├── cli.py              # Local diagnostics using the same domain logic
│   └── domain/
│       ├── boundaries.py   # Architecture-boundary conformance
│       ├── contracts.py    # Contract validation and secret scanning
│       ├── decisions.py    # Architecture-decision discovery for the CLI
│       ├── dependencies.py # Static Python dependency evidence
│       └── workspace.py    # Guarded and inline source-reader boundaries
└── tests/
```

Shared Pydantic input and output contracts live in
[`shared/schemas`](../../shared/schemas) so the server, CLI, host adapters, and
tests use the same structured definitions.

The CLI deliberately has local diagnostic commands that accept user-supplied
paths, including architecture-decision discovery. The optional MCP surface does
not expose a filesystem root or ADR-listing tool, and the current Codex package
does not register the MCP server at all.

## Local Development

Run these commands from the repository root. The project uses
[uv](https://docs.astral.sh/uv/) and supports Python 3.11 through 3.13.

Create the locked workspace environment:

```powershell
uv sync --locked --all-packages
```

Inspect the CLI:

```powershell
uv run ai-architect-tools --help
```

Run the package tests and static checks:

```powershell
uv run pytest tools/python-mcp/tests
uv run ruff check tools/python-mcp
uv run mypy
```

Do not start `ai-architect-mcp` in an ordinary interactive terminal and expect a
human-readable interface. It is a STDIO protocol process intended to be launched
by an MCP host or the repository's runtime smoke tests.

## Packaging

The versioned source of truth is this Python package together with the shared
schemas and lock file. The self-contained Windows executable placed under
`build/` and the assembled plugin under `dist/` are generated release artifacts,
not canonical source.

Any change to this package, the shared schemas, its dependencies, or `uv.lock`
requires its tests and optional transport package to be rebuilt. The current Codex
build also bundles the domain validation functions into its short-lived hook runtime:

```powershell
.\scripts\build-codex-plugin.ps1
```

The Codex build packages the short-lived hook runtime, validates generated provenance,
and smoke-tests activation, write guards, contract validation, artifact scanning, and
response checks. It does not create `.mcp.json` or package the historical launcher.
See the repository's [build instructions](../../README.md#build-the-codex-adapter)
and [release guide](../../docs/RELEASING.md) for the complete workflow.

## Further Documentation

- [AI Software Architect specification](../../specs/AISoftwareArchitect.md#shared-python-core-and-optional-stdio-mcp-adapter)
- [Main project README](../../README.md)
- [Codex adapter](../../adapters/codex)
