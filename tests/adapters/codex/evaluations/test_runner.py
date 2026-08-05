# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from adapters.codex.evaluations.grading import grade_phase
from adapters.codex.evaluations.models import (
    AssertionStatus,
    EvaluationStatus,
    VerificationPolicy,
    load_fixture,
)
from adapters.codex.evaluations.runner import (
    DEFAULT_MANIFEST,
    InstalledPluginIdentity,
    _capture_process,
    _codex_command,
    _continuation_sandbox,
    _installed_plugin_identity,
    _load_campaign,
    _parse_events,
    _phase_telemetry,
    main,
)

ROOT = Path(__file__).resolve().parents[4]
FIXTURES = ROOT / "shared" / "evaluations" / "model-fixtures"


def test_all_campaign_fixtures_satisfy_the_shared_typed_contract() -> None:
    fixture_names = {
        "clarify-ui-architecture.yaml",
        "architecture-option-comparison.yaml",
        "read-only-architecture-review.yaml",
        "abstract-factory-example.yaml",
        "avoid-overengineering.yaml",
    }
    fixtures = [load_fixture(FIXTURES / name) for name in fixture_names]

    assert {fixture.id for fixture in fixtures} == {
        name.removesuffix(".yaml") for name in fixture_names
    }
    assert all(fixture.verification.repository_changes == "forbid" for fixture in fixtures)
    comparison = next(
        fixture for fixture in fixtures if fixture.id == "architecture-option-comparison"
    )
    review = next(
        fixture for fixture in fixtures if fixture.id == "read-only-architecture-review"
    )
    assert "Inspect the supplied repository" in comparison.prompt
    assert "budget_book.py" in comparison.repository
    assert "budget_book.py" in review.repository
    assert "describe-subagent-results-accurately" in review.expected
    assert comparison.continuation is not None
    assert comparison.observe_decision is True
    assert comparison.continuation.verification.repository_changes == "architecture-artifacts-only"
    assert comparison.continuation.verification.required_repository_changes == [
        ".ai-architect/project-context.md",
        ".ai-architect/architecture-contract.yaml",
        ".ai-architect/implementation-plan.md",
        ".ai-architect/decisions/ADR-*.md",
    ]
    clarification = next(
        fixture for fixture in fixtures if fixture.id == "clarify-ui-architecture"
    )
    assert clarification.continuation is not None
    assert clarification.continuation.verification.repository_changes == "forbid"
    assert _continuation_sandbox(clarification.continuation.verification) == "read-only"
    assert _continuation_sandbox(comparison.continuation.verification) == "workspace-write"


def test_german_campaign_is_separate_and_typed() -> None:
    fixtures = _load_campaign(DEFAULT_MANIFEST, set(), "german")

    assert [fixture.id for _, fixture in fixtures] == [
        "de-clarify-ui-architecture",
        "de-architecture-option-comparison",
    ]
    assert all(fixture.response_language == "de" for _, fixture in fixtures)
    assert all("respond-in-german" in fixture.expected for _, fixture in fixtures)
    assert all(fixture.continuation is not None for _, fixture in fixtures)


def test_unknown_campaign_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown exploratory campaign"):
        _load_campaign(DEFAULT_MANIFEST, set(), "missing")


def test_fixture_contract_rejects_repository_path_escape(tmp_path: Path) -> None:
    fixture = (FIXTURES / "clarify-ui-architecture.yaml").read_text(encoding="utf-8")
    fixture += '\nrepository:\n  "../outside.py": "unsafe"\n'
    path = tmp_path / "unsafe.yaml"
    path.write_text(fixture, encoding="utf-8")

    with pytest.raises(ValidationError, match="must remain relative"):
        load_fixture(path)


def test_fixture_language_contract_accepts_brazilian_portuguese_tag(
    tmp_path: Path,
) -> None:
    fixture = (FIXTURES / "de-clarify-ui-architecture.yaml").read_text(encoding="utf-8")
    fixture = fixture.replace("response_language: de", "response_language: pt-BR")
    path = tmp_path / "pt-br.yaml"
    path.write_text(fixture, encoding="utf-8")

    assert load_fixture(path).response_language == "pt-BR"


def test_grading_enforces_markers_events_and_architecture_only_writes() -> None:
    policy = VerificationPolicy(
        repository_changes="architecture-artifacts-only",
        forbidden_event_types=["mcp_tool_call"],
        forbidden_response_markers=["<!-- ai-architect-"],
    )

    assertions = grade_phase(
        exit_code=0,
        final_response="Visible answer <!-- ai-architect-decision-shape: comparison -->",
        event_types={"thread.started", "mcp_tool_call"},
        repository_changes=[".ai-architect/decisions/ADR-001.md", "app.py"],
        policy=policy,
    )

    failures = {item.name for item in assertions if item.status == AssertionStatus.FAIL}
    assert failures == {
        "response-marker-absent:<!-- ai-architect-",
        "event-type-absent:mcp_tool_call",
        "repository-change-policy",
    }


def test_grading_requires_every_configured_architecture_artifact() -> None:
    policy = VerificationPolicy(
        repository_changes="architecture-artifacts-only",
        required_repository_changes=[
            ".ai-architect/project-context.md",
            ".ai-architect/architecture-contract.yaml",
            ".ai-architect/implementation-plan.md",
            ".ai-architect/decisions/ADR-*.md",
        ],
    )

    assertions = grade_phase(
        exit_code=0,
        final_response="Validation blocked the write.",
        event_types={"item.completed"},
        repository_changes=[],
        policy=policy,
    )

    failures = {
        assertion.name
        for assertion in assertions
        if assertion.status == AssertionStatus.FAIL
    }
    assert failures == {
        "required-repository-change:.ai-architect/project-context.md",
        "required-repository-change:.ai-architect/architecture-contract.yaml",
        "required-repository-change:.ai-architect/implementation-plan.md",
        "required-repository-change:.ai-architect/decisions/ADR-*.md",
    }


def test_jsonl_parser_extracts_thread_final_response_and_item_types() -> None:
    stdout = "\n".join(
        [
            json.dumps({"type": "thread.started", "thread_id": "thread-123"}),
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {"id": "item-1", "type": "agent_message", "text": "Done"},
                }
            ),
        ]
    )

    events, event_types, thread_id, response = _parse_events(stdout)

    assert len(events) == 2
    assert event_types == {"thread.started", "item.completed", "agent_message"}
    assert thread_id == "thread-123"
    assert response == "Done"


def test_phase_telemetry_uses_only_runner_observed_jsonl_data() -> None:
    lines = [
        (
            0.25,
            json.dumps({"type": "thread.started", "thread_id": "thread-123"}),
        ),
        (
            0.75,
            json.dumps(
                {
                    "type": "item.started",
                    "item": {
                        "id": "tool-1",
                        "type": "command_execution",
                        "command": "private command",
                    },
                }
            ),
        ),
        (
            1.5,
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {
                        "id": "tool-1",
                        "type": "command_execution",
                        "command": "private command",
                        "aggregated_output": "private output",
                        "status": "completed",
                    },
                }
            ),
        ),
        (
            3.0,
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {"type": "agent_message", "text": "Done"},
                }
            ),
        ),
        (
            3.1,
            json.dumps(
                {
                    "type": "turn.completed",
                    "usage": {
                        "input_tokens": 120,
                        "cached_input_tokens": 80,
                        "output_tokens": 30,
                    },
                }
            ),
        ),
    ]

    telemetry = _phase_telemetry(lines)

    assert telemetry.first_event_seconds == 0.25
    assert telemetry.first_agent_message_seconds == 3.0
    assert telemetry.last_agent_message_seconds == 3.0
    assert telemetry.agent_message_count == 1
    assert telemetry.tool_call_count == 1
    assert telemetry.item_counts == {"agent_message": 1, "command_execution": 1}
    assert telemetry.input_tokens == 120
    assert telemetry.cached_input_tokens == 80
    assert telemetry.output_tokens == 30
    assert len(telemetry.tool_events) == 1
    tool_event = telemetry.tool_events[0]
    assert tool_event.model_dump() == {
        "ordinal": 1,
        "tool_type": "command_execution",
        "started_seconds": 0.75,
        "completed_seconds": 1.5,
        "duration_seconds": 0.75,
        "gap_from_previous_tool_seconds": None,
        "status": "completed",
    }
    assert "private command" not in telemetry.model_dump_json()
    assert "private output" not in telemetry.model_dump_json()
    assert "pre_tool_use_hook_seconds" in telemetry.unavailable_metrics


def test_process_capture_preserves_stdout_and_observed_line_order(tmp_path: Path) -> None:
    capture = _capture_process(
        [
            sys.executable,
            "-c",
            (
                "import time; "
                "print('{\"type\":\"thread.started\"}', flush=True); "
                "time.sleep(0.02); "
                "print('{\"type\":\"turn.completed\"}', flush=True)"
            ),
        ],
        workspace=tmp_path,
        timeout_seconds=5,
    )

    assert capture.returncode == 0
    assert len(capture.stdout_lines) == 2
    assert capture.stdout_lines[0][0] <= capture.stdout_lines[1][0]
    assert capture.stdout.count("\n") == 2


def test_codex_command_is_ephemeral_only_without_a_continuation() -> None:
    initial = _codex_command(
        executable="codex",
        model="gpt-5.6",
        reasoning_effort="medium",
        prompt="$ai-software-architect Review this.",
        sandbox="read-only",
        ephemeral=True,
    )
    continuation = _codex_command(
        executable="codex",
        model="gpt-5.6",
        reasoning_effort="medium",
        prompt="Approve it.",
        sandbox="workspace-write",
        ephemeral=False,
        resume_thread="thread-123",
    )

    assert "--ephemeral" in initial
    assert initial[-1].startswith("$ai-software-architect")
    assert "--ephemeral" not in continuation
    assert continuation[-3:] == ["resume", "thread-123", "Approve it."]


def test_codex_command_sets_fast_service_tier_explicitly() -> None:
    command = _codex_command(
        executable="codex",
        model="gpt-5.6",
        reasoning_effort="medium",
        prompt="$ai-software-architect Review this.",
        sandbox="read-only",
        ephemeral=True,
        speed="fast",
    )

    assert 'service_tier="fast"' in command


def test_installed_plugin_identity_uses_one_enabled_plugin_across_marketplaces(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "installed": [
            {
                "pluginId": "ai-software-architect@personal",
                "version": "0.2.0",
                "installed": True,
                "enabled": True,
            }
        ]
    }

    def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        assert command == [
            "codex",
            "plugin",
            "list",
            "--json",
        ]
        return subprocess.CompletedProcess(command, 0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert _installed_plugin_identity("codex") == InstalledPluginIdentity(
        plugin_id="ai-software-architect@personal",
        marketplace="personal",
        version="0.2.0",
    )


def test_installed_plugin_identity_rejects_enabled_duplicates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "installed": [
            {
                "pluginId": f"ai-software-architect@{marketplace}",
                "version": "0.2.0",
                "installed": True,
                "enabled": True,
            }
            for marketplace in ("personal", "ai-software-architect-release")
        ]
    }

    def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(ValueError, match="exactly one installed and enabled"):
        _installed_plugin_identity("codex")


def test_expected_plugin_version_mismatch_fails_before_evaluation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from adapters.codex.evaluations import runner

    output = tmp_path / "campaign"
    monkeypatch.setattr(runner, "_codex_version", lambda _: "codex-cli test")
    monkeypatch.setattr(
        runner,
        "_installed_plugin_identity",
        lambda _: InstalledPluginIdentity("ai-software-architect@personal", "personal", "0.2.0"),
    )

    exit_code = main(
        [
            "--manifest",
            str(DEFAULT_MANIFEST),
            "--output-directory",
            str(output),
            "--codex-command",
            "codex",
            "--expected-plugin-version",
            "0.1.0",
        ]
    )

    assert exit_code == 2
    assert not output.exists()
    assert "Expected AI Software Architect 0.1.0" in capsys.readouterr().err


def test_dry_run_plans_the_campaign_without_invoking_codex(tmp_path: Path) -> None:
    output = tmp_path / "campaign"

    exit_code = main(
        [
            "--manifest",
            str(DEFAULT_MANIFEST),
            "--output-directory",
            str(output),
            "--dry-run",
        ]
    )

    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert len(report["results"]) == 5
    assert {result["status"] for result in report["results"]} == {
        EvaluationStatus.PLANNED.value
    }
    assert report["installed_plugin_version"] is None
    assert not (output / "workspaces").exists()
