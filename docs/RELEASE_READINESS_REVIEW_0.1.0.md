<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Release Readiness Review: 0.1.0

## Review Metadata

```yaml
review_date: 2026-07-21
reviewed_commit: dcc9760c7fdbdce1d79af736e547e27c513551b5
branch: main
review_focus:
  - release identity and evidence
  - Codex hook trust boundaries
  - repository execution resistance
  - architecture artifact integrity
  - package provenance and lifecycle
  - public security documentation
excluded:
  - minor code style
  - speculative refactoring
  - feature enhancements unrelated to release safety
decision: conditional-go-after-remaining-manual-release-gates
```

This review intentionally reports only findings with material release impact. It
does not replace the remaining manual gates in `docs/RELEASING.md`, especially
clean-machine installation and first-attempt Codex Desktop uninstall.

## Resolution Verification

All four high-severity blockers were resolved on 2026-07-21:

- RB-001: the runner now searches all marketplaces, requires one unambiguous enabled
  installation, validates available source provenance, and records plugin ID,
  marketplace, version, and provenance digest;
- RB-002: active shell inspection now uses a fail-closed single-command static-read
  allowlist and denies composition, variables, call operators, script blocks,
  redirection, unknown commands, and executable tooling;
- RB-003: active artifact writes require a trustworthy workspace, complete resulting
  content, per-ADR and contract validation, secret scanning, atomic bundle validation
  during approval handoff, and no deletion; and
- RB-004: every hook command declares its exact event, and runtime failures deny
  PreToolUse or stop unverifiable PostToolUse operations without exposing payload data.

Verification evidence:

```yaml
automated_tests: 100-passed
ruff: passed
mypy: passed
package_validation: passed
runtime_smoke_test: passed
full_exploratory_campaign:
  plugin_version: 0.1.0+codex.20260721193701
  evidence: .tmp/evaluations/20260721T194020Z
  deterministic_result: all-five-manual-review-no-failures
```

Manual semantic review confirmed the clarification gate, three-option comparison,
approved canonical four-artifact write, read-only evidence limitations, canonical
Abstract Factory example and link, and proportionate no-pattern recommendation. The
remaining clean-machine installation, first-attempt uninstall, and release-record
steps in `docs/RELEASING.md` remain required before publication.

## Verification Performed

The following checks passed:

- `uv lock --check`;
- Ruff over schemas, Python MCP tools, adapters, and tests;
- mypy over the configured project;
- all 96 automated tests;
- validation of the assembled `dist/codex/ai-software-architect` package;
- packaged short-lived hook-runtime smoke testing;
- provenance inventory and SHA-256 verification for every packaged file; and
- a repository scan for likely committed credentials, with only intentional
  synthetic test values found.

The package correctly contains no persistent MCP registration. These passing checks
are meaningful, but the adversarial probes below exercise behaviors not covered by
the current suite.

## Release Blockers

### RB-001: The exploratory runner can verify the wrong installed plugin

**Severity:** High  
**Impact:** Release evidence can claim that the release candidate was evaluated
while Codex actually loaded a different personal-marketplace package.

The published ZIP defines the marketplace
`ai-software-architect-release` in
`adapters/codex/templates/marketplace.json`, and the installation guide instructs
users to install from **AI Software Architect Release**. The exploratory runner,
however, queries only:

```text
codex plugin list --marketplace personal --json
```

and hard-codes `ai-software-architect@personal` in
`adapters/codex/evaluations/runner.py:37` and
`adapters/codex/evaluations/runner.py:239-240`.

If a stale personal copy and the packaged release copy both exist, the runner records
the personal version but cannot prove which same-named skill Codex executes. This
defeats the purpose of `-ExpectedPluginVersion` and the exact-candidate Gate C.

**Required remediation:**

- Query all installed plugins, not only the personal marketplace.
- Match the plugin by name and require exactly one enabled installation, or require
  an explicit expected plugin ID/marketplace for release evaluation.
- Fail before model calls when multiple matching installations are enabled.
- Record plugin ID, marketplace, version, sanitized package identity, and the
  reviewed provenance hash in release evidence without publishing a local user path.
- Add tests for personal installation, release-marketplace installation, missing or
  disabled installation, version mismatch, and duplicate enabled installations.

**Acceptance criterion:** A campaign installed from the release ZIP reports and
executes that exact marketplace plugin; a stale or duplicate personal installation
causes an actionable preflight failure rather than ambiguous execution.

### RB-002: Static-only repository inspection can be bypassed through shell composition

**Severity:** High  
**Impact:** Untrusted repository code can be executed during an architecture review,
contrary to the product's documented static-inspection boundary.

`adapters/codex/control_plane.py:58-88` uses deny-list regular expressions to
identify interpreters and executable files. The PreToolUse guard allowed both of
these commands in a directly reproduced active architecture context:

```powershell
& (Get-Command python) -c "print('repository code ran')"
Get-Item .\repo-tool.ps1 | ForEach-Object { & $_ }
```

For both probes, `tool_denial_reason(...)` returned `None`. Similar indirection can
be expressed through variables, aliases, script blocks, or other shell composition.
A deny-list regular expression cannot provide the advertised non-execution
guarantee for PowerShell or general shell syntax.

The impact remains bounded by Codex sandboxing, host permissions, and user approval;
this is not evidence of an operating-system sandbox escape. It is nevertheless a
release blocker because repository content is explicitly treated as untrusted and
the plugin promises that architect reviews do not run analyzed code.

**Required remediation:**

- Replace shell execution deny-listing with a fail-closed policy.
- Prefer native read tools. If shell reads remain necessary, allow only a small,
  parsed grammar of explicitly supported static-read commands and arguments;
  reject composition, call operators, pipelines into executable blocks, variables
  used as commands, nested shells, and unknown commands.
- Add adversarial tests for PowerShell call operators, variables, aliases,
  `Get-Command`, `ForEach-Object`, script blocks, pipelines, executable extensions,
  encoded commands, and nested command invocations.
- Keep ordinary Codex tasks unaffected when the architect control plane is inactive.

**Acceptance criterion:** Every supported static-read form has a positive test, and
representative direct and indirect execution forms are deterministically denied
before the shell tool runs.

### RB-003: Pre-write validation is not mandatory for every permitted architecture write

**Severity:** High  
**Impact:** Invalid, incomplete, or deleted architecture records can be persisted
despite claims that candidates are validated before one atomic write.

Three behaviors were directly reproduced:

1. An invalid ADR containing only `not a valid ADR` was allowed even with a valid
   workspace root; `handle_pre_tool_use(...)` returned `{}`.
2. The same invalid ADR was allowed when the hook payload omitted `cwd`, because
   `adapters/codex/hook_entry.py:311` runs artifact validation only when a workspace
   is present.
3. A patch deleting the contract, context, implementation plan, and ADR was allowed.
   `adapters/codex/artifact_guard.py:104-105` deliberately ignores delete sections,
   leaving no candidates to validate or verify after the mutation.

In addition, `validate_artifact_bundle_candidates()` returns without bundle
validation unless a contract and more than one artifact kind are present
(`adapters/codex/artifact_guard.py:205-206`). Consequently, a standalone invalid
ADR or an incomplete multi-file handoff can pass pre-write checks. PostToolUse can
stop the workflow after some inconsistencies, but it cannot make a completed
mutation atomic or undo data loss.

**Required remediation:**

- Deny all active architect writes when a trustworthy workspace root is unavailable.
- Validate every ADR's typed YAML frontmatter, including standalone updates.
- Require the complete four-type bundle for `record_and_handoff`; reject incomplete
  multi-file writes before mutation.
- Deny architecture-artifact deletion in the first release unless a separately
  specified, approved, and validated deletion workflow exists.
- Reconstruct the complete resulting document for Edit/Write operations rather than
  validating only a replacement fragment.
- Treat an empty or partially parsed patch candidate set as denial, not success.
- Add tests proving that invalid ADRs, missing workspace context, incomplete bundles,
  deletes, ambiguous patches, and partial edits are rejected before any file change.

**Acceptance criterion:** No permitted architecture write can occur without complete
pre-write reconstruction, secret scanning, applicable Pydantic validation, and the
required cross-artifact consistency check; destructive or unverifiable operations
are denied before mutation.

### RB-004: PreToolUse runtime failures explicitly fail open

**Severity:** High  
**Impact:** A hook parsing, state, environment, or size failure removes the
deterministic guard at precisely the point where a tool is about to execute.

`adapters/codex/hook_entry.py:504-505` rejects input over 1,000,000 bytes, while the
generic exception handler at `adapters/codex/hook_entry.py:516-525` emits only a
system message stating that the hook "failed open." It does not return a PreToolUse
denial. Missing `PLUGIN_DATA`, malformed state, unexpected payload variants, and
other runtime exceptions follow the same path.

The generated skill correctly says hooks are defense in depth and that correctness
must not depend on hook availability. However, the public plugin description and
release criteria also describe deterministic write and execution guardrails. A
known fail-open path must not be presented as mandatory enforcement.

**Required remediation:**

- Fail closed for active PreToolUse events whenever the guard cannot validate the
  request, including oversized input, missing required workspace data, malformed
  tool input, and internal validation exceptions.
- Keep fail-open behavior only where blocking would break unrelated, inactive Codex
  work and no architect-controlled tool is pending.
- Ensure diagnostics contain no prompt, repository, secret, or tool-argument content.
- Add subprocess-level tests for oversized and malformed hook inputs, missing
  environment variables, corrupt state, and internal validator exceptions.

**Acceptance criterion:** An active architect tool call is either explicitly allowed
after complete validation or explicitly denied; internal hook failure cannot be
interpreted as permission to execute the tool.

## Significant Public-Security Documentation Correction

`SECURITY.md:20` currently presents the optional Python STDIO MCP runtime as the
project's security model. The released Codex plugin does not register persistent MCP;
its active controls are the short-lived hook runtime, host-native static inspection,
typed artifact guard, and host sandbox/permissions.

Before public release, revise `SECURITY.md` to:

- describe the Codex hook runtime and its precise trust boundary first;
- describe `tools/python-mcp/` as optional and not registered by the Codex package;
- state which guarantees are mechanically enforced and which remain model
  instructions or host responsibilities;
- document failure semantics after RB-004 is resolved; and
- avoid implying that the optional MCP's read-only behavior protects normal Codex
  plugin execution.

This mismatch is not a separate exploit, but it materially affects informed hook
approval and vulnerability reporting and should be corrected in the same release.

## Positive Findings

No additional release-blocking issue was found in these reviewed areas:

- package file inventory and provenance hash validation;
- exclusion of persistent MCP registration from the Codex package;
- bounded short-lived runtime invocation and smoke testing;
- release bundle path confinement and checksum generation;
- canonical artifact path naming at the lexical level;
- secret scanning for reconstructed artifact content; and
- deterministic comparison rendering and exploratory fixture infrastructure.

These positive findings do not override the four blockers above.

## Go/No-Go Recommendation

Do not publish `v0.1.0` until RB-001 through RB-004 are fixed, regression-tested,
and rerun through the deterministic package gates and all five exploratory fixtures.
Afterward, complete the clean-machine and first-attempt uninstall gates and update
the public security model before making the repository and release public.
