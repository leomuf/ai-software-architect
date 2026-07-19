# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Launch the packaged STDIO runtime and exercise pathless deterministic tools."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import TextIO, cast

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

EXPECTED_TOOLS = {
    "validate_complete_architecture_contract",
    "analyze_python_dependencies",
    "check_python_architecture_boundaries",
    "scan_generated_architecture_artifact",
}


async def smoke_test(executable: Path) -> None:
    parameters = StdioServerParameters(command=str(executable.resolve()), args=[])
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as errlog:
        async with stdio_client(parameters, errlog=cast(TextIO, errlog)) as (
            read_stream,
            write_stream,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                initialized = await session.initialize()
                tools = await session.list_tools()
                names = {tool.name for tool in tools.tools}
                if names != EXPECTED_TOOLS:
                    raise RuntimeError(f"unexpected tool set: {sorted(names)}")
                result = await session.call_tool(
                    "validate_complete_architecture_contract",
                    arguments={
                        "request": {
                            "validation_scope": "complete-candidate-contract",
                            "yaml_content": (
                                "schema_version: 1.0.0\nrevision: 1\nscope: smoke-test\n"
                            ),
                        }
                    },
                )
                if result.isError:
                    raise RuntimeError(f"pathless validation failed: {result.content}")
                dependency_result = await session.call_tool(
                    "analyze_python_dependencies",
                    arguments={
                        "request": {
                            "dependency_statements": [
                                {
                                    "relative_path": "budget.py",
                                    "start_line": 9,
                                    "statement": "import decimal",
                                }
                            ],
                            "languages": ["python"],
                        }
                    },
                )
                if dependency_result.isError:
                    raise RuntimeError(
                        f"inline dependency analysis failed: {dependency_result.content}"
                    )
                structured = dependency_result.structuredContent or {}
                edges = structured.get("result", {}).get("edges", [])
                if not any(
                    edge.get("source") == "budget"
                    and edge.get("target") == "decimal"
                    and edge.get("evidence") == "budget.py:9"
                    for edge in edges
                ):
                    raise RuntimeError(
                        f"inline dependency evidence was missing: {dependency_result.content}"
                    )
                print(
                    f"{initialized.serverInfo.name}: {len(names)} tools; "
                    "pathless validation and fast statement analysis succeeded"
                )
        errlog.seek(0)
        stderr = errlog.read()
        if "Traceback" in stderr:
            raise RuntimeError(f"runtime wrote a traceback to stderr:\n{stderr}")


def _windows_hook_command(executable: Path) -> str:
    plugin_root = executable.resolve().parents[3]
    hooks_path = plugin_root / "hooks" / "hooks.json"
    hooks = json.loads(hooks_path.read_text("utf-8"))
    command = hooks["hooks"]["UserPromptSubmit"][0]["hooks"][0]["commandWindows"]
    if not isinstance(command, str):
        raise TypeError("the Windows hook command must be a string")
    return command


def smoke_test_hook(executable: Path) -> None:
    with tempfile.TemporaryDirectory() as plugin_data:
        payload = {
            "session_id": "smoke-session",
            "turn_id": "smoke-turn",
            "hook_event_name": "UserPromptSubmit",
            "prompt": (
                "$ai-software-architect I want a web interface built with Tkinter. "
                "Which architecture should I use?"
            ),
        }
        environment = os.environ.copy()
        environment["PLUGIN_DATA"] = plugin_data
        environment["PLUGIN_ROOT"] = str(executable.resolve().parents[3])
        command = _windows_hook_command(executable)
        powershell = shutil.which("powershell.exe")
        if powershell is None:
            raise RuntimeError("PowerShell is required to test the Windows hook command")
        result = subprocess.run(  # noqa: S603
            [
                powershell,
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                command,
            ],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=environment,
            timeout=10,
            check=True,
        )
        response = json.loads(result.stdout)
        context = response["hookSpecificOutput"]["additionalContext"]
        if "Route: complete architecture workflow" not in context:
            raise RuntimeError(f"hook routing smoke test failed: {response}")
        if result.stderr:
            raise RuntimeError(f"hook runtime wrote to stderr:\n{result.stderr}")

        shell_payload = {
            "session_id": "smoke-session",
            "turn_id": "smoke-turn",
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {
                "command": "python -m py_compile analyzed_repository.py",
            },
        }
        shell_guard = subprocess.run(  # noqa: S603
            [
                powershell,
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                command,
            ],
            input=json.dumps(shell_payload),
            text=True,
            capture_output=True,
            env=environment,
            timeout=10,
            check=True,
        )
        shell_response = json.loads(shell_guard.stdout)
        if (
            shell_response.get("hookSpecificOutput", {}).get(
                "permissionDecision"
            )
            != "deny"
            or "does not run interpreters"
            not in shell_response.get("hookSpecificOutput", {}).get(
                "permissionDecisionReason",
                "",
            )
        ):
            raise RuntimeError(
                f"read-only shell guard smoke test failed: {shell_response}"
            )
        if shell_guard.stderr:
            raise RuntimeError(
                f"read-only shell hook runtime wrote to stderr:\n{shell_guard.stderr}"
            )

        stop_payload = {
            "session_id": "smoke-session",
            "turn_id": "smoke-turn",
            "hook_event_name": "Stop",
            "stop_hook_active": False,
            "last_assistant_message": (
                "I recommend a modular monolith.\n\n"
                "<!-- ai-architect-outcome: recommendation -->"
            ),
        }
        outcome_guard = subprocess.run(  # noqa: S603
            [
                powershell,
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                command,
            ],
            input=json.dumps(stop_payload),
            text=True,
            capture_output=True,
            env=environment,
            timeout=10,
            check=True,
        )
        outcome_response = json.loads(outcome_guard.stdout)
        if (
            outcome_response.get("decision") != "block"
            or "approve, revise, more-information action marker"
            not in outcome_response.get("reason", "")
        ):
            raise RuntimeError(
                f"complete-workflow outcome guard failed: {outcome_response}"
            )
        if outcome_guard.stderr:
            raise RuntimeError(
                "complete-workflow outcome guard wrote to stderr:\n"
                f"{outcome_guard.stderr}"
            )

        payload["turn_id"] = "smoke-turn-missing-skill"
        payload["prompt"] = (
            "[@AI Software Architect]"
            "(plugin://ai-software-architect@personal) "
            "Suggest design templates for my project."
        )
        missing_skill = subprocess.run(  # noqa: S603
            [
                powershell,
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                command,
            ],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=environment,
            timeout=10,
            check=True,
        )
        missing_response = json.loads(missing_skill.stdout)
        if (
            missing_response.get("decision") != "block"
            or "$ai-software-architect" not in missing_response.get("reason", "")
            or "$evaluate-architecture-options"
            not in missing_response.get("reason", "")
        ):
            raise RuntimeError(
                f"missing-skill hook smoke test failed: {missing_response}"
            )
        if missing_skill.stderr:
            raise RuntimeError(
                f"missing-skill hook runtime wrote to stderr:\n{missing_skill.stderr}"
            )

        payload["turn_id"] = "smoke-turn-pattern-reference"
        payload["prompt"] = (
            "$evaluate-architecture-options Give an Abstract Factory Python example."
        )
        pattern_reference = subprocess.run(  # noqa: S603
            [
                powershell,
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                command,
            ],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=environment,
            timeout=10,
            check=True,
        )
        pattern_response = json.loads(pattern_reference.stdout)
        pattern_context = pattern_response["hookSpecificOutput"]["additionalContext"]
        if (
            "<bundled-canonical-reference>" not in pattern_context
            or "from typing import Protocol" not in pattern_context
            or "Do not fetch another copy from the web" not in pattern_context
        ):
            raise RuntimeError(
                f"bundled pattern injection smoke test failed: {pattern_response}"
            )
        if pattern_reference.stderr:
            raise RuntimeError(
                "pattern-reference hook runtime wrote to stderr:\n"
                f"{pattern_reference.stderr}"
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    args = parser.parse_args()
    asyncio.run(smoke_test(args.executable))
    smoke_test_hook(args.executable)


if __name__ == "__main__":
    main()
