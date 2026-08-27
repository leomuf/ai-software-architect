<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Release Evidence: `<version>`

Copy this file to `docs/releases/<version>.md` and replace every placeholder.
Do not record secrets, hidden reasoning, unnecessary source content, or sensitive
local paths.

## Candidate Identity

| Field | Value |
|---|---|
| Release version | `<version>` |
| Git tag | `<tag>` |
| Commit SHA | `<sha>` |
| Plugin provenance hash | `<hash>` |
| Package SHA-256 | `<hash>` |
| Codex version | `<version>` |
| Installed plugin version | `<version detected by the evaluation runner>` |
| Model and reasoning effort | `gpt-5.6-sol`, medium |
| Operating system | Windows x86-64 `<version>` |
| Evaluator | `<name>` |
| Evaluation date | `<YYYY-MM-DD>` |

## Gate A: Deterministic Repository Validation

- [ ] `uv lock --check`
- [ ] locked dependency synchronization
- [ ] schema generation produced no diff
- [ ] acceptance generation produced no diff
- [ ] third-party notice generation produced no diff
- [ ] Ruff
- [ ] mypy
- [ ] pytest
- [ ] release-candidate build
- [ ] plugin validation
- [ ] packaged runtime smoke test

Evidence or workflow URL: `<link or concise note>`

## Gate B: Package Inspection

- [ ] manifest and provenance versions match the candidate
- [ ] provenance inventory and hashes validate
- [ ] license and third-party notices are present
- [ ] no development environment, cache, credential, or placeholder is packaged
- [ ] fixed bundled short-lived hook-runtime command is present
- [ ] no persistent MCP registration or startup command is packaged
- [ ] no first-run dependency download is required

Evidence: `<link or concise note>`

## Gate C: Structured Plugin-Mention Smoke

- exact structured mention: `[@ai-software-architect](plugin://ai-software-architect@personal)`
- result:
- evidence path:
- confirmed excluded from exploratory performance ledger: [ ]

## Gate D: Exploratory Fixtures

- Runner output directory:
- `report.json` SHA-256:
- `SUMMARY.md` reviewed:
- All deterministic assertions passed:
- All semantic expected and forbidden behaviors reviewed:

| Fixture | Result | Expected behaviors | Forbidden behaviors | Side effects | Evidence |
|---|---|---|---|---|---|
| `clarify-ui-architecture` | `<pass/fail>` | `<result>` | `<result>` | `<result>` | `<link/note>` |
| `architecture-option-comparison` | `<pass/fail>` | `<result>` | `<result>` | `<result>` | `<link/note>` |
| `read-only-architecture-review` | `<pass/fail>` | `<result>` | `<result>` | `<result>` | `<link/note>` |
| `abstract-factory-example` | `<pass/fail>` | `<result>` | `<result>` | `<result>` | `<link/note>` |
| `avoid-overengineering` | `<pass/fail>` | `<result>` | `<result>` | `<result>` | `<link/note>` |

Unresolved infrastructure errors: `<none or details>`

## Gate E: Codex Desktop Acceptance

- [ ] exact candidate installed or updated through the Plugins window
- [ ] current hook definitions reviewed and activated
- [ ] displayed version matches the candidate
- [ ] the single `$ai-software-architect` skill invokes without an `@` plugin mention
- [ ] expected short-lived hook behavior and absence of optional MCP use confirmed
- [ ] candidate exercised from multiple tasks
- [ ] first-attempt uninstall succeeded while Codex remained open
- [ ] no plugin hook-runtime process or stale installed package remained
- [ ] reinstall succeeded and exposed the same version

Lifecycle evidence: `<process observations and concise result>`

## Gate F: Clean-Machine Acceptance

- [ ] tested on clean Windows x86-64
- [ ] Python and `uv` were not preinstalled requirements
- [ ] no first-run dependency download occurred
- [ ] main workflow succeeded
- [ ] deterministic pre-write and post-write artifact validation succeeded
- [ ] no network listener appeared
- [ ] first-attempt uninstall succeeded

Evidence: `<link or concise note>`

## Deviations and Residual Risks

`<none, or each accepted deviation with owner, justification, and follow-up>`

## Release Decision

- Decision: `<GO/NO-GO>`
- Decided by: `<name>`
- Date: `<YYYY-MM-DD>`
- Rationale: `<concise rationale>`
