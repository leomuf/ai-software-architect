<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Install AI Software Architect in Codex

This prebuilt package installs AI Software Architect without Python, `uv`, a
virtual environment, project dependencies, or a separate model API key. The
initial release supports Codex Desktop on Windows x86-64.

## Requirements

- Codex Desktop with plugin, Agent Skill, and hook support.
- A Codex account and model allocation.
- Permission to extract a ZIP archive and open its directory as a Codex
  project.

## Verify the Download

Download the release ZIP and `SHA256SUMS.txt` from the same GitHub Release. In
PowerShell, run the following command from the download directory:

```powershell
Get-FileHash .\ai-software-architect-v0.1.0-windows-x86_64.zip -Algorithm SHA256
```

Compare the displayed hash with `SHA256SUMS.txt`. Stop if they differ.

## Install

1. Extract `ai-software-architect-v0.1.0-windows-x86_64.zip`.
2. Open the extracted `ai-software-architect-v0.1.0-windows-x86_64` directory
   as a project in Codex Desktop.
3. Restart Codex Desktop if the included **AI Software Architect Release**
   marketplace is not immediately visible.
4. Open **Plugins**.
5. Select **AI Software Architect Release** from the marketplace selector.
6. Open **AI Software Architect** and select **Install**.
7. Review the bundled hook definitions and activate them. The hooks are
   short-lived local checks: they make no model or network calls, start no
   persistent process, and do not bypass Codex permissions.
8. Start a new task before using the installed skill.

Codex supports repository marketplaces through
`.agents/plugins/marketplace.json`. The extracted bundle contains that catalog
and the complete prebuilt plugin under `plugins/ai-software-architect/`.

## Try It

Begin each new architecture request by selecting the public skill in the Codex
composer:

```text
$ai-software-architect Suggest suitable design patterns for my current project.
```

Do not use the `@AI Software Architect` plugin selector as a substitute for the
`$ai-software-architect` skill invocation.

For the reproducible end-to-end demonstration, open the bundled source
repository's `demo/expense-insights/` project and follow its `README.md` and
`DEMO_PROMPTS.md`.

## Uninstall

Open **Plugins → Installed → AI Software Architect → Uninstall**. No persistent
AI Software Architect process should remain running while the plugin is idle.

## Troubleshooting

- If the marketplace is absent, confirm that the extracted directory contains
  `.agents/plugins/marketplace.json`, then restart Codex Desktop with that
  directory open as the current project.
- If the plugin is visible but cannot be installed, confirm that
  `plugins/ai-software-architect/.codex-plugin/plugin.json` exists and that the
  archive was fully extracted.
- If hooks are disabled, open the plugin page, review their current definitions,
  and activate them before testing the complete workflow.
- Report reproducible problems through the repository's public support and
  security channels. Do not publish credentials, private repository content, or
  sensitive diagnostic data.
