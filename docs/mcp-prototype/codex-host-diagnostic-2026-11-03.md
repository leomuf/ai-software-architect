<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Codex anonymous MCP host diagnostic, 2026-11-03

One real two-turn workflow completed the deterministic checks: a synthetic
architecture comparison saved a client-local checkpoint, then the natural short
reply resumed the same CLI chat and produced an exact-byte validated draft export.
This is an unscored diagnostic, not a completed migration/reliability cohort.

## Frozen setup and evidence

| Item | Observed value |
| --- | --- |
| Cohort | `mcp-phase-0-anonymous-stateless-codex-diagnostic` |
| Fixture | `shared/evaluations/mcp-prototype/codex-local-review-export.yaml`, revision 1 |
| Fixture SHA-256 | `97311c653f7d9fd29c7e2f007af8f17a1cde05c3bcc5a87fbfbea2d4c27b4040` |
| Client | Codex CLI `0.156.1`, native Windows 11 |
| Model / effort / speed | `gpt-6-sol` / `xhigh` / `standard` |
| Reference snapshot | `22a43fe6f48594c550db2a014e933171e5db3bd0f000640e3190f5821cf61e21` |
| MCP | SDK `1.30.0`, negotiated protocol `2025-11-25`, anonymous loopback HTTP |
| Per-phase diagnostic limits | 600 seconds, 50 observed tool calls |
| Source baseline | `d54ac4b` plus uncommitted runner/handshake changes; source hashes preserved with the evidence |
| Isolation | Temporary Codex home; hooks/plugins/apps/subagents disabled; 18 discovered external skills disabled; only the experimental MCP server configured |
| Machine result | `manual-review`, all 12 checks in the captured runner version passed |
| Regression | 440 tests passed; Ruff and Mypy passed (50 source files) |

The successful evidence directory is
`.tmp/mcp-host/codex-2026-11-03-diagnostic-03/`. It contains the pre-call
`frozen-run.json`, original `report.json`/`SUMMARY.md`, initial and continuation
client JSONL/timing records, initial checkpoint, profile/model catalog, and the
workspace's final checkpoint plus `draft-export.json`. Source hashes were also
captured while this run was active in `evidence/source-provenance.json`.
`evidence/derived-metrics.json` summarizes preserved events without changing the
original report. These are local synthetic client-side test artifacts, not
project records stored by the MCP service. The temporary copy of the Codex host
login was removed; the source login/configuration and legacy performance ledger
were not changed by the runner.

## Observed sequence and measurements

| Phase | Time | Observed tool calls | MCP calls / failed MCP calls |
| --- | ---: | ---: | ---: |
| Comparison and local checkpoint | 139.569 s | 12 | 7 / 2 |
| Short-reply continuation and draft export | 288.117 s | 15 | 7 / 0 |
| Sum of measured phases | 427.686 s | 27 | 14 / 2 |

The continuation prompt was exactly `Ja, bitte als Draft exportieren.` with no
second skill mention, operation reminder or corrective operator prompt. The CLI
chat ID stayed the same; a native read returned the selected checkpoint before
preparation. The local checkpoint advanced from revision 1 / `analysis` to
revision 3 / `exported`, with the actual export digest. Only that checkpoint and
`draft-export.json` changed in the synthetic workspace. Four proposed artifacts
and their manifest matched the actual MCP result and the shared validator; no
architecture artifacts were installed at their canonical paths.

The CLI reported 203,905 input / 163,072 cached input / 4,880 output tokens in the
initial turn and 869,710 input / 820,096 cached input / 16,021 output tokens in the
continuation. These are CLI-reported aggregates across calls, not unique context
sizes. One workflow provides no meaningful P50/P90 host-reliability estimate.

## Agent semantic review

The implementing agent separately read both final responses and all four exported
artifacts. This is an agent assessment, not a human architectural approval or an
independent blinded evaluation; the original `manual-review` status is preserved.

- The comparison used six German sections, three alternatives for the UI/domain
  boundary, explicit ordinal scores and no claim of measured percentages.
- A separate module with simple functions was recommended proportionately. The
  Layered alternative cited its canonical reference; supporting patterns were
  explicitly unnecessary. Source inspection was correctly described as absent.
- ADR, contract, context and handoff agree on the proposed boundary. The ADR stays
  `proposed`; milestones trace to it and the dependency rules. The handoff treats
  implementation checks as future work, not as executed application tests.
- The final answer accurately distinguishes a local draft-export file from
  installing canonical architecture artifacts. It claims neither server-verified
  human acceptance nor server-verified customer-local persistence.

No critical semantic failure was identified in this one diagnostic. Arbitrary
host disclosure prevention, forced context loss, two active reviews, hostile
repository behavior and independent human acceptance were not established by it.

## Failures and repairs preserved

| Attempt | Observation | Disposition |
| --- | --- | --- |
| `diagnostic-01` | The server rejected the client's initial version offer instead of negotiating the profile version. The CLI session did not start. | Fixed handshake-only version negotiation and added older/current/newer-offer regression cases. Initial report was preserved; this was a startup failure, not model reasoning evidence. |
| `diagnostic-02` | The provider rejected desktop-configured `gpt-6.1-sol` for this CLI/account path. | Preserved the API error; selected explicitly catalog-listed `gpt-6-sol` for a new frozen run. No silent model substitution or CLI upgrade. Future runner preflight checks the CLI catalog; a catalog is not an entitlement guarantee. |
| `diagnostic-03` | Two reference IDs omitted `/references/` and returned `not-found`. | The model retrieved the catalog and repaired both calls without operator help. Counted as failed calls, not discarded. Better public-ID guidance remains a possible instruction improvement. |

The CLI also emitted a PowerShell shell-snapshot warning and a rollout-flush
warning after the initial turn. They did not prevent the observed resume/export;
stderr remains in the evidence. Later runner changes add explicit SDK/source
provenance, derived metrics and rejection of malformed JSONL, with regression
coverage. They do not retroactively change this run's original check list.

## Remaining gate

Phase 0 remains open. Freeze agreed cohort latency/call budgets and run the
required diagnostic repetitions plus at least 19/20 full exports and 19/20 short
continuations per host in Codex and Claude Code (or Copilot). This local HTTP run
does not verify public HTTPS onboarding, Foundry, other operating systems,
infrastructure-wide no-retention controls or directory eligibility. See the
[prototype contract](../MCP_PROTOTYPE.md) and
[implementation plan](../plans/2026-11-03-mcp-skills-privacy-and-distribution.md).
