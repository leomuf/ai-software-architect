<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Install AI Software Architect in Codex

This prebuilt package installs AI Software Architect without Python, `uv`, a
virtual environment, project dependencies, or a separate model API key. The
prebuilt package supports Codex Desktop on Windows x86-64.

## Available Versions

- **Version 0.2.4:** use the Windows ZIP attached to its
  [GitHub release](https://github.com/leomuf/ai-software-architect/releases).
  Use the installation prompt below to set it up across existing projects.
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

## Install with a Codex Prompt

1. Download the Windows ZIP and `SHA256SUMS.txt` from the same GitHub release.
   Save both in the same folder.
2. Open a new task in Codex Desktop. Paste the prompt below and replace the ZIP
   path with the actual location of your download. Use the filename of the version
   you downloaded.
3. Let Codex perform the setup, then follow its instructions for any remaining
   installation clicks. Review and approve all five hooks yourself.

The maintainer successfully tested this prompt on Windows. It asks Codex to set
up the plugin for your user account, so you can use it across existing projects.
You do not need to create or edit a JSON file as part of normal installation.

```text
Please install AI Software Architect from this local ZIP:
C:\Users\<your-name>\Downloads\ai-software-architect-v0.2.4-windows-x86_64.zip

Set it up for my Windows user account so I can use it across my existing Codex projects.

Verify the ZIP against SHA256SUMS.txt in the same folder. Extract it to a permanent location under my user folder. Inspect the included marketplace and use Codex's supported marketplace registration command if available.

Preserve existing plugins and settings. Do not overwrite an existing marketplace catalog, edit Codex's installed-plugin cache, or change my project files. Avoid creating a duplicate active installation.

Complete the setup you can perform, then tell me exactly what I need to click in Codex to install or enable the plugin and review all five hooks. Do not approve hooks on my behalf.

Finally, explain how I can verify that the plugin is available in a different existing project.
```

Keep the permanent folder that Codex uses for the plugin source. If Codex reports
that the checksum differs or it cannot complete registration, stop and follow
[Troubleshooting](#troubleshooting).

### Approve All Five Hooks

Before first use, go to **Settings → Coding → Hooks** and review and approve:

1. `UserPromptSubmit`
2. `PreToolUse`
3. `PostToolUse`
4. `PostCompact`
5. `Stop`

Alternatively, click the hook icon with the yellow dot below the message input
(**Review hooks**) to review pending hooks. Start a new task after approval.

All five hooks are required for routing, continuation, safety checks, artifact
validation, and complete responses. They make no model or network calls, start
no persistent process, and do not bypass Codex permissions.

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

### Check the Setup Report First

Codex may register the marketplace already included in the extracted ZIP, rather
than create a personal `marketplace.json`. Use the source folder and marketplace
name from its setup report. A missing personal catalog alone does not mean that
installation failed. Do not add a second registration if the plugin already works.

- **Checksum differs:** download the ZIP and checksum file again from the same
  release. Do not install an archive with a different checksum.
- **Marketplace or plugin missing:** ask Codex to check its registration and source
  folder, then restart Codex Desktop. Make sure the complete package was extracted.
- **Older version still shown:** compare the installed version with the download's
  `VERSION.txt`. Ask Codex to check which source is registered and which copy is
  enabled. Use **Update**, or uninstall and reinstall through Codex if necessary.
  Review all five hooks again and start a new task.
- **Plugin missing in another project:** check that it is installed and enabled,
  then check whether project or organization settings disable it.
- **Hooks unavailable or disabled:** open **Settings → Coding → Hooks** and
  approve all five before using the complete workflow.

### Manual Recovery: Personal Marketplace JSON

Use this only if Codex cannot complete registration with the installation prompt.
These are repair instructions, not an additional normal installation method.
Back up existing configuration first. If Codex already registered the bundled
marketplace, resolve that registration before adding another one.

Both locations below belong to your Windows account, outside your project folders:

| Purpose | Location |
| --- | --- |
| Plugin source files | `%USERPROFILE%\.codex\plugins\ai-software-architect` |
| Personal marketplace catalog | `%USERPROFILE%\.agents\plugins\marketplace.json` |

`%USERPROFILE%` means your Windows user folder, usually `C:\Users\YourName`.
Register the source folder once, install the plugin through Codex, and approve
its five hooks. You do not need a separate copy in each project.

#### Copy the Plugin Source

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

#### Repair the Personal Marketplace Catalog

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

After repairing the source and catalog, restart Codex Desktop. Open **Plugins**,
select **Personal** (or the catalog's display name), and install or update
**AI Software Architect**. Confirm the version against the download's `VERSION.txt`,
review all five hooks, and test a new task in another existing project.

If the problem remains, use the repository's
[support page](https://github.com/leomuf/ai-software-architect/blob/main/SUPPORT.md).
Do not share credentials, private repository content, or sensitive diagnostic data.
