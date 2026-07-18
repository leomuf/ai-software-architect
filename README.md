<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# AI Software Architect

![AI Software Architect logo](assets/AISoftwareArchitect.png)

AI Software Architect is an open-source, host-native architecture agent for coding assistants. It helps developers clarify architecture-significant requirements, compare credible options, approve and record decisions, prepare coding handoffs, and review implementation conformance.

Maintained by Leonardo Muffato at [AUTOSOFT Engineering](https://www.autosoft-engineering.de).

## Why AI Software Architect?

AI coding assistants are excellent at generating working code quickly, but they can begin implementation before making the architecture explicit. Important questions about constraints, quality attributes, component boundaries, data ownership, viable alternatives, and long-term trade-offs may therefore remain hidden inside one conversation—or never be considered at all. The result can work today while becoming unnecessarily coupled, difficult to test, or expensive to evolve.

AI Software Architect introduces a repeatable **architecture-first workflow** before substantial code generation. It asks only questions that can change a material decision, compares credible options instead of forcing a favorite pattern, requests approval, and records the outcome as durable repository artifacts. The coding assistant can then implement from an approved architecture contract and later review the code for drift.

Unlike a one-off architecture prompt, the project supplies a reusable method, focused architectural knowledge, structured outputs, deterministic validation, and a conformance workflow. Unlike a separate hosted architecture service, it runs inside the coding assistant the developer already uses. This cannot guarantee one universally “best” architecture, but it makes better architecture substantially more likely by exposing assumptions, alternatives, and consequences before they become code.

The first implementation target is an installable [Codex](https://openai.com/codex/) plugin. The canonical skills, schemas, templates, and repository artifacts are designed for reuse by future adapters for **GitHub Copilot, Claude Code, Google Antigravity, Cursor, JetBrains AI Assistant, Gemini Code Assist, Windsurf, and other coding assistants**. Each host continues using its own model, subscription, credits, and permission system.

## Features

- **Architecture-first reasoning:** discovers constraints, stakeholders, risks, and prioritized quality attributes before implementation.
- **Focused clarification:** asks a bounded number of questions only when the answers can materially change a decision.
- **Credible option comparison:** evaluates multiple approaches, their trade-offs, assumptions, uncertainty, and the option of using no named pattern.
- **Clear, trustworthy findings:** clearly distinguishes verified facts from assumptions and possibilities, and shows the evidence behind important conclusions.
- **Explicit human approval:** recommendations remain proposals until the user approves or revises them.
- **Durable architecture artifacts:** creates Architecture Decision Records (ADRs), a machine-readable architecture contract, project context, and an implementation plan inside the repository.
- **Coding-agent handoff:** gives the implementation task clear component responsibilities, dependency rules, constraints, milestones, and verification steps.
- **Architecture conformance review:** links implementation findings to accepted decisions and distinguishes confirmed violations from possible drift or acceptable deviations.
- **Host-native model execution:** uses the selected coding assistant and model; the project makes no model calls and requires no additional model-provider API key.
- **Local-first operation:** requires no managed backend, hosted database, account system, usage metering, or project-data upload service.
- **Modular Agent Skills:** separates interviewing, option evaluation, decision creation, coding handoff, and conformance review into reusable skills based on the open `SKILL.md` format.
- **Progressive disclosure:** initially exposes only skill metadata, loads a workflow when activated, and reads only the architecture references relevant to the current decision.
- **Ready-to-use Python examples:** every GoF pattern reference includes a compact, syntax-validated implementation example that is loaded only when the pattern is relevant or the user requests it.
- **Deterministic local tools:** bundles a small read-only Python STDIO MCP server for Pydantic contract validation, ADR inspection, Python dependency evidence, architecture-boundary checks, and pre-write secret scanning. When Codex does not forward MCP roots, it can use compact line-preserving import statements for faster routine scans or bounded full source for higher-assurance analysis.
- **Portable source of truth:** stores accepted architecture state as reviewable Markdown and YAML rather than in a proprietary service.

## Architecture and Pattern Knowledge

The architect selects references from the forces it discovers; users do not need to choose a pattern in advance, and the catalog is never loaded all at once.

- **Architecture styles:** Modular Monolith, Service-Oriented Architecture, Layered Architecture, Clean Architecture, Hexagonal Architecture, Vertical Slice Architecture, Event-Driven Architecture, and Model-View-Controller.
- **GoF object-design patterns:** all 23 Gang of Four patterns are available as separate focused references with progressively disclosed Python examples, with deeper initial evaluation coverage for Strategy, Factory Method, Observer, Adapter, and Command.
- **Dependencies and boundaries:** Dependency Inversion, Dependency Injection, Ports and Adapters, and Anti-Corruption Layer.
- **Data and integration:** Repository, Unit of Work, Idempotency, Idempotent Consumer, Transactional Outbox, Saga, and Publish/Subscribe.
- **Resilience and performance:** Retry with Backoff, Timeout and Deadline Propagation, Circuit Breaker, and Cache-Aside.
- **Complexity control:** explicitly recommends no named pattern when additional structure is not justified.

## Project Structure

```text
ai-software-architect/
├── shared/
│   ├── skills/                 # Canonical modular workflows and focused references
│   ├── schemas/                # Pydantic models and generated JSON Schema
│   └── evaluations/            # Gherkin acceptance criteria and verification map
├── tools/
│   └── python-mcp/             # Read-only MCP server, CLI, and domain logic
├── adapters/
│   └── codex/                  # Codex Composite, plugin packaging, and smoke tests
├── tests/                      # Schema, security, conformance, and packaging tests
├── specs/                      # Approved product and security specification
├── .github/                    # CI, CodeQL, release, and dependency automation
├── pyproject.toml              # uv workspace and development tooling
└── uv.lock                     # Reproducible locked dependency resolution
```

Generated plugin packages are written under `dist/` and are intentionally excluded from version control.

## Requirements

### Using the released Codex plugin

- A Codex version that supports plugins, Agent Skills, and local STDIO MCP servers.
- Windows x86-64 for the initial packaged runtime.
- A Codex account and model allocation.
- No separate OpenAI API key, Python installation, `uv`, virtual environment, or first-run dependency download.

### Developing from source

- Git.
- [uv](https://docs.astral.sh/uv/) `0.11.x`.
- Python `3.13.12`, as recorded in [`.python-version`](.python-version). `uv` can provision it.
- Windows x86-64 to build and smoke-test the initial self-contained runtime.

## Quick Start

Create the locked development environment:

```powershell
uv sync --locked --all-packages
```

Run the test and quality gates:

```powershell
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

The assembled plugin is written to `dist/codex/ai-software-architect/`.

## Security Guardrails

The project assumes its public controls are known to an attacker and treats repository content as untrusted data.

- The local MCP server is read-only and has no network access, model calls, shell execution, subprocess execution, destructive writes, credentials, or telemetry.
- MCP filesystem reads require one host-confirmed workspace root and fail closed when it cannot be established. Dependency and boundary analysis can instead parse bounded Python content already read through the host's native workspace permissions: compact static-import statements for fast scans or full source for stronger verification. Neither inline mode opens a path.
- Paths are canonicalized and checked against traversal, symlink, junction, reparse-point, protected-file, and final-open-handle escapes.
- Supported files are parsed without executing repository code; YAML aliases, duplicate keys, unsafe object construction, binary files, archives, unknown formats, and oversized input are rejected or safely skipped.
- File, byte, dependency-edge, timeout, and process-call budgets bound repository analysis.
- Generated ADRs, contracts, context, and implementation plans are scanned for likely secrets before writing; suspected values are never echoed.
- Repository text—including comments, documentation, filenames, and generated content—cannot authorize actions, expand scope, override instructions, or request secrets.
- All artifact writes remain subject to the coding assistant’s native sandbox, permission prompts, explicit decision approval, and concurrent-edit protection.

These controls reduce risk but do not claim perfect prompt-injection prevention. See [SECURITY.md](SECURITY.md) for reporting and the [approved specification](specs/AISoftwareArchitect.md) for the complete threat model, architecture, schemas, and acceptance criteria.

## License

MIT License. See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## 💖 Acknowledgments & Recognition

This project was developed for the [OpenAI Build Week Hackathon](https://openai.com/build-week). We would like to express our deepest gratitude to the entire [Devpost](https://devpost.com/) and [OpenAI](https://openai.com/) teams for providing this extraordinary learning opportunity and equipping us with the cutting-edge [Codex](https://openai.com/codex/) coding agent that helped bring this project to life.
