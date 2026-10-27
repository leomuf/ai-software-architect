<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Install AI Software Architect in Codex

This prebuilt package installs AI Software Architect without Python, `uv`, a
virtual environment, project dependencies, or a separate model API key. Choose a
release archive that matches your operating system and CPU architecture.

## Package Availability

| Platform | Package availability |
| --- | --- |
| Windows x86-64 | Included in the 0.2.4 release |
| macOS | Planned; no package in 0.2.4 |
| Linux | Planned; no package in 0.2.4 |

These instructions are shared across platforms. They do not make the current
Windows runtime compatible with macOS or Linux. Use only a published package for
your platform and a Codex host that supports its plugins and hooks.

## Available Versions

- **Version 0.2.4:** use the supported release archive attached to its
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
- A release archive compatible with your operating system and CPU architecture.
- Permission to extract the archive and copy files into your user folder.

## Install with a Codex Prompt

1. Download the archive for your platform and `SHA256SUMS.txt` from the same GitHub release.
   Save both in the same folder.
2. Open a new task in Codex Desktop. Paste the prompt below and replace the archive
   path with the actual location of your download. Use the filename of the version
   you downloaded.
3. Let Codex perform the setup, then follow its instructions for any remaining
   installation clicks. Review and approve all five hooks yourself.

The clean Windows Sandbox test found that Smart App Control blocks the current
unsigned runtime even after hook approval. A signed package and a successful
runtime check are required before this installation can be considered ready.
See [Windows release signing](https://github.com/leomuf/ai-software-architect/blob/main/docs/WINDOWS_CODE_SIGNING.md).
The prompt below includes that check; its revised flow still needs a live test
with a signed package. Normal installation does not require manual JSON editing.

```text
Please install AI Software Architect in Codex Desktop for use across my projects:
<full path to the downloaded archive>

Check OS/CPU compatibility and verify the archive against SHA256SUMS.txt. Preserve existing plugins and settings.

Guide me through installation, folder trust, and restarting Codex. Leave folder trust and hook approval to me.

Run the installed runtime's --self-test. Report any operating-system security block without disabling protection.

Before reporting success, ask me to confirm that all five hooks are visible and a plugin request works in another project.
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
is available in the source repository. It is not included in the plugin release
archive and is not required for installation.

## Uninstall

Open **Plugins → Installed → AI Software Architect → Uninstall**. No persistent
AI Software Architect process should remain running while the plugin is idle.

## Troubleshooting

### Check the Setup Report First

- **Application control blocks the runtime (Windows error 4551):** setup is
  incomplete, even if all hooks appear enabled. Use a publisher-signed package
  validated with Smart App Control enabled. Folder trust does not override this
  Windows policy. Do not disable Windows protection or move hooks outside the
  plugin. See the Windows signing document linked above.
- **Runtime check:** the installed executable's `--self-test` must return
  `{"status":"ok","runtime":"ai-architect-runtime"}` with exit code zero.
  Older archives may not support this check; ask for the updated package.

Codex may register the marketplace already included in the extracted archive, rather
than create a personal `marketplace.json`. Use the source folder and marketplace
name from its setup report. A missing personal catalog alone does not mean that
installation failed. Do not add a second registration if the plugin already works.

- **Platform mismatch:** use a package built for your operating system and CPU.
  If no matching package is available, installation is not supported yet. Renaming
  an archive does not change the platform its runtime supports.
- **Checksum differs:** download the archive and checksum file again from the same
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

Both locations below belong to your user account, outside your project folders.
The macOS and Linux paths are reference examples for future supported packages,
not a claim that those packages are available or tested.

| Platform | Plugin source folder | Personal marketplace catalog |
| --- | --- | --- |
| Windows | `%USERPROFILE%\.codex\plugins\ai-software-architect` | `%USERPROFILE%\.agents\plugins\marketplace.json` |
| macOS / Linux | `~/.codex/plugins/ai-software-architect` | `~/.agents/plugins/marketplace.json` |

`%USERPROFILE%` means your Windows user folder, usually `C:\Users\YourName`.
`~` means your home folder, commonly `/Users/YourName` on macOS or
`/home/YourName` on Linux. Use the locations from Codex's setup report if your
configuration differs from these defaults.
Register the source folder once, install the plugin through Codex, and approve
its five hooks. You do not need a separate copy in each project.

#### Copy the Plugin Source

Extract the verified, compatible archive. Inside the extracted bundle, open
`plugins` and copy the complete `ai-software-architect` folder to the plugin
source folder in the table. Create missing parent folders and include hidden
files. The resulting source folder must contain `.codex-plugin/plugin.json`.

If an older source folder already exists at that destination, move it aside first
so files from different versions are not mixed. Keep the new source folder here.
Codex manages its installed copy under `cache`; do not edit that cache yourself.

#### Repair the Personal Marketplace Catalog

Open or create the personal marketplace catalog from the table, creating parent
folders if needed. This is also written as `~/.agents/plugins/marketplace.json`
in the Codex docs.

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

The path starts from your user folder, not from `.agents/plugins`.
Use the forward slashes shown in the JSON on every platform.
See OpenAI's [personal marketplace documentation](https://developers.openai.com/plugins/build/plugins#install-a-local-plugin-manually).

After repairing the source and catalog, restart Codex Desktop. Open **Plugins**,
select **Personal** (or the catalog's display name), and install or update
**AI Software Architect**. Confirm the version against the download's `VERSION.txt`,
review all five hooks, and test a new task in another existing project.

If the problem remains, use the repository's
[support page](https://github.com/leomuf/ai-software-architect/blob/main/SUPPORT.md).
Do not share credentials, private repository content, or sensitive diagnostic data.
