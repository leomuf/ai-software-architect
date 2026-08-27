<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# GitHub Release Guide

This guide describes how to publish the OpenAI Build Week release of AI
Software Architect. It complements the complete release-candidate gates in
[`RELEASING.md`](RELEASING.md); it does not replace them.

The first public release is `v0.1.0`. The immutable hackathon snapshot uses the
additional `build-week-2026-submission` tag. Both tags identify the same Git
commit.

## 1. Complete the Release Commit

Do not create or push `v0.1.0` until the final commit contains:

- the installable marketplace template and packaging logic;
- dependency-free installation instructions;
- the updated release workflow;
- the approved README, specification, and demo documentation;
- the complete plugin source and reproducible locked dependencies; and
- any approved release evidence that belongs in the tagged source.

The release package must let a Windows x86-64 Codex user install and run the
plugin without Python, `uv`, a virtual environment, project dependencies, or a
separate model API key.

Before tagging, confirm that the working tree is clean and record the candidate
commit:

```powershell
git status --short
git rev-parse HEAD
```

Run every release-candidate gate documented in
[`RELEASING.md`](RELEASING.md), including deterministic validation, package
inspection, exploratory fixtures, Codex Desktop acceptance, clean-machine
installation, and first-attempt uninstall.

After installing the exact candidate and activating all five hooks, run the
structured plugin-invocation smoke test, then start the five-fixture exploratory
campaign:

```powershell
.\scripts\run-codex-plugin-invocation-smoke.ps1
```

```powershell
.\scripts\run-codex-exploratory-evaluations.ps1
```

Archive the generated summary and report as release evidence, then complete the
required semantic review described in `RELEASING.md`.

## 2. Create the Release Tags

Replace `<commit-sha>` with the exact reviewed submission commit:

```powershell
git tag -a v0.1.0 <commit-sha> -m "AI Software Architect v0.1.0"
git tag -a build-week-2026-submission <commit-sha> -m "OpenAI Build Week 2026 submission"
```

Verify that both tags resolve to the same commit:

```powershell
git rev-list -n 1 v0.1.0
git rev-list -n 1 build-week-2026-submission
```

Push both tags:

```powershell
git push origin v0.1.0 build-week-2026-submission
```

Only `v0.1.0` triggers the current tag workflow because
[`.github/workflows/release.yml`](../.github/workflows/release.yml) matches
tags beginning with `v`.

Never move or recreate a published release tag. If a correction is required,
create an appropriate new version instead.

## 3. Verify the GitHub Actions Build

Open the repository's
[GitHub Actions page](https://github.com/leomuf/ai-software-architect/actions)
and select the **Release artifact** run for `v0.1.0`.

Confirm that every step passes and that the workflow produces:

```text
ai-software-architect-v0.1.0-windows-x86_64.zip
SHA256SUMS.txt
```

Sanitized release evidence may be attached separately after the manual gates;
it is not generated automatically by the tag workflow.

The release ZIP should be a ready-to-install local marketplace bundle:

```text
ai-software-architect-v0.1.0-windows-x86_64/
├── .agents/
│   └── plugins/
│       └── marketplace.json
├── plugins/
│   └── ai-software-architect/
├── INSTALL.md
└── VERSION.txt
```

`SHA256SUMS.txt` sits beside the ZIP because it authenticates the complete
archive and therefore cannot be embedded as its own archive checksum.

Download the workflow artifact and extract it. GitHub Actions wraps uploaded
files in an additional artifact ZIP, so attach the actual release bundle and its
checksum—not the outer Actions download—to the GitHub Release.

If the workflow still produces only the raw plugin directory, stop. That output
is useful for development but does not yet satisfy the dependency-free
installation requirement.

## 4. Draft the GitHub Release

Open [Create a new release](https://github.com/leomuf/ai-software-architect/releases/new).

1. Select the existing `v0.1.0` tag.
2. Confirm that it targets the recorded Build Week submission commit.
3. Set the release title to `AI Software Architect v0.1.0`.
4. Attach the installable marketplace ZIP.
5. Attach `SHA256SUMS.txt`.
6. Attach sanitized release evidence when available.
7. Mark the release as the latest release.
8. Do not mark `v0.1.0` as a prerelease.
9. Save it as a draft before publishing.

Creating a draft first makes it possible to verify the notes and all binary
assets together before publication. See GitHub's official
[release-management documentation](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository).

## 5. Add Release Notes

Use the following as a starting point and update it to match the final package
exactly:

```markdown
# AI Software Architect v0.1.0

First public release of AI Software Architect, created for OpenAI Build Week
2026.

AI Software Architect is an architecture-first Codex plugin that helps
developers:

- clarify architecture-significant requirements;
- compare project-fit architecture styles and design patterns;
- approve and record Architecture Decision Records;
- generate machine-readable architecture contracts and coding handoffs; and
- review implementation conformance.

## Supported platform

- Codex Desktop
- Windows x86-64
- Codex account and model allocation required
- No Python, uv, separate API key, or project dependency installation required

## Installation

Download `ai-software-architect-v0.1.0-windows-x86_64.zip` and follow its
included `INSTALL.md`.

After installation, review and activate all five bundled hooks, start a new Codex
task, type `@`, select **AI Software Architect** from the picker, and add the
request after the selected structured mention:

`@AI Software Architect Suggest suitable design patterns for my current project.`

Do not merely type the literal display name. `$ai-software-architect <request>`
remains supported as a direct/advanced invocation.

## Verification

Verify the downloaded package against `SHA256SUMS.txt`.

## License

MIT
```

GitHub automatically provides source-code ZIP and TAR archives for the tagged
commit. Those archives are not substitutes for the prebuilt marketplace
bundle. See GitHub's overview of
[release assets and tags](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases).

## 6. Publish and Verify the Release

Before selecting **Publish release**:

- confirm the selected tag and commit SHA;
- verify the release title and notes;
- confirm that every intended asset is attached;
- verify the recorded SHA-256 checksum locally; and
- confirm that no development cache, credential, local path, hidden reasoning,
  or sensitive evidence is included.

After publication:

1. Open the release while signed out or from another account.
2. Download the release bundle and verify its checksum.
3. Extract it on a clean Windows x86-64 environment without Python or `uv`.
4. Open the extracted marketplace directory as a Codex project.
5. Restart Codex if the marketplace is not immediately visible.
6. Open **Plugins**, select the included marketplace, and install
   **AI Software Architect**.
7. Review and activate all five bundled hook definitions.
8. Start a new task and select AI Software Architect from the `@` picker.
9. Run the documented demonstration workflow.
10. Uninstall the plugin successfully on the first attempt.

Any failed checksum, installation, runtime, hook, exploratory, or uninstall
check blocks the release.

## 7. Complete the Devpost Submission

Use the published GitHub repository and release URLs in the OpenAI Build Week
submission. Before the deadline, confirm that:

- the repository is public with its MIT license, or the private repository is
  shared with the required evaluator accounts;
- the public YouTube demonstration is under three minutes and its narration
  explains the project, Codex, and GPT-5.6;
- the primary Codex `/feedback` Session ID is entered;
- the **Developer Tools** category is selected;
- the plugin installation and testing field links to the release and its
  dependency-free instructions; and
- Devpost shows the project as **Submitted**, not **Draft**.

The submitted repository, release, video, and project description must remain
available to the evaluators throughout the evaluation period.
