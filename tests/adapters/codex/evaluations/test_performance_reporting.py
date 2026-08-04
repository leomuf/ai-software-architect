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
    DecisionObservation,
    DeterministicAssertion,
    EvaluationStatus,
    FixtureResult,
    PhaseResult,
    PhaseTelemetry,
    ToolTimelineEvent,
)
from adapters.codex.evaluations.performance_import import import_reports
from adapters.codex.evaluations.performance_ledger import load_performance_ledger
from adapters.codex.evaluations.performance_models import SpeedMode
from adapters.codex.evaluations.performance_report import (
    fixture_overview_statistics,
    grouped_statistics,
    latency_objective_rows,
    observation_rows,
    recommendation_consistency_rows,
    write_reports,
)


def _phase(
    name: Literal["initial", "continuation"],
    duration: float,
    thread_id: str = "thread-1",
    decision_observation: DecisionObservation | None = None,
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
            tool_events=[
                ToolTimelineEvent(
                    ordinal=1,
                    tool_type="command_execution",
                    started_seconds=1.0,
                    completed_seconds=2.5,
                    duration_seconds=1.5,
                    status="completed",
                )
            ],
            unavailable_metrics=["pre_tool_use_hook_seconds"],
        ),
        decision_observation=decision_observation,
    )


def _write_report(
    path: Path,
    *,
    plugin_version: str = "0.1.0",
    comparison_initial: float = 10.0,
    comparison_continuation: float = 20.0,
    started_offset_minutes: int = 0,
) -> None:
    started = datetime(2026, 7, 21, 19, 50, tzinfo=UTC) + timedelta(
        minutes=started_offset_minutes
    )
    report = CampaignReport(
        started_at=started,
        completed_at=started + timedelta(seconds=50),
        codex_command="codex",
        codex_version="codex-cli test",
        installed_plugin_id="ai-software-architect@personal",
        installed_plugin_marketplace="personal",
        installed_plugin_version=plugin_version,
        installed_plugin_provenance_sha256="a" * 64,
        model="gpt-5.6-sol",
        reasoning_effort="medium",
        results=[
            FixtureResult(
                fixture_id="architecture-option-comparison",
                scenario="FLOW-004",
                status=EvaluationStatus.MANUAL_REVIEW,
                workspace="bounded-workspace",
                phases=[
                    _phase(
                        "initial",
                        comparison_initial,
                        decision_observation=DecisionObservation(
                            selected_category="Architecture",
                            selected_name="Layered Architecture",
                            material_assumption_sha256="b" * 64,
                            material_assumption_word_count=4,
                        ),
                    ),
                    _phase("continuation", comparison_continuation),
                ],
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
    assert (output / "performance-tool-timeline.csv").is_file()
    performance_json = json.loads(
        (output / "performance.json").read_text(encoding="utf-8")
    )
    assert performance_json["schema_version"] == "1.5.0"
    assert len(performance_json["fixture_overview_statistics"]) == 6
    phases = {
        row["phase"] for row in performance_json["fixture_overview_statistics"]
    }
    assert "observed-total" in phases
    assert "completed-workflow-total" in phases
    assert len(performance_json["subphase_telemetry"]) == 3
    assert performance_json["subphase_telemetry"][0]["first_event_seconds"] == 0.2
    assert len(performance_json["tool_timeline"]) == 3
    assert performance_json["tool_timeline"][0]["tool_type"] == "command_execution"
    assert performance_json["latency_objectives"] == []
    assert len(performance_json["recommendation_consistency"]) == 1
    consistency = performance_json["recommendation_consistency"][0]
    assert consistency["selection_distribution"] == (
        "Architecture/Layered Architecture=1"
    )
    assert consistency["plugin_version"] == "0.1.0"
    assert consistency["plugin_provenance"] == "a" * 64
    assert consistency["assessment"] == "stable-selection"
    assert (output / "recommendation-consistency.csv").is_file()


def test_latency_objectives_are_release_specific_warning_only(tmp_path: Path) -> None:
    report_paths = []
    for index in range(5):
        report_path = tmp_path / f"Run-{index}" / "report.json"
        _write_report(
            report_path,
            plugin_version="0.2.0",
            comparison_initial=50.0 + index,
            comparison_continuation=100.0 + index,
            started_offset_minutes=index,
        )
        report_paths.append(report_path)

    ledger = tmp_path / "history.jsonl"
    import_reports(
        reports=report_paths,
        ledger=ledger,
        overrides_path=tmp_path / "missing.yaml",
        default_speed=SpeedMode.STANDARD,
        default_git_commit="commit-1",
        default_host="windows-x86_64",
        apply=True,
    )

    records = load_performance_ledger(ledger)
    unknown_records = [
        record.model_copy(
            update={
                "runtime": record.runtime.model_copy(
                    update={"plugin_version": "unknown"}
                )
            }
        )
        for record in records
    ]
    objectives = latency_objective_rows([*records, *unknown_records])
    initial = next(row for row in objectives if row.phase == "initial")
    continuation = next(row for row in objectives if row.phase == "continuation")

    assert initial.plugin_version == "0.2.0"
    assert initial.count == 5
    assert initial.status == "warn"
    assert initial.percentile_90_provisional is True
    assert continuation.status == "pass"
    assert all(row.plugin_version != "unknown" for row in objectives)


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


def test_consistency_flags_different_selections_under_identical_assumption(
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
    changed_initial = original.phases.initial.model_copy(
        update={
            "decision_observation": DecisionObservation(
                selected_category="GoF",
                selected_name="Strategy",
                material_assumption_sha256="b" * 64,
                material_assumption_word_count=4,
            )
        }
    )
    changed = original.model_copy(
        update={
            "phases": original.phases.model_copy(update={"initial": changed_initial})
        }
    )

    rows = recommendation_consistency_rows([original, changed])

    assert len(rows) == 1
    assert rows[0].distinct_selections == 2
    assert rows[0].distinct_assumptions == 1
    assert rows[0].assessment == "contradiction-candidate-under-identical-assumption"


def test_consistency_separates_plugin_versions_and_provenance(tmp_path: Path) -> None:
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
    another_version = original.model_copy(
        update={
            "runtime": original.runtime.model_copy(
                update={"plugin_version": "0.2.0", "plugin_provenance": "c" * 64}
            )
        }
    )

    rows = recommendation_consistency_rows([original, another_version])

    assert len(rows) == 2
    assert {row.plugin_version for row in rows} == {"0.1.0", "0.2.0"}
    assert {row.plugin_provenance for row in rows} == {"a" * 64, "c" * 64}
