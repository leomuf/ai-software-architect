# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import json
import subprocess
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
    _codex_command,
    _installed_plugin_identity,
    _parse_events,
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
    assert comparison.continuation is not None
    assert comparison.continuation.verification.repository_changes == "architecture-artifacts-only"


def test_fixture_contract_rejects_repository_path_escape(tmp_path: Path) -> None:
    fixture = (FIXTURES / "clarify-ui-architecture.yaml").read_text(encoding="utf-8")
    fixture += '\nrepository:\n  "../outside.py": "unsafe"\n'
    path = tmp_path / "unsafe.yaml"
    path.write_text(fixture, encoding="utf-8")

    with pytest.raises(ValidationError, match="must remain relative"):
        load_fixture(path)


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
