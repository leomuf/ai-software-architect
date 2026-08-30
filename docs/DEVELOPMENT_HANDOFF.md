<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Development Handoff

This document summarizes the project state and the architectural decisions needed
to continue development without relying on the original Codex conversation. It is
a point-in-time handoff, not a replacement for the living specification or release
documentation.

## Snapshot

```yaml
handoff_date: 2026-07-21
branch: main
head_commit: dcc9760
head_summary: hardens Codex release-candidate runner
remote_state_at_handoff: origin/main matched HEAD
target_release: 0.1.0
installed_codex_plugin_version: 0.1.0
specification_status: approved, pre-release, living specification
license: MIT
working_tree_note: docs/DEMO_VIDEO.md was the only untracked file before this handoff was added
```

The historical tag `pre-release-mcp-server` points to commit `8f2f035`. It preserves
the earlier persistent-MCP Codex design as a rollback and comparison point.

## Product Summary

AI Software Architect is an open-source, coding-assistant-hosted architecture
companion. It helps users clarify requirements, inspect a repository statically,
compare three to five credible architecture or design-pattern alternatives, make a
user-controlled decision, record Architecture Decision Records (ADRs) and related
artifacts, prepare a coding handoff, and review architectural conformance.

The first release is an installable Codex plugin. GitHub Copilot, Claude Code, and
Google Antigravity adapters are planned and already have adapter-specific README
placeholders. Model reasoning remains host-native: the user's selected coding-
assistant model performs the reasoning with the user's applicable account or
credits. No managed AI backend is required.

## Architecture Decisions to Preserve

### Canonical shared source

- Reusable skills, schemas, reference material, templates, and evaluation fixtures
  live under `shared/`.
- Codex packaging is an adapter under `adapters/codex/`; future hosts should reuse
  the shared source and implement only host-specific integration.
- All 23 Gang of Four patterns have focused progressive-disclosure references.
  Architecture, presentation, dependency, data, integration, resilience, and
  modernization patterns are separated by category.
- Pattern references include short Python implementation examples and a human-
  readable example context.

### One public Codex skill

Users normally select the plugin from Codex's `@` picker; Codex displays the
structured selection as:

```text
@AI Software Architect <request>
```

Merely typing the literal display name does not activate the plugin. The direct,
advanced skill entry remains supported:

```text
$ai-software-architect <request>
```

The host model chooses between focused help and the complete architecture workflow.
Internal modular skills remain hidden implementation building blocks; users should
not need to choose among them. Documentation should recommend structured selection
from the `@` picker while retaining `$` skill invocation for direct/advanced use.
Bare or mistaken `@` activation receives recovery guidance from the control plane
instead of silently doing nothing.

### Strongest plugin-native workflow

The product was initially considered as a separately configured autonomous agent.
The first release instead uses an easily installed Codex plugin with modular skills
and deterministic hooks. This is not a true independently scheduled autonomous
agent, but the hooks make the plugin-native workflow reliably agentic while leaving
semantic reasoning to the selected Codex model.

The Codex package uses these short-lived hooks:

- `UserPromptSubmit`: activation, routing, continuation, and a compact safety
  envelope. Exact reference hints are added only for explicitly named canonical
  references; when exactly one is resolved, its trusted packaged content is supplied
  inline to avoid a separate tool roundtrip. One exact installed comparison-bundle
  path supplies both the workflow and compact catalog for open comparisons, while
  the authoring-bundle path is added only for a
  typed decision continuation. A typed clarification continuation instead receives
  only a compact resume-design envelope and relies on the already-active Composite
  to load its selected workflow module.
  Five comparable runs of plugin `0.1.0+codex.20260804120052` confirmed two initial
  comparison calls instead of three and reduced P50 from 58.098 to 52.075 seconds.
  Its 62.680-second P90 remains provisional at `n = 5`, so no tail-latency improvement
  is claimed yet.
- The repository-side evaluator now records a validated comparison's public selected
  category/name and only a normalized fingerprint plus word count for its material
  assumption. Five exact runs on 2026-08-04 selected `No pattern` four times and
  Strategy once, with five different fingerprints. Manual review found the variation
  aligned with different explicit growth assumptions rather than contradictory
  choices under one identical assumption. The next decision is whether unknown future
  growth should default to current-evidence recommendations or trigger one focused
  clarification. The shared skill now resolves that policy by anchoring the primary
  recommendation in current evidence, keeping growth-dependent options conditional,
  and clarifying only when no responsible current-evidence default exists. This change
  was rebuilt as plugin `0.1.0+codex.20260804141427`. Its exact five-run cohort selected
  `No pattern` in every run and passed semantic review, artifact persistence, and
  application-source immutability checks without retries or exclusions. Initial
  P50/P90 were 63.888/69.671 seconds and continuation P50/P90 were
  113.293/135.065 seconds. The stable semantic result is accepted; another five exact
  samples are required before interpreting the provisional P90 or mixed latency shift.
  The cohort now has ten exact observations: all select `No pattern`, with established
  initial P50/P90 of 57.004/65.422 seconds and continuation P50/P90 of
  105.751/125.098 seconds. Continuation passes its warning-only objective; initial
  remains a warning only on the 40-second P50 target. Initial tool execution totals
  about 1.1 seconds on average, while the final response completes roughly 40 seconds
  after the second tool, so the next isolated optimization targets concise model-side
  synthesis rather than repository snapshot or comparison-bundle I/O.
  The next candidate adds a soft 350–450 visible-word target for routine
  small-repository comparisons and performance schema `1.4.0` records only visible
  response word count. Plugin `0.1.0+codex.20260804150751` passed ten unretried
  semantic/performance runs: selection remained stable, visible-response P50 fell
  from 514 to 429 words, initial P50/P90 fell from 57.004/65.422 to
  52.209/57.391 seconds, and completed-workflow P50/P90 fell from
  162.755/197.250 to 151.990/169.045 seconds. Every continuation persisted exactly
  four architecture artifacts and left application source unchanged. The established
  result supports retaining the soft synthesis budget.
  A later isolated candidate grouped the generated catalog into `Name=File` pairs.
  Plugin `0.1.0+codex.20260804183145` reduced mean initial input by 2.9%, but regressed
  initial and continuation P50 and produced one future-growth-driven Layered
  Architecture recommendation. The experiment is retained in the ledger as negative
  evidence; the grouped representation was reverted.
  A subsequent workflow-deduplication candidate reduced packaged comparison prose by
  9.1% and mean initial input by 6.1%, but regressed both latency medians and fragmented
  five recommendations across three selections. The removed repetition therefore had
  behavioral value for the host model; the complete wording was restored and the
  candidate remains only as negative evaluation evidence.
- The exploratory runner now supports separately named language campaigns without
  changing the canonical five-fixture English baseline. The first valid `german`
  campaign (`20260805T134102Z`) exercised clarification and comparison plus both
  continuations. Deterministic safeguards, four-artifact persistence, and source
  immutability passed. Manual review remains open because stable comparison headings
  were English and the German comparison used plausible future growth to recommend
  Layered Architecture instead of the current-evidence `No pattern` baseline. The
  subsequent candidate moves visible comparison labels into one declarative locale
  catalog shared by parser, Stop hook, continuation detection, and deterministic
  renderer. English, German, and Brazilian Portuguese catalogs are implemented; the
  BCP 47-shaped fixture contract and catalog-only parser design keep future locale
  additions independent of semantic routing.
  Rebuilt plugin `0.1.0+codex.20260805140210` passed five exact German comparison
  observations (`20260805T140517Z`, `20260805T141543Z`, `20260805T141827Z`,
  `20260805T142143Z`, and `20260805T142456Z`). Every response used the coherent German
  label set without a Stop correction, selected the current-evidence `No pattern`
  baseline, and kept future growth conditional. Each approval persisted exactly four
  validated architecture artifacts without changing application source. Initial
  latency was P50/P90 56.317/59.033 seconds, continuation latency was
  117.299/124.570 seconds, and completed-workflow latency was 173.616/183.032 seconds;
  all P90 values remain provisional at five observations. The second-language pass is
  accepted. The subsequent complete English regression campaign
  `20260805T143611Z` passed all five deterministic and manual semantic reviews on the
  same installed plugin, added five measured observations without exclusions, and
  preserved clarification, current-evidence comparison, four-artifact persistence,
  static review, bundled pattern help, and proportionate-simplicity behavior.
  Brazilian Portuguese (`pt-BR`) now has a complete catalog and a separate two-fixture,
  four-phase exploratory campaign. Plugin `0.1.0+codex.20260805190919` passed 151
  deterministic tests and campaign `20260805T192152Z`. Semantic review accepted the
  focused clarification and its local-Tkinter continuation, the comparison's coherent
  Portuguese contract and current-evidence `No pattern` selection, and the approval
  continuation's four validated architecture artifacts. No application source changed;
  the initial campaign and four targeted repetitions established an exact five-run
  comparison cohort. Every run selected `No pattern` and safely persisted four
  artifacts. Initial P50/provisional-P90 were 52.178/58.793 seconds, continuation
  P50/provisional-P90 were 118.082/128.183 seconds, and completed-workflow values were
  171.070/186.652 seconds. The continuation latency objective passes; the initial
  objective retains only its deliberately ambitious P50 warning. The reporter now
  resolves locale-prefixed fixture objectives from their canonical workflow suffix
  while keeping every locale, revision, provenance, and runtime cohort separate.
- Plugin `0.1.0+codex.20260805190919` also passed the complete English regression
  campaign `20260805T194142Z` and German regression campaign `20260805T194731Z` after
  `pt-BR` was added. Manual review found no mixed labels or semantic regression; both
  comparisons selected the current-evidence `No pattern` option and both approval
  continuations persisted exactly four artifacts without application-source changes.
- Neutral Spanish (`es`) now has a complete catalog and a separate two-fixture,
  four-phase exploratory campaign following the same language-neutral workflow and
  parser contracts. Deterministic validation is required before packaging, followed
  by the Spanish campaign and English, German, and Brazilian Portuguese regressions
  on the same release candidate.
- A separate `python-project-variety` campaign provides reproducible cross-structure
  evidence without changing the five-fixture baseline. Campaign `20260805T150133Z`
  passed deterministic and manual semantic review for both a cohesive single-file
  expense CLI and a six-file `src`-layout order service. The first recommendation
  preserved the one-file design and added only a validated CSV row-parsing boundary;
  the second identified the application service's concrete SQLite dependency and
  proposed one minimal repository port without a framework or broader layer rewrite.
  Reviews completed in 25.610 and 31.543 seconds, used one bounded static snapshot
  each, disclosed limitations, and changed no repository files.
- A later attempt to extend the exact English baseline exposed semantic instability
  rather than a latency regression. Campaign `20260805T150704Z` on plugin
  `0.1.0+codex.20260805140210` passed deterministic checks but selected Layered
  Architecture for the small one-file comparison because separable concerns and
  testability were treated as sufficient current forces. Keep this measured run as
  append-only negative evidence; do not accept it as a release semantic baseline.
  The portable option workflow now requires a demonstrated current force that simple
  functional or modular refactoring cannot adequately handle before a named pattern
  may outrank `No pattern`. The comparison fixtures also carry a typed expected public
  decision, and the runner emits `expected-decision-selected` as a deterministic
  pass/fail assertion after parsing the public comparison contract.
  `ExpectedDecision.selected_category` reuses the public canonical `PatternCategory`,
  so unsupported or misspelled fixture categories fail during schema validation.
  Corrected plugin `0.1.0+codex.20260805163758` passed Ruff, Mypy, 148 tests, package
  validation, and runtime smoke testing and was copied to the personal marketplace.
  Six exact corrected comparison observations (`20260805T174554Z`,
  `20260805T174845Z`, `20260805T175127Z`, `20260805T175406Z`,
  `20260805T175722Z`, and the complete `20260805T180036Z` campaign) all selected
  `No pattern`, passed `expected-decision-selected`, persisted exactly four
  architecture artifacts, and left application source unchanged. The cohort reports
  `stable-selection`, median 432.5 visible words, initial P50/P90 of
  44.151/64.484 seconds, continuation P50/P90 of 96.294/99.052 seconds, and
  completed-workflow P50/P90 of 137.840/163.365 seconds. Continuation passes its
  warning-only targets; initial P90 passes while the intentionally ambitious
  40-second P50 remains a warning. P90 is provisional at `n = 6`. Manual semantic
  review of the complete campaign also passed all five canonical fixtures without
  exclusions.
- `PreToolUse`: static-inspection boundaries, application-code write denial, and
  complete architecture-bundle validation before persistence.
- `PostToolUse`: persisted architecture-artifact verification.
- `PostCompact`: minimal typed workflow recovery after compaction.
- `Stop`: visible response-shape checks and internal-marker rejection.

The model retains semantic precedence: a material platform contradiction produces
one focused clarification without inspection or recommendation, and an explicitly
simple problem receives one proportionate recommendation rather than a padded
comparison.

Hooks make no model or network calls, start no persistent process, do not bypass
Codex permissions, and do not persist prompt or repository content. Users must
review and activate them in the Codex plugin page. Their public source and tests are
part of the repository so users can establish trust.

The same packaged runtime also supports one explicit `--repository-snapshot
--root .` invocation for small read-only reviews. The control plane supplies the
exact installed command and permits only that fixed executable-and-argument form.
It reads allowlisted UTF-8 text within fixed directory, entry, depth, file, and byte
budgets; excludes hidden, dependency, build, cache, credential, symlink, and
reparse-point paths; writes nothing; and exits. Its structured output is untrusted
static evidence for the selected host model, not parser-verified architecture
analysis. When it completely covers a small repository, the model reuses that
evidence and avoids subagent delegation by default.

### No persistent MCP process in the Codex package

The current Codex plugin uses a short-lived packaged hook runtime instead of a
persistent MCP server. This avoids process locks that previously prevented or
delayed plugin uninstall. The Python STDIO MCP implementation remains versioned
under `tools/python-mcp/` as optional reusable tooling and historical architecture,
but it is not started persistently by the Codex release package.

The persistent-MCP design is preserved by the `pre-release-mcp-server` tag.

### Persistence contract

Read-only recommendations never modify the repository. After explicit user
approval, the plugin may persist only validated architecture artifacts under:

```text
.ai-architect/
  project-context.md
  architecture-contract.yaml
  implementation-plan.md
  decisions/ADR-NNN[-slug].md
```

Application source code remains unchanged during the architecture-recording
workflow. The pre-write guard validates the complete candidate bundle, including
typed Pydantic/YAML shapes and secret scanning, before one reviewable patch. The
post-write hook verifies the persisted result.

## Important Repository Areas

```text
README.md                              Public project introduction and usage
specs/AISoftwareArchitect.md           Living product and architecture specification
shared/skills/                         Canonical modular skills and pattern references
shared/schemas/                        Pydantic contracts and generated JSON Schemas
shared/evaluations/                    Cross-host fixtures and release automation plan
adapters/codex/                        Codex control plane, hooks, packaging, and eval runner
adapters/github_copilot/               Planned GitHub Copilot adapter guidance
adapters/claude_code/                  Planned Claude Code adapter guidance
adapters/antigravity/                  Planned Google Antigravity adapter guidance
tools/python-mcp/                      Optional Python STDIO MCP tools, not persistent in Codex
scripts/                               Build, package, install-copy, release, and eval entry points
docs/RELEASING.md                      Canonical release process
docs/release-evidence-template.md      Release evidence checklist/template
TODO.md                                Current release blockers and deferred work
```

## Current Build and Installation Flow

Build the exact release candidate from the repository root:

```powershell
.\scripts\build-codex-plugin.ps1 -PluginVersion 0.1.0
```

This performs a full self-contained Windows x86-64 runtime build, plugin validation,
and runtime smoke test. Do not use `-ReuseRuntime` for a release candidate.

Create the marketplace bundle with the release/package scripts documented in
`docs/RELEASING.md` and `scripts/README.md`. The bundle is intended to install
without Python, `uv`, or first-run dependency downloads.

## Exploratory Evaluation System

Five shared fixtures currently form the main campaign:

1. `clarify-ui-architecture` (`FLOW-001`)
2. `architecture-option-comparison` (`FLOW-004`), including approval continuation
3. `read-only-architecture-review` (`REVIEW-002`)
4. `abstract-factory-example` (`SKILL-007`)
5. `avoid-overengineering` (`FLOW-002`)

Run the release campaign with:

```powershell
.\scripts\run-codex-exploratory-evaluations.ps1 `
  -ExpectedPluginVersion 0.1.0
```

Current behavior:

- defaults to `gpt-5.6-sol` with medium reasoning;
- asks Codex for the one unambiguous installed and enabled AI Software Architect
  across all marketplaces and records its identity and version;
- records the actual version in `SUMMARY.md` and `report.json`;
- treats `-ExpectedPluginVersion` as a mismatch guard and stops before model calls
  when the active version differs;
- never installs, disables, or switches plugins;
- keeps `-PluginVersion` as a backward-compatible PowerShell alias;
- shows live `[current/total]` fixture and phase progress;
- prints detailed fixture, phase, assertion, Codex, and stderr diagnostics on failure;
- preserves responses, JSONL events, stderr, isolated repositories, and change
  evidence under `.tmp/evaluations/<timestamp>/`;
- appends eligible completed phase timings and provenance to the canonical
  `evaluation-data/exploratory-runs.jsonl` history; and
- keeps dry runs, cancelled work, and infrastructure failures out of performance
  statistics.

`manual-review` means deterministic safeguards passed; it is not automatically a
semantic pass. A human must still review expected and forbidden behavior.

### Latest reviewed campaign

The campaign at `.tmp/evaluations/20260721T164129Z/` used `gpt-5.6-sol`, medium
reasoning, and Codex CLI `0.145.0-alpha.18`. It ran for approximately seven minutes.
All five fixtures passed deterministic checks and subsequent human semantic review.

Notable evidence:

- clarification correctly stopped at the Tkinter-versus-web contradiction;
- option comparison presented three same-scope alternatives with fit scores,
  categories, canonical links, evidence, assumptions, benefits, and liabilities;
- approval continuation persisted exactly four allowed architecture artifacts and
  did not modify application source;
- the pre-write hook rejected an initially incorrect artifact filename and the
  model corrected it before persistence;
- read-only review remained static and disclosed incomplete evidence;
- Abstract Factory loaded the bundled canonical example;
- the tiny-script scenario correctly recommended no named pattern;
- no MCP call or internal response marker was observed.

The older report did not record the plugin version because it predated automatic
version detection. Captured installed-skill paths nevertheless showed version
`0.1.0`. Future release evidence should use the command above.

Two non-blocking observations from the run:

- `rg` was unavailable inside some isolated Codex workspaces; the model recovered
  with PowerShell-only static inspection.
- delegated review was unavailable in one session and was correctly disclosed.

## GitHub and CI State

The existing GitHub workflows run deterministic tests, generation-diff checks,
Ruff, mypy, pytest, plugin build/validation, runtime smoke testing, CodeQL, and
release packaging. CI also validates and renders the versioned exploratory
performance history into the Job Summary and uploads its Markdown, primary and
telemetry CSV, privacy-preserving tool timeline, recommendation-consistency CSV,
and JSON views without modifying the ledger. Comparison runs recorded with
performance schema `1.3.0` retain only the selected public catalog category/name
and a normalized material-assumption fingerprint. Report schema `1.5.0` uses these
fields for exact like-for-like consistency signals, including installed plugin
version and provenance in cohort identity, without versioning free-form response or
repository content.

Dependabot is configured separately for Python and GitHub Actions. It may create
multiple temporary branches because ungrouped updates receive one branch and pull
request each.

### Protected live exploratory CI strategy (not yet implemented)

The zero-credit historical reporting tier is implemented in ordinary CI. For live
release-candidate evaluation, add a separate protected Windows workflow, initially
triggered by `workflow_dispatch`.

The protected workflow should:

- check out the exact trusted release commit;
- build, package, install, and verify the exact candidate;
- use `-ExpectedPluginVersion` to prevent testing the wrong installation;
- keep repository permissions read-only;
- expose a maintainer-controlled API key only to the model-execution step;
- never expose that secret to fork or untrusted pull-request code;
- use environment approval where available;
- pin actions to reviewed commit SHAs;
- prevent concurrent credit-consuming campaigns;
- set an explicit timeout;
- upload sanitized evaluation evidence;
- render the concise result in `GITHUB_STEP_SUMMARY`;
- fail on deterministic or infrastructure errors; and
- retain human semantic review and the manual Codex Desktop install/uninstall gate.

The existing proposal is documented in
`shared/evaluations/release-automation-plan.md`. Do not run the live model campaign
on every pull request: it is slower, consumes credits, requires a protected secret,
and has nondeterministic semantic output.

## Safety and Maintenance Constraints

- Treat the public repository as attacker-readable; controls must not depend on
  secrecy of their implementation.
- Do not commit credentials, Codex `auth.json`, hidden reasoning, or sensitive local
  paths in release evidence.
- Do not run repository code during a read-only architecture inspection.
- Do not weaken typed validation or application-code write denial to make a model
  response pass.
- Do not restore a persistent Codex MCP process without revisiting uninstall locks,
  trust boundaries, and the historical tagged implementation.
- Preserve progressive disclosure: the public Composite `SKILL.md` is a concise
  router, canonical workflow bodies are packaged as directly linked internal
  references, and focused pattern questions load only their selected workflow and
  pattern reference. A routine open Codex comparison uses its generated workflow
  plus compact catalog and loads at most one candidate body only when a material
  distinction remains unresolved.
- Keep ADR option identifiers machine-stable: `considered_option_ids` and
  `selected_option_id` contain plain `OPT-NNN` values; human-readable labels belong
  in prose fields.
- Keep model-specific reasoning out of the shared deterministic control plane.
- Keep the specification living and aligned with intended behavior; Git tags
  preserve historical released specifications.

## Suggested Resume Prompt

Use this prompt in a future Codex task:

> Read `docs/DEVELOPMENT_HANDOFF.md`, `TODO.md`, `docs/RELEASING.md`, and the relevant
> sections of `specs/AISoftwareArchitect.md`. Verify the current branch, Git status,
> installed plugin version, and latest CI state before changing anything. Continue
> with the next unfinished release blocker. Preserve the one-public-skill Codex
> design, short-lived hooks, host-native model reasoning, validated `.ai-architect`
> persistence, and the no-persistent-MCP Codex package decision.
