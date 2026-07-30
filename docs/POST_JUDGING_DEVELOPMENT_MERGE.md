<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Merge Development After the Hackathon Judging Period

## Purpose

This guide records how to merge work from the separate private development
repository back into the submitted repository after the OpenAI Build Week winner
announcement.

Do not run these commands during the judging period. Until the organizers permit
changes again, do not push commits, branches, tags, releases, or other changes to the
submitted repository.

## Assumptions

- `main` is the frozen branch in the submitted repository.
- `develop` contains the reviewed post-submission work in the separate development
  repository.
- Both repositories share the submitted commit as a common ancestor.
- The submitted repository is addressed by the `submission` remote.
- The private development repository is addressed by the `development` remote.
- The working tree is clean before the integration begins.

## 1. Verify the local repository

Open PowerShell in the `ai-software-architect` repository:

```powershell
Set-Location C:\projects\OpenAIBuildWeek\ai-software-architect
git status
git remote -v
```

Do not continue if `git status` reports uncommitted changes. Commit them to the
appropriate development branch or preserve them separately first.

## 2. Add the development remote

If the `development` remote does not exist yet:

```powershell
git remote add development <URL-OF-THE-DEVELOPMENT-REPOSITORY>
```

If it already exists, verify its URL instead:

```powershell
git remote get-url development
```

## 3. Fetch the development history

```powershell
git fetch development
```

Fetching updates the local remote-tracking branches. It does not modify local
`main`.

## 4. Review the history and changes

```powershell
git log --oneline --graph --decorate --all
git diff main...development/develop
```

Confirm that:

- `main` still points to the submitted history;
- `development/develop` starts from the expected submission commit;
- only intended post-submission changes will be merged;
- generated caches, credentials, temporary files, and local test artifacts are not
  included.

## 5. Update local `main`

```powershell
git switch main
git status
git pull --ff-only submission main
```

`--ff-only` prevents an unexpected local merge while synchronizing the frozen
submission branch.

## 6. Merge the reviewed development branch

```powershell
git merge --no-ff development/develop
```

The explicit merge commit preserves the boundary between:

- the frozen hackathon submission; and
- development performed during the judging period.

If conflicts occur, do not push an incomplete merge. Resolve and review each
conflict, run the required validation, and inspect the resulting diff before
continuing.

## 7. Validate the merged result

Run the project checks appropriate for the next release. At minimum, inspect:

```powershell
git status
git diff submission/main...main
git log --oneline --graph --decorate --max-count 30
```

Build, test, and run the exploratory release checks according to
[`RELEASING.md`](RELEASING.md) before publishing the merged result.

## 8. Push the integrated `main`

Only after the winner announcement, organizer permission, merge review, and
successful validation:

```powershell
git push submission main
```

## Optional cleanup

After the integration is safely published, keep the development repository for
traceability or archive it according to the project retention policy. Do not delete
it until the merge commit, remote branch, and required release evidence have been
verified.

