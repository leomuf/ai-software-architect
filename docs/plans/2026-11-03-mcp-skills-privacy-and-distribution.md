<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Implementation plan: MCP, skills, privacy, and distribution

Date: 2026-11-03

Status: Updated to the agreed anonymous, stateless service; prototype implemented,
with real-host and production migration gates still open.
This plan describes intended delivery; it does not itself deploy or publish a service.

## Agreed change during implementation (2026-11-03)

The user selected a **public, stateless MCP service without registration, an
account, login, or access token**. **Workflow and checkpoints remain local to the
user's host; our service stores no reviews or candidates.** This decision applies
to the primary hosted delivery, not only to a temporary prototype exception.

It supersedes this plan's earlier hosted identity/workspace enrollment, workflow
database, server-side review/checkpoint APIs, candidate storage, approval records,
and controlled remote persistence design. Optional customer-managed access
controls are a separate deployment choice and must not become a requirement for
using the public endpoint.

The host model owns interviews, analysis, decisions, local continuation and
checkpoint revisions. The service provides capability discovery, versioned
references, and self-contained complete draft-bundle validation with exact-byte
export in the same call. It does not issue workflow/session IDs or retain export
handles, candidate history or idempotency records. Client-local checkpoints must
never be uploaded as a substitute for local persistence.

Project artifacts sent for validation are processed transiently in memory;
**no persistent storage does not mean no transmission**. Reference-only use
requires no project context. Short session duration is not the isolation model:
there is no shared retrievable customer state or API for another user's data.
Bounded in-memory operational rate counters are separate from project content;
public hosting must exclude payloads from logs, caches, traces and crash dumps.

The implemented prototype contract and evidence limits are recorded in
[MCP_PROTOTYPE.md](../MCP_PROTOTYPE.md). Its separate deterministic cohort passed
25 checks, including loopback HTTPS; the full regression suite passed 425 tests.
These results do not establish public availability, live host-model reliability,
Foundry compatibility, verified human acceptance or customer-local persistence.

## Implementation-readiness review

Review date: 2026-11-03. The bounded anonymous/stateless prototype is implemented;
phase 0's real-host migration gate is still open. **Do not proceed directly to the
full migration.** Validate the host-model interaction and resolve the following
gates before expanding the service. Protocol compatibility alone cannot establish
workflow reliability:
[MCP defines tools as model-controlled](https://modelcontextprotocol.io/specification/2025-11-25/server/tools),
without mandating a particular user interaction model.

| Risk | Required resolution | Gate |
| --- | --- | --- |
| P1: Models may omit calls, lose continuation, or claim completion without validation. | Run the phase 0 vertical slice in real hosts, including adversarial and interrupted workflows, with predeclared pass/fail criteria. | Before phases 2–6 expand beyond the prototype. |
| P1: A normal MCP call does not establish that a human approved a particular bundle. | Prove an independent approval channel, or explicitly limit that profile to draft export without verified acceptance/persistence. Separate decision acceptance, data-transfer consent, and permission to write. | Before advertising approved artifacts or enabling controlled persistence. |
| P1: A hook-free, configuration-only adapter cannot enforce redaction of arbitrary model-supplied free text before transmission. | Identify the actual host-side disclosure control or classify it as instruction-guided; offer reference-only/local modes when stronger prevention is required. | Before accepting real customer project data or making prevention claims. |
| P1: An anonymous service must not retain or expose customer payloads across calls. | Reuse portable complete-bundle checks, keep request data call-local, and verify concurrent response isolation, no project storage/caching/logging, bounded processing, retries and sanitized failures. | Before a hosted pilot with customer data. |
| P2: Six hosts, three OS families, three deployment modes, and multiple directories obscure the feasibility experiment. | Preserve them as delivery targets, but test Codex plus one other coding assistant first; probe Foundry schemas and anonymous endpoint access early. | Before broad adapter and distribution work. |

The unresolved decisions at the end of this plan are not all harmless deferrals.
Anonymous access and client-local workflow state are decided, not open identity or
storage choices. Deployment-level no-retention evidence, local checkpoint behavior,
wire/version contracts and approval limits still gate their advertised capabilities.
Provider selection and directory publication must not delay the synthetic experiment.

## Objective and agreed direction

Deliver AI Software Architect primarily as an **externally hosted, anonymous,
stateless MCP server** with reusable architecture skills and thin integrations
for Codex, Claude Code, GitHub Copilot, Google Antigravity, Cursor, and Microsoft
Foundry. Customers must
be able to call the hosted service from **Windows, macOS, and Linux** through
supported assistant/client surfaces. Support other MCP-capable assistants through
the same protocol and thin adapters where needed; the named list is not a closed
architecture boundary. Select the hosting provider and implement the service as
part of this work. Keep architecture reasoning in the customer's selected
assistant/model. Do not require a separate model API key or assume MCP Sampling
support across clients. Connecting to our public service requires only its URL,
without an account or token. Keep workflow, analysis and checkpoints in the user's
host environment; the service must not acquire a project-state database later as
an implicit continuation of this plan.

Minimize disclosure of codebase information to infrastructure operated by AI
Software Architect. A complete repository upload must not be a prerequisite.
Also provide an optional local deployment that customers download from the public
[GitHub repository](https://github.com/leomuf/ai-software-architect) and run on
their own computers. Plan optional customer-managed network hosting for cloud
clients too. These are additional deployment choices using the same shared core.

Target OpenAI's public plugin directory with the remote HTTPS MCP endpoint and
accompanying hook-free skills. The GitHub download/run option is a separate manual
distribution path; no local MCP package submission to OpenAI is planned. Also
target discovery through mcpservers.org and distribution for Foundry Tools,
Claude Code, GitHub Copilot, Antigravity, and Cursor. Technical compatibility and
acceptance into each external catalog are separate deliverables. Manual remote
endpoint configuration remains a supported onboarding route when a catalog listing
is unavailable or pending.

The prototype does not complete the future delivery work. Keep the current
hook-based adapter, existing release work, and current public availability
statements unchanged while the alternative is evaluated. Update the living specification and acceptance
criteria before intentionally changing product guarantees.

## Boundaries and expected behavior

The intended architecture workflow remains: clarify significant requirements,
inspect bounded static evidence when needed, compare credible options, present a
decision, obtain approval, prepare the ADR/contract/context/handoff bundle, and
review conformance. Preserve proportionality, multilingual continuation, focused
help without repository inspection, and the existing artifact formats.
The public profile delivers proposed drafts with acceptance unverified. Any
accepted record and local installation require a separately authorized native
host workflow; the service does not certify either outcome.

A server can enforce validation within its own call. This service deliberately
does not persist customer workflow state. It cannot generally intercept every
host tool, receive every user message, restore context
automatically after host compaction, or prevent a host from ending its response.
Do not advertise a hook-free implementation as an identical replacement for all
current host-level controls.

## Operating-system and assistant compatibility goals

These are implementation requirements, not claims of support already verified.

### Required customer operating systems

| ID / customer OS | Hosted-service requirement | Verification boundary |
| --- | --- | --- |
| OS-01 Windows | The same anonymous remote HTTPS MCP endpoint and architecture workflows are usable from a supported Windows client. No Windows-specific server build or bundled executable is required for hosted use. | Test the named client/version, access without login/token, tools, local checkpoint continuation, and exported artifacts on Windows. Record native versus WSL execution explicitly. |
| OS-02 macOS | The same endpoint, contracts, privacy choices, and workflows are usable from a supported macOS client. | Test the named client/version, anonymous access, tools, local checkpoint continuation, and exported artifacts on macOS. |
| OS-03 Linux | The same endpoint, contracts, privacy choices, and workflows are usable from a supported Linux client. | Test the named client/version, anonymous access, tools, local checkpoint continuation, and exported artifacts on Linux; record the distribution used. |

The server's hosting OS is independent of the customer's OS. Keep the public
protocol, hosted onboarding, and core domain free of dependencies on a customer's
PowerShell, Bash, drive letters, or local executables. Use platform-neutral
resource IDs and artifact-relative paths. Test spaces, Unicode, separators,
case-sensitive paths, and line endings with synthetic fixtures; do not interpret
a customer-local path as a readable path on the hosted server.

All three customer OS families are fixed targets. Exact OS versions and CPU
architectures still need a maintained support matrix. The optional GitHub-run
server has its own installation/lifecycle matrix for Windows, macOS, and Linux;
hosted client compatibility does not prove that local installation works.

### Required assistant and platform targets

| ID / target | Initial surface to configure and validate | Adapter responsibility |
| --- | --- | --- |
| HOST-01 Codex | Supported desktop, CLI, or IDE surfaces, recorded separately; remote public-directory package is the primary distribution. | Composite skill, focused references, remote configuration, activation and continuation. |
| HOST-02 Claude Code | Supported CLI/editor surfaces, recorded separately. | Shared entry workflow, anonymous remote MCP configuration, instruction/reference loading, local checkpoints and host-local review/approval limits. |
| HOST-03 GitHub Copilot | VS Code and CLI first; other Copilot surfaces require their own validation. | Shared workflow as supported skills/instructions, remote configuration and per-surface capability handling. |
| HOST-04 Google Antigravity | IDE and CLI first where available; do not infer app/SDK compatibility from either. | Thin Antigravity configuration and skill/rule projection from shared sources, anonymous endpoint access, activation and local continuation. |
| HOST-05 Cursor | IDE first, then CLI where available; cloud agents are a separately validated surface. | Thin Cursor configuration and skill/instruction projection, anonymous endpoint access and client-local evidence/approval handling. |
| HOST-06 Microsoft Foundry / Foundry Tools | Foundry agent calling the remote service; SDK/portal setup and private-network profile tested separately. | Agent instructions, supported schemas, anonymous tool attachment, reference retrieval and customer-controlled checkpoint storage. |

These six named targets are planned deliverables, including Antigravity, Cursor,
and Foundry. For each desktop/CLI target, enumerate Windows, macOS, and Linux
cells and the vendor-supported surface available in each. If a vendor does not
provide that surface on an OS, record the constraint and assess another supported
surface; an adapter cannot manufacture a missing vendor application. Keep an
unresolved cell visible rather than silently dropping it or claiming a pass.
Foundry executes the agent in the cloud: customer OS coverage concerns access
and setup, while MCP/schema/workflow validation occurs against the cloud agent.
For a cloud host, client-local means the customer's host/storage environment,
never our MCP infrastructure. Verify its actual durable storage capability; when
absent, disclose that durable resume is unavailable instead of uploading state.

Maintain a versioned compatibility record with target, surface, client version,
customer OS/execution environment, model, transport and anonymous access, instruction
loading, supported capabilities, known limits, test evidence, and status
(`planned`, `verified`, or `blocked by host capability`). A working tool call alone
is not a complete workflow pass. Mark a target verified only after onboarding,
clarification, comparison, decision/bundle export, conformance, and continuation
scenarios pass with its documented capability limits.

### Shared adapter contract and additional assistants

Use one hosted MCP service and one shared semantic/domain core for every target.
An adapter may supply anonymous endpoint configuration, schema projection,
workflow instructions, tool-name mapping, reference loading, or output rendering.
Configuration-only integration is sufficient where it satisfies the contract;
do not build a separate architecture engine or server for each assistant.

Keep all six canonical workflow modules host-neutral. Native skills are one
delivery mechanism; agent instructions/rules plus selective reference retrieval
must support hosts without equivalent automatic `SKILL.md` activation. Core
workflows cannot depend on hooks, MCP Sampling, MCP Apps, or Skills over MCP.
Handle optional capabilities progressively with explicit fallbacks and limits.

The onboarding checklist for another assistant is: verify its current remote MCP
without login/token requirements, add a thin configuration/instruction projection,
validate schema and reference delivery, run the same workflow/OS scenarios, and
publish its tested configuration and limits. Include Gemini CLI as an additional
compatibility candidate using its documented remote MCP configuration; assess
further major clients as the ecosystem changes. New clients should not require
changes to architecture reasoning or weakened privacy/security contracts.

## Hook responsibilities and host limits

| Current hook | Intended replacement | Remaining host dependency |
| --- | --- | --- |
| `UserPromptSubmit` | Client-local workflow start/resume and checkpoint files; a skill describing when remote validation is needed. | Activation, local file permissions and routing of subsequent replies. |
| `PreToolUse` | Enforce permissions, candidate validation, secret scanning, and path boundaries inside our artifact operation. | Independent shell, web, and application-code tools are outside this server's control. |
| `PostToolUse` | Validate/export exact submitted bytes in one stateless call; any local apply/verification is a separate native host action. | The service cannot verify customer-local files. |
| `PostCompact` | Read the user's client-local checkpoint rather than reconstructing it from memory. | The assistant must find the correct local workflow; the service cannot recover lost files. |
| `Stop` | Model-owned complete report and accurately labeled local completion/export state. | The service does not enforce workflow order or final prose. |

## Deployment modes and data boundaries

| Mode | Execution and storage | Project-data boundary |
| --- | --- | --- |
| Primary externally hosted service | Anonymous stateless service at a stable HTTPS endpoint; provider/region/compute to be selected, with no customer-state store. | Reference-only access needs no project context. Complete draft validation processes deliberately submitted artifact bytes transiently; no reviews, candidates, checkpoints, export history or approval records are retained. |
| Optional local, downloaded from GitHub | Customer machine; native host-local checkpoints and separately authorized `.ai-architect/` artifact installation. | No project-content requests to our infrastructure; no runtime telemetry, cloud fallback, account, or license-server dependency. |
| Optional customer-managed service | Customer-controlled server/cloud running the same stateless core; customer-selected network access controls if needed. | Workflow/checkpoints stay in the customer's host/storage environment. Private access controls do not introduce accounts/tokens into our public service or authorize our infrastructure to retain state. |

### Primary hosted delivery and user experience

- Operate an anonymous, stateless Streamable HTTP MCP endpoint over HTTPS, without
  login, account, access token or workspace enrollment. Hosting is required;
  provider, region, compute, costs and operational controls remain open. A
  project-state database is excluded, not a deferred storage-provider choice.
- Package the endpoint configuration and shared skills for the supported hosts.
  The normal hosted workflow must work without installing our local MCP server,
  Python, `uv`, hook scripts, or a platform-specific runtime binary.
- Keep source inspection in the customer's assistant execution environment using
  supported bounded static capabilities. Any optional deterministic local parser
  must not become an undeclared dependency of the public hosted package. Disclose
  evidence limits when that capability is unavailable.
- Implement capabilities, references and complete draft validation/export, not
  merely a documentation endpoint. Keep interviews, analysis, workflow transitions,
  revisions and checkpoint storage in the host; do not expose remote submission,
  review recovery or candidate-storage APIs. No persisted project retention is
  permitted; audit transient processing and every infrastructure log/cache layer.
- Offer a reference-only use of the hosted service for customers who decline
  project-data transfer. Explain which workflow features then remain model-guided
  or require an explicitly chosen local/customer-managed deployment.
- Deliver validated architecture bundles through export by default. Applying
  those files on a customer's computer is a separate host/user action with its
  own permissions; export success must never be reported as verified local
  persistence. There is no public MCP commit tool or approval store. Any future
  controlled local apply capability needs its own tested native permissions and
  approval mechanism. No repository write token is a hosted prerequisite.
- Reuse the remote endpoint across compatible clients on Linux, macOS, and Windows.
  Test each advertised host/OS combination; distinguish endpoint compatibility from
  availability of a particular desktop app. Per-OS native builds are unnecessary
  for this hosted distribution.

### Optional local GitHub download and execution

This option remains planned for customers who want to run the service themselves.
Its installation and lifecycle requirements are independent of the remote public
submission. A local-directory submission or local-MCP partner allowlisting is not
a prerequisite or milestone for the chosen remote submission path.

- Provide a versioned source archive and a clone/checkout path using an immutable
  release reference. Keep source, dependency lock, license, and notices available.
- Document prerequisites and installation separately from runtime. Setup may need
  to download dependencies; do not describe that as an offline installation.
- Use the locked `uv` workspace for the source installation. Validate the exact
  user commands in a clean environment before publishing them in the README.
- Make the existing `ai-architect-mcp` entry point the starting point for local
  transport work, not evidence that the new workflow already exists.
- Prefer client-managed STDIO where lifecycle tests pass. Evaluate loopback HTTP
  only where needed; bind to loopback, document access controls, and avoid exposing
  a local server to the network by default.
- Give users copyable client configurations with explicit executable path,
  working directory, workspace permissions, state location, and startup behavior.
- Test start, idle, restart, reconnection, upgrade, uninstall, and state cleanup.
  Resolve the previously observed Codex retained-process/cache-lock and closed-
  transport problems before making local Codex compatibility claims.
- Document what the customer must install, start, update, and stop. Do not install
  the service automatically or silently switch to our remote endpoint.
- Support local export/persistence without a GitHub account, GitHub write token,
  or permission to push. Downloading from GitHub does not imply storing customer
  artifacts on GitHub.
- Advertise each OS/architecture only after its source-installation and lifecycle
  tests pass. Existing Windows package support does not establish support for a
  new MCP distribution or for macOS/Linux.
- The planned source-based Python distribution and hosted service do not ship our
  own native executable and do not require us to obtain a binary code-signing
  certificate. PR #48 and the legacy binary-signing work are not prerequisites
  for this migration. If native executables/installers are introduced later,
  reassess platform signing for that separate distribution. HTTPS certificates
  for remote transport are a separate operational concern.

### Data minimization

- Keep source inspection, deterministic dependency extraction, and source/secret
  checks in the customer execution environment whenever possible. Parse code
  statically; never execute the analyzed application to inspect its architecture.
- The initial centrally hosted surface must not expose the existing raw-source
  `source_files` or import-statement inputs as remote analysis tools. Keep those
  capabilities local/customer-managed until a separate data-flow decision exists.
- Offer reference retrieval without project context. Complete draft validation is
  the only primary hosted operation accepting project artifact content; disclose
  that transfer and require a deliberate customer choice. Requirements, analysis,
  module relationships and conformance history stay client-local. Additional
  project-input operations require a separate scope/data-flow decision.
- Treat graphs, names, requirements, findings, and ADRs as potentially confidential,
  even when they contain no source code. Avoid calling them anonymous by default.
- Keep durable workflow and checkpoint state client-local. The public transport
  issues no persistent session ID; short session duration is not a substitute for
  isolation. Do not upload checkpoints, analysis history or full chats to resume.
- Avoid project data in application/access logs, crash reports, metrics, URLs,
  third-party observability, caches, crash dumps and backups. No project content,
  review/candidate/approval record or retry result may be persisted by our service.
  Document any bounded operational metadata separately and test its lifetime.
- Use narrow schemas and client-side disclosure controls. A server rejection
  after receiving source text does not undo the transfer. Free-text fields can
  still contain sensitive content, so do not promise zero disclosure based only
  on schema names or instructions to the model.
- For every host, name the component that inspects the exact outgoing arguments
  before transmission and test whether it can be bypassed or auto-approved.
  A skill instruction, server-side scope check, or server-side secret scan is not
  such a component. If the host provides no enforceable control, label minimization
  as instruction-guided and require deliberate opt-in to that residual risk.
  Where the host supports a per-tool allowlist, reference-only configuration must
  omit the artifact-validation tool rather than merely hide it in prose. Without
  enforceable host filtering, disclose that reference-only behavior is instruction-
  guided on a public endpoint. Allowlisted reference IDs accept no project context;
  anonymous access does not provide a per-user permission tier.
- If an operation needs data that the customer declined to share, return a clear
  limitation or use the local capability; never silently broaden collection.
- Test per-request input/response isolation and absence of shared customer state
  on the anonymous service. Apply native workspace/file permissions to local
  checkpoints; keep private customer-managed access controls separate.
- Do not claim independently source-verified findings when our server only
  received summaries or locally produced evidence. Preserve provenance and limits.

The selected assistant/model has a separate data flow. Running our MCP server
locally does not imply that code read by a cloud-based model stays on the device.
The strict local product promise concerns our components and infrastructure, not
uncontrolled host tools or a separately selected model provider.

## Shared implementation structure

Reuse `shared/skills/`, `shared/schemas/`, shared evaluations, and the deterministic
domain functions under `tools/python-mcp/`. Keep workflow/checkpoint contracts
client-local and pure reference/validation operations separate from native file
handling. The anonymous HTTP core must not depend on a workflow database or
project-payload cache. Optional transports reuse the deterministic rules, with
explicit mode-specific capabilities. Avoid duplicating architecture knowledge.

### Existing-code extraction boundary

The current `tools/python-mcp/src/ai_architect_tools/mcp_server.py` exposes four
local, read-only tools. It has a 15-second idle self-reaper and a process-global
200-call budget. Neither belongs in a shared HTTP worker: one idle interval or
customer's calls must not terminate service for other customers. Create separate
transport entry points with explicit lifespan and anonymous per-IP/request limits;
reuse domain functions, not the local process wrapper or its global state.

Complete-bundle validation originated in `adapters/codex/artifact_guard.py` and
`artifact_paths.py`, beyond the individual contract/scanner tools. The prototype
extracts portable path-kind, completeness, ADR filename/ID, cross-artifact and
secret checks into `ai_architect_tools.domain.artifacts` and `artifact_paths`.
Keep host patch reconstruction and filesystem binding in adapters. The existing
hook adapter and new MCP preparation must continue to share these rules, with
legacy regression fixtures.

`adapters/codex/continuation.py` stores hook/session-specific checkpoints. Reuse
its continuation requirements in the client-local `LocalWorkflowCheckpoint`
contract, not in a new hosted store. Local IDs/revisions coordinate native host
files; they do not authorize the server or attest approval. Without a host-local
read/write capability, disclose that durable continuation is unavailable.

### Anonymous stateless operation surface

The prototype exposes three operations. Preserve this small, self-contained
surface for the primary hosted profile; future additions require an explicit
contract/data-flow review.

| Operation | Purpose |
| --- | --- |
| `get_architecture_capabilities` | Disclose anonymous access, no project retention, client-local workflow, supported versions, limits and draft-only export capability. |
| `get_architecture_resource` | Retrieve one identified, versioned workflow reference/template or catalog without project context; allowlisted IDs and bounded content. |
| `prepare_architecture_bundle` | Validate a complete self-contained proposed bundle and return its exact bytes and manifest as a draft export in the same response, without retaining the candidate. |

Preparation owns complete cross-artifact validation and inline draft delivery in
one operation. There is no separate remote export handle, repository commit,
review creation/list/resume/cancel/delete, or clarification/analysis/conformance
submission API. Those workflow activities stay in the host. Do not create a
generic code-execution layer or one tool per internal validator/hook.

No account-scoped read/prepare/export permissions are needed for these public,
read-only operations. Data-transfer permission and native filesystem permissions
are host/user responsibilities. A public tool-call permission dialog does not
establish verified human acceptance. Reject invented approval, tenant, review,
checkpoint or revision arguments rather than treating them as authority.

Return bounded structured results and sanitized errors with a stable constraint
code, retryability and repair hint. Optional local inspection/apply capabilities
require a separately documented host-native boundary; they must not appear in
the primary public surface or turn export into a local persistence claim.

### Approval and export semantics

Standard MCP invocation and annotations do not provide a server-verifiable human
approval receipt. Automatic host tool approval and a model's transcript quotation
are not that receipt. The anonymous service has no human confirmation surface or
approval store and must remain **validated draft export only**. An independent
future host-local acceptance/apply mechanism is a separate capability; it may not
introduce accounts or retained approvals into the public service by implication.

Keep three events distinct: permission to transmit artifacts for transient
processing, acceptance of an architectural decision, and authorization to install
exact artifact bytes locally. Agreement with a recommendation does not authorize
unseen file bytes. The existing `ArchitectureArtifactBundle` still requires
accepted ADRs. The separate `DraftArchitectureArtifactBundle` requires proposed
ADRs; model-supplied `accepted` or `approved: true` cannot manufacture proof.

Return the exact validated UTF-8 bytes with relative paths, sizes, hashes, schema
version, bundle digest, draft status and unverified acceptance/local persistence.
There is no retained prepared version or later download endpoint. Bound the full
inline response including its text fallback and fail explicitly when oversized.
Changed local bytes require fresh validation; a digest describes the returned
bytes, not freshness against some other local candidate or workflow history.
Never ask the model to regenerate an export and call those bytes server-validated.

The host owns local candidate revisions, invalidates earlier digests on change,
and handles native writes/concurrent edits/recovery separately. The service cannot
verify host-written files, even when the host reports matching hashes. Any future
controlled local apply must independently check paths, exact approval, current-file
digests and post-write bytes with a tested multi-file failure strategy. Preserve
symlink/junction protections and the `.ai-architect/` boundary. A successful export
does not complete an approved-persistence workflow.

### Workflow and wire contract requirements

- Do not enroll or infer a tenant, principal or workspace for public calls. The
  endpoint has no identity-bound project operations. Local paths, MCP roots and
  model-supplied workspace names never authorize hosted filesystem access.
- Publish host-owned active/clarification/analysis/prepared/exported/cancelled
  transitions, proportional shortcuts and required context. Store the local ID,
  revision, questions, comparison, evidence limits, reference version and digest
  under `.ai-architect/.mcp-workflows/<local-review-id>.json` using native file
  permissions. Checkpoint retention/deletion is user-controlled, not a server API.
- Read the current local revision before updating and do not overwrite an
  unexpected edit. Recover local checkpoints after context loss; ask if several
  reviews match. Without a local file capability, disclose missing durable resume.
  The server cannot enforce workflow ordering or reconstruct lost local state.
- Calls are naturally retry-safe, with no persisted mutation/idempotency ledger.
  Repeating identical self-contained inputs on the same contract returns identical
  validation/export results across workers/restarts. A lost response is retried
  with the complete input, not a server candidate ID. Different bytes receive
  their own validation, not a revision-conflict claim based on nonexistent state.
- Pin workflow/tool-contract/artifact/reference versions in the local checkpoint
  and packaged skill. Reject incompatible request/reference versions with an
  actionable recovery path. Keep old local checkpoints readable where supported;
  never claim a server rollout migrates or verifies client workflow state.
- Freeze exact supported MCP protocol and SDK versions during the spike (the
  current lock contains Python `mcp==1.30.0`). Test the actual `tools/list` schemas
  and `tools/call` results in each host, not just Pydantic model validation. Use
  explicit object input/output envelopes; preserve structured results and a compact
  text fallback, and map domain failures to MCP tool errors (`isError: true`).
  Tool annotations describe the actual read-only service: there are no project
  writes and identical requests are repeatable without stored replay results.
- Probe Foundry early with generated schemas: its
  [MCP documentation](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/model-context-protocol#common-questions-and-errors)
  flags `anyOf`,
  `allOf`, and multi-type parameters as possible incompatibilities. Use a common
  compatible wire subset where possible, with full canonical validation behind it;
  do not merely remove schema constraints. If projection is required, serve a
  documented schema profile from the same service and test semantic equivalence.

### Hosted security and lifecycle minimum

Before accepting real project data, test genuinely anonymous access in every
advertised host, including Foundry. No OAuth discovery, token issuance or private
workspace mapping belongs in the public service. Test TLS, allowed Host/Origin,
request/response isolation, public abuse controls and the proxy boundary. Optional
private customer-managed authentication is separate and cannot be an onboarding
requirement for this endpoint. Authentication to the customer's host/cloud account
is distinct from authentication to our MCP service.

Use stateless HTTP without persistent MCP session IDs or shared project memory.
Test lost responses, interrupted requests, reconnects, worker restarts and parallel
clients with distinct payloads, checking for mixed or stale results. Session
duration alone is not isolation. Bound bytes, collection sizes, parser depth/time,
result size, concurrency, and per-IP/request rates before resource exhaustion.
Keep operational counters bounded and separate from payloads; do not promise
immediate memory erasure or a retention lifetime that has not been verified.

Audit YAML/Pydantic/framework failures, application/proxy logs, traces, caches,
crash dumps and hosting backups for payload leakage. Return stable bounded error
codes/field locations without input values, tested with synthetic secrets; never
forward parser exception text. Serve no-store responses. No project content,
candidate, approval, result history or local checkpoint may be persisted by any
service layer. Document any operational metadata separately, with verified cleanup.
There is no server review expiry/delete flow because no reviews exist; native
local cancellation and user-controlled checkpoint deletion remain distinct actions.

## Skills to adapt and deliver

### Packaging decision and research basis

Keep **one public Composite skill backed by six canonical workflow modules**:
one orchestrator and five specialists. These six source skills already exist;
the work is to adapt their hook assumptions, contracts, packaging, and evaluations
for MCP. Do not describe them as six entirely new skills or expose six public
entry points merely because six source folders exist.

The existing Codex builder already packages these modules as
`references/workflow-*.md` beneath `skills/ai-software-architect/`. Preserve that
progressive loading approach and the existing 500-line Composite limit. A focused
pattern question must not load every module, all 23 GoF bodies, or artifact
authoring templates. Users continue to ask the Architect for help without choosing
an internal specialist. Native sibling-skill activation is not a dependency.

The [plugin structure research](2026-11-03-mcp-plugin-structure-research.md)
compares Atlassian, Cloudflare, Stripe, AWS, and Supabase, as well as the earlier
Figma, Notion, and Slack examples. It records source-specific skill counts,
hosting evidence, hook findings, and limits of the comparison. The most useful
patterns are outcome-oriented server operations, references loaded on demand,
shared skill sources with host-specific packaging, and explicit capability modes.
These are design recommendations for our product, not proof that another plugin
reproduces our five hooks.

### Module ownership and MCP interactions

The paths below are existing folders under `shared/skills/`; each owns its
`SKILL.md`. The public prototype's three operations are defined above; workflow
handoffs and continuation are client-local.

| ID / module | Model-owned responsibility and handoff | MCP relationship |
| --- | --- | --- |
| SK-01 `orchestrate-architecture-workflow` | Select focused help, comparison, full lifecycle, or conformance; load the minimum modules; connect short replies to the active local review; produce the complete user report. | Discover capabilities/references; use native host tools for local start/resume/checkpoints. Explain unavailable persistence/approval capabilities. |
| SK-02 `conduct-architecture-interview` | Establish material constraints, quality requirements, contradictions, and evidence sufficiency. Hand off clarified context and outstanding questions, without selecting patterns. | Update/read client-local context and checkpoints only; no remote clarification submission. |
| SK-03 `evaluate-architecture-options` | Compare credible alternatives for one decision, cite evidence, state assumptions, and recommend proportionately. Hand off structured options and a proposed decision awaiting review. | Retrieve relevant references; keep model-produced analysis client-local. Static parsers remain local/customer-managed. |
| SK-04 `create-architecture-decisions` | Turn the recommendation into a proposed ADR/contract/context draft and own the complete bundle's logical consistency. | With transfer permission, send the complete candidate to the stateless prepare/export tool and deliver its exact response bytes. No remote candidate record, verified acceptance or commit. |
| SK-05 `prepare-coding-handoff` | Translate decisions into milestones, dependencies, boundaries and checks; in the draft-only public profile, label the plan as tracing to proposed decisions. | Contribute the implementation-plan portion of the same candidate. No partial persistence or application-code edits. Accepted local handoff remains a separately authorized host workflow. |
| SK-06 `review-architecture-conformance` | Compare user-owned accepted contracts/ADRs with bounded static evidence; distinguish confirmed findings, possible violations, and acceptable deviations. | Keep evidence-linked findings local and model-guided; no public conformance submission/history API. Never silently revise accepted artifacts or claim parser verification from summaries. |

The customer's host model performs all six semantic workflows. The server checks
request/artifact schemas, compatible versions, required fields and complete-bundle
invariants; it does not verify local transitions or store project state, and it
does not decide architecture quality through keyword rules. The
orchestrator coordinates modules by loading their packaged instruction files and
passing typed context. It does not spawn agents or assume a host can invoke one
skill from another programmatically.

### Shared MCP usage reference and continuation contract

Use the additional protocol reference
`shared/skills/orchestrate-architecture-workflow/references/mcp-workflow-protocol.md`.
This is supporting material, **not a seventh public skill**. Generate host-specific
tool-name/configuration details from it and the canonical contracts. Cover:

- Capability discovery for the primary hosted profile, with reference-only use
  when project-data transfer is declined, and explicitly selected optional local
  or customer-managed profiles. Establish the data boundary before submissions;
  reject silently switching modes.
- Client-local start/resume, workspace/file permissions, checkpoint revisions,
  cancellation, stale local edits and multiple active reviews. Local review IDs
  are not remote identifiers; no persistent MCP session ID is issued.
- Typed handoffs for clarification, options, decisions, artifact candidates, and
  conformance findings, with provenance, uncertainty, and missing evidence.
- Transfer permission, stateless complete preparation/export, exact-byte integrity,
  draft status and separately authorized host-local installation. Instructions
  must not manufacture approval or infer persistence from an attempted write.
- Short replies and context recovery: read the known local checkpoint when relevant;
  ask only when the correct active review cannot be established. No promise of
  automatic recovery if the host never loads the skill or reads local files.
- A compact local checkpoint with next-step context and missing evidence. It is
  host/instruction-guided, not a remotely verified transition result. A host
  without local storage must disclose that durable resume is unavailable.
- Reference IDs, versions, and selective retrieval. Bundle canonical references for
  local use; generic guidance needs neither a review nor project-data transmission.
- Typed failure and recovery rules, with no repeated blind retries or success claims
  when a capability, permission, evidence item, or supported approval path is absent.

Audit all six modules and adapter-rendered instructions for assumptions about
`UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PostCompact`, and `Stop`. Replace
those assumptions in the new mode with the explicit protocol; retain the current
hook adapter until migration acceptance is met. Maintain a traceability table
linking each old responsibility to its new owner, scenario, and residual host limit.

### Skill-level acceptance

| Module | Required acceptance evidence |
| --- | --- |
| SK-01 | Focused help loads only necessary references and performs no repository inspection or workflow creation; multilingual short replies resume correctly; concurrent reviews remain distinct. |
| SK-02 | Material contradictions are clarified before comparison; preserve the existing maximum of five questions per round and three rounds; sufficient supplied context avoids unnecessary questions or file reads. |
| SK-03 | Preserve the six-section comparison contract, genuine alternatives, separate supporting patterns, ordinal fit scores, proportionate no-pattern recommendations, and individually addressable GoF references. |
| SK-04 | Produce the complete proposed context/contract/ADR/implementation-plan draft; changed candidates invalidate local digests and require revalidation; rejection installs no architecture artifacts; report exact-byte draft export with acceptance/local persistence unverified. |
| SK-05 | Draft handoff traces to proposed decisions with concrete milestones/checks; accepted handoff requires a separate native approval/apply workflow. No partial persistence or application-source modification. |
| SK-06 | Findings cite rule and evidence locations and confidence; description-only or incomplete evidence is disclosed; analysis does not execute project code or silently revise accepted decisions. |

Use semantic fixtures for workflow choice, clarification, architectural reasoning,
and user-facing completeness. Use deterministic tests for local checkpoint schemas,
stateless requests, references, bundle invariants, payload isolation and generation.
Verify native checkpoint permissions/continuation in real hosts. Record loaded modules,
reference size, tool calls, and latency without logging customer contents. Evaluate
instruction compliance separately from server enforcement; prose is not a guard.

## Integration and publication targets

| Target | Planned deliverable | Acceptance and distribution boundary |
| --- | --- | --- |
| OpenAI public directory / Codex | Remote HTTPS MCP endpoint with one Composite skill and focused references; hook-free public package. | Prepare the remote MCP submission and validate activation, continuation, permissions, and endpoint compatibility. OpenAI review/acceptance is separate from implementation. Optional local GitHub setup is a separate manual path. |
| Claude Code | Hook-free plugin containing generated skills and the primary remote MCP configuration; direct manual setup too. | Validate HTTP first, then the optional local STDIO profile; offer our public GitHub marketplace/package, then separately investigate official-directory submission. |
| GitHub Copilot | Skills/agent instructions and the primary remote MCP configuration for explicitly named surfaces. | Start with VS Code and CLI; test each instead of claiming every Copilot surface. Treat registry discovery, organization allowlists, and public listing as separate work. |
| Google Antigravity | Thin adapter with remote MCP configuration, generated workflow skills/instructions, and focused reference access. | Validate IDE and CLI separately on vendor-supported OS surfaces. Investigate store/plugin publication independently; manual remote setup remains available. |
| Cursor | Thin adapter with remote MCP configuration, generated workflow skills/instructions, and focused references. | Validate IDE and CLI separately on vendor-supported OS surfaces; cloud-agent support needs separate testing. Investigate marketplace publication independently. |
| Microsoft Foundry / Foundry Tools | Agent instructions, compatible tool schemas, an HTTP deployment recipe, and tool attachment examples. | A cloud Foundry agent needs a reachable remote endpoint, not a laptop STDIO process. Include customer-managed deployment and the documented private-network route. |
| Additional MCP clients, initially Gemini CLI | Reusable configuration/instruction recipe and capability discovery against the same endpoint. | Apply the shared adapter contract and compatibility checks before advertising support; prioritize additional adapters from verified customer needs. |

### OpenAI remote public submission

Use the remote **With MCP** submission route described in the
[OpenAI submission guide](https://developers.openai.com/plugins/deploy/submission).
Prepare a stable service URL, compatible Streamable HTTP tools, anonymous access
with no account/token, privacy/support/terms documentation, accompanying skills,
and reviewer instructions with representative test cases. Inspect the exact public
package for lifecycle hooks and mandatory local launchers before submission.

The submitted package connects to the hosted endpoint. It does not contain a
required STDIO server or depend on the optional GitHub-run deployment. Local MCP
submission approval is outside this delivery path. Keep manual source distribution
documented separately. Actual submission and publication remain later actions
requiring an explicit user request; passing our tests does not guarantee approval.

For Foundry, document two discovery tracks: custom MCP tool attachment and an
organization-scoped private tool catalog. The latter is currently preview.
Investigate the current public Tools Catalog publisher/partner route and its
review requirements as a separate milestone; do not equate adding a URL to one
agent with public availability in Foundry Tools. Report that route as unresolved
until its requirements and acceptance are established.

For Claude Code, Copilot, Antigravity, and Cursor, prepare versioned
configuration/packaging from the same shared source. Verify the then-current
official marketplace/registry publication procedure and record its outcome before
claiming an official listing. Existing support for MCP is not itself directory
approval. Manual remote setup and installation from the public repository remain
supported paths regardless of discovery.

Foundry schema compatibility must be tested against its supported schema subset;
derive any adapter projection from canonical schemas rather than maintaining
inconsistent contracts. Capabilities such as resources, prompts, interactive UI,
Sampling, and private networking require per-host verification and fallbacks.

Generate workflow instructions and references from the six shared modules for
each adapter. Codex keeps the Composite; Claude Code and Copilot initially use an
equivalent entry workflow with supported local references. Antigravity and Cursor
receive equivalent generated entry instructions using their supported mechanisms.
Foundry receives agent instructions and retrievable workflow resources: attaching
an MCP server alone establishes neither native `SKILL.md` loading nor customer-
controlled checkpoint storage. Test actual activation, local/customer-host
storage and follow-up behavior; disclose absent durable resume rather than adding
state to our public service.

Current vendor documentation illustrates why adapters may be necessary:
[Antigravity](https://antigravity.google/docs/mcp) and
[Cursor](https://cursor.com/docs/mcp) document their own remote configuration and
connection conventions; verify anonymous access rather than requiring their optional
authentication features. [Gemini CLI](https://geminicli.com/docs/tools/mcp-server/)
also documents its transport-specific configuration. Generate the correct setup
per host and recheck it during implementation instead of treating one JSON file
as universally interchangeable.

Reference delivery must work through packaged files and the focused
`get_architecture_resource` tool when a client lacks resource discovery. Evaluate
Skills over MCP as an optional capability, inspired by Cloudflare; do not make a
new extension mandatory across all hosts. Pin the workflow/reference version for
an active client-local review so a content update cannot silently change its obligations.

## mcpservers.org listing readiness

Checked on 2026-11-03 against the live
[German submission form](https://mcpservers.org/de/submit), including its conditional
remote fields and page-provided submission schema. No entry was submitted.

| Published form item | Plan |
| --- | --- |
| Server name | `AI Software Architect MCP`. |
| Category | `development` / Entwicklung. |
| Short description | One sentence describing the hosted tools and optional local/privacy mode accurately. |
| Repository, website, or documentation URL | Public GitHub project or dedicated installation documentation; not the MCP endpoint. |
| Contact email | Maintainer supplies and reviews the actual address before submission. |
| Official MCP Registry name | Optional; include only after separately registered and verified. |
| Remote support | Optional in the form; include it for the primary hosted release after verification. Provide the working endpoint and authentication type `none`/anonymous; no account or token is required. Never submit credentials. |
| Submission plan | Free listing is available; paid promotion is optional and not a technical prerequisite. |

The form permits a local-only submission; the directory also lists locally
installed servers. A public hosted endpoint is not a prerequisite for this
directory's basic listing. An [existing local-server entry](https://mcpservers.org/de/servers/cameroncooke/xcodebuildmcp)
provides supporting evidence, not a certification of our implementation.

Our planned entry nevertheless describes the verified remote service, with the
optional GitHub-run deployment explained in linked documentation. The form's
local-only allowance does not change the primary hosted delivery decision.

No comprehensive technical certification checklist was found in the checked
submission UI. Do not invent a minimum star count, package-registry requirement,
Code Signing requirement, or official MCP Registry requirement. Additional review
conditions or future form changes must be checked immediately before submission.

Our own readiness gate, beyond the published form fields:

- Public release/reference is downloadable without repository membership.
- A clean installation can initialize MCP, enumerate the intended tools, call
  representative tools, and shut down using only the documented instructions.
- README starts with hosted setup/client configuration and includes implemented
  capabilities, examples, limitations, license, support, and data flows. Document
  optional local prerequisites/startup and customer hosting in separate sections.
- The description distinguishes a real MCP server from a skills-only package and
  accurately states local, customer-hosted, and centrally hosted availability.
- Remote availability is advertised only after endpoint, protocol, anonymous access,
  reconnect, no-retention and per-request isolation tests pass. Do not enable remote
  discovery merely for a local loopback service or a third-party tunnel that is
  not a supported service.
- Registry name and endpoint, when present, identify the released server. Do not
  submit planned or placeholder URLs.
- Prepare the exact listing for review. Actual submission, paid promotion, and
  publication require a later explicit user request. Acceptance remains the
  directory operator's decision, not something implementation tests guarantee.

## Sequenced build work and verification checkpoints

### 0. Feasibility prototype and migration gate

This phase deliberately precedes production hardening and broad distribution.
Implement a narrow, reusable slice with synthetic projects only, an isolated
anonymous stateless HTTPS endpoint, one Composite instruction package, and one
supported surface each for Codex and Claude Code (Copilot may replace Claude if access is
unavailable). Probe Foundry tool discovery, a representative nested input/result,
and access without login/token now; its full workflow integration remains phase 5. Keep all
six host targets and three OS targets in the later delivery matrix.

- [x] Record the revised anonymous/stateless contract, host-local transitions and
      checkpoint schema, no project retention, and draft-only export capability.
      Mark the experiment in the specification/acceptance source and preserve the
      released hook workflow. See [the prototype contract](../MCP_PROTOTYPE.md).
- [x] Implement capability discovery, versioned references, complete proposed
      candidate validation and bounded exact-byte draft export in one stateless
      call. Include a separate client-local checkpoint schema and generated
      Composite. No database, remote start/resume/submission API or account system.
- [ ] Exercise focused help; full review/export; multilingual short continuation;
      rejection/revision; loss of the local review ID; two active local reviews;
      forced context loss/server restart; and omitted/reordered calls or fabricated approval.
      Include poisoned repository text as data. Test without hooks and without
      repeatedly reminding the model which MCP operation to call.
      Use an isolated host profile and verify that legacy Architect hooks or
      instructions are not supplying missing behavior to the MCP experiment.
- [ ] Verify the draft-only boundary in real hosts: rejection, automatic tool
      approval and changed-after-validation bytes must not produce verified
      acceptance or false local-persistence claims. No independent human
      confirmation channel is implemented. Any future accepted/apply capability
      requires a separate local trust mechanism, not a hosted approval store.
- [x] Add a dedicated prototype harness and maintained entry point
      `scripts/run-mcp-prototype-evaluations.ps1`. Record the separate
      `mcp-phase-0-anonymous-stateless-deterministic` cohort, where hook inactivity
      is expected. Preserve the legacy campaign/ledger. Real-host diagnostics and
      their unscored rubric are in `shared/evaluations/mcp-prototype/scenarios.yaml`.
- [ ] Freeze models, versions, prompts, evidence rubric, latency/call budgets, and
      success criteria before scoring. Use at least five independent repetitions
      per diagnostic scenario per host. For the go/no-go cohort, require at least
      19/20 successful complete review/export runs and 19/20 correct short-reply
      continuations per host without corrective operator prompting. This is an
      initial engineering threshold, not proof of a 95% population success rate.
      Log all failures, repairs, tool counts, and P50/P90 latency; compare matched
      legacy fixtures separately and agree a numerical latency budget before runs.
- [ ] Require zero observed cross-request payload disclosure, retained/retrievable
      project data, fabricated verified approvals, changed unvalidated bytes
      reported as validated, or false server persistence claims. Separately record
      host-only misuse/false claims: server
      refusal does not make an unsafe host result a pass. Critical host failures
      block advertising that host/profile until its scope or controls are revised.

Current evidence: 25 dedicated deterministic checks and the 425-test regression
suite passed. Live host cohorts, numerical host-latency budget, Foundry probing
and public deployment remain unverified; phase 0 is not complete.

Checkpoint: a written go/no-go decision with reproducible evidence and a list of
capabilities actually demonstrated. Passing allows the full design/build below;
failure leads to revised instructions/contracts or a deliberately narrower product
profile and a rerun. It does not justify silently removing the current hooks or
weakening the gate. Production hosting and the remaining target integrations are
still required for the full migration, not for this feasibility result.

### 1. Baseline, scope, and contracts

- [ ] Inventory existing five-hook behavior, shared schemas, and four optional
      MCP tools. Record what is reused, replaced, or not enforceable in each host.
- [ ] Update the living specification/threat model and canonical acceptance source
      for the new mode before implementing it; preserve current release behavior.
- [ ] Specify anonymous/public versus optional private deployment boundaries,
      input/output contracts, transient data categories, native local permissions
      and checkpoint storage, and host capability requirements.
- [ ] Close applicable readiness gates: freeze client-local transitions/workspace
      file binding, draft/accepted limits, data-transfer consent, exact export
      bytes/limits, version policy and stateless retry behavior from the evidence.
      Record actual client disclosure controls and their residual limitations.
- [ ] Finalize capabilities/references/self-contained validation-export, no project
      retention, and client-local workflow/checkpoints. Treat optional local
      inspection/persistence capabilities as separate from the hosted baseline.
- [ ] Map SK-01 through SK-06 to canonical handoff schemas, resources, proposed
      tools, old hook responsibilities, and mode-specific data transfers.
- [ ] Define a versioned capability/compatibility matrix for instruction loading,
      references, continuation, approvals, resources, and optional extensions.
- [ ] Populate OS-01 through OS-03 and HOST-01 through HOST-06 with intended
      surfaces, vendor platform availability, exact versions, adapter needs,
      required scenario coverage, and evidence status; keep all six named targets.
- [ ] Prepare the OpenAI remote-submission requirements and verify the public
      Foundry/Claude/Copilot/Antigravity/Cursor routes, recording concrete unresolved
      external dependencies rather than assuming approval. Exclude local MCP
      submission approval from the remote delivery milestones.

Checkpoint: reviewable contracts and an explicit difference between domain
guarantees, skill-guided behavior, and host-enforced restrictions.

### 2. Shared workflow and artifact core

- [ ] Validate durable client-local checkpoint handling and model-produced analysis
      in each host; add no server workflow or candidate store.
- [ ] Reuse validators, bounded static evidence, references, and canonical outputs.
- [ ] Extract the complete portable artifact checks from the Codex adapter and
      keep both transports/adapters on those rules; run legacy regression fixtures.
- [ ] Validate pure complete prepare/export with concurrency, retry and no-retention
      evidence. Any future approved local apply/verify is a separately gated native
      capability, not a required public MCP operation.
- [ ] Keep semantic reasoning in the host model; never replace it with keyword
      routing. Keep generic help and proportional workflows lightweight.
- [ ] Adapt all six shared skill modules for the explicit MCP protocol; implement
      the shared usage reference and preserve the existing focused-help behavior.
- [ ] Keep mode-specific instructions in generated hook/MCP projections so adapting
      shared modules cannot silently break the retained hook package. Test both
      packages and pin the instructions used by each evaluation cohort.
- [ ] Add the skill-level semantic fixtures and deterministic contract checks;
      demonstrate that malformed model submissions cannot bypass server invariants.
- [ ] Expose complete validation/export outcomes and actionable errors in one call;
      keep compact checkpoints/next-step context local and avoid unnecessary remote calls.

Checkpoint: the six adapted modules and protocol reference are reviewable alongside
the core. Tests cover invalid bundles/paths, exact-byte export, repeated/parallel
requests, sanitized failures and no retained project state. Real-host evaluations
cover local transitions, checkpoint revisions, changed-after-validation candidates,
native permissions and each module's semantic behavior; the service cannot attest
those local transitions.

### 3. Primary external hosting and remote service

- [ ] Select and document the hosting provider, region, stateless compute/ingress,
      cost assumptions, and deployment/update procedure. No provider is selected.
- [ ] Deploy anonymous stateless Streamable HTTP over HTTPS with capabilities,
      references and self-contained validation/export, without any project-state
      database, session store, export cache or approval record.
- [ ] Test no-login/token onboarding, per-request isolation and infrastructure-wide
      no-retention controls, including application/proxy logs, caches, traces,
      crash dumps and backups. Document operational metadata separately.
- [ ] Meet the hosted security/lifecycle minimum: TLS/Host/Origin, rate/concurrency
      limits, bounded parsing/results, sanitized failures, parallel clients and
      retry/restart equivalence. Do not reuse the local watchdog/global process
      budget or add tenant enrollment to the anonymous entry point. Keep draft-only
      semantics; no public acceptance/commit capability is enabled.
- [ ] Validate reference-only use and deliberate minimal-data submissions; reject
      raw-source ingestion and unsupported persistence operations.
- [ ] Verify hosted onboarding and representative review/validation/export flows
      without accounts/tokens, our local runtime, Python, `uv`, hooks, or repository write tokens.
- [ ] Verify the same hosted endpoint from Windows, macOS, and Linux using
      supported clients. Test platform-neutral contracts and synthetic artifact
      fixtures; do not confuse the hosting platform with customer OS coverage.
- [ ] Validate cold starts, timeouts, reconnects, repeated complete inputs after
      restart and no payload crossover between workers. Confirm the host resumes
      its local checkpoint independently before choosing a production provider.

Checkpoint: a working external HTTPS MCP endpoint supports the intended primary
workflow with disclosed minimal inputs and accurate export results. Denied
transfers remain denied; tests support every processing/storage claim. Remote
service delivery is a required milestone, independent of optional local packaging.

### 4. Optional GitHub-run and customer-managed deployments

- [ ] Build and document the source-download/locked-install/start/connect/stop flow
      for customers who choose local execution, using the same shared core.
- [ ] Separate local-only state and permissions from all hosted configuration.
- [ ] Verify no runtime project-data requests, telemetry, hidden fallback, or
      automatic update traffic from our local components. Capture process/network
      evidence in controlled tests without collecting real customer contents.
- [ ] Prove lifecycle behavior, export, host-local checkpoint handling, upgrade and
      uninstall per advertised OS/client. Gate approved local apply independently
      if offered; do not count draft export as approved persistence.
- [ ] Provide a customer-managed stateless container/service recipe, with optional
      customer-selected access controls and explicit customer-host checkpoint
      storage. No data fallback or checkpoint storage on our infrastructure.
- [ ] Document manual source/client configuration without a local OpenAI directory
      submission or local-MCP submission approval dependency.

Checkpoint: a customer can run the optional deployment without our infrastructure;
the separately chosen model's traffic is documented. This work remains a planned
deliverable and can proceed alongside host integration; it does not gate the
primary remote-submission package.

### 5. Major assistant adapters and Microsoft Foundry

- [ ] Generate hook-free skills/instructions and configurations for Codex and
      Claude Code; validate the primary remote mode and optional local profiles
      independently. The public package must use the hosted endpoint.
- [ ] Generate the Composite, selective workflow references, reference catalog,
      and resource fallback from shared sources; check package-relative links and
      required files. Do not depend on sibling-skill activation.
- [ ] Implement/test Copilot VS Code and CLI integration; list unsupported surfaces.
- [ ] Implement/test the Antigravity adapter from shared sources; verify IDE/CLI
      configuration, anonymous endpoint access, reference loading, activation and local continuation.
- [ ] Implement/test the Cursor adapter from shared sources; verify IDE/CLI
      configuration, anonymous endpoint access, reference loading, activation and local continuation.
      Treat cloud agents as a separate profile if included.
- [ ] Attach the HTTP tools to a Foundry agent and test schemas, anonymous access,
      draft/approval limits and continuation in customer-controlled storage with
      the configured model. Disclose any missing local storage capability.
- [ ] Verify Foundry's instruction/resource projection and each host's short-reply
      activation; record skill-guided limitations where hooks formerly enforced them.
- [ ] Test customer-managed/private Foundry deployment and document required Azure
      resources/permissions/cost boundaries. Prepare the private-catalog recipe.
- [ ] Prepare public catalog/marketplace/registry materials where a verified route
      exists; retain manual setup while external publication is pending.
- [ ] Prepare the OpenAI remote **With MCP** review package and test installation
      against the hosted service; exclude lifecycle hooks and required local
      executables. Keep GitHub-run configuration in the manual distribution path.
- [ ] Run the shared scenario suite for HOST-01 through HOST-06 across the
      documented Windows/macOS/Linux surface matrix; record evidence and unresolved
      host constraints per cell, including Foundry's cloud execution distinction.
- [ ] Validate the additional-client onboarding contract with Gemini CLI where
      feasible; document the steps needed for further MCP-capable assistants.

Checkpoint: the shared workflows and contracts are validated for all six named
assistant/platform targets and all three customer OS families through their
available supported surfaces. Any host-blocked cell remains explicitly unresolved,
not counted as a pass. No extra model subscription or Sampling capability is assumed.

### 6. Documentation, release evidence, and listing packages

- [ ] Add a prominent README privacy section and a local-versus-hosted choice.
      Explain source, derived evidence, artifacts, state, logs, and model-provider
      processing separately; label planned features and residual limitations.
- [ ] Lead the README with the primary hosted service and public-directory setup;
      clearly label local GitHub execution as optional. State provider/region and
      actual data flows once selected; say no account/token and no project retention,
      distinguish transient artifact transfer, and avoid implying local submission is needed.
- [ ] Add maintained local setup, customer-hosting, host-specific configuration,
      privacy, and troubleshooting guides. Update component docs and handoff.
- [ ] Document one public entry skill versus six internal modules, what is loaded
      on demand, model/server ownership, and the tested instruction-loading method
      for each host. Report capability differences without promising hook parity.
- [ ] Publish a maintained compatibility table for Windows, macOS, Linux and all
      six named assistants/platforms, with exact tested versions/surfaces, setup
      links, adapter requirements, capability limits, and evidence status.
- [ ] Verify service deployment provenance, dependency licenses, and package/source
      checksums. The planned hosted/source distribution needs no native binary
      signing; revisit that only if a separate binary distribution is introduced.
- [ ] Run relevant domain/security/transport/packaging tests and real host
      evaluations. Use the maintained exploratory entry point when running the
      canonical Codex campaigns; preserve baseline/cohort distinctions.
- [ ] Prepare the mcpservers.org form values and verify links/configurations from
      the exact release. Recheck submission rules on that date.
- [ ] Prepare separate Foundry, Claude Code, Copilot, Antigravity, Cursor, and OpenAI
      distribution status records. Keep technical compatibility separate from
      catalog acceptance. Publication/submission is a later explicitly authorized action.

Checkpoint: documented, reproducible release evidence; customer privacy claims
match observed behavior. No listing is reported as accepted merely because its
materials are ready.

## Cross-host acceptance scenarios

| Scenario | Required evidence |
| --- | --- |
| Primary hosted setup without our local runtime or account | A supported client connects using the endpoint URL alone, with no service account/login/token/enrollment, and completes the advertised draft workflow without our Python/STDIO server, hooks or native binaries. |
| Hosted client coverage on Linux, macOS, and Windows | The same endpoint works in each advertised supported client/OS combination; no per-OS native package is required for hosted use. |
| Required assistant coverage | Codex, Claude Code, GitHub Copilot, Antigravity, Cursor, and Microsoft Foundry each have configuration/instructions plus complete workflow evidence; connection-only checks are insufficient. |
| Portable adapters and missing optional capabilities | The same canonical workflow works through each host's supported instruction/reference mechanism without hooks, Sampling, Apps, or native skill discovery being mandatory. |
| Cross-platform artifact handling | Synthetic paths/names with spaces, Unicode, case differences, separators, and line endings preserve valid bundles and boundaries; customer paths are never treated as hosted filesystem access. |
| Foundry from each customer OS | Setup/invocation works through supported portal/SDK access on all three OS families, with the actual workflow and MCP calls tested in the cloud agent. |
| Focused concept or pattern question | Minimum relevant reference loaded; no repository read, complete-workflow setup, or project-data upload. |
| Skill packaging and reference delivery | All six modules map to the released version; selective loading works through supported files/tools, including without Skills over MCP. |
| Short multilingual reply after clarification | The correct client-local checkpoint resumes without a second explicit skill mention; no checkpoint or analysis-history upload is used. |
| Review, revision, or rejection | The host updates the intended local checkpoint, invalidates changed candidate digests and revalidates changed bytes; rejection installs no architecture artifacts. |
| Approval provenance and draft-only boundary | Auto-approved tool calls and model claims cannot create verified human approval. Public exports remain proposed drafts with acceptance/local persistence unverified; future accepted local apply needs independent native authorization. |
| Hosted artifact export and optional local persistence | Export returns the validated bundle without claiming local installation; verified persistence is tested separately where a controlled storage capability exists. |
| Context compaction and server restart | The host reads its local checkpoint and retries a complete request if needed; the server has no state to restore. Missing host-local storage is disclosed. |
| Two concurrent local reviews or clients | Distinct native checkpoints remain distinct. Parallel remote calls with distinguishable inputs return only their own response contents; no shared project-state access exists. |
| Lost local review ID and multi-worker retry | Native local discovery selects the intended review or asks if ambiguous. Identical complete requests return the same export across restarts/workers without server IDs, revisions or an idempotency ledger. |
| No retained/retrievable customer data | No project database, candidate/export cache, checkpoint API or payload logs/traces/dumps/backups exist across application and hosting layers. A later call cannot retrieve another client's earlier input or output. Short session duration is not counted as this evidence. |
| Invalid contract, secret, or cross-artifact mismatch | Validation returns a sanitized failure and no valid export; no customer files are modified. |
| Path traversal, symlink/junction escape, application-source target | Public preparation rejects noncanonical artifact paths without resolving customer files; optional native apply must separately preserve symlink/junction and allowed-root checks. |
| Repeated call, interrupted transfer, concurrent local change | Pure repeated calls create no artifacts or remote records. Interrupted responses can be retried; changed local bytes need fresh validation. No local write success is inferred. |
| Local runtime with network blocked after setup | Supported local operations work without our service; host-model dependency is separately declared. |
| Remote source payload or declined transfer | Test the named client-side control where one exists; otherwise label minimization instruction-guided and verify reference-only/local fallback. Server rejection is not prevention of transfer; errors and all log layers must omit payloads. |
| Hosted limits, no retention, and upgrades | Oversized/deep inputs and rate/concurrency abuse are bounded. Unexpected identity/review/checkpoint/approval arguments fail; no server credentials or review expiry/deletion flow exists. Operational metadata and no-retention controls are evidenced; incompatible contract/reference versions fail safely. |
| Export integrity and size limits | Returned bytes/hashes match the prepared version; truncation or model reconstruction is never reported as validated delivery or verified local persistence. |
| Canonical complete report versus host summary | Report completeness verified; host deviations measured separately. |
| Model skips a required step or fabricates approval | The server validates only the supplied complete bundle and makes no workflow-order attestation. Invalid bundle/approval/commit calls fail; omitted local steps and false host claims are measured separately and can fail a host campaign. |
| Independent host-tool misuse | Residual boundary is recorded; no claim that MCP globally blocks other tools. |
| Remote public-package onboarding | Hook-free skills/configuration connect to the reviewed remote endpoint; the package has no mandatory local server and no local-submission approval dependency. |
| Optional local GitHub install | Commands tested from the source release, capabilities correct, lifecycle reliable; setup uses the manual distribution path. |

Semantic review must accompany deterministic checks. Record target host/version,
model, effort, language, capabilities, and deployment mode so results are
comparable. Do not delete the hook-based implementation until evidence and an
approved specification change justify the migration.

## Source references and remaining decisions

Directory and host documentation was checked on 2026-11-03. Revalidate before
implementation/publication because interfaces and review processes can change.

- [mcpservers.org submission](https://mcpservers.org/de/submit).
- [Foundry MCP connections and private endpoints](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/model-context-protocol).
- [Foundry private tool catalog (preview)](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/private-tool-catalog).
- [Claude Code plugins and distribution](https://code.claude.com/docs/en/plugins).
- [GitHub Copilot MCP integration](https://docs.github.com/en/copilot/how-tos/provide-context/use-mcp/extend-copilot-chat-with-mcp).
- [Google Antigravity MCP configuration](https://antigravity.google/docs/mcp).
- [Cursor MCP integration](https://cursor.com/docs/mcp).
- [Gemini CLI MCP configuration](https://geminicli.com/docs/tools/mcp-server/).
- [OpenAI plugin MCP server deployment](https://developers.openai.com/plugins/build/mcp-server).
- [OpenAI public remote plugin submission](https://developers.openai.com/plugins/deploy/submission).
- [OpenAI packaging and hook eligibility](https://developers.openai.com/plugins/build/plugins#bundled-mcp-servers-and-lifecycle-hooks).
- [MCP tools, result schemas, annotations, and error handling](https://modelcontextprotocol.io/specification/2025-11-25/server/tools).
- [MCP HTTP transport, sessions, and origin validation](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports).
- [MCP authorization and protected-resource discovery](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization).
- [MCP security guidance, including session and token boundaries](https://modelcontextprotocol.io/docs/2025-11-25/tutorials/security/security_best_practices).
- [Claude Code MCP retries, approvals, and tool annotations](https://code.claude.com/docs/en/mcp).
- [Comparative plugin research and source snapshots](2026-11-03-mcp-plugin-structure-research.md).
- [Existing optional MCP adapter](../../tools/python-mcp/README.md).
- [Living product specification](../../specs/AISoftwareArchitect.md).

Decided: the primary external endpoint is anonymous and stateless, without an
account/login/token, service-managed reviews/candidates/checkpoints, project-state
database or verified-acceptance/commit capability. Workflow/checkpoints remain
client-local. The three prototype operations provide capabilities, references and
complete proposed-draft validation/export in one call. These decisions supersede
the earlier hosted authentication/storage design; they must not reappear as open
provider or implementation choices. Transport/workflow IDs are not an isolation
substitute, and no persistent storage is not a no-transmission promise.

Open work: select hosting provider/region/stateless compute/ingress and costs;
verify infrastructure-wide no payload retention, operational metadata handling,
abuse controls, real-host local checkpoint/continuation behavior, numerical latency
budgets, production wire/output limits and rollout compatibility. Record actual
client/OS versions, vendor surface availability and customer-controlled storage
for cloud agents. Any future accepted local apply needs a separate trusted native
approval/recovery capability, not stored approvals on the public service.

Optional local installation/lifecycle, public Foundry catalog route,
registry/package channel, optional Skills over MCP support and maintainer contact
details remain delivery/publication work. Primary external hosting and remote
OpenAI submission are still required; one public Composite, six shared modules,
one protocol reference, all six named hosts and Windows/macOS/Linux remain fixed
targets, with additional clients supported through thin adapters. The anonymous
prototype and deterministic checks exist; real-host evidence and the migration
gate remain open. Catalog acceptance may come later; privacy, local workflow
reliability and accurately bounded approval/export claims must be settled before
advertising the corresponding capabilities.
