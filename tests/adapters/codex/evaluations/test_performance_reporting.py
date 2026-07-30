# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

from adapters.codex.evaluations.models import (
    AssertionStatus,
    CampaignReport,
    DeterministicAssertion,
    EvaluationStatus,
    FixtureResult,
    PhaseResult,
    PhaseTelemetry,
)
from adapters.codex.evaluations.performance_import import import_reports
from adapters.codex.evaluations.performance_ledger import load_performance_ledger
from adapters.codex.evaluations.performance_models import SpeedMode
from adapters.codex.evaluations.performance_report import (
    fixture_overview_statistics,
    grouped_statistics,
    observation_rows,
    write_reports,
)


def _phase(
    name: Literal["initial", "continuation"],
    duration: float,
    thread_id: str = "thread-1",
) -> PhaseResult:
    return PhaseResult(
        name=name,
        exit_code=0,
        duration_seconds=duration,
        thread_id=thread_id,
        final_response_file=f"{name}.response.md",
        event_log_file=f"{name}.jsonl",
        stderr_file=f"{name}.stderr.txt",
        event_types=["turn.completed"],
        repository_changes=[],
        assertions=[
            DeterministicAssertion(
                name="completed",
                status=AssertionStatus.PASS,
                evidence="complete",
            )
        ],
        manual_review=[],
        telemetry=PhaseTelemetry(
            first_event_seconds=0.2,
            first_agent_message_seconds=duration - 0.2,
            last_agent_message_seconds=duration - 0.1,
            agent_message_count=1,
            tool_call_count=2,
            item_counts={"agent_message": 1, "command_execution": 2},
            input_tokens=100,
            cached_input_tokens=50,
            output_tokens=25,
            unavailable_metrics=["pre_tool_use_hook_seconds"],
        ),
    )


def _write_report(path: Path) -> None:
    started = datetime(2026, 7, 21, 19, 50, tzinfo=UTC)
    report = CampaignReport(
        started_at=started,
        completed_at=started + timedelta(seconds=50),
        codex_command="codex",
        codex_version="codex-cli test",
        installed_plugin_id="ai-software-architect@personal",
        installed_plugin_marketplace="personal",
        installed_plugin_version="0.1.0",
        installed_plugin_provenance_sha256="a" * 64,
        model="gpt-5.6-sol",
        reasoning_effort="medium",
        results=[
            FixtureResult(
                fixture_id="architecture-option-comparison",
                scenario="FLOW-004",
                status=EvaluationStatus.MANUAL_REVIEW,
                workspace="bounded-workspace",
                phases=[_phase("initial", 10.0), _phase("continuation", 20.0)],
            ),
            FixtureResult(
                fixture_id="avoid-overengineering",
                scenario="FLOW-002",
                status=EvaluationStatus.MANUAL_REVIEW,
                workspace="bounded-workspace",
                phases=[_phase("initial", 5.0, "thread-2")],
            ),
        ],
    )
    path.parent.mkdir(parents=True)
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")


def test_report_import_preview_and_apply_are_idempotent(tmp_path: Path) -> None:
    report_path = tmp_path / "Run20" / "report.json"
    ledger = tmp_path / "history.jsonl"
    preview_path = tmp_path / "preview.json"
    _write_report(report_path)

    preview = import_reports(
        reports=[report_path],
        ledger=ledger,
        overrides_path=tmp_path / "missing.yaml",
        default_speed=SpeedMode.STANDARD,
        default_git_commit="commit-1",
        default_host="windows-x86_64",
        apply=False,
    )
    assert len(preview.accepted) == 2
    assert preview.applied_records == 0
    assert Path(preview.reports[0]).name == "report.json"
    assert not Path(preview.reports[0]).is_absolute()
    assert not ledger.exists()

    applied = import_reports(
        reports=[report_path],
        ledger=ledger,
        overrides_path=tmp_path / "missing.yaml",
        default_speed=SpeedMode.STANDARD,
        default_git_commit="commit-1",
        default_host="windows-x86_64",
        apply=True,
    )
    assert applied.applied_records == 2
    assert (
        import_reports(
            reports=[report_path],
            ledger=ledger,
            overrides_path=tmp_path / "missing.yaml",
            default_speed=SpeedMode.STANDARD,
            default_git_commit="commit-1",
            default_host="windows-x86_64",
            apply=True,
        ).applied_records
        == 0
    )
    preview_path.write_text(applied.model_dump_json(), encoding="utf-8")
    assert json.loads(preview_path.read_text(encoding="utf-8"))["applied_records"] == 2


def test_reporting_excludes_missing_continuation_from_statistics(tmp_path: Path) -> None:
    report_path = tmp_path / "Run20" / "report.json"
    ledger = tmp_path / "history.jsonl"
    _write_report(report_path)
    import_reports(
        reports=[report_path],
        ledger=ledger,
        overrides_path=tmp_path / "missing.yaml",
        default_speed=SpeedMode.STANDARD,
        default_git_commit="commit-1",
        default_host="windows-x86_64",
        apply=True,
    )

    records = load_performance_ledger(ledger)
    rows = observation_rows(records)
    statistics_rows = grouped_statistics(records)

    avoid = next(row for row in rows if row.fixture == "avoid-overengineering")
    assert avoid.continuation_seconds is None
    assert avoid.completed_workflow_total_seconds is None
    assert not any(
        row.fixture == "avoid-overengineering" and row.phase == "continuation"
        for row in statistics_rows
    )
    assert not any(
        row.fixture == "avoid-overengineering"
        and row.phase == "completed-workflow-total"
        for row in statistics_rows
    )
    comparison = next(
        row for row in rows if row.fixture == "architecture-option-comparison"
    )
    assert comparison.observed_total_seconds == 30
    assert comparison.completed_workflow_total_seconds == 30

    output = tmp_path / "rendered"
    assert write_reports(ledger, output) == (2, 6)
    assert "—" in (output / "performance.md").read_text(encoding="utf-8")
    assert (output / "performance.csv").is_file()
    assert (output / "performance-telemetry.csv").is_file()
    performance_json = json.loads(
        (output / "performance.json").read_text(encoding="utf-8")
    )
    assert performance_json["schema_version"] == "1.2.0"
    assert len(performance_json["fixture_overview_statistics"]) == 6
    phases = {
        row["phase"] for row in performance_json["fixture_overview_statistics"]
    }
    assert "observed-total" in phases
    assert "completed-workflow-total" in phases
    assert len(performance_json["subphase_telemetry"]) == 3
    assert performance_json["subphase_telemetry"][0]["first_event_seconds"] == 0.2


def test_fixture_overview_aggregates_revisions_but_reports_heterogeneity(
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "Run20" / "report.json"
    ledger = tmp_path / "history.jsonl"
    _write_report(report_path)
    import_reports(
        reports=[report_path],
        ledger=ledger,
        overrides_path=tmp_path / "missing.yaml",
        default_speed=SpeedMode.STANDARD,
        default_git_commit="commit-1",
        default_host="windows-x86_64",
        apply=True,
    )
    original = next(
        record
        for record in load_performance_ledger(ledger)
        if record.test.fixture_id == "architecture-option-comparison"
    )
    another_revision = original.model_copy(
        update={
            "test": original.test.model_copy(
                update={"fixture_revision": "b" * 64}
            ),
            "runtime": original.runtime.model_copy(
                update={"model": "another-model", "speed": SpeedMode.FAST}
            ),
            "phases": original.phases.model_copy(
                update={
                    "initial": original.phases.initial.model_copy(
                        update={"duration_seconds": 20.0}
                    ),
                    "continuation": original.phases.continuation.model_copy(
                        update={"duration_seconds": 40.0}
                    ),
                }
            ),
            "timing": original.timing.model_copy(
                update={"measured_phase_seconds": 60.0}
            ),
        }
    )

    overview = fixture_overview_statistics([original, another_revision])
    initial = next(row for row in overview if row.phase == "initial")

    assert initial.observation_count == 2
    assert initial.revision_count == 2
    assert initial.workload_count == 1
    assert initial.model_count == 2
    assert initial.speed_count == 2
    assert initial.fixture_observation_count == 2
    assert initial.mean_seconds == 15
    assert initial.median_seconds == 15
    assert initial.percentile_75_seconds == 17.5
    assert initial.percentile_90_seconds == 19
    assert initial.median_absolute_deviation_seconds == 5
    assert initial.percentile_90_median_gap_seconds == 4

    completed_total = next(
        row for row in overview if row.phase == "completed-workflow-total"
    )
    assert completed_total.observation_count == 2
    assert completed_total.fixture_observation_count == 2
    assert completed_total.median_seconds == 45
