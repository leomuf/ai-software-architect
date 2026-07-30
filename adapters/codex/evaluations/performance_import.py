# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Preview and import machine-readable exploratory reports into performance history."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

import yaml
from pydantic import Field

from adapters.codex.evaluations.models import (
    CampaignReport,
    EvaluationStatus,
    FixtureResult,
    StrictModel,
    load_fixture,
)
from adapters.codex.evaluations.performance_ledger import append_performance_observations
from adapters.codex.evaluations.performance_models import (
    CampaignMetadata,
    EvaluationOutcome,
    ExecutionMode,
    MeasurementQuality,
    ObservationSource,
    PerformanceObservation,
    PhaseMeasurement,
    PhaseMeasurements,
    PhaseStatus,
    ResultMetadata,
    RuntimeMetadata,
    SpeedMode,
    TestMetadata,
    TimingMetadata,
    build_performance_observation,
)

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LEDGER = ROOT / "evaluation-data" / "exploratory-runs.jsonl"
DEFAULT_OVERRIDES = ROOT / "evaluation-data" / "historical-import-overrides.yaml"
FIXTURE_DIRECTORY = ROOT / "shared" / "evaluations" / "model-fixtures"


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.name


class CampaignOverride(StrictModel):
    campaign_id: str = Field(min_length=1)
    speed: SpeedMode | None = None
    git_commit: str | None = Field(default=None, min_length=1)
    host: str | None = Field(default=None, min_length=1)


class ImportOverrides(StrictModel):
    schema_version: str
    overrides: list[CampaignOverride] = Field(default_factory=list)


class ImportExclusion(StrictModel):
    report: str
    fixture_id: str
    phase: str | None = None
    reason: str


class ReportImportPreview(StrictModel):
    schema_version: str = "1.0.0"
    generated_at: datetime
    reports: list[str]
    accepted: list[PerformanceObservation]
    exclusions: list[ImportExclusion]
    applied_records: int = 0


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _workload_fingerprint(fixture_path: Path) -> str:
    fixture = load_fixture(fixture_path)
    payload = json.dumps(
        fixture.repository,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _fixture_path(fixture_id: str) -> Path:
    path = FIXTURE_DIRECTORY / f"{fixture_id}.yaml"
    if not path.is_file():
        raise ValueError(f"No shared fixture exists for report result: {fixture_id}")
    return path


def _load_overrides(path: Path) -> dict[str, CampaignOverride]:
    if not path.is_file():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    parsed = ImportOverrides.model_validate_json(json.dumps(raw))
    return {item.campaign_id: item for item in parsed.overrides}


def _phase_is_eligible(result: FixtureResult, phase_index: int) -> bool:
    phase = result.phases[phase_index]
    return (
        phase.exit_code == 0
        and phase.final_response_file is not None
        and "invalid-jsonl" not in phase.event_types
    )


def _outcome(status: EvaluationStatus) -> EvaluationOutcome:
    if status == EvaluationStatus.DETERMINISTIC_FAILURE:
        return EvaluationOutcome.DETERMINISTIC_FAILURE
    return EvaluationOutcome.MANUAL_REVIEW


def _report_observations(
    *,
    report_path: Path,
    speed: SpeedMode,
    git_commit: str,
    host: str,
    source: ObservationSource = ObservationSource.REPORT_IMPORT,
) -> tuple[list[PerformanceObservation], list[ImportExclusion]]:
    report = CampaignReport.model_validate_json(report_path.read_text(encoding="utf-8"))
    campaign_id = report_path.parent.name
    wall_clock = (
        report.campaign_wall_clock_seconds
        if report.campaign_wall_clock_seconds is not None
        else max((report.completed_at - report.started_at).total_seconds(), 0.0)
    )
    accepted: list[PerformanceObservation] = []
    exclusions: list[ImportExclusion] = []

    for result in report.results:
        if result.status in {EvaluationStatus.PLANNED, EvaluationStatus.INFRASTRUCTURE_ERROR}:
            exclusions.append(
                ImportExclusion(
                    report=_display_path(report_path),
                    fixture_id=result.fixture_id,
                    reason=result.error or f"result status is {result.status.value}",
                )
            )
            continue
        eligible_phases = [
            phase
            for index, phase in enumerate(result.phases)
            if _phase_is_eligible(result, index)
        ]
        for index, phase in enumerate(result.phases):
            if not _phase_is_eligible(result, index):
                exclusions.append(
                    ImportExclusion(
                        report=_display_path(report_path),
                        fixture_id=result.fixture_id,
                        phase=phase.name,
                        reason="phase did not produce a completed usable response",
                    )
                )
        initial = next((item for item in eligible_phases if item.name == "initial"), None)
        if initial is None:
            exclusions.append(
                ImportExclusion(
                    report=_display_path(report_path),
                    fixture_id=result.fixture_id,
                    phase="initial",
                    reason="no eligible initial phase remained",
                )
            )
            continue
        continuation = next(
            (item for item in eligible_phases if item.name == "continuation"),
            None,
        )
        fixture_path = _fixture_path(result.fixture_id)
        phases = PhaseMeasurements(
            initial=PhaseMeasurement(
                status=PhaseStatus.COMPLETED,
                duration_seconds=initial.duration_seconds,
            ),
            continuation=(
                PhaseMeasurement(
                    status=PhaseStatus.COMPLETED,
                    duration_seconds=continuation.duration_seconds,
                )
                if continuation is not None
                else PhaseMeasurement(status=PhaseStatus.NOT_RUN)
            ),
        )
        measured = sum(
            phase.duration_seconds or 0.0
            for phase in (phases.initial, phases.continuation)
        )
        accepted.append(
            build_performance_observation(
                campaign=CampaignMetadata(
                    id=campaign_id,
                    execution_mode=ExecutionMode.SEQUENTIAL_CODEX_CLI,
                    started_at=report.started_at,
                    completed_at=report.completed_at,
                    wall_clock_seconds=round(wall_clock, 3),
                ),
                test=TestMetadata(
                    fixture_id=result.fixture_id,
                    fixture_revision=_sha256(fixture_path),
                    workload_fingerprint=_workload_fingerprint(fixture_path),
                    task_name=None,
                    task_id=initial.thread_id,
                ),
                runtime=RuntimeMetadata(
                    model=report.model,
                    reasoning_effort=report.reasoning_effort,
                    speed=speed,
                    codex_version=report.codex_version,
                    plugin_version=report.installed_plugin_version or "unknown",
                    plugin_provenance=report.installed_plugin_provenance_sha256,
                    git_commit=git_commit,
                    host=host,
                ),
                phases=phases,
                timing=TimingMetadata(measured_phase_seconds=round(measured, 3)),
                result=ResultMetadata(
                    outcome=_outcome(result.status),
                    source=source,
                    measurement_quality=MeasurementQuality.MEASURED,
                    notes="Imported from an existing machine-readable Codex runner report.",
                ),
            )
        )
    return accepted, exclusions


def import_reports(
    *,
    reports: Sequence[Path],
    ledger: Path,
    overrides_path: Path,
    default_speed: SpeedMode,
    default_git_commit: str,
    default_host: str,
    apply: bool,
) -> ReportImportPreview:
    overrides = _load_overrides(overrides_path)
    accepted: list[PerformanceObservation] = []
    exclusions: list[ImportExclusion] = []
    for report_path in reports:
        campaign_id = report_path.parent.name
        override = overrides.get(campaign_id)
        try:
            observations, report_exclusions = _report_observations(
                report_path=report_path,
                speed=(override.speed if override and override.speed else default_speed),
                git_commit=(
                    override.git_commit
                    if override and override.git_commit
                    else default_git_commit
                ),
                host=override.host if override and override.host else default_host,
            )
        except (OSError, ValueError) as exc:
            exclusions.append(
                ImportExclusion(
                    report=_display_path(report_path),
                    fixture_id="*",
                    reason=f"report could not be imported: {exc}",
                )
            )
            continue
        accepted.extend(observations)
        exclusions.extend(report_exclusions)
    applied = append_performance_observations(ledger, accepted) if apply else 0
    return ReportImportPreview(
        generated_at=datetime.now().astimezone(),
        reports=[_display_path(path) for path in reports],
        accepted=accepted,
        exclusions=exclusions,
        applied_records=applied,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", action="append", type=Path, default=[])
    parser.add_argument("--reports-root", type=Path)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--overrides", type=Path, default=DEFAULT_OVERRIDES)
    parser.add_argument("--preview", type=Path, required=True)
    parser.add_argument("--speed", choices=[item.value for item in SpeedMode], default="unknown")
    parser.add_argument("--git-commit", default="unknown")
    default_host = f"{platform.system().lower()}-{platform.machine().lower()}"
    parser.add_argument("--host", default=default_host)
    parser.add_argument("--apply", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    reports = list(args.report)
    if args.reports_root:
        reports.extend(sorted(args.reports_root.glob("*/report.json")))
    reports = sorted(set(path.resolve() for path in reports))
    if not reports:
        print("No report.json files were selected.", file=sys.stderr)
        return 2
    missing = [path for path in reports if not path.is_file()]
    if missing:
        print(f"Report does not exist: {missing[0]}", file=sys.stderr)
        return 2
    try:
        preview = import_reports(
            reports=reports,
            ledger=args.ledger,
            overrides_path=args.overrides,
            default_speed=SpeedMode(args.speed),
            default_git_commit=args.git_commit,
            default_host=args.host,
            apply=args.apply,
        )
    except (OSError, ValueError) as exc:
        print(f"Performance import failed: {exc}", file=sys.stderr)
        return 1
    args.preview.parent.mkdir(parents=True, exist_ok=True)
    args.preview.write_text(
        preview.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"Reviewed {len(preview.reports)} report(s): "
        f"{len(preview.accepted)} accepted observation(s), "
        f"{len(preview.exclusions)} exclusion(s), "
        f"{preview.applied_records} newly applied."
    )
    print(args.preview)
    return 0


if __name__ == "__main__":
    sys.exit(main())
