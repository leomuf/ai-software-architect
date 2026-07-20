<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Release Evidence Records

Store one sanitized release-gate record per published version in this directory
when a version-controlled copy is useful. Create each record from
[`../release-evidence-template.md`](../release-evidence-template.md) and name it
after the plugin version, for example:

```text
0.1.0-beta.1.md
```

Complete the working record without changing the tested candidate commit. Attach it
to the GitHub Release first; commit this documentation copy after the release tag
and link it to that immutable tag.

Do not commit credentials, hidden reasoning, unnecessary repository content, or
sensitive local paths.
