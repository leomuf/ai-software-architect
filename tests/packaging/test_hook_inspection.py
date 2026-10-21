# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from adapters.codex.hook_entry import handle_hook
from adapters.codex.inspection import EVIDENCE_PREFIX, RESOURCE_REQUEST, SNAPSHOT_REQUEST


def _request(tmp_path: Path, command: str, **overrides: object) -> dict[str, object]:
    workspace = tmp_path / "workspace"
    workspace.mkdir(exist_ok=True)
    (workspace / "README.md").write_bytes(b"workspace evidence")
    payload = {
        "hook_event_name": "UserPromptSubmit", "session_id": "inspection",
        "turn_id": "first", "cwd": str(workspace),
        "prompt": "$ai-software-architect Review this project.",
    }
    data, plugin = tmp_path / "data", tmp_path / "plugin"
    handle_hook(payload, data, plugin)
    return handle_hook({
        **payload, "hook_event_name": "PreToolUse", "tool_name": "Bash",
        "tool_input": {"command": command}, **overrides,
    }, data, plugin)["hookSpecificOutput"]  # type: ignore[no-any-return]


@pytest.mark.parametrize("suffix", [" ", "\n", "; python app.py", " --root .."])
def test_modified_snapshot_request_never_returns_evidence(tmp_path: Path, suffix: str) -> None:
    output = _request(tmp_path, SNAPSHOT_REQUEST + suffix)
    assert output["permissionDecision"] == "deny"
    assert EVIDENCE_PREFIX not in str(output["permissionDecisionReason"])


def test_read_uses_host_workspace_not_model_arguments(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "README.md").write_text("outside evidence", encoding="utf-8")
    output = _request(tmp_path, SNAPSHOT_REQUEST, tool_input={
        "command": SNAPSHOT_REQUEST, "cwd": str(outside), "workdir": str(outside),
        "root": str(outside), "shell": "./project-shell", "login": True,
        "env": {"BASH_ENV": "./bootstrap.sh"},
    })
    assert output["permissionDecision"] == "deny"
    evidence = json.loads(str(output["permissionDecisionReason"]).removeprefix(EVIDENCE_PREFIX))
    assert evidence["files"][0]["content"] == "workspace evidence"
    assert "untrusted data" in evidence["trust"]


@pytest.mark.parametrize("cwd", [None, "", "relative", "missing-absolute-root"])
def test_invalid_workspace_returns_no_evidence(tmp_path: Path, cwd: str | None) -> None:
    value = str(tmp_path / "missing") if cwd == "missing-absolute-root" else cwd
    output = _request(tmp_path, SNAPSHOT_REQUEST, cwd=value)
    assert output["permissionDecision"] == "deny"
    assert EVIDENCE_PREFIX not in str(output["permissionDecisionReason"])


@pytest.mark.parametrize("relative", [
    "../README.md", "references/../../README.md", "references/x.md; echo unsafe",
    "references/x.md\n", "C:/private.md", "/private.md", "references/x.py",
    "references\\x.md", "references/missing.md",
])
def test_invalid_resource_requests_are_denied(tmp_path: Path, relative: str) -> None:
    output = _request(tmp_path, RESOURCE_REQUEST + relative)
    assert output["permissionDecision"] == "deny"
    assert EVIDENCE_PREFIX not in str(output["permissionDecisionReason"])


def test_resource_reads_installed_file_and_enforces_budget(tmp_path: Path) -> None:
    root = tmp_path / "plugin" / "skills" / "ai-software-architect"
    resource = root / "references" / "workflow-review.md"
    resource.parent.mkdir(parents=True)
    resource.write_bytes(b"# Trusted workflow")
    output = _request(tmp_path, RESOURCE_REQUEST + "references/workflow-review.md")
    assert output["permissionDecision"] == "deny"
    evidence = json.loads(str(output["permissionDecisionReason"]).removeprefix(EVIDENCE_PREFIX))
    assert evidence["content"] == "# Trusted workflow"
    resource.write_bytes(b"x" * 131_073)
    output = _request(tmp_path, RESOURCE_REQUEST + "references/workflow-review.md")
    assert EVIDENCE_PREFIX not in str(output["permissionDecisionReason"])


@pytest.mark.parametrize("link_kind", ["directory"] if sys.platform == "win32"
                         else ["file", "directory"])
def test_linked_resource_is_rejected(tmp_path: Path, link_kind: str) -> None:
    # Use a real junction on Windows without needing the symlink privilege.
    # macOS/Linux also exercise a symlink at the resource file itself.
    outside = tmp_path / "outside"
    outside.mkdir()
    target = outside / "linked.md"
    target.write_bytes(b"outside data must not enter hook evidence")
    references = tmp_path / "plugin/skills/ai-software-architect/references"
    references.parent.mkdir(parents=True)
    resource = references / "linked.md"
    if link_kind == "file":
        references.mkdir()
        link = resource
        link.symlink_to(target)
    else:
        link = references
        if sys.platform == "win32":
            # CPython's Windows helper avoids invoking a shell in this fixture.
            import _winapi

            _winapi.CreateJunction(str(outside), str(link))
            assert link.is_junction()
        else:
            link.symlink_to(outside, target_is_directory=True)
    try:
        assert resource.resolve(strict=True) == target.resolve(strict=True)
        assert resource.read_bytes() == target.read_bytes()
        output = _request(tmp_path, RESOURCE_REQUEST + "references/linked.md")
        assert output["permissionDecision"] == "deny"
        assert EVIDENCE_PREFIX not in str(output["permissionDecisionReason"])
        assert "outside data" not in str(output["permissionDecisionReason"])
    finally:
        # Remove only the link, never recursively traverse its target.
        if sys.platform == "win32":
            assert link.is_junction()
            link.rmdir()
        else:
            link.unlink()
    assert target.read_bytes() == b"outside data must not enter hook evidence"


def test_reparse_workspace_is_rejected_without_reading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from adapters.codex import inspection

    monkeypatch.setattr(inspection, "_is_reparse_point", lambda path: path.name == "workspace")
    output = _request(tmp_path, SNAPSHOT_REQUEST)
    assert output["permissionDecision"] == "deny"
    assert EVIDENCE_PREFIX not in str(output["permissionDecisionReason"])


def test_focused_activation_never_requests_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from adapters.codex import inspection

    def unexpected_read(root: Path) -> None:
        pytest.fail("activation must not inspect the repository")

    monkeypatch.setattr(inspection, "create_repository_snapshot", unexpected_read)
    result = handle_hook({
        "hook_event_name": "UserPromptSubmit", "session_id": "focused", "turn_id": "one",
        "cwd": str(tmp_path), "prompt": "$ai-software-architect Explain Abstract Factory.",
    }, tmp_path / "data")
    assert "gof-abstract-factory.md" in result["hookSpecificOutput"]["additionalContext"]


def test_activation_reads_nothing_and_continuation_keeps_read_protocol(tmp_path: Path) -> None:
    # A nonexistent cwd proves that activation does not prefetch repository contents.
    payload = {
        "hook_event_name": "UserPromptSubmit", "session_id": "continuation",
        "turn_id": "first", "cwd": str(tmp_path / "missing"),
        "prompt": "$ai-software-architect Clarify this project.",
    }
    data = tmp_path / "data"
    result = handle_hook(payload, data)
    assert SNAPSHOT_REQUEST in result["hookSpecificOutput"]["additionalContext"]
    assert not (tmp_path / "missing").exists()
    handle_hook({**payload, "hook_event_name": "Stop",
                 "last_assistant_message": "Which language?"}, data)
    result = handle_hook({**payload, "turn_id": "second", "prompt": "Python."}, data)
    assert SNAPSHOT_REQUEST in result["hookSpecificOutput"]["additionalContext"]
    output = handle_hook({**payload, "turn_id": "second", "cwd": str(tmp_path),
                         "hook_event_name": "PreToolUse", "tool_name": "Bash",
                         "tool_input": {"command": "python app.py"}}, data)
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_inactive_hook_does_not_read_or_intercept_requests(tmp_path: Path) -> None:
    result = handle_hook({
        "hook_event_name": "PreToolUse", "session_id": "inactive", "turn_id": "one",
        "cwd": str(tmp_path), "tool_name": "Bash",
        "tool_input": {"command": SNAPSHOT_REQUEST},
    }, tmp_path / "data")
    assert result == {}
