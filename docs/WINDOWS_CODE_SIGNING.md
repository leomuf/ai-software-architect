<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Windows Release Signing

The `--self-test` command and installation prompt are platform-neutral. These
signing helpers are for Windows Authenticode only. Future macOS packages need
Developer ID signing, notarization, and Gatekeeper tests; see
[Apple's distribution guidance](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution).
Linux packages need native runtime builds and checks for their supported
distributions and execution policies. A Windows certificate does not establish
macOS or Linux package compatibility. Neither native package is available yet.

Windows Smart App Control blocked the unsigned 0.2.4 runtime in the clean Windows
Sandbox test. The older 0.2.3 runtime was also blocked there. Windows reported
error 4551 and Code Integrity event 3077 under the `VerifiedAndReputableDesktop`
policy. Folder trust and Codex hook approval do not override this Windows check.

## Required Signing Identity

The project currently has no configured trusted Code Signing identity. S/MIME
certificates are for email and cannot replace a Code Signing certificate.
The required certificate purpose is Code Signing (`1.3.6.1.5.5.7.3.3`), with a
publicly trusted issuer suitable for Windows distribution.

These scripts prepare the release process; they do not issue certificates or make
an unsigned package compatible with Smart App Control. The signed package must
still pass a clean Windows test with Smart App Control enabled. A self-signed or
privately trusted development certificate does not prove public compatibility.

## Build, Sign, Then Assemble

Signing changes file bytes. Sign the build runtime **before** assembling the plugin
and recording provenance. Do not sign an assembled plugin or edit an existing ZIP.

1. Build the runtime without assembling the plugin:

   ```powershell
   uv run python adapters/codex/build_plugin.py --build-runtime-only
   ```

2. Have the approved signing provider sign the unsigned executables, DLLs, and
   Python extensions. List the inputs with:

   ```powershell
   .\scripts\check-windows-runtime-signatures.ps1 -RuntimePath build/runtime/ai-architect-runtime -Mode ListUnsigned
   ```

   The check requires embedded signatures instead of relying on a catalog installed
   only on the build machine. It preserves signatures Windows identifies as valid
   Authenticode signatures. Catalog-reported files are selected for embedded signing.
   Verification uses the Windows SDK SignTool when catalog lookup would hide the
   embedded signature; its automatic catalog fallback is disabled for that check.
   Linked paths and invalid signatures stop the operation.

   If the certificate and key provider are already available in `CurrentUser\My`,
   use the installed Windows SDK SignTool without exporting the private key:

   ```powershell
   .\scripts\sign-windows-runtime.ps1 `
     -RuntimePath build/runtime/ai-architect-runtime `
     -CertificateThumbprint '<Code Signing certificate thumbprint>' `
     -SignToolPath '<absolute path to signtool.exe>' `
     -TimestampServer '<provider HTTPS RFC3161 timestamp URL>'
   ```

   This helper rejects S/MIME and self-signed certificates. Obtain the certificate
   and timestamp endpoint from the publisher's approved signing provider.

3. Verify with the exact subject from the reviewed publisher certificate:

   ```powershell
   .\scripts\check-windows-runtime-signatures.ps1 `
     -RuntimePath build/runtime/ai-architect-runtime `
     -ExpectedPublisherSubject '<exact publisher certificate subject>'
   ```

   Every executable file must have a valid embedded Code Signing signature.
   The entry executable must match the publisher and have a timestamp.

4. Assemble the signed runtime, then follow [RELEASING.md](RELEASING.md) for package
   validation, runtime smoke tests, and the remaining release gates:

   ```powershell
   uv run python adapters/codex/build_plugin.py --runtime build/runtime/ai-architect-runtime --plugin-version 0.2.4
   ```

## GitHub Release Gate

The tag workflow verifies signatures before assembly. Set the repository variable
`WINDOWS_SIGNING_PUBLISHER_SUBJECT` to the exact reviewed certificate subject. This
is public metadata, not a password or private key.

**The workflow intentionally stops until signing is configured.** The approved
signing step still needs integration between build and verification. Setting the
publisher variable alone does not sign files. No signing service, credentials,
cloud resources, or OIDC access have been configured. Ordinary CI continues to
build unsigned development packages; those are not signed public release candidates.

## Installation Acceptance

The runtime accepts `--self-test`. It loads hook dependencies, returns
`{"status":"ok","runtime":"ai-architect-runtime"}`, and exits without reading
project files or writing hook state. A startup error means setup is incomplete.
Visible or approved hook switches alone do not prove execution works.

If Windows reports error 4551, report the application-control block. Do not disable
Smart App Control, install an untrusted root certificate, or move hooks outside
the plugin as a workaround.

References: [App Control diagnostics](https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/operations/appcontrol-debugging-and-troubleshooting),
[policy identities](https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/operations/inbox-appcontrol-policies),
and [Smart App Control](https://learn.microsoft.com/en-us/windows/apps/develop/smart-app-control/overview).
