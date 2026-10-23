# PR #28 review response draft

This is a local draft, not a posted GitHub response. The contribution is based on
upstream `bcc30295440934fc7e56c4acd6fbe14efd53fadf`, with the macOS changes
selectively reapplied. It retains upstream's Python architecture and current
security policy.

1. **Inspection safety:** retained the v0.2.4 trusted-hook read protocol and shell
   denial implementation. The native smoke tester now runs on Windows and macOS
   and preserves the malicious-filename and command-mutation assertions. It also
   checks all five hook entry points, including post-write mismatch detection.
2. **Windows typing:** guarded Windows-only filesystem/process APIs with explicit
   `sys.platform` branches. Strict mypy passes on Linux and macOS; mypy's Windows
   platform analysis passes on Linux. Actual Windows execution remains a CI gate.
3. **Path and permission tests:** native macOS tests execute on macOS and skip
   elsewhere. Shared tests retain portable target checks; a regression test
   compares every generated Windows hook command with the unchanged template.
   The executable-permission validator remains enforced.
4. **Checksums:** retained upstream's release collector and its existing validation
   tests. The final job now depends on both native builds and expects both ZIPs.
   No separate checksum merger is introduced.
5. **Native release evidence:** built an Apple Silicon runtime, packaged it,
   extracted it with `ditto`, validated provenance and executable permissions, and
   smoke-tested the extracted runtime with `PATH=/usr/bin:/bin`. ZIP members now
   include the regular-file type as well as permission bits; without the type,
   `ditto` discarded executable permissions. No post-extraction repair is used.

Validation: Linux has 374 passing tests and 5 native-platform skips; macOS has
377 passing tests and 2 Windows skips. Ruff and strict mypy pass on both hosts.
The installed Mac app-server workflow completed recommendation, approval, validated
four-artifact persistence, and uninstall with no application-source changes or
shell executions. All five hooks were trusted; temporary trust entries were removed.
Detailed candidate identity and remaining acceptance gates are recorded in
[the macOS evidence](releases/pr28-macos-validation.md).

The existing uncommitted PR checkout was left intact. Windows native CI, Desktop
UI installation, clean-machine acceptance, and the real two-platform publication
set must still be completed before release. This draft has not been posted as a
GitHub comment, and no release has been published by this work.
