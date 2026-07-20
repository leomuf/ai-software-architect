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

The product is designed for multiple coding agents. One canonical set of skills, schemas, templates, evaluation scenarios, and repository artifacts supplies the shared architecture behavior; a thin adapter maps that source into each host's native packaging, invocation, tools, and safety controls. Each host continues using its own model, subscription, credits, and permission system.

The first implemented adapter is an installable [Codex](https://openai.com/codex/) plugin. GitHub Copilot, Claude Code, Google Antigravity, and other coding-agent integrations are planned but are not yet available. See [Coding Agent Integrations](#coding-agent-integrations) for the status and intended approach for each host.

## Delivery Strategy: Host-Native Instead of a Separate Agent Runtime

The project’s initial concept was a standalone autonomous software-architecture agent. For the first public release, we deliberately chose host-native plugins and adapters instead. This gives a broader audience a simpler installation path and lets people keep using the coding agent, model, credits, tools, sandbox, and permission workflow they already trust—without operating another agent runtime, supplying another model API key, or depending on a hosted service.

Every adapter is expected to combine the strongest native capabilities its host provides:

- **Shared skills and references** provide the architecture method, specialized knowledge, progressive disclosure, and model-guided workflow.
- **Host-native lifecycle controls**, where available, reinforce activation, tool boundaries, and critical response outcomes.
- **The local MCP server** provides deterministic, bounded evidence and validation tools without performing model reasoning.
- **The selected coding agent remains the runtime**, performing reasoning and tool orchestration with the user’s selected model.

This is intentionally not an unsupervised background agent. The architect runs only when explicitly invoked, presents material decisions for human approval, and does not silently implement its own recommendations. Host-specific differences are isolated in adapters and documented separately below; they do not create independent copies of the shared architectural knowledge.

## Features

- **Architecture-first reasoning:** discovers constraints, stakeholders, risks, and prioritized quality attributes before implementation.
- **Focused clarification:** asks a bounded number of questions only when the answers can materially change a decision.
- **Credible option comparison:** evaluates three to five approaches for one decision when that many are credible, presents an ordinal `NN/100` fit with benefits, liabilities, assumptions, and links, and asks the user to make the final choice.
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
- **Deterministic local tools:** provides a small read-only Python STDIO MCP server for complete-contract validation, Python dependency evidence, architecture-boundary checks, and pre-write secret scanning.
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
│   └── codex/                  # Codex Composite, control plane, packaging, and smoke tests
├── tests/                      # Schema, security, conformance, and packaging tests
├── specs/                      # Approved product and security specification
├── .github/                    # CI, CodeQL, release, and dependency automation
├── pyproject.toml              # uv workspace and development tooling
└── uv.lock                     # Reproducible locked dependency resolution
```

Generated plugin packages are written under `dist/` and are intentionally excluded from version control.

## Coding Agent Integrations

The shared architecture method is independent of any one coding agent. Platform adapters package that method for a specific host and map invocation, lifecycle controls, local tools, permissions, and installation to the host's native capabilities. An adapter is not considered supported until its behavior, security boundaries, packaging, installation, upgrade, and removal have been validated on that host.

| Coding agent | Status | Delivery approach |
|---|---|---|
| OpenAI Codex | **Implemented** | Installable plugin with Agent Skills, trusted hooks, and a packaged local STDIO MCP runtime. |
| GitHub Copilot | **Planned** | Native Copilot adapter generated from the canonical skills, references, schemas, and evaluations. |
| Claude Code | **Planned** | Native Claude Code adapter generated from the same canonical source and connected to bounded local tools. |
| Google Antigravity | **Planned** | Native Antigravity adapter using the configured Gemini model and host-native controls. |
| Other coding agents | **Roadmap** | Additional adapters where the host can preserve explicit activation, human approval, repository artifacts, and safety constraints. |

### OpenAI Codex — Implemented

The Codex adapter is the current working product. It packages the main Composite workflow and a focused option-evaluation skill, a deterministic hook-based control plane, and a self-contained Windows x86-64 MCP runtime. Codex remains the agent runtime and uses the model and credits selected by the user.

The plugin does not install or modify Codex custom-agent or subagent profiles. That keeps normal installation simple and avoids silently changing a user's agent configuration. Advanced users may combine the installed skills and tools with their own custom-agent setup, but this is optional and outside the plugin's installation contract.

#### Requirements

- A Codex version that supports plugins, Agent Skills, hooks, and local STDIO MCP servers.
- Lifecycle hooks explicitly reviewed and activated from the plugin page for the recommended deterministic safeguards described below.
- Windows x86-64 for the initial packaged runtime.
- A Codex account and model allocation.
- No separate OpenAI API key, Python installation, `uv`, virtual environment, or first-run dependency download.

#### Quick Start

Selecting the plugin with `@` makes its bundled capabilities available; it does not by itself run the architect workflow. Explicitly invoke the main skill:

```text
$ai-software-architect Compare suitable architectures for this project.
```

For a direct pattern explanation or stored implementation example, invoke the focused skill:

```text
$evaluate-architecture-options Show me the canonical Python Abstract Factory example.
```

Implicit skill invocation is intentionally disabled so ordinary coding requests do not silently become architecture sessions. New or changed plugin hooks are skipped until you review their definitions and activate them from the plugin page. Codex may show them as disabled rather than opening a separate approval prompt. The skills remain usable without hooks, but deterministic invocation guidance, focused reference injection, tool restrictions, and option-rendering checks are then unavailable.

If you select `@AI Software Architect` but forget the `$` invocation, a trusted control-plane hook does not guess which workflow you intended. It blocks the malformed prompt before it reaches the model or any plugin tool, then displays both valid commands so you can resend it correctly.

<a id="why-codex-asks-you-to-trust-the-hooks"></a>

#### Why You Need to Review and Activate the Codex Hooks

Codex does not necessarily open a proactive approval dialog for plugin hooks. New or changed non-managed hooks are marked for review and skipped until you explicitly trust their current definitions. In Codex Desktop, open the AI Software Architect plugin page, review the hooks, and use the available control to activate them. In the CLI, use `/hooks` to inspect and trust them. Codex records trust for the current hook definition, so a later change requires another review. This is a useful security boundary because a hook is local code that can observe a specific workflow event and return a bounded instruction to Codex. See the official [Codex hooks documentation](https://learn.chatgpt.com/docs/hooks).

For AI Software Architect, the hooks are recommended because skills and prompts guide the selected model, while hooks add a small **deterministic safety and quality layer** around that reasoning. They prevent an accidental bare `@AI Software Architect` invocation from silently doing nothing, inject one explicitly matched bundled reference, keep repository inspection static, prevent the architect role from editing application code, stop architect tools that are structurally outside a focused skill route, verify the focused option-comparison rendering, and ensure a complete-workflow recommendation offers a clear next choice. They deliberately do not classify free-form architecture intent from language-specific keywords; the selected host model and canonical skills retain that responsibility.

The three hooks have deliberately narrow responsibilities:

| Hook | When it runs | What it does |
|---|---|---|
| `UserPromptSubmit` | After you submit a prompt | Distinguishes the real plugin URI from explicit `$` skill invocations, supplies a single matching bundled reference for the focused skill, or explains how to correct an incomplete `@` invocation. |
| `PreToolUse` | Before a shell command, file patch, or AI Software Architect MCP tool runs | Blocks repository interpreters, test/build/package runners, mutating shell commands, and application-code patches during architect turns. Approved architecture artifacts remain patchable only under `.ai-architect/`. It also denies MCP operations that are structurally outside a focused route. It cannot grant extra filesystem or network permissions. |
| `Stop` | Before Codex accepts an architect response | Checks the stable focused-comparison sections or one hidden complete-workflow outcome marker. A `recommendation` outcome must also offer approve, revise, or more information. It may request one complete corrected response, with a loop guard preventing repeated correction cycles. |

What happens locally:

- Codex supplies the corresponding event payload; the implementation reads only the current prompt, selected tool name and arguments, or final response fields required for that check.
- The hooks make no model calls and no network requests. Pattern examples are read from the plugin's bundled reference files.
- They do not execute repository code and do not bypass Codex's sandbox, native permission prompts, or user approval.
- They never persist prompts, responses, repository content, or tool arguments. Shell and patch arguments are inspected only in memory to classify forbidden execution or mutation and to validate patch target paths. Temporary turn state contains only a hashed session/turn key, the explicit route, and an optional bundled-reference identifier. Abandoned state is age- and count-bounded.
- If a hook fails unexpectedly, it **fails open with a visible warning** so that a local guard failure does not silently trap the user.
- Each hook command has a five-second execution limit.

The complete implementation is public and reviewable:

- [`hooks.json`](https://github.com/leomuf/ai-software-architect/blob/main/adapters/codex/templates/hooks.json) declares the three events, the exact local command, and their timeouts.
- [`hook_entry.py`](https://github.com/leomuf/ai-software-architect/blob/main/adapters/codex/hook_entry.py) reads the bounded event payload, manages minimal temporary state, and returns the hook decision.
- [`control_plane.py`](https://github.com/leomuf/ai-software-architect/blob/main/adapters/codex/control_plane.py) contains the pure routing, tool-denial, and response-validation rules.
- [`test_codex_control_plane.py`](https://github.com/leomuf/ai-software-architect/blob/main/tests/packaging/test_codex_control_plane.py) verifies allowed and denied behavior, stored-reference injection, correction limits, and privacy boundaries.
- [`smoke_test_runtime.py`](https://github.com/leomuf/ai-software-architect/blob/main/adapters/codex/smoke_test_runtime.py) launches the packaged command exactly as Codex does and checks the hook and MCP surfaces before release.

Activating these reviewed hooks therefore does not mean granting the architect unrestricted control. It authorizes the reviewed local checks above to run at those three Codex lifecycle points. The skills remain usable if hooks are not activated, but deterministic invocation guidance, focused tool restrictions, reference injection, and option-rendering checks will then be unavailable.

#### Plugin Lifecycle and Uninstall

The normal uninstall path is **Codex → Plugins → Installed → AI Software Architect → Uninstall**. The packaged local-tool process is designed to release itself automatically. A release is not considered ready until this succeeds in Codex Desktop without asking users to edit the plugin cache or manually terminate processes.

If a Codex host defect prevents uninstall, close tasks actively using the plugin, wait up to the reviewed 120-second idle shutdown interval, and retry once. Restart Codex if the host still retains the connection. Needing this retry is still a lifecycle defect for the current release gate, even when no permanent orphan remains. Please report it with the Codex version and operating system through the project's GitHub issue tracker.

### GitHub Copilot — Planned

**TO BE IMPLEMENTED IN A FUTURE VERSION.**

The planned adapter will reuse the canonical skills, focused references, schemas, templates, repository artifacts, and acceptance scenarios. The implementation will add Copilot-native packaging and invocation, connect the bounded local MCP tools where the host supports them, map deterministic safeguards to supported host controls, and validate installation, permissions, output contracts, and removal before claiming feature parity. Copilot users will use their Copilot plan and selected model.

### Claude Code — Planned

**TO BE IMPLEMENTED IN A FUTURE VERSION.**

The planned adapter will reuse the same canonical source, add Claude Code-native workflow entry points and local-tool configuration, and map activation, permissions, lifecycle enforcement, and response validation to the host capabilities available at implementation time. Claude Code users will use their existing Claude configuration; the project will not require a second model API key.

### Google Antigravity — Planned

**TO BE IMPLEMENTED IN A FUTURE VERSION.**

The planned adapter will package the canonical workflow for Antigravity, use its host-native repository tools and safety controls, and connect deterministic local validation where supported. Antigravity users will use their configured Gemini model and Google account allocation.

### Other Coding Agents — Roadmap

**TO BE IMPLEMENTED IN FUTURE VERSIONS AS HOST CAPABILITIES AND PROJECT PRIORITIES ALLOW.**

Potential adapters include Cursor, JetBrains AI Assistant, Gemini Code Assist, and Windsurf. Each adapter should remain thin: shared reasoning knowledge and durable artifact formats stay canonical, while only host-specific packaging, invocation, tool bindings, lifecycle controls, and validation change. Recommendations may differ between hosts and models; identical reasoning output is not a portability requirement.

## Development from Source

The current build and packaging commands target the implemented Codex adapter.

### Requirements

- Git.
- [uv](https://docs.astral.sh/uv/) `0.11.x`.
- Python `3.13.12`, as recorded in [`.python-version`](.python-version). `uv` can provision it.
- Windows x86-64 to build and smoke-test the initial self-contained runtime.

### Setup and Validation

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

### Build the Codex Adapter

Build and smoke-test the self-contained Windows x86-64 plugin:

```powershell
uv run python adapters/codex/build_plugin.py --build-runtime
uv run python adapters/codex/smoke_test_runtime.py dist/codex/ai-software-architect/runtime/windows-x86_64/ai-architect-mcp/ai-architect-mcp.exe
```

For a local cache-busted package, pass the complete SemVer through `--plugin-version` during the build. The version is written before provenance hashes are generated; packaged files must not be re-stamped afterward.

The assembled plugin is written to `dist/codex/ai-software-architect/`.

## Security Guardrails

The project assumes its public controls are known to an attacker and treats repository content as untrusted data.

### Shared Controls

- The local MCP server is read-only and has no network access, model calls, shell execution, subprocess execution, destructive writes, credentials, or telemetry.
- Paths are canonicalized and checked against traversal, symlink, junction, reparse-point, protected-file, and final-open-handle escapes.
- Supported files are parsed without executing repository code; YAML aliases, duplicate keys, unsafe object construction, binary files, archives, unknown formats, and oversized input are rejected or safely skipped.
- File, byte, dependency-edge, timeout, and process-call budgets bound repository analysis.
- Generated ADRs, contracts, context, and implementation plans are scanned for likely secrets before writing; suspected values are never echoed.
- Repository text—including comments, documentation, filenames, and generated content—cannot authorize actions, expand scope, override instructions, or request secrets.
- All artifact writes remain subject to the coding agent's native sandbox, permission prompts, explicit decision approval, and concurrent-edit protection.
- Future adapters must preserve these security properties even when their host-specific implementation differs.

### Additional Codex Adapter Controls

- The Codex MCP surface exposes no filesystem root or ADR-listing operation. Dependency and boundary analysis parses only bounded Python content already read through Codex's native workspace permissions: compact static-import statements for fast scans or full source for stronger verification. Neither mode opens a path.
- The architecture workflow activates only for an explicit `$ai-software-architect` or `$evaluate-architecture-options` invocation. A plugin `@` mention alone is blocked before model or MCP execution and persists no turn state. Valid architect turns store only a hashed turn key and route classification in Codex's plugin-data directory, never the user's prompt or repository content.
- Trusted hooks keep architect inspection static by denying repository interpreters, test/build/package runners, mutating shell and Git commands, and application-code patches. Approved architecture artifacts are patchable only under `.ai-architect/`; focused option/reference turns remain entirely patch-free. The same hooks may deny structurally invalid focused-route MCP calls and request one corrected focused option rendering. Complete-workflow responses carry one hidden `clarify`, `recommendation`, or `complete` outcome marker; only `recommendation` also carries the stable decision-action marker. The hook checks these structures rather than interpreting localized prose. It fails open with a visible warning, avoids infinite retries, and does not replace Codex's sandbox, permissions, or semantic model reasoning.

These controls reduce risk but do not claim perfect prompt-injection prevention. See [SECURITY.md](SECURITY.md) for reporting and the [approved specification](specs/AISoftwareArchitect.md) for the complete threat model, architecture, schemas, and acceptance criteria.

## License

MIT License. See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## 💖 Acknowledgments & Recognition

This project was developed for the [OpenAI Build Week Hackathon](https://openai.com/build-week). We would like to express our deepest gratitude to the entire [Devpost](https://devpost.com/) and [OpenAI](https://openai.com/) teams for providing this extraordinary learning opportunity and equipping us with the cutting-edge [Codex](https://openai.com/codex/) coding agent that helped bring this project to life.
