# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adapters.codex import control_plane
from adapters.codex.hook_entry import handle_pre_tool_use, handle_user_prompt_submit
from adapters.codex.inspection import EVIDENCE_PREFIX, SNAPSHOT_REQUEST
from adapters.codex.snapshot_launch import default_snapshot_shell, snapshot_shells

ROOT = Path(__file__).resolve().parents[2]


def _activate(data: Path, workspace: Path, plugin: Path) -> dict[str, object]:
    payload: dict[str, object] = {
        "session_id": "snapshot-security", "turn_id": "one", "cwd": str(workspace),
        "hook_event_name": "UserPromptSubmit",
        "prompt": "$ai-software-architect Review this repository.",
    }
    handle_user_prompt_submit(payload, data, plugin)
    return dict(payload, hook_event_name="PreToolUse", tool_name="exec_command")


@pytest.mark.parametrize("change", [
    {"cmd": "rg needle *"},
    {"cmd": "git show HEAD"},
    {"cmd": "Get-Content app.py"},
    {"shell": "bash"},
    {"shell": "powershell.exe"},
    {"shell": "./project-shell.exe"},
    {"login": True},
    {"login": None},
    {"tty": True},
    {"env": {"BASH_ENV": "./bootstrap.sh"}},
    {"executable": "./project-shell"},
    {"shell_args": ["-File", "./bootstrap.ps1"]},
    {"sandbox_permissions": "require_escalated"},
    {"workdir": ".."},
    {"cmd": None},
    {"command": "rg needle *"},
])
def test_pretooluse_rejects_command_and_interpreter_overrides(
    tmp_path: Path, change: dict[str, object],
) -> None:
    data, plugin = tmp_path / "data", tmp_path / "plugin"
    payload = _activate(data, tmp_path, plugin)
    tool_input: dict[str, object] = {
        "cmd": control_plane.repository_snapshot_command(plugin),
        "shell": default_snapshot_shell(), "login": False,
    }
    tool_input.update(change)
    payload["tool_input"] = tool_input
    result = handle_pre_tool_use(payload, data, plugin)
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


@pytest.mark.parametrize("suffix", [
    " --root ..", " --extra", "; echo unsafe", " && echo unsafe", "\necho unsafe", " ",
])
def test_pretooluse_rejects_any_change_to_the_fixed_command(tmp_path: Path, suffix: str) -> None:
    data, plugin = tmp_path / "data", tmp_path / "plugin"
    payload = _activate(data, tmp_path, plugin)
    payload["tool_input"] = {
        "cmd": control_plane.repository_snapshot_command(plugin) + suffix,
        "shell": default_snapshot_shell(), "login": False,
    }
    assert handle_pre_tool_use(payload, data, plugin)["hookSpecificOutput"][
        "permissionDecision"
    ] == "deny"


@pytest.mark.parametrize("tool,key", [("Bash", "command"), ("exec_command", "cmd")])
def test_host_shaped_read_never_executes_project_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tool: str, key: str,
) -> None:
    project = tmp_path / "project's files"
    project.mkdir()
    marker = project / "EXECUTED"
    (project / "--pre=sh").write_text("", encoding="utf-8")
    (project / "sitecustomize.py").write_text(
        "from pathlib import Path\nPath('EXECUTED').touch()\n", encoding="utf-8",
    )
    (project / "README.md").write_bytes(b"# Safe static evidence\n")
    (project / ".env").write_text("SECRET=never-return-this\n", encoding="utf-8")
    monkeypatch.setenv("BASH_ENV", str(project / "sitecustomize.py"))
    data, plugin = tmp_path / "data", tmp_path / "plugin"
    payload = _activate(data, project, plugin)
    payload.update(tool_name=tool, tool_input={key: SNAPSHOT_REQUEST})
    result = handle_pre_tool_use(payload, data, plugin)["hookSpecificOutput"]
    assert result["permissionDecision"] == "deny"
    snapshot = json.loads(result["permissionDecisionReason"].removeprefix(EVIDENCE_PREFIX))
    files = {item["path"]: item["content"] for item in snapshot["files"]}
    assert files["README.md"] == "# Safe static evidence\n"
    assert ".env" not in files
    assert not marker.exists()


def test_pretooluse_rejects_outside_workspace_and_shell_mismatch(tmp_path: Path) -> None:
    data, plugin = tmp_path / "data", tmp_path / "plugin"
    payload = _activate(data, tmp_path, plugin)
    command = control_plane.repository_snapshot_command(plugin)
    payload["tool_input"] = {
        "cmd": command, "shell": default_snapshot_shell(), "login": False,
        "workdir": str(tmp_path.parent),
    }
    assert handle_pre_tool_use(payload, data, plugin)["hookSpecificOutput"][
        "permissionDecision"
    ] == "deny"
    for shell in snapshot_shells():
        if control_plane.repository_snapshot_command(plugin, shell=shell) == command:
            continue
        payload["tool_input"] = {"cmd": command, "shell": shell, "login": False}
        assert handle_pre_tool_use(payload, data, plugin)["hookSpecificOutput"][
            "permissionDecision"
        ] == "deny"


def test_pretooluse_requires_shell_and_disallows_session_input(tmp_path: Path) -> None:
    data, plugin = tmp_path / "data", tmp_path / "plugin"
    payload = _activate(data, tmp_path, plugin)
    command = control_plane.repository_snapshot_command(plugin)
    for tool_input in [command, {"cmd": command}, {"cmd": command, "login": False}]:
        payload["tool_input"] = tool_input
        assert handle_pre_tool_use(payload, data, plugin)["hookSpecificOutput"][
            "permissionDecision"
        ] == "deny"
    payload.update(
        tool_name="write_stdin", tool_input={"session_id": 123, "chars": "python app.py\n"},
    )
    assert handle_pre_tool_use(payload, data, plugin)["hookSpecificOutput"][
        "permissionDecision"
    ] == "deny"


@pytest.mark.parametrize("tool", ["Bash", "shell_command", "write_stdin"])
def test_fixed_command_cannot_be_replayed_through_another_shell_tool(
    tmp_path: Path, tool: str,
) -> None:
    data, plugin = tmp_path / "data", tmp_path / "plugin"
    payload = _activate(data, tmp_path, plugin)
    payload.update(tool_name=tool, tool_input={
        "command": control_plane.repository_snapshot_command(plugin),
        "shell": default_snapshot_shell(), "login": False,
    })
    assert handle_pre_tool_use(payload, data, plugin)["hookSpecificOutput"][
        "permissionDecision"
    ] == "deny"


def test_bash_is_unavailable_with_startup_script_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BASH_ENV", "./project-startup.sh")
    assert "bash" not in snapshot_shells().values()
