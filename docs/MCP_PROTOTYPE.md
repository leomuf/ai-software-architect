<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Phase 0: anonymous stateless MCP prototype

Revised direction, 2026-11-03: the user's preference for a public service without
accounts/tokens supersedes the original server-side review/identity design.
Workflow and checkpoints remain client-local. The
[implementation plan](plans/2026-11-03-mcp-skills-privacy-and-distribution.md) now
incorporates this direction for the primary hosted delivery; this document records
the implemented prototype and its limits.
This is an experimental, synthetic-only prototype, not a deployed public endpoint,
an accepted-persistence workflow, or a migration go decision.

## Responsibility and privacy contract

| Client / host model | Anonymous MCP service |
| --- | --- |
| Workflow choice, clarification, architectural reasoning, comparison, review and report | Versioned canonical references and templates |
| Local checkpoint files, active review selection, short-reply continuation | Capability discovery, with no project context |
| Local candidate drafting and revision | Complete self-contained proposed-bundle validation and exact-byte inline export |
| Native file permissions and explicit artifact installation | No repository reads/writes, review storage, approval or commit capability |

No registration, login, account, access token, workspace enrollment or review ID
is required by the service. MCP transport is stateless; no sessions are issued.
The server stores no reviews, checkpoints, candidates, export results, project
payloads, approval records or retry history. It has no workflow database, backups,
model calls, telemetry or outbound requests. Only trusted bundled references are
read at startup. HTTP responses are not cached. Operational counters hold at most
1,024 remote IPs for a one-minute rate window; expired entries are removed on the
next request and all counters disappear when the process exits. No project content
is included.

**No storage does not mean no transfer.** Draft validation sends all supplied
artifact text to the server for transient processing in memory. The skill must
explain that boundary and obtain permission to transmit it. Reference-only usage
requires no project data. Users who decline transfer can keep using references
or explicitly run the same service locally; never silently switch deployments.
The selected host/model has a separate data flow. Secret detection after receipt
is best-effort and cannot prevent arbitrary host disclosure before transmission.

Project bodies must not enter proxy logs, tracing, caches, crash reporting or
backups in a later deployment. The application disables access/payload logging,
sanitizes errors and does not trust forwarded client/scheme headers. Public cloud
hosting and its infrastructure policies remain a later deployment gate.

## Frozen protocol and limits

- Locked Python SDK `mcp==1.30.0`, protocol `2025-11-25`, Streamable HTTP with
  structured object results and an exact JSON text fallback. All remote input
  schemas use object envelopes without `anyOf`, `allOf` or multi-type parameters.
  Canonical artifact checks remain enforced behind these wire schemas.
- Tool contract `0.1.0`, artifact schema `1.0.0`, reference snapshot SHA-256. The
  local checkpoint pins the snapshot version. Writes to the service do not exist.
- `get_architecture_capabilities`, `get_architecture_resource` and
  `prepare_architecture_bundle` are the complete anonymous tool surface. They are
  read-only and naturally retry-safe; no idempotency key or server revision is used.
- The preparation tool validates and exports in one call. It never returns a
  server candidate handle or accepts a checkpoint/approval/tenant argument.
  Repeating the same self-contained request yields the same result across workers
  or restarts with the same contract/reference snapshot. Changed bytes require
  fresh validation; earlier hashes do not validate later modifications.
- Preserve the accepted `ArchitectureArtifactBundle` contract. A separate
  `DraftArchitectureArtifactBundle` requires only proposed ADRs and checks complete
  contract/context/ADR/handoff, canonical paths, duplicates, filename/ID alignment,
  cross-artifact references and likely secrets through the same portable core as
  the legacy hook adapter. Semantic quality remains the host model's responsibility.
- Export returns exact submitted UTF-8 text, paths, byte sizes, hashes and digest.
  Status is always draft; acceptance and customer-local persistence are unverified.
  The server cannot attest prior workflow order, freshness against a different
  local candidate, human acceptance, or the contents of customer-local files.
- 256 KiB raw request, JSON depth 32 before parsing, YAML depth 50 during parsing,
  at most 8 files / 64 KiB total artifact bytes, 128 KiB full tool response including
  structured data and text fallback. Oversized results fail explicitly.
- 60 HTTP requests/minute per remote IP per worker. This is a bounded prototype
  limit, not distributed anti-abuse infrastructure. HTTPS and exact Host/Origin
  validation are required outside explicit loopback-only HTTP testing.
- Failures use `isError: true`, structured `ok: false`, stable codes and repair
  hints. Never serialize framework/parser exceptions, request values or secrets.

## Local workflow and checkpoint contract

The generated Composite guides native client file tools to store checkpoints in
`.ai-architect/.mcp-workflows/<local-review-id>.json` when a stateful review needs
continuation. `LocalWorkflowCheckpoint` is the canonical client-local schema,
also retrievable as `protocol/local-workflow-checkpoint.schema.json`. It is never
accepted by an MCP operation. Users control local retention/deletion; checkpoints
are plaintext, not verified approval receipts. No local helper/runtime installation
is required for a host that already has native file tools.

The host reads the latest local revision before updates and avoids overwriting
unexpected edits. It owns active/clarification/analysis/prepared/exported/cancelled
transitions, proportional skips, three rounds of up to five questions, rejection
and digest invalidation. These are instruction-guided client behaviors, not server
enforcement. After context loss, discover local checkpoints and ask if multiple
reviews match. Without local files or their permissions, disclose the absence of
durable resume; never upload the checkpoint to compensate. Short replies in any
language must bind to the selected local review, not to an MCP session.

## Run and verify

From the repository root:

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.uv-cache'
uv sync --locked --all-packages
.\scripts\run-mcp-prototype-evaluations.ps1
```

The dedicated runner generates the one-Composite instruction package and writes
`report.json`, `SUMMARY.md`, `junit.xml` and schema snapshots beneath
`.tmp/mcp-prototype/<timestamp>/`. It exercises actual loopback HTTPS with an
ephemeral trusted test certificate. It never updates the legacy exploratory ledger.
Reported test-case P50/P90 is not host-model or tool-call latency.

For a foreground, anonymous loopback experiment:

```powershell
uv run --locked python -m adapters.mcp.build_instructions --output .tmp/mcp-prototype/skill
uv run --locked ai-architect-mcp-prototype --resources shared/skills --public-url http://127.0.0.1:8765/mcp --allow-loopback-http
```

Stop with Ctrl+C. Restarting requires no workflow data or database. To serve HTTPS,
use the exact HTTPS `/mcp` URL and replace `--allow-loopback-http` with
`--cert <certificate.pem> --key <private-key.pem>`. Use a client-trusted certificate;
the default bind is `127.0.0.1`. External test exposure needs an explicitly selected
bind/ingress and TLS. The prototype does not implement trusted reverse-proxy TLS
termination. Never expose the HTTP test mode beyond loopback.

Codex configuration for the loopback test needs only:

```toml
[mcp_servers.architect_prototype]
url = "http://127.0.0.1:8765/mcp"
```

Claude's equivalent manual configuration is:

```json
{"mcpServers":{"architect_prototype":{"type":"http","url":"http://127.0.0.1:8765/mcp"}}}
```

Use a disposable host profile with the legacy Architect hooks/plugin disabled and
load the generated Composite `SKILL.md`. No auth setting or secret is needed.
These are setup candidates, not proof of successful live-host continuation.
See [official Codex MCP configuration](https://developers.openai.com/codex/mcp)
and [Claude HTTP setup](https://code.claude.com/docs/en/mcp).

## Evidence and migration gate

### Isolated real Codex host diagnostic

Use the separate entry point for the synthetic two-phase host fixtures:

```powershell
.\scripts\run-codex-mcp-host-evaluation.ps1 -Model <available-cli-model> -ReasoningEffort xhigh -Speed standard
.\scripts\run-codex-mcp-host-evaluation.ps1 -Model <available-cli-model> -ReasoningEffort xhigh -Scenario context-loss
.\scripts\run-codex-mcp-host-evaluation.ps1 -Model <available-cli-model> -ReasoningEffort xhigh -Scenario two-active-reviews
```

Select an explicit model from the installed CLI's `codex debug models` catalog;
the desktop configuration and an older standalone CLI can expose different
catalogs. A catalog entry is not proof of account entitlement: the real inference
call must succeed. The runner never substitutes a model silently. The exact CLI,
model, effort, speed, fixture, instructions, reference snapshot and per-phase
budgets are frozen before the first model call. Defaults are 600 seconds and 50
observed tool calls per phase; the runner stops a process after an observed budget
violation. This is a diagnostic, not an agreed statistical latency budget.

The runner creates a temporary Codex home, disables hooks, plugins, apps,
subagents, bundled skills and discovered external skills, and configures only the
anonymous loopback MCP endpoint. It builds the Composite into the synthetic
workspace's native skill directory. It reuses the existing Codex host login in
the private OS temporary directory and removes that copy afterward; no credential
is placed in prompts or the evidence directory. The MCP endpoint still needs no
account or token. Normal user configuration and the installed plugin are unchanged.

The first phase compares the supplied synthetic design and saves a local
checkpoint. The default `local-review-export` scenario resumes the exact CLI chat
with a natural short reply without another skill mention or corrective operator
prompt. `context-loss` starts a new CLI chat, with the same local files but no
resumed transcript, and explicitly activates the skill again. This simulates loss
of conversation context; it does not force the client's compaction mechanism or
restart the service. `two-active-reviews` also uses a new chat and adds a separate
CSV-import checkpoint before continuation. That distractor is explicitly
runner-seeded, validated against the canonical schema and frozen before the first
model call; it is not evidence that the model created a second review. The user
prompt selects the UI/domain review by topic, without supplying its local ID.

Deterministic checks inspect the
native checkpoint read, actual MCP validation result, exact delivered JSON file,
checkpoint revision/digest and workspace changes. Recovery scenarios require
distinct chat IDs. Two-review checks require exactly the expected checkpoint set,
the selected review's updated revision/digest and the other review's unchanged
bytes. Semantic review must also confirm that the exported decision concerns the
selected topic. Model prose alone cannot pass.
Local checkpoint IDs/paths and internal workflow history must also be excluded
from outgoing artifact text, including evidence citations. This rule is host
guidance; the service cannot prevent transmission of arbitrary free text before
receipt. The ID-absence check is a narrow diagnostic signal requiring separate
semantic review.
Failed/aborted attempts remain separate evidence; API/startup failures are not
semantic workflow failures or successful legacy runs.

Evidence under `.tmp/mcp-host/<timestamp>/` includes `frozen-run.json`, `report.json`,
`SUMMARY.md`, the generated workspace/skill, client JSONL, phase timings and
sanitized-profile/model-catalog metadata. These synthetic client-side test records
are distinct from the service, which does not store project content or log payloads.
The diagnostic uses loopback HTTP; it does not establish remote HTTPS compatibility.

A successful deterministic result is `manual-review`: architectural quality,
report completeness, evidence limits and absence of false approval/persistence
claims still need semantic review. It cannot complete the repeated multi-host
migration gate or enter `evaluation-data/exploratory-runs.jsonl`. The maintained
legacy exploratory entry point remains unchanged.

The server negotiates the profile's fixed MCP version `2025-11-25` during
initialization, even when a newer client offers another version. Subsequent
explicit protocol headers must match the selected version. This normalizes only
handshake metadata, never artifact/tool arguments. See
[MCP version negotiation](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle)
and the official [Codex CLI](https://learn.chatgpt.com/docs/cli/reference) and
[configuration](https://learn.chatgpt.com/docs/config-file/config-reference) references.

### Broader migration evidence

One real Codex CLI comparison/checkpoint/short-reply/export diagnostic now passes
its deterministic checks. The separate agent semantic review, measurements and
preserved startup/API failures are recorded in
[the 2026-11-03 diagnostic](mcp-prototype/codex-host-diagnostic-2026-11-03.md).
This does not mark the repeated host-reliability cohort as passed.
New-chat recovery and two-review diagnostics, including a preserved local-ID
disclosure failure and the resulting instruction clarification, are recorded in
[the 2026-11-05 recovery record](mcp-prototype/codex-recovery-diagnostics-2026-11-05.md).

The cohort `mcp-phase-0-anonymous-stateless-deterministic` tests actual tools/list,
call envelopes, HTTPS, no-login usage, retry/restart equivalence, exact bytes,
invalid candidates, malformed/deep/oversized input, sanitized errors, poisoned
text as data, multiple workers and no project file writes/state history. Generated
packaging checks one public Composite, six canonical modules, 23 individually
addressable GoF references, local links and provenance. The shared protocol
overrides canonical modules' accepted-record/hook/persistence wording in this mode.

Gate: **no-go for full migration pending real-host evidence**. Local checkpoint
validation and multilingual strings do not prove model continuation. Run isolated
Codex and Claude (or Copilot) cohorts with fixed versions/model/reasoning/speed,
prompts/rubric and an agreed numerical latency budget before scoring. Require five
repetitions per diagnostic and at least 19/20 full exports and 19/20 correct short
continuations per host, with zero fabricated verified approvals, false persistence
claims or other critical host failures. An independent acceptance channel remains
unavailable; the advertised profile must stay draft-only.

The unscored diagnostic prompts and evidence rubric are versioned in
[the separate host cohort](../shared/evaluations/mcp-prototype/scenarios.yaml).

Foundry live discovery, anonymous access and a nested tool call still require a
provisioned cloud agent and reachable HTTPS endpoint. Schema inspection alone is
not a Foundry pass. All six host targets and Windows/macOS/Linux compatibility
cells remain planned; native Windows deterministic HTTPS is the implemented
transport evidence. Public hosting, directory submission and all client/version/
model workflow cells remain separate work.

| Old hook responsibility | New owner | Residual limit |
| --- | --- | --- |
| Prompt routing | Composite and local checkpoint | Host may omit activation/recovery. |
| Pre-write guard | Shared stateless bundle validation | Other host tools cannot be intercepted. |
| Post-write verification | Exact-byte response manifest | Local files remain unverified by server. |
| Compaction recovery | Native local checkpoint reads | Lost local state cannot be recovered remotely. |
| Stop/report completeness | Host instructions | Final prose cannot be enforced by MCP. |
