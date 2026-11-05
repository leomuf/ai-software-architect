# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Real Codex CLI diagnostic, isolated from legacy hooks and performance history.

The MCP service remains unchanged and never logs payloads. Synthetic client-side
JSONL and local files are evaluation evidence, not service-side project storage.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import shutil
import socket
import subprocess
import tempfile
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import uvicorn
import yaml
from ai_architect_schemas.mcp_workflow import LocalWorkflowCheckpoint, PrepareRequest
from ai_architect_tools.domain.workflow import (
    ReferenceSnapshot,
    canonical_json,
    digest,
    prepare_draft,
)
from ai_architect_tools.workflow_server import PROTOCOL_VERSION, create_app

from .build_instructions import ROOT, build

FIXTURES = {
    name: ROOT / f"shared/evaluations/mcp-prototype/codex-{name}.yaml"
    for name in ("local-review-export", "context-loss", "two-active-reviews")
}
SERVER_NAME = "architect_prototype"
COHORT = "mcp-phase-0-anonymous-stateless-codex-diagnostic"


@dataclass(frozen=True)
class Settings:
    model: str
    reasoning_effort: str
    speed: str = "standard"
    timeout_seconds: int = 600
    max_tool_calls: int = 50
    scenario: str = "local-review-export"


class HostRunError(ValueError):
    """A fixed, non-payload-bearing diagnostic code."""


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): digest(path.read_bytes())
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }


def command(
    executable: str,
    settings: Settings,
    *,
    thread_id: str | None = None,
) -> list[str]:
    result = [
        executable,
        "exec",
        "--json",
        "--strict-config",
        "--model",
        settings.model,
        "--config",
        f'model_reasoning_effort="{settings.reasoning_effort}"',
    ]
    if thread_id is None:
        result.extend(["--sandbox", "workspace-write", "--skip-git-repo-check"])
    else:
        result.extend(["resume", "--skip-git-repo-check", thread_id])
    result.append("-")  # Prompts go through stdin, never shell interpolation.
    return result


def external_skill_paths(auth_root: Path) -> list[Path]:
    roots = [auth_root / "skills", Path.home() / ".agents/skills"]
    return sorted(
        {
            path.resolve()
            for root in roots
            if root.is_dir()
            for path in root.rglob("SKILL.md")
            if path.is_file()
        }
    )


def isolated_config(
    workspace: Path,
    endpoint: str,
    settings: Settings,
    disabled_skills: list[Path],
) -> str:
    quote = json.dumps
    skill_rules = ",\n".join(
        f"  {{ path = {quote(path.as_posix())}, enabled = false }}" for path in disabled_skills
    )
    return f"""# Generated diagnostic profile; no inherited plugin, hook or MCP configuration.
model = {quote(settings.model)}
model_reasoning_effort = {quote(settings.reasoning_effort)}
service_tier = {quote("fast" if settings.speed == "fast" else "default")}
approval_policy = "never"
sandbox_mode = "workspace-write"
web_search = "disabled"
cli_auth_credentials_store = "file"
check_for_update_on_startup = false

[features]
hooks = false
plugins = false
apps = false
multi_agent = false

[skills]
config = [
{skill_rules}
]

[skills.bundled]
enabled = false

[projects.{quote(workspace.as_posix())}]
trust_level = "trusted"

[mcp_servers.{SERVER_NAME}]
url = {quote(endpoint)}
required = true
startup_timeout_sec = 20
tool_timeout_sec = 60

[windows]
sandbox = "unelevated"
"""


@contextmanager
def local_service(references: ReferenceSnapshot) -> Iterator[str]:
    # Loopback HTTP is intentional for local host diagnostics, not HTTPS/remote evidence.
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        endpoint = f"http://127.0.0.1:{listener.getsockname()[1]}/mcp"
        server = uvicorn.Server(
            uvicorn.Config(
                create_app(references, endpoint, loopback_http=True),
                log_level="critical",
                access_log=False,
                proxy_headers=False,
            )
        )
        worker = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
        worker.start()
        try:
            deadline = time.monotonic() + 10
            while not server.started and worker.is_alive() and time.monotonic() < deadline:
                time.sleep(0.02)
            if not server.started:
                raise RuntimeError("loopback-service-startup-failed")
            yield endpoint
        finally:
            server.should_exit = True
            worker.join(timeout=10)
            if worker.is_alive():
                raise RuntimeError("loopback-service-shutdown-failed")


def probe(endpoint: str) -> dict[str, Any]:
    with httpx.Client(trust_env=False, timeout=10) as client:
        response = client.post(
            endpoint,
            headers={"Accept": "application/json, text/event-stream"},
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        )
        response.raise_for_status()
        tools = response.json()["result"]["tools"]
    names = sorted(tool["name"] for tool in tools)
    if names != sorted(
        [
            "get_architecture_capabilities",
            "get_architecture_resource",
            "prepare_architecture_bundle",
        ]
    ):
        raise ValueError("unexpected-mcp-tool-surface")
    return {
        "transport": "loopback-http",
        "authentication": "none",
        "tools": names,
        "persistent_session_header": "mcp-session-id" in response.headers,
    }


def capture_phase(
    argv: list[str],
    prompt: str,
    workspace: Path,
    environment: dict[str, str],
    evidence: Path,
    name: str,
    settings: Settings,
) -> dict[str, Any]:
    started = time.monotonic()
    events: list[dict[str, Any]] = []
    stderr: list[str] = []
    tool_ids: set[str] = set()
    exceeded = threading.Event()
    process = subprocess.Popen(  # noqa: S603
        argv,
        cwd=workspace,
        env=environment,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    assert process.stdin is not None and process.stdout is not None and process.stderr is not None

    def read_stdout() -> None:
        assert process.stdout is not None
        with (evidence / f"{name}.jsonl").open("w", encoding="utf-8", newline="\n") as log:
            for line in process.stdout:
                log.write(line)
                log.flush()
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    events.append({"type": "invalid-jsonl"})
                    continue
                if not isinstance(event, dict):
                    events.append({"type": "invalid-jsonl"})
                    continue
                event["runner_elapsed_seconds"] = round(time.monotonic() - started, 3)
                events.append(event)
                item = event.get("item", {})
                if isinstance(item, dict) and item.get("type") in {
                    "command_execution",
                    "file_change",
                    "mcp_tool_call",
                    "web_search",
                }:
                    tool_ids.add(str(item.get("id")))
                    if len(tool_ids) > settings.max_tool_calls:
                        exceeded.set()

    def read_stderr() -> None:
        assert process.stderr is not None
        stderr.extend(process.stderr)

    readers = [
        threading.Thread(target=reader, daemon=True) for reader in (read_stdout, read_stderr)
    ]
    for reader in readers:
        reader.start()
    process.stdin.write(prompt)
    process.stdin.close()
    stop_reason = ""
    while process.poll() is None:
        if exceeded.is_set() or time.monotonic() - started >= settings.timeout_seconds:
            stop_reason = "tool-budget-exceeded" if exceeded.is_set() else "timeout"
            if os.name == "nt":
                subprocess.run(  # noqa: S603
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],  # noqa: S607
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
            if process.poll() is None:
                process.kill()
            break
        time.sleep(0.1)
    returncode = process.wait(timeout=10)
    for reader in readers:
        reader.join(timeout=10)
    (evidence / f"{name}.stderr.txt").write_text("".join(stderr), encoding="utf-8")
    finals = [
        event["item"]["text"]
        for event in events
        if event.get("type") == "item.completed"
        and isinstance(event.get("item"), dict)
        and event["item"].get("type") == "agent_message"
    ]
    final = finals[-1] if finals else ""
    (evidence / f"{name}.response.md").write_text(final, encoding="utf-8")
    write_json(evidence / f"{name}.timed-events.json", events)
    return {
        "exit_code": returncode,
        "duration_seconds": round(time.monotonic() - started, 3),
        "stop_reason": stop_reason,
        "tool_calls": len(tool_ids),
        "events": events,
        "thread_id": next(
            (event.get("thread_id") for event in events if event.get("type") == "thread.started"),
            None,
        ),
    }


def mcp_calls(phase: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        event["item"]
        for event in phase["events"]
        if event.get("type") == "item.completed"
        and isinstance(event.get("item"), dict)
        and event["item"].get("type") == "mcp_tool_call"
    ]


def event_metrics(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize client-reported usage and observed calls without retaining payloads."""

    calls = mcp_calls({"events": events})
    usage: dict[str, Any] = next(
        (
            event["usage"]
            for event in reversed(events)
            if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict)
        ),
        {},
    )
    return {
        "token_usage": {
            key: usage[key]
            for key in (
                "input_tokens",
                "cached_input_tokens",
                "output_tokens",
                "reasoning_output_tokens",
            )
            if isinstance(usage.get(key), int)
        },
        "mcp_call_count": len(calls),
        "mcp_failed_call_count": sum(item.get("status") == "failed" for item in calls),
        "mcp_tool_names": [item.get("tool") for item in calls],
        "requested_resource_ids": [
            item["arguments"].get("resource_id")
            for item in calls
            if item.get("tool") == "get_architecture_resource"
            and isinstance(item.get("arguments"), dict)
        ],
    }


def payload_from_call(item: dict[str, Any]) -> dict[str, Any]:
    result = item.get("result")
    if not isinstance(result, dict):
        raise ValueError("missing-mcp-result")
    for key in ("structuredContent", "structured_content"):
        if isinstance(result.get(key), dict):
            return result[key]  # type: ignore[no-any-return]
    for block in result.get("content", []):
        if isinstance(block, dict) and block.get("type") == "text":
            try:
                payload = json.loads(block["text"])
            except (ValueError, KeyError):
                continue
            if isinstance(payload, dict) and "ok" in payload:
                return payload
    raise ValueError("missing-structured-mcp-payload")


def load_checkpoints(workspace: Path) -> dict[str, tuple[Path, LocalWorkflowCheckpoint]]:
    directory = workspace / ".ai-architect/.mcp-workflows"
    if directory.is_symlink() or directory.parent.is_symlink():
        raise ValueError("checkpoint-directory-is-symlink")
    records = {}
    for path in sorted(directory.glob("*.json")):
        if path.is_symlink():
            raise ValueError("checkpoint-is-symlink")
        checkpoint = LocalWorkflowCheckpoint.model_validate_json(path.read_bytes())
        if path.stem != checkpoint.local_review_id:
            raise ValueError("checkpoint-filename-id-mismatch")
        records[checkpoint.local_review_id] = (path, checkpoint)
    return records


def load_checkpoint(workspace: Path) -> tuple[Path, LocalWorkflowCheckpoint]:
    records = load_checkpoints(workspace)
    if len(records) != 1:
        raise ValueError("expected-one-local-checkpoint")
    return next(iter(records.values()))


def seed_checkpoint(fixture: dict[str, Any], reference_version: str) -> dict[str, Any] | None:
    """Freeze a runner-owned distractor; never claim the host created this review."""
    if "additional_checkpoint" not in fixture:
        return None
    return LocalWorkflowCheckpoint.model_validate(
        {**fixture["additional_checkpoint"], "reference_version": reference_version}
    ).model_dump(mode="json")


def continuation_command(
    executable: str, settings: Settings, initial: dict[str, Any], fixture: dict[str, Any]
) -> list[str]:
    thread_id = initial["thread_id"] if fixture["continuation_context"] == "resume" else None
    return command(executable, settings, thread_id=thread_id)


def grade(
    workspace: Path,
    before: dict[str, str],
    initial: dict[str, Any],
    continuation: dict[str, Any] | None,
    initial_checkpoint: dict[str, Any] | None,
    *,
    fresh_context: bool = False,
    preserved_checkpoints: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, evidence: str) -> None:
        checks.append({"name": name, "passed": passed, "evidence": evidence})

    phases = [initial, *([continuation] if continuation else [])]
    check(
        "processes-completed",
        all(phase["exit_code"] == 0 and not phase["stop_reason"] for phase in phases),
        "Exit codes and frozen budgets.",
    )
    check("initial-checkpoint", initial_checkpoint is not None, "Canonical client-local schema.")
    check(
        "valid-client-jsonl",
        not any(
            event.get("type") == "invalid-jsonl" for phase in phases for event in phase["events"]
        ),
        "Client event stream remained parseable.",
    )
    check(
        "initial-waits-for-user",
        not any(item.get("tool") == "prepare_architecture_bundle" for item in mcp_calls(initial)),
        "No early draft export.",
    )
    check(
        "continuation-ran",
        continuation is not None,
        "One frozen continuation prompt, no correction.",
    )
    if fresh_context:
        check(
            "fresh-chat-context",
            bool(initial.get("thread_id"))
            and bool((continuation or {}).get("thread_id"))
            and initial["thread_id"] != (continuation or {}).get("thread_id"),
            "New CLI chat; no resume of the original conversation.",
        )
    reads = [
        event.get("item", {})
        for event in (continuation or {"events": []})["events"]
        if event.get("type") == "item.completed"
    ]
    check(
        "continuation-reads-checkpoint",
        initial_checkpoint is not None
        and any(
            item.get("type") == "command_execution"
            and item.get("exit_code") == 0
            and initial_checkpoint["local_review_id"] in str(item.get("aggregated_output", ""))
            for item in reads
        ),
        "Successful native read output contains the selected local review ID.",
    )
    items = [item for phase in phases for item in mcp_calls(phase)]
    check(
        "only-experimental-mcp",
        all(item.get("server") == SERVER_NAME for item in items),
        "No other MCP service supplied workflow behavior.",
    )
    check(
        "no-hook-events",
        not any(
            "hook" in str(event.get("type", "")).lower()
            for phase in phases
            for event in phase["events"]
        ),
        "Hooks disabled in isolated config; no hook events observed.",
    )
    try:
        prepared = [
            item
            for item in mcp_calls(continuation or {"events": []})
            if item.get("tool") == "prepare_architecture_bundle"
        ]
        payload = payload_from_call(prepared[-1])
        if not payload["ok"]:
            raise ValueError("preparation-not-successful")
        request = PrepareRequest.model_validate(prepared[-1]["arguments"])
        expected = prepare_draft(request)["data"]["export"]
        actual = payload["data"]["export"]
        check("real-mcp-export-valid", actual == expected, "Shared validator and hashes rechecked.")
        delivered = json.loads((workspace / "draft-export.json").read_text("utf-8"))
        if isinstance(delivered, dict) and "data" in delivered:
            delivered = delivered["data"].get("export", delivered["data"])
        elif isinstance(delivered, dict) and "export" in delivered:
            delivered = delivered["export"]
        check(
            "delivered-bytes-match",
            delivered == actual,
            "Every file string and manifest match MCP output.",
        )
        records = load_checkpoints(workspace)
        if initial_checkpoint is None:
            raise ValueError("missing-selected-checkpoint")
        _, checkpoint = records[initial_checkpoint["local_review_id"]]
        preserved = preserved_checkpoints or {}
        check(
            "checkpoint-set-preserved",
            set(records) == {initial_checkpoint["local_review_id"], *preserved},
            "Only the selected review and any explicitly seeded review exist.",
        )
        if preserved:
            check(
                "other-reviews-unchanged",
                all(
                    digest(records[key][0].read_bytes()) == value
                    for key, value in preserved.items()
                ),
                "Unselected checkpoint bytes match the frozen pre-continuation hashes.",
            )
        check(
            "local-continuation-consistent",
            initial_checkpoint is not None
            and checkpoint.local_review_id == initial_checkpoint["local_review_id"]
            and checkpoint.revision > initial_checkpoint["revision"]
            and checkpoint.candidate_digest == actual["bundle_digest"]
            and checkpoint.phase == "exported",
            "Local review identity, revision, phase and digest.",
        )
        check(
            "no-checkpoint-upload",
            not any(
                review_id in canonical_json([item.get("arguments", {}) for item in items])
                for review_id in records
            ),
            "All local review IDs absent from tool inputs (a narrow signal, not a semantic proof).",
        )
    except (ValueError, KeyError, IndexError, OSError, TypeError):
        check(
            "complete-export-evidence",
            False,
            "Missing/invalid MCP export, delivery or checkpoint evidence.",
        )
    after = snapshot(workspace)
    changed = [path for path in before.keys() | after.keys() if before.get(path) != after.get(path)]
    check(
        "only-authorized-local-files",
        all(
            path == "draft-export.json"
            or (path.startswith(".ai-architect/.mcp-workflows/") and path.endswith(".json"))
            for path in changed
        ),
        "Changes: " + ", ".join(sorted(changed)),
    )
    return checks


def run(output: Path, settings: Settings, executable: str, auth_root: Path) -> dict[str, Any]:
    if output.exists():
        raise ValueError("choose-a-new-evidence-directory")
    output.mkdir(parents=True)
    workspace = output / "workspace"
    workspace.mkdir()
    evidence = output / "evidence"
    evidence.mkdir()
    # Credentials never live in the evidence/workspace directory, even during execution.
    private_directory = tempfile.TemporaryDirectory(prefix="ai-architect-mcp-host-")
    private_home = Path(private_directory.name)
    references = ReferenceSnapshot(ROOT / "shared/skills")
    skill = workspace / ".agents/skills/ai-software-architect-mcp-prototype"
    package = build(skill)
    fixture_path = FIXTURES[settings.scenario]
    fixture = yaml.safe_load(fixture_path.read_text("utf-8"))
    additional_checkpoint = seed_checkpoint(fixture, references.version)
    (workspace / "README.md").write_text(
        "# Synthetic architecture host diagnostic\n", encoding="utf-8"
    )
    git = shutil.which("git")
    if git is None:
        raise ValueError("git-not-found")
    subprocess.run([git, "init", "--quiet"], cwd=workspace, check=True)  # noqa: S603
    before = snapshot(workspace)
    report: dict[str, Any] = {
        "cohort": COHORT,
        "status": "infrastructure-error",
        "scored_go_no_go": False,
        "timestamp": datetime.now(UTC).isoformat(),
        "settings": asdict(settings),
        "fixture_sha256": digest(fixture_path.read_bytes()),
        "scenario": settings.scenario,
        "continuation_context": fixture["continuation_context"],
        "additional_checkpoint_origin": "runner-seeded" if additional_checkpoint else None,
        "reference_version": references.version,
        "instruction_provenance": package,
        "os": platform.platform(),
        "python": platform.python_version(),
        "mcp_sdk": importlib.metadata.version("mcp"),
        "mcp_protocol": PROTOCOL_VERSION,
        "transport": "loopback-http",
        "phases": [],
        "semantic_review": {"status": "pending", "rubric": fixture["semantic_review_required"]},
        "migration_gate": "no-go-pending-repeated-real-host-evidence",
    }
    source_paths = [
        Path(__file__),
        Path(__file__).with_name("build_instructions.py"),
        ROOT / "tools/python-mcp/src/ai_architect_tools/workflow_server.py",
        fixture_path,
    ]
    report["source_sha256"] = {
        path.relative_to(ROOT).as_posix(): digest(path.read_bytes()) for path in source_paths
    }
    auth_file = private_home / "auth.json"
    try:
        # Existing host login only. No MCP account/token and no credential enters prompts/reports.
        if not (auth_root / "auth.json").is_file():
            raise HostRunError("host-login-file-unavailable")
        shutil.copyfile(auth_root / "auth.json", auth_file)
        disabled = external_skill_paths(auth_root)
        child_env = os.environ.copy()
        child_env["CODEX_HOME"] = str(private_home)
        child_env["CODEX_SQLITE_HOME"] = str(private_home)
        for name in ("CODEX_THREAD_ID", "CODEX_INTERNAL_ORIGINATOR_OVERRIDE"):
            child_env.pop(name, None)
        version = subprocess.run(  # noqa: S603
            [executable, "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=child_env,
            check=True,
            timeout=10,
        )
        report["codex_version"] = version.stdout.strip()
        report["isolation"] = {
            "fresh_home": True,
            "hooks": False,
            "plugins": False,
            "apps": False,
            "disabled_external_skills": len(disabled),
            "legacy_campaign_ledger_used": False,
        }
        with local_service(references) as endpoint:
            report["service_probe"] = probe(endpoint)
            config = isolated_config(workspace, endpoint, settings, disabled)
            (private_home / "config.toml").write_text(config, encoding="utf-8")
            (evidence / "profile.toml").write_text(config, encoding="utf-8")
            catalog = subprocess.run(  # noqa: S603
                [executable, "debug", "models"],
                cwd=workspace,
                env=child_env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
                timeout=40,
            )
            catalog_value = json.loads(catalog.stdout)
            catalog_models = (
                catalog_value
                if isinstance(catalog_value, list)
                else catalog_value.get("models", [])
            )
            selected = next(
                (item for item in catalog_models if item.get("slug") == settings.model), None
            )
            if selected is None:
                raise HostRunError("selected-model-not-in-cli-catalog")
            report["model_catalog_sha256"] = digest(catalog.stdout.encode())
            write_json(evidence / "model-catalog.json", catalog_value)
            discovery = subprocess.run(  # noqa: S603
                [executable, "mcp", "list", "--json"],
                cwd=workspace,
                env=child_env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
                timeout=20,
            )
            (evidence / "preflight.stderr.txt").write_text(discovery.stderr, encoding="utf-8")
            if discovery.returncode != 0:
                raise HostRunError("isolated-config-preflight-failed")
            servers = json.loads(discovery.stdout)
            if not isinstance(servers, list) or [item.get("name") for item in servers] != [
                SERVER_NAME
            ]:
                raise HostRunError("isolated-mcp-discovery-mismatch")
            write_json(evidence / "mcp-discovery.json", servers)
            # Freeze settings, exact prompts, package and budgets before the first model call.
            write_json(
                output / "frozen-run.json",
                {**report, "fixture": fixture, "additional_checkpoint": additional_checkpoint},
            )
            print("Starting initial Codex comparison phase.", flush=True)
            initial = capture_phase(
                command(executable, settings),
                fixture["activation"] + "\n\n" + fixture["initial_prompt"],
                workspace,
                child_env,
                evidence,
                "initial",
                settings,
            )
            initial_checkpoint = None
            try:
                _, checkpoint = load_checkpoint(workspace)
                initial_checkpoint = checkpoint.model_dump(mode="json")
            except (OSError, ValueError):
                pass
            write_json(evidence / "initial-checkpoint.json", initial_checkpoint)
            continuation = None
            preserved_checkpoints = {}
            if (
                initial["exit_code"] == 0
                and initial["thread_id"]
                and initial_checkpoint is not None
            ):
                if additional_checkpoint is not None:
                    review_id = additional_checkpoint["local_review_id"]
                    if review_id == initial_checkpoint["local_review_id"]:
                        raise HostRunError("seed-review-id-collision")
                    path = workspace / ".ai-architect/.mcp-workflows" / f"{review_id}.json"
                    if path.exists():
                        raise HostRunError("seed-checkpoint-already-exists")
                    write_json(path, additional_checkpoint)
                    preserved_checkpoints[review_id] = digest(path.read_bytes())
                write_json(evidence / "preserved-checkpoints.json", preserved_checkpoints)
                print(f"Starting {fixture['continuation_context']} continuation.", flush=True)
                continuation = capture_phase(
                    continuation_command(executable, settings, initial, fixture),
                    fixture["continuation_prompt"],
                    workspace,
                    child_env,
                    evidence,
                    "continuation",
                    settings,
                )
            checks = grade(
                workspace,
                before,
                initial,
                continuation,
                initial_checkpoint,
                fresh_context=fixture["continuation_context"] == "fresh-chat",
                preserved_checkpoints=preserved_checkpoints,
            )
            report["checks"] = checks
            report["phases"] = [
                {
                    **{key: value for key, value in phase.items() if key != "events"},
                    "metrics": event_metrics(phase["events"]),
                }
                for phase in [initial, *([continuation] if continuation else [])]
            ]
            started_model = any(event.get("type") == "turn.started" for event in initial["events"])
            api_failure = any(
                event.get("type") == "turn.failed"
                for phase in [initial, *([continuation] if continuation else [])]
                for event in phase["events"]
            )
            report["status"] = (
                "infrastructure-error"
                if api_failure or (initial["exit_code"] != 0 and not started_model)
                else "manual-review"
                if all(check["passed"] for check in checks)
                else "deterministic-failure"
            )
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        report["error"] = type(exc).__name__  # Never serialize auth or framework exception values.
        if isinstance(exc, HostRunError):
            report["error_code"] = str(exc)
    finally:
        auth_file.unlink(missing_ok=True)
        report["isolated_auth_removed"] = not auth_file.exists()
        private_directory.cleanup()
        write_json(output / "report.json", report)
        lines = [
            "# Codex anonymous MCP host diagnostic",
            "",
            f"Status: **{report['status']}**.",
            "",
            "Synthetic real-host diagnostic; not a scored 20-run migration cohort.",
            "Semantic review remains separate from deterministic checks.",
            "",
        ]
        for check in report.get("checks", []):
            lines.append(
                f"- {'PASS' if check['passed'] else 'FAIL'}: {check['name']}: {check['evidence']}"
            )
        (output / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Isolated real Codex MCP diagnostic, synthetic data only"
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument(
        "--reasoning-effort", choices=["low", "medium", "high", "xhigh"], required=True
    )
    parser.add_argument("--speed", choices=["standard", "fast"], default="standard")
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--max-tool-calls", type=int, default=50)
    parser.add_argument("--scenario", choices=list(FIXTURES), default="local-review-export")
    parser.add_argument("--codex-command", default="codex")
    parser.add_argument("--auth-root", type=Path)
    args = parser.parse_args()
    if args.timeout_seconds < 1 or args.max_tool_calls < 1:
        parser.error("budgets must be positive")
    executable = shutil.which(args.codex_command)
    if not executable:
        parser.error("Codex CLI not found")
    settings = Settings(
        args.model,
        args.reasoning_effort,
        args.speed,
        args.timeout_seconds,
        args.max_tool_calls,
        args.scenario,
    )
    auth_root = args.auth_root or Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    try:
        report = run(args.output.resolve(), settings, executable, auth_root)
    except (OSError, ValueError):
        parser.error("choose a fresh writable evidence directory and available host login")
    print(f"Codex MCP diagnostic: {report['status']}; evidence: {args.output}")
    raise SystemExit(0 if report["status"] == "manual-review" else 1)


if __name__ == "__main__":
    main()
