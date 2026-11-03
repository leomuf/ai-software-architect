<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# MCP plugin structure research for AI Software Architect

Date: 2026-11-03

Companion to the [implementation plan](2026-11-03-mcp-skills-privacy-and-distribution.md).
This is design research; no integration was installed or implemented.

## Selection and evidence limits

Research extends beyond Figma, Notion, and Slack to established providers with
publicly documented Codex/MCP integrations: Atlassian, Cloudflare, Stripe, AWS,
and Supabase. Catalog discovery confirmed Atlassian, Stripe, and Supabase in this
session; Cloudflare and AWS document their Codex installation paths themselves.
Sources below establish packaging and behavior, not successful execution in our
environment or marketplace acceptance of our own plugin.

There is direct scale evidence for Atlassian: its 2026-10-28 engineering article
reports nearly two million monthly MCP users and over 15 million calls per weekday.
Those are vendor-reported figures across clients, not Codex plugin installation
counts. Comparable plugin-specific adoption figures were not established for the
other examples. Brand size and GitHub stars are not substitutes for those figures.
[Source: Atlassian engineering](https://www.atlassian.com/blog/how-we-build/jira-depth-on-demand).

Counts describe the identified source/package snapshot. Templates, reference
files, archived skills, duplicated host packages, slash commands, and tools are
not counted as additional active skills. They can differ from marketplace builds.

## Five additional comparisons

| Provider / inspected skill count | Distribution of work | What we can reuse |
| --- | --- | --- |
| **Atlassian: 7 active v2 skills**, excluding 6 archived v1 skills. | Outcome workflows include knowledge search, specification-to-backlog, status reporting, and triage. The MCP service coordinates underlying product operations. | Model handles interpretation; server handles constrained multi-step operations. Keep actionable errors and explicit read/write boundaries. |
| **Cloudflare: 19 source skills.** | A platform entry skill routes user needs to specialist instructions and narrow references; MCP handles live platform access. | One entry workflow plus selective specialist/reference loading. Keep knowledge delivery separate from account/project operations. |
| **Stripe: 10 skills** in the inspected Agent Plugins package, also present as 10 canonical root skills. | Best-practice guidance routes into domain references; separate skills cover distinct jobs such as upgrades. Host packages accompany a remote MCP configuration. | Generate thin host packages from shared workflows; test positive activation and incidental-name non-activation. |
| **AWS Core: 25 directly packaged source skills** in the inspected tree. | Domain guides include an evidence-based Well-Architected review. MCP knowledge tools can discover/retrieve additional workflows. | Explicit review stages, coverage ledger, source uncertainty, authoritative report template, and on-demand reference delivery. |
| **Supabase: 2 documented bundled skills.** | Broad Supabase guidance plus Postgres best practices; vendor manifests/configurations share real skill files. MCP exposes configurable tool groups and project scope. | Small public instruction surface, shared source, host-specific configuration, deterministic read-only/project restrictions, and local/hosted choices. |

Count and packaging sources:

- [Atlassian tree `37e57a7`](https://github.com/atlassian/atlassian-mcp-server/tree/37e57a78b1938a099d1dcffdfc5a61154068c15e/skills)
  and [v2 versus archived v1 guidance](https://github.com/atlassian/atlassian-mcp-server/blob/main/skills/README.md).
- [Cloudflare tree `1f2cd0a`](https://github.com/cloudflare/skills/tree/1f2cd0a19588e2c6197c91dd7c71729df1fb6156/skills),
  [entry skill](https://github.com/cloudflare/skills/blob/main/skills/cloudflare/SKILL.md),
  and [Codex setup](https://developers.cloudflare.com/agent-setup/codex/).
- [Stripe tree `5091f72`](https://github.com/stripe/ai/tree/5091f72943e6cb4ca439c98ee4783d6085de1318/providers/agent-plugins/plugin/skills),
  [shared integration guidance](https://github.com/stripe/ai/blob/main/skills/stripe-best-practices/SKILL.md),
  and [plugin manifest with activation review cases](https://github.com/stripe/ai/blob/main/providers/agent-plugins/plugin/plugin.json).
- [AWS tree `8b32dfe`](https://github.com/aws/agent-toolkit-for-aws/tree/8b32dfe0f91144b0e5d3fef487c515cb93ce0fb2/plugins/aws-core/skills)
  and [official plugin installation](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/plugins.html).
  Count is from the directory, not the shorter README overview.
- [Supabase plugin source](https://github.com/supabase-community/supabase-plugin),
  [included skills](https://supabase.com/docs/guides/ai-tools/plugins), and
  [Codex manifest](https://github.com/supabase-community/supabase-plugin/blob/main/.codex-plugin/plugin.json).

### Most relevant server design: Atlassian

Atlassian describes tools designed around complete jobs rather than REST endpoints,
with several API steps coordinated inside the server. It also documents selective
tool discovery, permission groups, compact versus expanded results, repair hints,
and checking the resulting product state. Our inference: prepare and commit should
own their entire validation/write sequences, and evaluation must inspect actual
artifacts rather than trust model claims. Its generic discovery/execution layer
is useful for a much larger catalog; our initial surface does not need that layer.
[Source](https://www.atlassian.com/blog/how-we-build/jira-depth-on-demand).

Its [specification-to-backlog skill](https://github.com/atlassian/atlassian-mcp-server/blob/main/skills/spec-to-backlog/SKILL.md)
shows analysis, presentation of a proposed result, approval, ordered writes, and
linked outputs. This is a useful workflow example, but prose requesting approval
does not establish tamper-resistant approval or atomic multi-artifact persistence.
Our stronger bundle requirements still need an explicit implementation.

### Closest review workflow: AWS Well-Architected

The [review skill](https://github.com/aws/agent-toolkit-for-aws/blob/main/plugins/aws-core/skills/aws-well-architected-review/SKILL.md)
uses selected procedure references, scoped review modes, evidence locations,
uncertainty, a fixed assessment inventory, and an authoritative report template.
These fit architecture conformance and report completeness. Our references remain
versioned/bundled where appropriate; do not copy a dependency on live documentation
for every local architecture question.

AWS's [knowledge tools](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/understanding-mcp-server-tools.html)
demonstrate workflow retrieval through ordinary MCP tools, independent of native
skill installation. This supports a focused reference-retrieval fallback for
Foundry and other clients that cannot load our packaged files.

Important counterexample: this AWS snapshot includes a
[PreToolUse hook](https://github.com/aws/agent-toolkit-for-aws/blob/8b32dfe0f91144b0e5d3fef487c515cb93ce0fb2/plugins/aws-core/com.anthropic.claude-code/hooks/hooks.json)
for secret-access checks; its
[Codex manifest](https://github.com/aws/agent-toolkit-for-aws/blob/8b32dfe0f91144b0e5d3fef487c515cb93ce0fb2/plugins/aws-core/.codex-plugin/plugin.json)
also declares the hook path. This does not establish public Codex acceptance or
hook activation. It does establish that MCP plus skills is not evidence of a
hook-free implementation or identical enforcement across clients.

### Knowledge delivery and deployment boundaries

Cloudflare additionally offers
[Skills over MCP](https://developers.cloudflare.com/changelog/post/2026-10-10-cloudflare-mcp-skills/):
supporting clients discover skills and retrieve their files through an extension.
Evaluate this as an optional delivery channel. Keep packaged references and an
ordinary retrieval tool available; verify extension support separately per host.
Do not copy its code-execution API merely to reduce a small tool catalog.

Supabase documents
[project scope, read-only mode, feature groups, local MCP, and client-dependent confirmation](https://supabase.com/docs/guides/ai-tools/mcp).
Its distinction between service restrictions and optional client dialogs is useful:
our write authorization must remain valid even when a client lacks interactive UI.
Our local/private modes must also be selected explicitly, not inferred from a skill.

## Hosting evidence

| Service | Established by checked sources | What remains unestablished |
| --- | --- | --- |
| Atlassian | Vendor-operated endpoint at `https://mcp.atlassian.com/v2/mcp`; see [server guidance](https://github.com/atlassian/atlassian-mcp-server/blob/main/skills/README.md). | Underlying compute provider/service for the production endpoint. |
| Cloudflare | Vendor endpoint `https://mcp.cloudflare.com/mcp`; public implementation uses Cloudflare Workers for generated-code execution; see [server source](https://github.com/cloudflare/mcp). | Exact production account, placement, and operational costs. |
| Stripe | Stripe explicitly operates `https://mcp.stripe.com`; see [Stripe MCP documentation](https://docs.stripe.com/mcp) and [repository](https://github.com/stripe/ai). | Underlying compute/cloud hosting provider. |
| AWS | AWS-operated managed MCP service; see [toolkit overview](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/). | Internal compute service/implementation; no implication that the public service is a customer-local server. |
| Supabase | Vendor endpoint `https://mcp.supabase.com/mcp`, plus local MCP through the customer's Supabase CLI stack; see [MCP documentation](https://supabase.com/docs/guides/ai-tools/mcp). | Underlying compute service of the hosted MCP endpoint. |

An endpoint domain does not identify its cloud provider. None of these examples
selects a hosting provider or establishes free-tier suitability for our service.
Local architecture evidence remains in the customer's environment under our plan.

## Earlier examples retained for comparison

| Example | Observed scope and useful structure |
| --- | --- |
| Figma | Public [Codex package snapshot](https://github.com/openai/plugins/tree/main/plugins/figma/skills) lists 12 skill folders; [upstream](https://github.com/figma/mcp-server-guide/tree/main/skills) lists 14. Counts differ by package/channel. General tool-use guidance plus specialized workflows illustrates separating API usage from task procedure. |
| Notion | [Public package snapshot](https://github.com/openai/plugins/tree/main/plugins/notion/skills) lists 4 task-oriented skills. [Spec-to-implementation](https://github.com/openai/skills/blob/main/skills/.curated/notion-spec-to-implementation/SKILL.md) keeps a multi-step user outcome in one workflow with supporting templates. |
| Slack | [Official README](https://github.com/slackapi/slack-skills-plugin) lists 9 skills, with separate commands. It distinguishes skills-only Codex packaging from MCP-enabled host packages; installing instructions alone does not prove tools are connected. |

The Figma/Notion Codex folder counts above came from public GitHub page snapshots,
not an installed version audited here. Do not collapse these examples into one
universal skill count or infer that an app-backed connector and a direct MCP
configuration use identical distribution plumbing.

## Decision for our implementation

Retain one public Composite and six existing canonical modules. Add a shared MCP
usage reference, explicit module handoffs, and generated host projections. Move
deterministic checks into complete server-owned operations; keep semantic review
with the customer's model. Test resulting state, reference-loading scope, privacy
boundaries, and continuation in each host. Optional extensions must have fallbacks.

These examples support that division of work. They do not demonstrate that a
standalone MCP server can intercept unrelated tools, every user message, host
compaction, or final response generation. The implementation plan retains those
limits and defines skill-guided behavior separately from enforced guarantees.
