<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Install AI Software Architect in Codex

This prebuilt package installs AI Software Architect without Python, `uv`, a
virtual environment, project dependencies, or a separate model API key. The
prebuilt package supports Codex Desktop on Windows x86-64.

## Choose an Installation Option

- **Version 0.2.4:** use the Windows ZIP attached to its
  [GitHub release](https://github.com/leomuf/ai-software-architect/releases).
  Follow the personal installation steps below to use it across existing projects.
- **Public marketplace:** version 0.2.3 remains available there and includes
  hooks, as confirmed by the maintainer. It does not include the improvements
  in 0.2.4.

OpenAI currently rejects new plugin submissions that contain hooks. All five hooks
are essential to this plugin, so 0.2.4 will be distributed through GitHub rather
than submitted to the public marketplace. Both versions include hooks; the
restriction applies to new uploads, not to the already published 0.2.3 package.
See the
[directory status](https://github.com/leomuf/ai-software-architect/blob/main/docs/OPENAI_SUBMISSION_STATUS.md)
for updates.

## Requirements

- Codex Desktop with plugin, Agent Skill, and hook support.
- A Codex account and model allocation.
- Permission to extract a ZIP and copy files into your Windows user folder.

## Verify the Download

Download the release ZIP and `SHA256SUMS.txt` from the same GitHub Release. In
PowerShell, run the following command from the download directory:

```powershell
Get-FileHash .\ai-software-architect-v*-windows-x86_64.zip -Algorithm SHA256
```

The command lists matching Windows release ZIPs in that folder. Compare the hash
for the ZIP you intend to install with its filename's entry in `SHA256SUMS.txt`.
Stop if they differ.

## Install Once for Your Existing Projects

This personal installation makes the plugin available across Codex projects on
your Windows account. Project or organization settings can still disable plugins.
You do not need to open the extracted download as a Codex project.

Both locations below belong to your Windows account, outside your project folders:

| Purpose | Location |
| --- | --- |
| Plugin source files | `%USERPROFILE%\.codex\plugins\ai-software-architect` |
| Personal marketplace catalog | `%USERPROFILE%\.agents\plugins\marketplace.json` |

`%USERPROFILE%` means your Windows user folder, usually `C:\Users\YourName`.
Register the source folder once, install the plugin through Codex, and approve
its five hooks. You do not need a separate copy in each project.

### 1. Copy the Plugin

Extract the verified ZIP. Inside the extracted bundle, open `plugins` and copy
the complete `ai-software-architect` folder into:

```text
%USERPROFILE%\.codex\plugins\
```

Paste this path into File Explorer's address bar. Create any missing folders.
The resulting manifest must be at:

```text
%USERPROFILE%\.codex\plugins\ai-software-architect\.codex-plugin\plugin.json
```

If an older source folder already exists at that destination, move it aside first
so files from different versions are not mixed. Keep the new source folder here.
Codex manages its installed copy under `cache`; do not edit that cache yourself.

### 2. Register the Plugin in Your Personal Marketplace

Open or create this file, creating the parent folders if needed:

```text
%USERPROFILE%\.agents\plugins\marketplace.json
```

This is also written as `~/.agents/plugins/marketplace.json` in the Codex docs.

For a **new file**, save this JSON using a text editor. Make sure the filename is
`marketplace.json`, not `marketplace.json.txt`:

```json
{
  "name": "personal",
  "interface": {
    "displayName": "Personal"
  },
  "plugins": [
    {
      "name": "ai-software-architect",
      "source": {
        "source": "local",
        "path": "./.codex/plugins/ai-software-architect"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Developer Tools"
    }
  ]
}
```

**Already have this file?** Back it up first. Keep its marketplace name and other
plugins. Add the AI Software Architect object to its `plugins` list, or update its
existing entry to use the `source` shown above. Do not replace the whole file or
add the same plugin twice. Separate entries in the list with commas.

The path starts from your Windows user folder, not from `.agents\plugins`.
See OpenAI's [personal marketplace documentation](https://developers.openai.com/plugins/build/plugins#install-a-local-plugin-manually).

### 3. Install and Approve the Hooks

1. Restart Codex Desktop.
2. Open **Plugins → Personal**, or select your existing personal marketplace's
   display name. Open **AI Software Architect**.
3. Select **Install**, or **Update** if available. Check that the displayed version
   matches the download's `VERSION.txt`. If another marketplace's copy is already
   active, disable or uninstall that copy first so only one copy is active.
4. Go to **Settings → Coding → Hooks** and review and approve **all five hooks**:
   `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PostCompact`, and `Stop`.
   Alternatively, click the hook icon with the yellow dot below the message input
   (**Review hooks**) to review pending hooks.
5. Open any existing project and start a new task.

All five hooks are required for routing, continuation, safety checks, artifact
validation, and complete responses. They make no model or network calls, start
no persistent process, and do not bypass Codex permissions.

## Alternative: Discover the Plugin from the Extracted Project

The ZIP also includes a project marketplace. To use it, open the extracted bundle
as a project in Codex Desktop, restart Codex if needed, and install from
**Plugins → AI Software Architect Release**. Approve all five hooks as above.

That marketplace is discovered from the project folder. Installation choices are
saved for your user account; opening the folder does not itself restrict the
installed plugin to that project. The personal setup above makes the installation
source discoverable across projects. Choose one setup to avoid duplicate copies.

## Try It

Begin each new architecture request by typing `@` in the Codex composer, selecting
**AI Software Architect** from the picker, and adding the request after the
structured mention:

```text
@AI Software Architect Suggest suitable design patterns for my current project.
```

Do not merely type the literal display name. Codex must insert the plugin mention
from the `@` picker. The direct `$ai-software-architect <request>` skill invocation
remains supported for advanced use.

All five hooks are required for reliable routing, continuation, safety checks,
validated architecture-artifact creation, and complete user-facing responses.

An optional [expense-insights demo](https://github.com/leomuf/ai-software-architect/tree/main/demo/expense-insights)
is available in the source repository. It is not included in the Windows plugin
ZIP and is not required for installation.

## Uninstall

Open **Plugins → Installed → AI Software Architect → Uninstall**. No persistent
AI Software Architect process should remain running while the plugin is idle.

## Troubleshooting

- **Personal marketplace missing:** check the catalog's filename, JSON syntax,
  and `source.path` from step 2, then restart Codex Desktop.
- **Plugin cannot be installed:** check the full manifest path from step 1 and
  make sure the whole plugin folder was copied, including its runtime and hooks.
- **Older version still shown:** verify the copied manifest's version, restart
  Codex, and check for **Update**. If necessary, uninstall the old copy through
  **Plugins → Installed**, then install the new version from your personal
  marketplace. Review all five hooks again and start a new task.
- **Plugin missing in another project:** check that it is installed and enabled,
  then check whether project or organization settings disable it.
- **Hooks unavailable or disabled:** open **Settings → Coding → Hooks** and
  approve all five before using the complete workflow.
- Report reproducible problems through the repository's public support and
  security channels. Do not publish credentials, private repository content, or
  sensitive diagnostic data.
