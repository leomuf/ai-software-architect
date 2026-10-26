<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# OpenAI Plugin Submission

This directory is the version-controlled source for the OpenAI plugin-directory
submission. **AUTOSOFT Engineering** is the public brand and **XAVIER MUFFATO
LTDA** is the registered legal publisher and the business identity that must be
verified and selected. The files support manual entry in the OpenAI developer
portal; they do not submit or publish anything.

**0.2.4 will not be submitted under the current portal rules.** The maintainer
reported that OpenAI blocked its upload because the package contains hooks.
All five hooks remain required, so this version will be distributed through
GitHub. Version 0.2.3 remains available in the public marketplace with hooks
included; the current restriction concerns new uploads. See the
[installation guide](../INSTALL_CODEX_PLUGIN.md) and
[directory status](../OPENAI_SUBMISSION_STATUS.md). The materials here are retained
for reference and possible future submissions; building a ZIP does not establish
that the portal will accept it.

The public lifecycle state is maintained separately in
[`docs/OPENAI_SUBMISSION_STATUS.md`](../OPENAI_SUBMISSION_STATUS.md). Update that
record after confirmed submission or approval without changing an already
published release artifact.

- [`listing.yaml`](listing.yaml) contains publisher, listing, regional, and starter
  prompt values.
- [`test-cases.yaml`](test-cases.yaml) contains the five positive and three
  negative review cases required by the submission workflow.
- `scripts/package-openai-plugin-submission.ps1` creates the dedicated upload
  archive from an already built and validated plugin.

The OpenAI submission archive is different from the GitHub marketplace bundle.
The manifest includes the Support URL under `interface.supportURL`, alongside
the website, privacy policy, and terms links, so the portal can import it.
Its ZIP root is the actual plugin root, including `.codex-plugin/plugin.json`,
`skills/`, `hooks/`, and the self-contained runtime. It contains no outer
marketplace catalog and requires no Python or `uv` installation. The packaging
script writes normalized ZIP member paths without a leading `./`, so the archive
can also be opened and extracted with Windows Explorer.

## Testing and Evaluation Evidence

The public, privacy-preserving history currently records more than 350 eligible
exploratory evaluation observations across more than 140 campaigns and 13
fixtures, complemented by more than 160 deterministic automated tests. This
history intentionally contains successful release evidence as well as
failure-finding development runs; it is evidence of repeated evaluation, not a
claim that more than 350 tests passed. The source observations and reproducible
reporting instructions are versioned under
[`evaluation-data/`](../../evaluation-data/README.md).

Before preparing a future submission, first confirm that OpenAI accepts all
required package features. Then:

1. review every statement against the exact release candidate;
2. confirm the repository, privacy, terms, support, and security URLs are public;
3. test the exact upload archive on a clean supported Windows environment;
4. confirm the publishing OpenAI organization exposes `XAVIER MUFFATO LTDA` as
   the verified business identity and the submitter has Apps Management Write
   permission; and
5. confirm the live portal's available category and region choices.

Hooks are part of the complete local Codex experience. Users review and approve
all five under **Settings → Coding → Hooks**. Do not remove them to bypass the
current submission restriction. Hosts without Codex lifecycle hooks do not offer
the same checks.

In the portal's **Developer Identity** field, select the exact verified value
`XAVIER MUFFATO LTDA`. Do not replace it with the brand name or the combined
brand/legal wording. Public descriptive fields may use `AUTOSOFT Engineering`; the
manifest author and legal documents make the relationship explicit as
`AUTOSOFT Engineering (a brand of XAVIER MUFFATO LTDA)`.
