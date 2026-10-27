# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Exercise the packaged short-lived Codex hook runtime."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

try:
    from adapters.codex.inspection import EVIDENCE_PREFIX, SNAPSHOT_REQUEST
except ModuleNotFoundError as exc:
    if exc.name != "adapters":
        raise
    from inspection import (  # type: ignore[import-not-found, no-redef]
        EVIDENCE_PREFIX,
        SNAPSHOT_REQUEST,
    )


def _smoke_snapshot_gate(
    executable: Path,
    powershell: str,
    hook_command: str,
    base: dict[str, object],
    environment: dict[str, str],
    workspace: Path,
) -> None:
    (workspace / "--pre=sh").write_bytes(b"")
    (workspace / "payload.py").write_bytes(b"touch EXECUTED\n")
    (workspace / ".env").write_bytes(b"SECRET=not-evidence\n")
    payload = {
        **base, "hook_event_name": "PreToolUse", "tool_name": "Bash",
        "tool_input": {"command": SNAPSHOT_REQUEST},
    }
    response = _hook_output(_run_hook(powershell, hook_command, payload, environment))
    if response.get("permissionDecision") != "deny":
        raise RuntimeError("snapshot request allowed shell execution")
    snapshot = json.loads(str(response["permissionDecisionReason"]).removeprefix(EVIDENCE_PREFIX))
    paths = {item["path"] for item in snapshot["files"]}
    if "sample.py" not in paths or ".env" in paths:
        raise RuntimeError("hook snapshot did not preserve static-read boundaries")
    for command in ("rg needle *", "git show HEAD", "Get-Content sample.py",
                    SNAPSHOT_REQUEST + "; echo unsafe", str(executable)):
        denied = _hook_output(_run_hook(
            powershell, hook_command,
            {**payload, "tool_input": {"command": command}}, environment,
        ))
        if denied.get("permissionDecision") != "deny":
            raise RuntimeError("unsafe shell launch was accepted")
    if (workspace / "EXECUTED").exists():
        raise RuntimeError("project code ran during static inspection")


def _windows_hook_commands(executable: Path) -> dict[str, str]:
    plugin_root = executable.resolve().parents[3]
    hooks = json.loads((plugin_root / "hooks" / "hooks.json").read_text("utf-8"))
    commands = {
        event: groups[0]["hooks"][0]["commandWindows"]
        for event, groups in hooks["hooks"].items()
    }
    if not all(isinstance(command, str) for command in commands.values()):
        raise TypeError("every Windows hook command must be a string")
    return commands


def _run_hook(
    powershell: str,
    command: str,
    payload: dict[str, object],
    environment: dict[str, str],
) -> dict[str, object]:
    result = subprocess.run(  # noqa: S603
        [powershell, "-NoProfile", "-NonInteractive", "-Command", command],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=environment,
        timeout=10,
        check=True,
    )
    if result.stderr:
        raise RuntimeError(f"hook runtime wrote to stderr:\n{result.stderr}")
    return json.loads(result.stdout)  # type: ignore[no-any-return]


def _hook_output(response: dict[str, object]) -> dict[str, object]:
    output = response.get("hookSpecificOutput")
    if not isinstance(output, dict):
        raise RuntimeError(f"hook response has no structured output: {response}")
    return output


def smoke_test_hook(executable: Path) -> None:
    powershell = shutil.which("powershell.exe")
    if powershell is None:
        raise RuntimeError("PowerShell is required to test the Windows hook command")
    self_test = subprocess.run(  # noqa: S603
        [str(executable), "--self-test"],
        text=True, capture_output=True, timeout=10, check=True,
    )
    if self_test.stderr or json.loads(self_test.stdout) != {
        "status": "ok", "runtime": "ai-architect-runtime",
    }:
        raise RuntimeError("packaged runtime self-test failed")
    commands = _windows_hook_commands(executable)
    with tempfile.TemporaryDirectory() as plugin_data, tempfile.TemporaryDirectory() as workspace:
        sample = Path(workspace) / "sample.py"
        sample.write_text("import pathlib\n", encoding="utf-8")
        snapshot_result = subprocess.run(  # noqa: S603
            [str(executable), "--repository-snapshot", "--root", "."],
            cwd=workspace,
            text=True,
            capture_output=True,
            timeout=10,
            check=True,
        )
        snapshot = json.loads(snapshot_result.stdout)
        if snapshot["files"][0]["path"] != "sample.py":
            raise RuntimeError(f"bounded repository snapshot failed: {snapshot}")

        environment = os.environ.copy()
        environment["PLUGIN_DATA"] = plugin_data
        environment["PLUGIN_ROOT"] = str(executable.resolve().parents[3])
        environment["AI_ARCHITECT_HOOK_DEBUG"] = "1"
        base: dict[str, object] = {
            "session_id": "smoke-session",
            "turn_id": "smoke-turn",
            "cwd": workspace,
        }
        submit = {
            **base,
            "hook_event_name": "UserPromptSubmit",
            "prompt": "$ai-software-architect Review this project architecture.",
        }
        response = _run_hook(powershell, commands["UserPromptSubmit"], submit, environment)
        context = _hook_output(response).get("additionalContext")
        if "Route: model-selected workflow" not in str(context):
            raise RuntimeError(f"hook routing smoke test failed: {response}")
        _smoke_snapshot_gate(
            executable, powershell, commands["PreToolUse"], base, environment, Path(workspace),
        )

        compact = {
            **base,
            "hook_event_name": "PostCompact",
            "trigger": "auto",
        }
        compact_response = _run_hook(powershell, commands["PostCompact"], compact, environment)
        compact_context = _hook_output(compact_response).get("additionalContext")
        if "typed workflow checkpoint: phase=active" not in str(compact_context):
            raise RuntimeError(
                f"workflow checkpoint restoration failed: {compact_response}"
            )

        shell = {
            **base,
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "python -m py_compile analyzed_repository.py"},
        }
        shell_response = _run_hook(powershell, commands["PreToolUse"], shell, environment)
        if _hook_output(shell_response).get("permissionDecision") != "deny":
            raise RuntimeError(f"read-only shell guard failed: {shell_response}")

        invalid_contract = {
            **base,
            "hook_event_name": "PreToolUse",
            "tool_name": "apply_patch",
            "tool_input": (
                "*** Begin Patch\n*** Add File: .ai-architect/architecture-contract.yaml\n"
                "+schema_version: invalid\n+revision: 0\n+scope: smoke-test\n"
                "*** End Patch"
            ),
        }
        invalid_response = _run_hook(
            powershell, commands["PreToolUse"], invalid_contract, environment
        )
        if _hook_output(invalid_response).get("permissionDecision") != "deny":
            raise RuntimeError(f"invalid contract was not blocked: {invalid_response}")

        valid_yaml = (
            "schema_version: 1.0.0\nrevision: 1\nscope: smoke-test\n"
            "architecture_style: null\nquality_attributes: []\ncomponents: []\n"
            "external_boundaries: []\ndependency_rules: []\nrequired_practices: []\n"
            "prohibited_practices: []\ndecision_ids: []\nunresolved_questions: []\n"
        )
        valid_contract = {
            **base,
            "hook_event_name": "PreToolUse",
            "tool_name": "apply_patch",
            "tool_input": (
                "*** Begin Patch\n*** Add File: .ai-architect/architecture-contract.yaml\n"
                + "".join(f"+{line}\n" for line in valid_yaml.splitlines())
                + "*** End Patch"
            ),
        }
        if _run_hook(
            powershell, commands["PreToolUse"], valid_contract, environment
        ) != {}:
            raise RuntimeError("valid architecture contract was unexpectedly blocked")

        unsupported_artifact = {
            **base,
            "hook_event_name": "PreToolUse",
            "tool_name": "apply_patch",
            "tool_input": (
                "*** Begin Patch\n*** Add File: .ai-architect/unvalidated-notes.md\n"
                "+content that cannot bypass artifact validation\n*** End Patch"
            ),
        }
        unsupported_response = _run_hook(
            powershell, commands["PreToolUse"], unsupported_artifact, environment
        )
        if _hook_output(unsupported_response).get("permissionDecision") != "deny":
            raise RuntimeError(
                "unsupported architecture artifact path was not blocked: "
                f"{unsupported_response}"
            )

        stop = {
            **base,
            "hook_event_name": "Stop",
            "stop_hook_active": False,
            "last_assistant_message": (
                "## Your decision\nPlease approve, revise, or ask for more information.\n\n"
                "<!-- ai-architect-outcome: recommendation -->"
            ),
        }
        stop_response = _run_hook(powershell, commands["Stop"], stop, environment)
        if stop_response.get("decision") != "block":
            raise RuntimeError(f"visible-response marker guard failed: {stop_response}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    args = parser.parse_args()
    smoke_test_hook(args.executable)
    print("Short-lived Codex hook runtime smoke test passed")


if __name__ == "__main__":
    main()
