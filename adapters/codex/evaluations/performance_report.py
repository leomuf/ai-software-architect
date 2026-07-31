# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Render exploratory performance history as tables and grouped statistics."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, TypedDict

from adapters.codex.evaluations.performance_ledger import load_performance_ledger
from adapters.codex.evaluations.performance_models import (
    PerformanceObservation,
    PhaseStatus,
)

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LEDGER = ROOT / "evaluation-data" / "exploratory-runs.jsonl"
REPORT_SCHEMA_VERSION = "1.4.0"
MINIMUM_OBJECTIVE_SAMPLES = 5
PROVISIONAL_P90_SAMPLES = 10
LATENCY_OBJECTIVES_SECONDS: dict[tuple[str, str], tuple[float, float]] = {
    ("architecture-option-comparison", "continuation"): (120.0, 180.0),
    ("read-only-architecture-review", "initial"): (75.0, 120.0),
    ("clarify-ui-architecture", "continuation"): (50.0, 75.0),
    ("architecture-option-comparison", "initial"): (40.0, 75.0),
    ("abstract-factory-example", "initial"): (20.0, 35.0),
    ("clarify-ui-architecture", "initial"): (10.0, 15.0),
}


@dataclass(frozen=True)
class PerformanceRow:
    campaign: str
    fixture: str
    fixture_revision: str
    task_name: str
    plugin_version: str
    model: str
    reasoning_effort: str
    speed: str
    execution_mode: str
    initial_seconds: float
    continuation_seconds: float | None
    observed_total_seconds: float
    completed_workflow_total_seconds: float | None
    campaign_wall_clock_seconds: float
    outcome: str
    quality: str


@dataclass(frozen=True)
class TelemetryRow:
    campaign: str
    fixture: str
    fixture_revision: str
    phase: str
    model: str
    reasoning_effort: str
    speed: str
    execution_mode: str
    phase_seconds: float
    first_event_seconds: float | None
    first_agent_message_seconds: float | None
    last_agent_message_seconds: float | None
    agent_message_count: int
    tool_call_count: int
    input_tokens: int | None
    cached_input_tokens: int | None
    output_tokens: int | None
    item_counts: str
    unavailable_metrics: str


@dataclass(frozen=True)
class ToolTimelineRow:
    campaign: str
    fixture: str
    fixture_revision: str
    phase: str
    ordinal: int
    tool_type: str
    started_seconds: float
    completed_seconds: float
    duration_seconds: float
    gap_from_previous_tool_seconds: float | None
    status: str


@dataclass(frozen=True)
class StatisticRow:
    fixture: str
    phase: str
    model: str
    reasoning_effort: str
    speed: str
    execution_mode: str
    fixture_revision: str
    workload_fingerprint: str
    count: int
    group_observation_count: int
    mean_seconds: float
    sample_stddev_seconds: float | None
    median_seconds: float
    percentile_75_seconds: float
    percentile_90_seconds: float
    median_absolute_deviation_seconds: float
    percentile_90_median_gap_seconds: float
    minimum_seconds: float
    maximum_seconds: float


@dataclass(frozen=True)
class FixtureOverviewStatisticRow:
    fixture: str
    phase: str
    observation_count: int
    fixture_observation_count: int
    revision_count: int
    workload_count: int
    model_count: int
    speed_count: int
    execution_mode_count: int
    mean_seconds: float
    sample_stddev_seconds: float | None
    median_seconds: float
    percentile_75_seconds: float
    percentile_90_seconds: float
    median_absolute_deviation_seconds: float
    percentile_90_median_gap_seconds: float
    minimum_seconds: float
    maximum_seconds: float


@dataclass(frozen=True)
class LatencyObjectiveRow:
    plugin_version: str
    fixture: str
    phase: str
    model: str
    reasoning_effort: str
    speed: str
    execution_mode: str
    fixture_revision: str
    workload_fingerprint: str
    count: int
    median_seconds: float
    percentile_90_seconds: float
    median_target_seconds: float
    percentile_90_target_seconds: float
    percentile_90_provisional: bool
    status: str


class _Distribution(TypedDict):
    mean_seconds: float
    sample_stddev_seconds: float | None
    median_seconds: float
    percentile_75_seconds: float
    percentile_90_seconds: float
    median_absolute_deviation_seconds: float
    percentile_90_median_gap_seconds: float
    minimum_seconds: float
    maximum_seconds: float


def _distribution(samples: Sequence[float]) -> _Distribution:
    """Calculate conventional and robust descriptive latency statistics."""

    median = statistics.median(samples)
    if len(samples) == 1:
        percentile_75 = samples[0]
        percentile_90 = samples[0]
    else:
        percentile_75 = statistics.quantiles(
            samples,
            n=4,
            method="inclusive",
        )[2]
        percentile_90 = statistics.quantiles(
            samples,
            n=10,
            method="inclusive",
        )[8]
    return {
        "mean_seconds": round(statistics.mean(samples), 3),
        "sample_stddev_seconds": (
            round(statistics.stdev(samples), 3) if len(samples) > 1 else None
        ),
        "median_seconds": round(median, 3),
        "percentile_75_seconds": round(percentile_75, 3),
        "percentile_90_seconds": round(percentile_90, 3),
        "median_absolute_deviation_seconds": round(
            statistics.median(abs(sample - median) for sample in samples),
            3,
        ),
        "percentile_90_median_gap_seconds": round(percentile_90 - median, 3),
        "minimum_seconds": round(min(samples), 3),
        "maximum_seconds": round(max(samples), 3),
    }


def observation_rows(records: Sequence[PerformanceObservation]) -> list[PerformanceRow]:
    rows: list[PerformanceRow] = []
    for record in sorted(
        records,
        key=lambda item: (item.campaign.started_at, item.campaign.id, item.test.fixture_id),
    ):
        continuation = (
            record.phases.continuation.duration_seconds
            if record.phases.continuation.status == PhaseStatus.COMPLETED
            else None
        )
        rows.append(
            PerformanceRow(
                campaign=record.campaign.id,
                fixture=record.test.fixture_id,
                fixture_revision=record.test.fixture_revision,
                task_name=record.test.task_name or "—",
                plugin_version=record.runtime.plugin_version,
                model=record.runtime.model,
                reasoning_effort=record.runtime.reasoning_effort,
                speed=record.runtime.speed.value,
                execution_mode=record.campaign.execution_mode.value,
                initial_seconds=record.phases.initial.duration_seconds or 0.0,
                continuation_seconds=continuation,
                observed_total_seconds=record.timing.measured_phase_seconds,
                completed_workflow_total_seconds=(
                    record.timing.measured_phase_seconds
                    if continuation is not None
                    else None
                ),
                campaign_wall_clock_seconds=record.campaign.wall_clock_seconds,
                outcome=record.result.outcome.value,
                quality=record.result.measurement_quality.value,
            )
        )
    return rows


def telemetry_rows(records: Sequence[PerformanceObservation]) -> list[TelemetryRow]:
    rows: list[TelemetryRow] = []
    for record in sorted(
        records,
        key=lambda item: (item.campaign.started_at, item.campaign.id, item.test.fixture_id),
    ):
        for phase_name, phase in (
            ("initial", record.phases.initial),
            ("continuation", record.phases.continuation),
        ):
            telemetry = phase.telemetry
            if phase.status != PhaseStatus.COMPLETED or telemetry is None:
                continue
            rows.append(
                TelemetryRow(
                    campaign=record.campaign.id,
                    fixture=record.test.fixture_id,
                    fixture_revision=record.test.fixture_revision,
                    phase=phase_name,
                    model=record.runtime.model,
                    reasoning_effort=record.runtime.reasoning_effort,
                    speed=record.runtime.speed.value,
                    execution_mode=record.campaign.execution_mode.value,
                    phase_seconds=phase.duration_seconds or 0.0,
                    first_event_seconds=telemetry.first_event_seconds,
                    first_agent_message_seconds=telemetry.first_agent_message_seconds,
                    last_agent_message_seconds=telemetry.last_agent_message_seconds,
                    agent_message_count=telemetry.agent_message_count,
                    tool_call_count=telemetry.tool_call_count,
                    input_tokens=telemetry.input_tokens,
                    cached_input_tokens=telemetry.cached_input_tokens,
                    output_tokens=telemetry.output_tokens,
                    item_counts=json.dumps(
                        telemetry.item_counts,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    unavailable_metrics=",".join(telemetry.unavailable_metrics),
                )
            )
    return rows


def tool_timeline_rows(
    records: Sequence[PerformanceObservation],
) -> list[ToolTimelineRow]:
    rows: list[ToolTimelineRow] = []
    for record in sorted(
        records,
        key=lambda item: (item.campaign.started_at, item.campaign.id, item.test.fixture_id),
    ):
        for phase_name, phase in (
            ("initial", record.phases.initial),
            ("continuation", record.phases.continuation),
        ):
            if phase.status != PhaseStatus.COMPLETED or phase.telemetry is None:
                continue
            for event in phase.telemetry.tool_events:
                rows.append(
                    ToolTimelineRow(
                        campaign=record.campaign.id,
                        fixture=record.test.fixture_id,
                        fixture_revision=record.test.fixture_revision,
                        phase=phase_name,
                        ordinal=event.ordinal,
                        tool_type=event.tool_type,
                        started_seconds=event.started_seconds,
                        completed_seconds=event.completed_seconds,
                        duration_seconds=event.duration_seconds,
                        gap_from_previous_tool_seconds=(
                            event.gap_from_previous_tool_seconds
                        ),
                        status=event.status,
                    )
                )
    return rows


def fixture_overview_statistics(
    records: Sequence[PerformanceObservation],
) -> list[FixtureOverviewStatisticRow]:
    grouped: dict[tuple[str, str], list[tuple[PerformanceObservation, float]]] = (
        defaultdict(list)
    )
    for record in records:
        grouped[(record.test.fixture_id, "initial")].append(
            (record, record.phases.initial.duration_seconds or 0.0)
        )
        if record.phases.continuation.status == PhaseStatus.COMPLETED:
            grouped[(record.test.fixture_id, "continuation")].append(
                (record, record.phases.continuation.duration_seconds or 0.0)
            )
        grouped[(record.test.fixture_id, "observed-total")].append(
            (record, record.timing.measured_phase_seconds)
        )
        if record.phases.continuation.status == PhaseStatus.COMPLETED:
            grouped[(record.test.fixture_id, "completed-workflow-total")].append(
                (record, record.timing.measured_phase_seconds)
            )

    rows: list[FixtureOverviewStatisticRow] = []
    fixture_counts: dict[str, int] = defaultdict(int)
    for record in records:
        fixture_counts[record.test.fixture_id] += 1
    for (fixture, phase), observations in sorted(grouped.items()):
        samples = [duration for _, duration in observations]
        rows.append(
            FixtureOverviewStatisticRow(
                fixture=fixture,
                phase=phase,
                observation_count=len(samples),
                fixture_observation_count=fixture_counts[fixture],
                revision_count=len(
                    {record.test.fixture_revision for record, _ in observations}
                ),
                workload_count=len(
                    {record.test.workload_fingerprint for record, _ in observations}
                ),
                model_count=len({record.runtime.model for record, _ in observations}),
                speed_count=len(
                    {record.runtime.speed.value for record, _ in observations}
                ),
                execution_mode_count=len(
                    {record.campaign.execution_mode.value for record, _ in observations}
                ),
                **_distribution(samples),
            )
        )
    return rows


def grouped_statistics(records: Sequence[PerformanceObservation]) -> list[StatisticRow]:
    values: dict[tuple[str, ...], list[float]] = defaultdict(list)
    group_counts: dict[tuple[str, ...], int] = defaultdict(int)
    for record in records:
        common = (
            record.test.fixture_id,
            record.runtime.model,
            record.runtime.reasoning_effort,
            record.runtime.speed.value,
            record.campaign.execution_mode.value,
            record.test.fixture_revision,
            record.test.workload_fingerprint,
        )
        group_counts[common] += 1
        values[(*common, "initial")].append(record.phases.initial.duration_seconds or 0.0)
        if record.phases.continuation.status == PhaseStatus.COMPLETED:
            values[(*common, "continuation")].append(
                record.phases.continuation.duration_seconds or 0.0
            )
        values[(*common, "observed-total")].append(
            record.timing.measured_phase_seconds
        )
        if record.phases.continuation.status == PhaseStatus.COMPLETED:
            values[(*common, "completed-workflow-total")].append(
                record.timing.measured_phase_seconds
            )

    rows: list[StatisticRow] = []
    for key, samples in sorted(values.items()):
        fixture, model, effort, speed, mode, revision, workload, phase = key
        rows.append(
            StatisticRow(
                fixture=fixture,
                phase=phase,
                model=model,
                reasoning_effort=effort,
                speed=speed,
                execution_mode=mode,
                fixture_revision=revision,
                workload_fingerprint=workload,
                count=len(samples),
                group_observation_count=group_counts[key[:-1]],
                **_distribution(samples),
            )
        )
    return rows


def latency_objective_rows(
    records: Sequence[PerformanceObservation],
) -> list[LatencyObjectiveRow]:
    """Evaluate non-blocking objectives for exact release-compatible cohorts."""

    values: dict[tuple[str, ...], list[float]] = defaultdict(list)
    for record in records:
        if record.runtime.plugin_version == "unknown":
            continue
        common = (
            record.runtime.plugin_version,
            record.test.fixture_id,
            record.runtime.model,
            record.runtime.reasoning_effort,
            record.runtime.speed.value,
            record.campaign.execution_mode.value,
            record.test.fixture_revision,
            record.test.workload_fingerprint,
        )
        if (record.test.fixture_id, "initial") in LATENCY_OBJECTIVES_SECONDS:
            values[(*common, "initial")].append(
                record.phases.initial.duration_seconds or 0.0
            )
        if (
            record.phases.continuation.status == PhaseStatus.COMPLETED
            and (record.test.fixture_id, "continuation")
            in LATENCY_OBJECTIVES_SECONDS
        ):
            values[(*common, "continuation")].append(
                record.phases.continuation.duration_seconds or 0.0
            )

    rows: list[LatencyObjectiveRow] = []
    for key, samples in sorted(values.items()):
        if len(samples) < MINIMUM_OBJECTIVE_SAMPLES:
            continue
        (
            plugin_version,
            fixture,
            model,
            effort,
            speed,
            mode,
            revision,
            workload,
            phase,
        ) = key
        median_target, p90_target = LATENCY_OBJECTIVES_SECONDS[(fixture, phase)]
        distribution = _distribution(samples)
        status = (
            "pass"
            if distribution["median_seconds"] <= median_target
            and distribution["percentile_90_seconds"] <= p90_target
            else "warn"
        )
        rows.append(
            LatencyObjectiveRow(
                plugin_version=plugin_version,
                fixture=fixture,
                phase=phase,
                model=model,
                reasoning_effort=effort,
                speed=speed,
                execution_mode=mode,
                fixture_revision=revision,
                workload_fingerprint=workload,
                count=len(samples),
                median_seconds=distribution["median_seconds"],
                percentile_90_seconds=distribution["percentile_90_seconds"],
                median_target_seconds=median_target,
                percentile_90_target_seconds=p90_target,
                percentile_90_provisional=len(samples) < PROVISIONAL_P90_SAMPLES,
                status=status,
            )
        )
    return rows


def _seconds(value: float | None) -> str:
    return "—" if value is None else f"{value:.3f}"


def render_markdown(
    rows: Sequence[PerformanceRow],
    telemetry: Sequence[TelemetryRow],
    tool_timeline: Sequence[ToolTimelineRow],
    overview_rows: Sequence[FixtureOverviewStatisticRow],
    statistics_rows: Sequence[StatisticRow],
    objective_rows: Sequence[LatencyObjectiveRow],
) -> str:
    lines = [
        "# Exploratory Evaluation Performance",
        "",
        "## Observations",
        "",
        "| Campaign | Task | Fixture | Revision | Plugin | Model | Effort | Speed | Mode | "
        "Initial (s) | Continuation (s) | Observed total (s) | "
        "Completed workflow total (s) | Campaign wall (s) |",
        "|---|---|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for observation_row in rows:
        lines.append(
            f"| {observation_row.campaign} | {observation_row.task_name} | "
            f"{observation_row.fixture} | `{observation_row.fixture_revision[:8]}` | "
            f"{observation_row.plugin_version} | "
            f"{observation_row.model} | {observation_row.reasoning_effort} | "
            f"{observation_row.speed} | {observation_row.execution_mode} | "
            f"{_seconds(observation_row.initial_seconds)} | "
            f"{_seconds(observation_row.continuation_seconds)} | "
            f"{_seconds(observation_row.observed_total_seconds)} | "
            f"{_seconds(observation_row.completed_workflow_total_seconds)} | "
            f"{_seconds(observation_row.campaign_wall_clock_seconds)} |"
        )
    lines.extend(
        [
            "",
            "## Runner-observed subphase telemetry",
            "",
            "These values are captured from Codex JSONL as the runner receives it. "
            "First/last agent-message values mark completed message events, not "
            "time-to-first-token. Hook, template-loading, patch-construction, and "
            "subagent-duration timings remain unavailable unless Codex exposes them.",
            "",
            "| Campaign | Fixture | Revision | Phase | Model | Effort | Speed | Mode | "
            "Phase (s) | First event (s) | First agent message (s) | "
            "Last agent message (s) | Messages | Tool calls | Input tokens | "
            "Cached input | Output tokens |",
            "|---|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    if not telemetry:
        lines.append(
            "| — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |"
        )
    for telemetry_row in telemetry:
        input_tokens = (
            str(telemetry_row.input_tokens)
            if telemetry_row.input_tokens is not None
            else "—"
        )
        cached_input_tokens = (
            str(telemetry_row.cached_input_tokens)
            if telemetry_row.cached_input_tokens is not None
            else "—"
        )
        output_tokens = (
            str(telemetry_row.output_tokens)
            if telemetry_row.output_tokens is not None
            else "—"
        )
        lines.append(
            f"| {telemetry_row.campaign} | {telemetry_row.fixture} | "
            f"`{telemetry_row.fixture_revision[:8]}` | {telemetry_row.phase} | "
            f"{telemetry_row.model} | {telemetry_row.reasoning_effort} | "
            f"{telemetry_row.speed} | {telemetry_row.execution_mode} | "
            f"{_seconds(telemetry_row.phase_seconds)} | "
            f"{_seconds(telemetry_row.first_event_seconds)} | "
            f"{_seconds(telemetry_row.first_agent_message_seconds)} | "
            f"{_seconds(telemetry_row.last_agent_message_seconds)} | "
            f"{telemetry_row.agent_message_count} | {telemetry_row.tool_call_count} | "
            f"{input_tokens} | {cached_input_tokens} | {output_tokens} |"
        )
    lines.extend(
        [
            "",
            "## Privacy-preserving tool timeline",
            "",
            "The timeline records only tool category, order, relative timing, and "
            "status. Commands, paths, prompts, source text, and tool output are never "
            "copied into the performance ledger.",
            "",
            "| Campaign | Fixture | Revision | Phase | # | Tool type | Start (s) | "
            "End (s) | Duration (s) | Gap from prior tool (s) | Status |",
            "|---|---|---|---|---:|---|---:|---:|---:|---:|---|",
        ]
    )
    if not tool_timeline:
        lines.append("| â€” | â€” | â€” | â€” | â€” | â€” | â€” | â€” | â€” | â€” | â€” |")
    for event in tool_timeline:
        lines.append(
            f"| {event.campaign} | {event.fixture} | "
            f"`{event.fixture_revision[:8]}` | {event.phase} | {event.ordinal} | "
            f"{event.tool_type} | {_seconds(event.started_seconds)} | "
            f"{_seconds(event.completed_seconds)} | {_seconds(event.duration_seconds)} | "
            f"{_seconds(event.gap_from_previous_tool_seconds)} | {event.status} |"
        )
    lines.extend(
        [
            "",
            "## Cross-version fixture overview",
            "",
            "This descriptive overview answers how each fixture has typically performed "
            "across the complete recorded history. It may combine different revisions, "
            "workloads, models, speed tiers, and execution modes, so use the comparable-"
            "group statistics below for release-to-release conclusions. Robust P50, "
            "P75, P90, and MAD values lead this overview so isolated historical "
            "outliers do not dominate optimization priorities.",
            "",
            "| Fixture | Phase | Samples/Runs | Revisions | Workloads | Models | Speeds | "
            "Modes | P50 (s) | P75 (s) | P90 (s) | MAD (s) | P90-P50 (s) |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for overview_row in overview_rows:
        lines.append(
            f"| {overview_row.fixture} | {overview_row.phase} | "
            f"{overview_row.observation_count}/{overview_row.fixture_observation_count} | "
            f"{overview_row.revision_count} | "
            f"{overview_row.workload_count} | {overview_row.model_count} | "
            f"{overview_row.speed_count} | {overview_row.execution_mode_count} | "
            f"{_seconds(overview_row.median_seconds)} | "
            f"{_seconds(overview_row.percentile_75_seconds)} | "
            f"{_seconds(overview_row.percentile_90_seconds)} | "
            f"{_seconds(overview_row.median_absolute_deviation_seconds)} | "
            f"{_seconds(overview_row.percentile_90_median_gap_seconds)} |"
        )
    lines.extend(
        [
            "",
            "## Warning-only latency objectives",
            "",
            "These release-specific checks are informational and never fail CI. "
            "They appear only after five exact compatible observations. P90 remains "
            "provisional until ten observations are available.",
            "",
            "| Plugin | Fixture | Phase | Samples | P50/target (s) | "
            "P90/target (s) | P90 maturity | Status |",
            "|---|---|---|---:|---:|---:|---|---|",
        ]
    )
    if not objective_rows:
        lines.append("| â€” | â€” | â€” | â€” | â€” | â€” | â€” | not evaluated |")
    for objective_row in objective_rows:
        maturity = (
            "provisional" if objective_row.percentile_90_provisional else "established"
        )
        lines.append(
            f"| {objective_row.plugin_version} | {objective_row.fixture} | "
            f"{objective_row.phase} | {objective_row.count} | "
            f"{_seconds(objective_row.median_seconds)}/"
            f"{_seconds(objective_row.median_target_seconds)} | "
            f"{_seconds(objective_row.percentile_90_seconds)}/"
            f"{_seconds(objective_row.percentile_90_target_seconds)} | "
            f"{maturity} | {objective_row.status} |"
        )
    lines.extend(
        [
            "",
            "## Comparable-group statistics",
            "",
            "| Fixture | Revision | Workload | Phase | Model | Effort | Speed | Mode | "
            "Samples/Runs | Mean (s) | Stddev (s) | P50 (s) | P75 (s) | P90 (s) | "
            "MAD (s) | P90-P50 (s) | Min (s) | Max (s) |",
            "|---|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for statistic_row in statistics_rows:
        lines.append(
            f"| {statistic_row.fixture} | `{statistic_row.fixture_revision[:8]}` | "
            f"`{statistic_row.workload_fingerprint[:8]}` | {statistic_row.phase} | "
            f"{statistic_row.model} | {statistic_row.reasoning_effort} | "
            f"{statistic_row.speed} | {statistic_row.execution_mode} | "
            f"{statistic_row.count}/{statistic_row.group_observation_count} | "
            f"{_seconds(statistic_row.mean_seconds)} | "
            f"{_seconds(statistic_row.sample_stddev_seconds)} | "
            f"{_seconds(statistic_row.median_seconds)} | "
            f"{_seconds(statistic_row.percentile_75_seconds)} | "
            f"{_seconds(statistic_row.percentile_90_seconds)} | "
            f"{_seconds(statistic_row.median_absolute_deviation_seconds)} | "
            f"{_seconds(statistic_row.percentile_90_median_gap_seconds)} | "
            f"{_seconds(statistic_row.minimum_seconds)} | "
            f"{_seconds(statistic_row.maximum_seconds)} |"
        )
    lines.extend(
        [
            "",
            "`observed-total` is the sum of every phase actually completed in an "
            "observation. `completed-workflow-total` is emitted only when both the "
            "initial and continuation phases completed. Missing continuations are "
            "excluded from continuation and completed-workflow statistics and are "
            "never treated as zero. P90 is provisional for fewer than ten samples; "
            "groups with fewer than five samples are descriptive only.",
            "",
        ]
    )
    return "\n".join(lines)


def write_reports(ledger: Path, output_directory: Path) -> tuple[int, int]:
    records = load_performance_ledger(ledger)
    rows = observation_rows(records)
    telemetry = telemetry_rows(records)
    tool_timeline = tool_timeline_rows(records)
    overview_rows = fixture_overview_statistics(records)
    statistic_rows = grouped_statistics(records)
    objective_rows = latency_objective_rows(records)
    output_directory.mkdir(parents=True, exist_ok=True)

    markdown = render_markdown(
        rows,
        telemetry,
        tool_timeline,
        overview_rows,
        statistic_rows,
        objective_rows,
    )
    (output_directory / "performance.md").write_text(
        markdown,
        encoding="utf-8",
        newline="\n",
    )
    with (output_directory / "performance.csv").open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(PerformanceRow.__annotations__))
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)
    with (output_directory / "performance-telemetry.csv").open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(TelemetryRow.__annotations__))
        writer.writeheader()
        writer.writerows(asdict(row) for row in telemetry)
    with (output_directory / "performance-tool-timeline.csv").open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=list(ToolTimelineRow.__annotations__),
        )
        writer.writeheader()
        writer.writerows(asdict(row) for row in tool_timeline)
    payload: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "observations": [asdict(row) for row in rows],
        "subphase_telemetry": [asdict(row) for row in telemetry],
        "tool_timeline": [asdict(row) for row in tool_timeline],
        "fixture_overview_statistics": [asdict(row) for row in overview_rows],
        "statistics": [asdict(row) for row in statistic_rows],
        "latency_objectives": [asdict(row) for row in objective_rows],
    }
    (output_directory / "performance.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return len(rows), len(statistic_rows)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Write report files without printing the Markdown table.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        observations, groups = write_reports(args.ledger, args.output_directory)
    except (OSError, ValueError) as exc:
        print(f"Performance report failed: {exc}", file=sys.stderr)
        return 1
    if not args.quiet:
        print((args.output_directory / "performance.md").read_text(encoding="utf-8"))
    print(f"Rendered {observations} observation(s) and {groups} statistic row(s).")
    print(args.output_directory)
    return 0


if __name__ == "__main__":
    sys.exit(main())
