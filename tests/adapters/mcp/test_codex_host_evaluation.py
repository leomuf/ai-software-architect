# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tomllib
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest
from ai_architect_schemas.mcp_workflow import LocalWorkflowCheckpoint, PrepareRequest
from ai_architect_tools.domain.workflow import prepare_draft

from adapters.mcp import codex_host_evaluation as runner


def candidate_files() -> list[dict[str, str]]:
    return [
        {
            "path": ".ai-architect/architecture-contract.yaml",
            "content": "schema_version: 1.0.0\nrevision: 1\n"
            "scope: synthetic\ndecision_ids: [ADR-001]\n",
        },
        {
            "path": ".ai-architect/decisions/ADR-001.md",
            "content": """---
schema_version: 1.0.0
revision: 1
decision:
  id: ADR-001
  title: Keep a simple boundary
  status: proposed
  context: Synthetic description
  drivers: [Simplicity]
  considered_option_ids: [OPT-001]
  selected_option_id: OPT-001
  decision: Use functions.
  validation_criteria: [Review the dependency.]
---
# Draft
""",
        },
        {"path": ".ai-architect/project-context.md", "content": "# Context\r\n  "},
        {"path": ".ai-architect/implementation-plan.md", "content": "# Plan\n"},
    ]


def phase(events: list[dict[str, Any]]) -> dict[str, Any]:
    return {"events": events, "exit_code": 0, "stop_reason": ""}


def successful_evidence(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    checkpoint = LocalWorkflowCheckpoint(
        local_review_id="9f3fce90-fc74-4fc2-8f98-15bcd7d985f1",
        revision=1,
        phase="analysis",
        reference_version="a" * 64,
        scope="Synthetic",
        evidence_limits=["No source inspection"],
    )
    initial = checkpoint.model_dump(mode="json")
    request = {"files": candidate_files()}
    payload = prepare_draft(PrepareRequest.model_validate(request))
    exported = payload["data"]["export"]
    checkpoint.revision = 2
    checkpoint.phase = "exported"
    checkpoint.candidate_digest = exported["bundle_digest"]
    checkpoint_path = root / ".ai-architect/.mcp-workflows" / f"{checkpoint.local_review_id}.json"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text(checkpoint.model_dump_json(), encoding="utf-8")
    (root / "draft-export.json").write_text(json.dumps(exported), encoding="utf-8")
    read = {
        "type": "item.completed",
        "item": {
            "type": "command_execution",
            "exit_code": 0,
            "command": "Get-Content checkpoint.json",
            "aggregated_output": json.dumps(initial),
        },
    }
    call = {
        "type": "item.completed",
        "item": {
            "type": "mcp_tool_call",
            "server": runner.SERVER_NAME,
            "tool": "prepare_architecture_bundle",
            "arguments": request,
            "result": {"structuredContent": payload},
        },
    }
    return phase([]), phase([read, call]), initial


def test_isolated_profile_has_only_anonymous_mcp_and_explicitly_disabled_integrations(
    tmp_path: Path,
) -> None:
    text = runner.isolated_config(
        tmp_path,
        "http://127.0.0.1:1234/mcp",
        runner.Settings("pinned-model", "medium"),
        [tmp_path / "foreign/SKILL.md"],
    )
    config = tomllib.loads(text)
    assert config["features"] == {
        "hooks": False,
        "plugins": False,
        "apps": False,
        "multi_agent": False,
    }
    assert list(config["mcp_servers"]) == [runner.SERVER_NAME]
    assert config["skills"]["bundled"]["enabled"] is False
    assert config["skills"]["config"][0]["enabled"] is False
    assert "bearer_token_env_var" not in text
    assert config["sandbox_mode"] == "workspace-write"
    assert config["approval_policy"] == "never"


def test_resume_pins_model_and_uses_stdin_without_reactivating_skill() -> None:
    argv = runner.command("codex", runner.Settings("pinned-model", "xhigh"), thread_id="exact-id")
    assert argv[-1] == "-"
    assert argv[argv.index("resume") + 2 :] == ["exact-id", "-"]
    assert "--ephemeral" not in argv
    assert "--dangerously-bypass-approvals-and-sandbox" not in argv
    assert argv[argv.index("--model") + 1] == "pinned-model"


@pytest.mark.parametrize("scenario", list(runner.FIXTURES))
def test_scenario_orchestration_uses_frozen_prompts_and_correct_chat_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, scenario: str
) -> None:
    auth_root = tmp_path / "login"
    auth_root.mkdir()
    (auth_root / "auth.json").write_text('{"synthetic": true}', encoding="utf-8")
    output = tmp_path / "run"
    captures = []

    @contextmanager
    def fake_service(_: Any) -> Any:
        yield "http://127.0.0.1:1234/mcp"

    def fake_run(argv: list[str], **_: Any) -> Any:
        stdout = (
            '[{"slug":"test-model"}]'
            if "models" in argv
            else '[{"name":"architect_prototype"}]'
            if "mcp" in argv
            else "synthetic-cli"
        )
        return subprocess.CompletedProcess(argv, 0, stdout, "")

    def fake_capture(
        argv: list[str],
        prompt: str,
        workspace: Path,
        environment: Any,
        evidence: Path,
        name: str,
        settings: runner.Settings,
    ) -> dict[str, Any]:
        frozen = json.loads((output / "frozen-run.json").read_text("utf-8"))
        assert prompt == (
            frozen["fixture"]["activation"] + "\n\n" + frozen["fixture"]["initial_prompt"]
            if name == "initial"
            else frozen["fixture"]["continuation_prompt"]
        )
        captures.append(argv)
        initial, continuation, checkpoint = successful_evidence(workspace)
        path = workspace / ".ai-architect/.mcp-workflows" / f"{checkpoint['local_review_id']}.json"
        if name == "initial":
            runner.write_json(path, checkpoint)
            (workspace / "draft-export.json").unlink()
            assert len(runner.load_checkpoints(workspace)) == 1
            return {**initial, "thread_id": "first-chat"}
        if scenario == "two-active-reviews":
            records = runner.load_checkpoints(workspace)
            seed = frozen["additional_checkpoint"]
            assert records[seed["local_review_id"]][1].model_dump(mode="json") == seed
        return {
            **continuation,
            "thread_id": "first-chat" if scenario == "local-review-export" else "new-chat",
        }

    monkeypatch.setattr(runner, "local_service", fake_service)
    monkeypatch.setattr(runner, "probe", lambda _: {"authentication": "none"})
    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(runner, "capture_phase", fake_capture)
    monkeypatch.setattr(runner, "external_skill_paths", lambda _: [])
    monkeypatch.setattr(runner.tempfile, "tempdir", str(tmp_path))
    report = runner.run(
        output, runner.Settings("test-model", "medium", scenario=scenario), "codex", auth_root
    )
    assert report["status"] == "manual-review", report
    assert report["isolated_auth_removed"]
    assert "resume" not in captures[0]
    assert ("resume" in captures[1]) == (scenario == "local-review-export")
    assert report["semantic_review"]["status"] == "pending"


@pytest.mark.parametrize(
    "violation",
    [None, "same-chat", "wrong-review", "mutated-other", "deleted-other", "extra-review"],
)
def test_recovery_detects_wrong_chat_and_cross_review_changes(
    tmp_path: Path, violation: str | None
) -> None:
    initial, continuation, checkpoint = successful_evidence(tmp_path)
    initial["thread_id"] = "original-chat"
    continuation["thread_id"] = "new-chat"
    fixture = {
        "additional_checkpoint": {
            "local_review_id": "f83f914c-54b7-4fa9-a570-8452078c30ed",
            "revision": 4,
            "phase": "analysis",
            "scope": "CSV import",
            "evidence_limits": ["Synthetic"],
        }
    }
    seed = runner.seed_checkpoint(fixture, "a" * 64)
    assert seed is not None
    directory = tmp_path / ".ai-architect/.mcp-workflows"
    other = directory / f"{seed['local_review_id']}.json"
    runner.write_json(other, seed)
    preserved = {seed["local_review_id"]: runner.digest(other.read_bytes())}
    if violation == "same-chat":
        continuation["thread_id"] = initial["thread_id"]
    elif violation == "wrong-review":
        path = directory / f"{checkpoint['local_review_id']}.json"
        exported = json.loads(path.read_text("utf-8"))
        runner.write_json(path, checkpoint)
        runner.write_json(other, {**exported, "local_review_id": seed["local_review_id"]})
    elif violation == "mutated-other":
        other.write_bytes(other.read_bytes() + b"\n")
    elif violation == "deleted-other":
        other.unlink()
    elif violation == "extra-review":
        third_id = "c344c046-8ee5-4c1e-9a79-a046e2cff377"
        runner.write_json(directory / f"{third_id}.json", {**seed, "local_review_id": third_id})
    checks = runner.grade(
        tmp_path,
        {},
        initial,
        continuation,
        checkpoint,
        fresh_context=True,
        preserved_checkpoints=preserved,
    )
    assert all(check["passed"] for check in checks) == (violation is None), checks


def test_multiple_checkpoints_require_explicit_selection_and_matching_filenames(
    tmp_path: Path,
) -> None:
    _, _, checkpoint = successful_evidence(tmp_path)
    directory = tmp_path / ".ai-architect/.mcp-workflows"
    second_id = "f83f914c-54b7-4fa9-a570-8452078c30ed"
    second = directory / f"{second_id}.json"
    runner.write_json(second, {**checkpoint, "local_review_id": second_id})
    assert len(runner.load_checkpoints(tmp_path)) == 2
    with pytest.raises(ValueError, match="expected-one"):
        runner.load_checkpoint(tmp_path)
    runner.write_json(second, checkpoint)
    with pytest.raises(ValueError, match="filename-id-mismatch"):
        runner.load_checkpoints(tmp_path)


def test_grading_requires_real_export_and_preserves_manual_review_boundary(tmp_path: Path) -> None:
    initial, continuation, checkpoint = successful_evidence(tmp_path)
    checks = runner.grade(tmp_path, {}, initial, continuation, checkpoint)
    assert all(check["passed"] for check in checks), checks
    initial["events"].append({"type": "invalid-jsonl"})
    checks = runner.grade(tmp_path, {}, initial, continuation, checkpoint)
    assert any(check["name"] == "valid-client-jsonl" and not check["passed"] for check in checks)
    initial["events"].clear()
    # Removing the actual MCP call cannot be rescued by a model's prose success claim.
    continuation["events"] = [
        continuation["events"][0],
        {
            "type": "item.completed",
            "item": {"type": "agent_message", "text": "Export succeeded and was approved."},
        },
    ]
    checks = runner.grade(tmp_path, {}, initial, continuation, checkpoint)
    assert any(not check["passed"] for check in checks)


@pytest.mark.parametrize(
    "violation",
    ["changed-bytes", "stale-revision", "checkpoint-upload", "source-write", "foreign-mcp"],
)
def test_critical_evidence_failures_are_detected(tmp_path: Path, violation: str) -> None:
    initial, continuation, checkpoint = successful_evidence(tmp_path)
    if violation == "changed-bytes":
        path = tmp_path / "draft-export.json"
        content = json.loads(path.read_text("utf-8"))
        content["files"][0]["content"] += "changed after validation"
        path.write_text(json.dumps(content), encoding="utf-8")
    elif violation == "stale-revision":
        path, record = runner.load_checkpoint(tmp_path)
        record.revision = checkpoint["revision"]
        path.write_text(record.model_dump_json(), encoding="utf-8")
    elif violation == "checkpoint-upload":
        item = continuation["events"][-1]["item"]
        item["arguments"]["files"][2]["content"] += checkpoint["local_review_id"]
        item["result"]["structuredContent"] = prepare_draft(
            PrepareRequest.model_validate(item["arguments"])
        )
    elif violation == "source-write":
        (tmp_path / "application.py").write_text("print('unauthorized')\n", encoding="utf-8")
    else:
        continuation["events"][-1]["item"]["server"] = "legacy-service"
    assert any(
        not check["passed"]
        for check in runner.grade(tmp_path, {}, initial, continuation, checkpoint)
    )


def test_capture_preserves_events_on_timeout_and_reports_limit(tmp_path: Path) -> None:
    helper = tmp_path / "fake-host.py"
    helper.write_text(
        "import json, time\n"
        "print(json.dumps({'type':'thread.started', 'thread_id':'fixture'}), flush=True)\n"
        "time.sleep(30)\n",
        encoding="utf-8",
    )
    result = runner.capture_phase(
        [sys.executable, str(helper)],
        "synthetic prompt",
        tmp_path,
        os.environ.copy(),
        tmp_path,
        "timeout",
        runner.Settings("unused", "medium", timeout_seconds=1),
    )
    assert result["stop_reason"] == "timeout"
    assert result["thread_id"] == "fixture"
    assert (tmp_path / "timeout.jsonl").is_file()


def test_temporary_host_login_removed_after_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    auth_root = tmp_path / "source-auth"
    auth_root.mkdir()
    sentinel = b'{"test_only":"not-a-real-authentication-token"}'
    (auth_root / "auth.json").write_bytes(sentinel)
    original_run = subprocess.run

    def fake_run(argv: list[str], **kwargs: Any) -> Any:
        if "--version" in argv:
            raise OSError("synthetic version failure")
        return original_run(argv, **kwargs)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(runner, "external_skill_paths", lambda _: [])
    monkeypatch.setattr(runner.tempfile, "tempdir", str(tmp_path))
    output = tmp_path / "evidence"
    report = runner.run(output, runner.Settings("unused", "medium"), "unused-cli", auth_root)
    assert report["status"] == "infrastructure-error"
    assert report["isolated_auth_removed"] is True
    assert (auth_root / "auth.json").read_bytes() == sentinel
    assert not list(output.rglob("auth.json"))
    assert not list(tmp_path.glob("ai-architect-mcp-host-*"))
    assert sentinel.decode() not in (output / "report.json").read_text("utf-8")


@pytest.mark.parametrize("upload_other_review", [False, True])
def test_local_id_in_valid_artifact_is_detected_even_when_export_and_digests_match(
    tmp_path: Path, upload_other_review: bool
) -> None:
    initial, continuation, checkpoint = successful_evidence(tmp_path)
    selected_path, selected = runner.load_checkpoint(tmp_path)
    other_id = "f83f914c-54b7-4fa9-a570-8452078c30ed"
    other_path = selected_path.with_name(f"{other_id}.json")
    runner.write_json(
        other_path, {**checkpoint, "local_review_id": other_id, "scope": "CSV import"}
    )
    preserved = {other_id: runner.digest(other_path.read_bytes())}
    leaked_id = other_id if upload_other_review else checkpoint["local_review_id"]
    call = continuation["events"][-1]["item"]
    call["arguments"]["files"][2]["content"] += f"\nSource: local checkpoint {leaked_id}\n"
    payload = prepare_draft(PrepareRequest.model_validate(call["arguments"]))
    call["result"]["structuredContent"] = payload
    exported = payload["data"]["export"]
    runner.write_json(tmp_path / "draft-export.json", exported)
    selected.candidate_digest = exported["bundle_digest"]
    selected_path.write_text(selected.model_dump_json(), encoding="utf-8")
    checks = runner.grade(
        tmp_path, {}, initial, continuation, checkpoint, preserved_checkpoints=preserved
    )
    assert [check["name"] for check in checks if not check["passed"]] == ["no-checkpoint-upload"]


def test_text_fallback_result_is_accepted_without_inventing_payload() -> None:
    payload = {"ok": True, "data": {"only": "synthetic"}}
    item = {"result": {"content": [{"type": "text", "text": json.dumps(payload)}]}}
    assert runner.payload_from_call(item) == payload
    invalid = copy.deepcopy(item)
    invalid["result"]["content"][0]["text"] = "Model claims success"
    with pytest.raises(ValueError, match="missing-structured"):
        runner.payload_from_call(invalid)


def test_metrics_preserve_failed_calls_and_only_report_explicit_token_usage() -> None:
    payload = {
        "type": "item.completed",
        "item": {
            "type": "mcp_tool_call",
            "tool": "get_architecture_resource",
            "status": "failed",
            "arguments": {"resource_id": "wrong-id", "sensitive": "synthetic-sentinel"},
        },
    }
    events = [
        payload,
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 200,
                "cached_input_tokens": 150,
                "output_tokens": 20,
            },
        },
    ]
    metrics = runner.event_metrics(events)
    assert metrics["mcp_failed_call_count"] == metrics["mcp_call_count"] == 1
    assert metrics["requested_resource_ids"] == ["wrong-id"]
    assert metrics["token_usage"] == {
        "input_tokens": 200,
        "cached_input_tokens": 150,
        "output_tokens": 20,
    }
    assert "reasoning_output_tokens" not in metrics["token_usage"]
    assert "synthetic-sentinel" not in json.dumps(metrics)
