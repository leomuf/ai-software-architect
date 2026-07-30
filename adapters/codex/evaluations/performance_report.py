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
from typing import Any

from adapters.codex.evaluations.performance_ledger import load_performance_ledger
from adapters.codex.evaluations.performance_models import (
    PerformanceObservation,
    PhaseStatus,
)

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LEDGER = ROOT / "evaluation-data" / "exploratory-runs.jsonl"


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
    total_seconds: float
    campaign_wall_clock_seconds: float
    outcome: str
    quality: str


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
    mean_seconds: float
    sample_stddev_seconds: float | None
    median_seconds: float
    minimum_seconds: float
    maximum_seconds: float


@dataclass(frozen=True)
class FixtureOverviewStatisticRow:
    fixture: str
    phase: str
    observation_count: int
    revision_count: int
    workload_count: int
    model_count: int
    speed_count: int
    execution_mode_count: int
    mean_seconds: float
    sample_stddev_seconds: float | None
    median_seconds: float
    minimum_seconds: float
    maximum_seconds: float


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
                total_seconds=record.timing.measured_phase_seconds,
                campaign_wall_clock_seconds=record.campaign.wall_clock_seconds,
                outcome=record.result.outcome.value,
                quality=record.result.measurement_quality.value,
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
        grouped[(record.test.fixture_id, "total")].append(
            (record, record.timing.measured_phase_seconds)
        )

    rows: list[FixtureOverviewStatisticRow] = []
    for (fixture, phase), observations in sorted(grouped.items()):
        samples = [duration for _, duration in observations]
        rows.append(
            FixtureOverviewStatisticRow(
                fixture=fixture,
                phase=phase,
                observation_count=len(samples),
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
                mean_seconds=round(statistics.mean(samples), 3),
                sample_stddev_seconds=(
                    round(statistics.stdev(samples), 3) if len(samples) > 1 else None
                ),
                median_seconds=round(statistics.median(samples), 3),
                minimum_seconds=round(min(samples), 3),
                maximum_seconds=round(max(samples), 3),
            )
        )
    return rows


def grouped_statistics(records: Sequence[PerformanceObservation]) -> list[StatisticRow]:
    values: dict[tuple[str, ...], list[float]] = defaultdict(list)
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
        values[(*common, "initial")].append(record.phases.initial.duration_seconds or 0.0)
        if record.phases.continuation.status == PhaseStatus.COMPLETED:
            values[(*common, "continuation")].append(
                record.phases.continuation.duration_seconds or 0.0
            )
        values[(*common, "total")].append(record.timing.measured_phase_seconds)

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
                mean_seconds=round(statistics.mean(samples), 3),
                sample_stddev_seconds=(
                    round(statistics.stdev(samples), 3) if len(samples) > 1 else None
                ),
                median_seconds=round(statistics.median(samples), 3),
                minimum_seconds=round(min(samples), 3),
                maximum_seconds=round(max(samples), 3),
            )
        )
    return rows


def _seconds(value: float | None) -> str:
    return "—" if value is None else f"{value:.3f}"


def render_markdown(
    rows: Sequence[PerformanceRow],
    overview_rows: Sequence[FixtureOverviewStatisticRow],
    statistics_rows: Sequence[StatisticRow],
) -> str:
    lines = [
        "# Exploratory Evaluation Performance",
        "",
        "## Observations",
        "",
        "| Campaign | Task | Fixture | Revision | Plugin | Model | Effort | Speed | Mode | "
        "Initial (s) | Continuation (s) | Total (s) | Campaign wall (s) |",
        "|---|---|---|---|---|---|---|---|---|---:|---:|---:|---:|",
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
            f"{_seconds(observation_row.total_seconds)} | "
            f"{_seconds(observation_row.campaign_wall_clock_seconds)} |"
        )
    lines.extend(
        [
            "",
            "## Cross-version fixture overview",
            "",
            "This descriptive overview answers how each fixture has typically performed "
            "across the complete recorded history. It may combine different revisions, "
            "workloads, models, speed tiers, and execution modes, so use the comparable-"
            "group statistics below for release-to-release conclusions.",
            "",
            "| Fixture | Phase | Observations | Revisions | Workloads | Models | Speeds | "
            "Modes | Mean (s) | Stddev (s) | Median (s) | Min (s) | Max (s) |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for overview_row in overview_rows:
        lines.append(
            f"| {overview_row.fixture} | {overview_row.phase} | "
            f"{overview_row.observation_count} | {overview_row.revision_count} | "
            f"{overview_row.workload_count} | {overview_row.model_count} | "
            f"{overview_row.speed_count} | {overview_row.execution_mode_count} | "
            f"{_seconds(overview_row.mean_seconds)} | "
            f"{_seconds(overview_row.sample_stddev_seconds)} | "
            f"{_seconds(overview_row.median_seconds)} | "
            f"{_seconds(overview_row.minimum_seconds)} | "
            f"{_seconds(overview_row.maximum_seconds)} |"
        )
    lines.extend(
        [
            "",
            "## Comparable-group statistics",
            "",
            "| Fixture | Revision | Workload | Phase | Model | Effort | Speed | Mode | "
            "n | Mean (s) | Stddev (s) | Median (s) | Min (s) | Max (s) |",
            "|---|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for statistic_row in statistics_rows:
        lines.append(
            f"| {statistic_row.fixture} | `{statistic_row.fixture_revision[:8]}` | "
            f"`{statistic_row.workload_fingerprint[:8]}` | {statistic_row.phase} | "
            f"{statistic_row.model} | {statistic_row.reasoning_effort} | "
            f"{statistic_row.speed} | {statistic_row.execution_mode} | "
            f"{statistic_row.count} | {_seconds(statistic_row.mean_seconds)} | "
            f"{_seconds(statistic_row.sample_stddev_seconds)} | "
            f"{_seconds(statistic_row.median_seconds)} | "
            f"{_seconds(statistic_row.minimum_seconds)} | "
            f"{_seconds(statistic_row.maximum_seconds)} |"
        )
    lines.extend(
        [
            "",
            "Missing continuations are excluded from continuation statistics and are never "
            "treated as zero.",
            "",
        ]
    )
    return "\n".join(lines)


def write_reports(ledger: Path, output_directory: Path) -> tuple[int, int]:
    records = load_performance_ledger(ledger)
    rows = observation_rows(records)
    overview_rows = fixture_overview_statistics(records)
    statistic_rows = grouped_statistics(records)
    output_directory.mkdir(parents=True, exist_ok=True)

    markdown = render_markdown(rows, overview_rows, statistic_rows)
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
    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "observations": [asdict(row) for row in rows],
        "fixture_overview_statistics": [asdict(row) for row in overview_rows],
        "statistics": [asdict(row) for row in statistic_rows],
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
