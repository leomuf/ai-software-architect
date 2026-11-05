<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Codex local-checkpoint recovery diagnostics, 2026-11-05

These synthetic diagnostics extend the earlier
[short-reply/export run](codex-host-diagnostic-2026-11-03.md). They exercise the
anonymous stateless MCP prototype with native Windows Codex CLI 0.156.1,
`gpt-6-sol`, `xhigh`, standard speed, and the locked Python/MCP environment.
The legacy plugin, hooks, other MCP servers and external skills are disabled in
each private temporary host profile. Runs are sequential and unscored; they do
not enter the legacy performance ledger or satisfy the migration cohort.

Each first phase creates a comparison and canonical client-local checkpoint.
Continuation starts a **new CLI chat**, explicitly activates the experimental
skill and supplies only the frozen continuation prompt plus existing local files.
The original conversation is not resumed or injected into that prompt. This
simulates lost conversation context; it does not force real compaction or restart
the MCP service. The second scenario adds a separate runner-seeded CSV-import
checkpoint whose exact contents are frozen before any model call. It tests
selection among existing reviews, not model creation of two reviews.

Budgets are 600 seconds and 50 observed tool calls per phase. Exact prompts,
settings, source hashes, reference version, instruction provenance and any seed
checkpoint are in each run's `frozen-run.json` before the first inference call.
Evidence is client-side synthetic evaluation output; the service does not retain
project payloads. Existing host login is copied only into a private OS temporary
directory and removed afterward. MCP access requires no login or token.

## Context-loss result

Evidence directory: `.tmp/mcp-host/codex-2026-11-05-context-loss-01/`.

All **15 deterministic checks passed**; original report status is `manual-review`.
Initial and continuation chat IDs differ. The fresh chat discovered and read the
existing checkpoint, confirmed its pinned reference version and exported the
selected UI/domain recommendation without a corrective operator prompt.

| Phase | Duration | Tool calls | MCP calls | Failed MCP calls |
| --- | ---: | ---: | ---: | ---: |
| Initial comparison/checkpoint | 138.904 s | 13 | 1 | 0 |
| Fresh-chat continuation/export | 313.041 s | 25 | 4 | 0 |
| Completed workflow | 451.945 s | 38 | 5 | 0 |

The local review `987cd582-e9f5-4768-bdf3-b07a58d272f6` advanced from revision 1 /
`analysis` to revision 2 / `exported`. Its reference version stayed unchanged.
The complete four-file export and manifest match the actual MCP result; the
checkpoint digest is
`f674ecbe53efa2cfbf6c6f87c312fd0e206bf55c9cc5cb04dd2478b0ac1cabea`.
Only that checkpoint and `draft-export.json` changed in the synthetic workspace.
No canonical architecture artifact was installed. The temporary login copy was
removed. The CLI emitted PowerShell snapshot and rollout-flush warnings, preserved
in stderr; neither prevented completion. An `rg` search with no AGENTS matches
returned exit code 1; no operator repair was supplied.

The implementing agent separately read both responses, all four export artifacts,
the final checkpoint and native read/write evidence. The comparison is
proportionate, uses six sections, credible alternatives and explicit ordinal
scores/evidence limits. The proposed separate functional domain module is
consistent across ADR, contract, context and handoff. Future implementation
checks are described as future work. The final response accurately reports draft
export and absence of canonical installation/application changes. No critical
semantic failure was identified in this case. This agent assessment is not human
architectural approval or an independent blinded evaluation; the original report
remains unchanged and semantic review is recorded separately in evidence.

## Two-active-review result

Evidence directory: `.tmp/mcp-host/codex-2026-11-05-two-active-reviews-01/`.

The first attempt is preserved as **`deterministic-failure`**: 15 of 16 checks
passed. The model correctly selected the UI/domain review, delivered the exact
four-file MCP export and left the CSV checkpoint unchanged. However, it cited the
selected local review UUID inside `project-context.md`, so that local metadata
was included in the submitted artifact text. `no-checkpoint-upload` correctly
failed despite valid artifacts, delivery hashes and local checkpoint updates.
The check is a narrow identifier signal, not proof that arbitrary checkpoint
content cannot be disclosed.

| Phase | Duration | Tool calls | MCP calls | Failed MCP calls |
| --- | ---: | ---: | ---: | ---: |
| Initial comparison/checkpoint | 111.785 s | 14 | 8 | 2 |
| Fresh-chat continuation/export | 172.457 s | 26 | 3 | 0 |
| Completed workflow, failed privacy check | 284.242 s | 40 | 11 | 2 |

The initial reference calls twice omitted `/references/`; the model recovered
using the resource catalog without operator help. Those failures remain in the
counts. Agent review found coherent architecture artifacts and accurate proposed/
not-installed claims, but the checkpoint-metadata disclosure prevents a pass.
The original report is unchanged; the temporary login copy was removed.

The shared protocol now explicitly excludes local review IDs, checkpoint paths,
phase/revision history and internal workflow records from outgoing artifact text,
including source citations. It requires inspection of outgoing text before
submission, while allowing public artifact IDs/schema revisions/reference
versions. This remains host instruction guidance; it does not turn server-side
validation into pre-transfer disclosure prevention or change the server's
no-retention boundary. The reference version therefore differs from the earlier
attempts, so these are not identical repeated reliability samples.

The new bounded attempt at
`.tmp/mcp-host/codex-2026-11-05-two-active-reviews-02/` passed **all 16 checks**;
original status remains `manual-review`. Neither review UUID nor checkpoint path
appears in the submitted artifact text. No corrective prompt was supplied inside
the run.

| Phase | Duration | Tool calls | MCP calls | Failed MCP calls |
| --- | ---: | ---: | ---: | ---: |
| Initial comparison/checkpoint | 134.410 s | 14 | 6 | 0 |
| Fresh-chat continuation/export | 252.338 s | 23 | 8 | 0 |
| Completed workflow | 386.748 s | 37 | 14 | 0 |

The selected local review `8366f3e4-8223-440c-a77c-13617511c54a` advanced from
revision 1 / `analysis` to revision 3 / `exported`, retaining reference version
`f91d196a9a1efb812f66e31e0189f31762628a32d525d4e6019f0feb33cc7819`.
The four-file response, delivered export and checkpoint digest agree on
`58c8c50403887674c6d5ad9ccba9e74bac27459ec7780f42ee3c0d502648b522`.
The independent CSV review stayed at revision 4 / `analysis`, with its exact
checkpoint SHA-256 unchanged:
`c1547b9e43000df50f38e13580886ce00a1335cf380a57afd06724dc8b77c56f`.
Only the selected checkpoint and `draft-export.json` were changed by the host;
the additional checkpoint was created by the runner before continuation. No
canonical artifacts or application files were installed/changed. The temporary
login copy was removed. CLI snapshot/rollout warnings remain in stderr.

Agent semantic review read both responses, all four returned artifacts and the
checkpoint/native-file evidence. The comparison retains six sections, credible
alternatives, ordinal scores and explicit evidence limits. The bundle addresses
the UI/domain boundary and leaves storage details undecided; it does not advance
the separate CSV-import decision. The proposed ADR, contract, context and future
handoff agree. Neither artifact prose nor tool arguments include local checkpoint
metadata. The final response correctly describes draft export without claiming
verified human acceptance, canonical installation or application changes. No
critical semantic failure was identified in this corrected diagnostic. The
separate agent-review sidecar does not change the original report or constitute
human approval. One successful new-version run is not proof of reliable
disclosure prevention.

## Verification and remaining gate

The runner has 24 tests, including orchestration of all three scenarios and
negative cases for reusing the old chat, advancing the wrong review, modifying or
deleting the other review, adding an unexpected review, changed export bytes and
application-source writes. Two new cases isolate selected/other-review UUIDs
inside otherwise valid artifact text: the privacy check must fail even when the
MCP result, delivered bytes and checkpoint digest all agree. Ruff and strict
Mypy pass; the expanded full regression passes **452 tests**. The server contracts and
legacy performance history are unchanged by this scenario extension.

These observations do not establish repeated host reliability, recovery when
the review topic is ambiguous, service-restart/compaction behavior, a second host,
public HTTPS onboarding, Foundry, other OS surfaces or infrastructure-wide
no-retention controls. Phase 0's migration gate stays open. See the
[prototype guide](../MCP_PROTOTYPE.md) and
[implementation plan](../plans/2026-11-03-mcp-skills-privacy-and-distribution.md).
