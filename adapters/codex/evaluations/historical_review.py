# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Export and apply Codex-assisted reviews of historical Desktop evaluations."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from collections.abc import Iterator, Sequence
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import IO, Any

from pydantic import Field, field_validator, model_validator

from adapters.codex.evaluations.models import StrictModel
from adapters.codex.evaluations.performance_import import (
    DEFAULT_LEDGER,
    _fixture_path,
    _workload_fingerprint,
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

EXPLORATORY_TITLE = re.compile(
    r"(?ix)"
    r"(?:\brun[\s_-]*\d+[\s_-]*exploratory[\s_-]*\d+\b)"
    r"|(?:\bexploratory[\s_-]*\d+\b)"
)
RUN_NUMBER = re.compile(r"(?i)\brun[\s_-]*(\d+)")
EXPLORATORY_NUMBER = re.compile(r"(?i)\bexploratory[\s_-]*(\d+)")
PLUGIN_VERSION = re.compile(r"(?i)\((?:v)?([^)]*\d[^)]*)\)")
CAMPAIGN_GAP_SECONDS = 120

FIXTURE_TITLE_MARKERS = {
    "abstract factory": "abstract-factory-example",
    "compare design patterns": "architecture-option-comparison",
    "pattern comparison": "architecture-option-comparison",
    "avoid overengineering": "avoid-overengineering",
    "clarify ui architecture": "clarify-ui-architecture",
    "read-only architecture review": "read-only-architecture-review",
    "read-only review": "read-only-architecture-review",
    "read-only": "read-only-architecture-review",
}


class ReviewDecision(StrEnum):
    ACCEPTED = "accepted"
    EXCLUDED = "excluded"
    NEEDS_REVIEW = "needs-review"


class ReviewConfidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class HistoricalPhaseReview(StrictModel):
    source_task_id: str
    source_task_title: str
    source_turn_id: str
    campaign_id: str
    fixture_id: str
    fixture_revision: str = Field(pattern=r"^[a-f0-9]{64}$")
    workload_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    phase: str = Field(pattern=r"^(initial|continuation)$")
    started_at: datetime
    completed_at: datetime
    duration_seconds: float = Field(ge=0)
    decision: ReviewDecision
    reason: str = Field(min_length=1, max_length=2_000)
    confidence: ReviewConfidence
    evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence_excerpt: str | None = Field(default=None, max_length=500)
    model: str = Field(default="unknown", min_length=1)
    reasoning_effort: str = Field(default="unknown", min_length=1)
    speed: SpeedMode = SpeedMode.UNKNOWN
    plugin_version: str = Field(default="unknown", min_length=1)
    codex_version: str = Field(default="unknown", min_length=1)
    git_commit: str = Field(default="unknown", min_length=1)
    host: str = Field(default="windows-x86_64", min_length=1)
    canonical_record_id: str | None = Field(
        default=None,
        pattern=r"^[a-f0-9]{64}$",
    )

    @field_validator("started_at", "completed_at")
    @classmethod
    def timestamps_are_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("historical review timestamps must include a timezone")
        return value

    @model_validator(mode="after")
    def completion_follows_start(self) -> HistoricalPhaseReview:
        if self.completed_at < self.started_at:
            raise ValueError("completed_at must not precede started_at")
        return self


class HistoricalReviewBatch(StrictModel):
    schema_version: str = "1.0.0"
    reviewer_session_id: str = Field(min_length=1)
    reviewed_at: datetime
    phases: list[HistoricalPhaseReview]


class ExportedTurn(StrictModel):
    id: str
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float | None = Field(default=None, ge=0)
    user_text: str
    agent_text: str
    evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class ExportedTask(StrictModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    cwd: str
    codex_version: str
    campaign_hint: str | None = None
    exploratory_number_hint: int | None = None
    turns: list[ExportedTurn]


class HistoricalTaskExport(StrictModel):
    schema_version: str = "1.0.0"
    exported_at: datetime
    archived: bool
    tasks: list[ExportedTask]


def fixture_id_from_title(title: str) -> str | None:
    """Map historical human-readable task titles to stable fixture IDs."""

    normalized = title.casefold().replace("…", "")
    return next(
        (
            fixture_id
            for marker, fixture_id in FIXTURE_TITLE_MARKERS.items()
            if marker in normalized
        ),
        None,
    )


def _campaign_ids(tasks: list[ExportedTask]) -> dict[str, str]:
    """Group unnumbered legacy tasks by their observed launch timestamps."""

    result: dict[str, str] = {}
    legacy_number = 0
    previous_created_at: datetime | None = None
    for task in sorted(tasks, key=lambda item: item.created_at):
        run_match = RUN_NUMBER.search(task.title)
        if run_match:
            result[task.id] = f"Run{run_match.group(1)}"
            continue
        gap = (
            (task.created_at - previous_created_at).total_seconds()
            if previous_created_at
            else None
        )
        if gap is None or gap > CAMPAIGN_GAP_SECONDS:
            legacy_number += 1
        result[task.id] = f"Legacy-{legacy_number:02d}"
        previous_created_at = task.created_at
    return result


def build_historical_review_draft(
    exported: HistoricalTaskExport,
    *,
    reviewer_session_id: str,
    reviewed_at: datetime | None = None,
) -> HistoricalReviewBatch:
    """Create a reviewable draft without silently approving semantic evidence."""

    campaign_ids = _campaign_ids(exported.tasks)
    phases: list[HistoricalPhaseReview] = []
    for task in sorted(exported.tasks, key=lambda item: item.created_at):
        fixture_id = fixture_id_from_title(task.title)
        if fixture_id is None:
            continue
        fixture_path = _fixture_path(fixture_id)
        initial_user_text = task.turns[0].user_text if task.turns else task.title
        input_match = re.search(
            r"(?is)<input>(.*?)</input>",
            initial_user_text,
        )
        effective_prompt = (
            input_match.group(1).strip() if input_match else initial_user_text.strip()
        )
        fixture_revision = hashlib.sha256(
            json.dumps(
                {"fixture_id": fixture_id, "prompt": effective_prompt},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        workload_fingerprint = _workload_fingerprint(fixture_path)
        version_match = PLUGIN_VERSION.search(task.title)
        plugin_version = version_match.group(1) if version_match else "unknown"
        for index, turn in enumerate(task.turns):
            complete_evidence = (
                turn.status == "completed"
                and turn.started_at is not None
                and turn.completed_at is not None
                and turn.duration_seconds is not None
                and bool(turn.agent_text.strip())
            )
            started_at = turn.started_at or task.created_at
            completed_at = turn.completed_at or started_at
            phases.append(
                HistoricalPhaseReview(
                    source_task_id=task.id,
                    source_task_title=task.title,
                    source_turn_id=turn.id,
                    campaign_id=campaign_ids[task.id],
                    fixture_id=fixture_id,
                    fixture_revision=fixture_revision,
                    workload_fingerprint=workload_fingerprint,
                    phase="initial" if index == 0 else "continuation",
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_seconds=turn.duration_seconds or 0.0,
                    decision=(
                        ReviewDecision.NEEDS_REVIEW
                        if complete_evidence
                        else ReviewDecision.EXCLUDED
                    ),
                    reason=(
                        "Completed phase with timestamped response; semantic "
                        "fitness requires reviewer approval."
                        if complete_evidence
                        else "Excluded because the phase was interrupted or lacks "
                        "complete timestamped response evidence."
                    ),
                    confidence=(
                        ReviewConfidence.MEDIUM
                        if complete_evidence
                        else ReviewConfidence.HIGH
                    ),
                    evidence_sha256=turn.evidence_sha256,
                    evidence_excerpt=(turn.agent_text.strip()[:500] or None),
                    plugin_version=plugin_version,
                    codex_version=task.codex_version,
                )
            )
    return HistoricalReviewBatch(
        reviewer_session_id=reviewer_session_id,
        reviewed_at=reviewed_at or datetime.now(UTC),
        phases=phases,
    )


class CodexAppServer:
    """Minimal JSON-RPC client for the documented local Codex app-server."""

    def __init__(self, executable: Path):
        self.executable = executable
        self.process: subprocess.Popen[str] | None = None
        self._next_id = 1

    def __enter__(self) -> CodexAppServer:
        self.process = subprocess.Popen(  # noqa: S603
            [str(self.executable), "app-server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.request(
            "initialize",
            {
                "clientInfo": {
                    "name": "ai-software-architect-evaluation-history",
                    "title": "AI Software Architect Evaluation History",
                    "version": "0.1.0",
                }
            },
        )
        self.notify("initialized", {})
        return self

    def __exit__(self, *_: object) -> None:
        if self.process is None:
            return
        if self.process.stdin is not None:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            self.process.wait(timeout=5)

    def _streams(self) -> tuple[IO[str], IO[str]]:
        if (
            self.process is None
            or self.process.stdin is None
            or self.process.stdout is None
        ):
            raise RuntimeError("Codex app-server is not running")
        return self.process.stdin, self.process.stdout

    def notify(self, method: str, params: dict[str, Any]) -> None:
        stdin, _ = self._streams()
        stdin.write(json.dumps({"method": method, "params": params}) + "\n")
        stdin.flush()

    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        request_id = self._next_id
        self._next_id += 1
        stdin, stdout = self._streams()
        stdin.write(
            json.dumps({"method": method, "id": request_id, "params": params}) + "\n"
        )
        stdin.flush()
        while line := stdout.readline():
            message = json.loads(line)
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise RuntimeError(f"Codex app-server {method} failed: {message['error']}")
            result = message.get("result")
            if not isinstance(result, dict):
                raise RuntimeError(f"Codex app-server {method} returned no object result")
            return result
        raise RuntimeError(f"Codex app-server closed while waiting for {method}")

    def list_threads(self, *, archived: bool) -> Iterator[dict[str, Any]]:
        cursor: str | None = None
        source_kinds = [
            "cli",
            "vscode",
            "exec",
            "appServer",
            "subAgent",
            "subAgentReview",
            "subAgentCompact",
            "subAgentThreadSpawn",
            "subAgentOther",
            "unknown",
        ]
        while True:
            result = self.request(
                "thread/list",
                {
                    "archived": archived,
                    "cursor": cursor,
                    "limit": 100,
                    "sortKey": "created_at",
                    "sortDirection": "asc",
                    "sourceKinds": source_kinds,
                },
            )
            data = result.get("data", [])
            if not isinstance(data, list):
                raise RuntimeError("Codex app-server returned invalid thread list data")
            yield from (item for item in data if isinstance(item, dict))
            cursor_value = result.get("nextCursor")
            if not isinstance(cursor_value, str) or not cursor_value:
                return
            cursor = cursor_value

    def read_thread(self, thread_id: str) -> dict[str, Any]:
        result = self.request(
            "thread/read",
            {"threadId": thread_id, "includeTurns": True},
        )
        thread = result.get("thread")
        if not isinstance(thread, dict):
            raise RuntimeError(f"Codex app-server returned no thread for {thread_id}")
        return thread


def _timestamp(value: object) -> datetime | None:
    return datetime.fromtimestamp(value, UTC) if isinstance(value, int | float) else None


def _message_text(items: object, item_type: str) -> str:
    if not isinstance(items, list):
        return ""
    texts: list[str] = []
    for item in items:
        if not isinstance(item, dict) or item.get("type") != item_type:
            continue
        if item_type == "agentMessage" and isinstance(item.get("text"), str):
            texts.append(item["text"])
        if item_type == "userMessage" and isinstance(item.get("content"), list):
            texts.extend(
                content["text"]
                for content in item["content"]
                if isinstance(content, dict)
                and content.get("type") == "text"
                and isinstance(content.get("text"), str)
            )
    return "\n\n".join(texts).strip()


def _export_turn(raw: dict[str, Any]) -> ExportedTurn:
    user_text = _message_text(raw.get("items"), "userMessage")
    agent_text = _message_text(raw.get("items"), "agentMessage")
    evidence = json.dumps(
        {
            "id": raw.get("id"),
            "status": raw.get("status"),
            "startedAt": raw.get("startedAt"),
            "completedAt": raw.get("completedAt"),
            "durationMs": raw.get("durationMs"),
            "userText": user_text,
            "agentText": agent_text,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    duration_ms = raw.get("durationMs")
    return ExportedTurn(
        id=str(raw.get("id", "")),
        status=str(raw.get("status", "unknown")),
        started_at=_timestamp(raw.get("startedAt")),
        completed_at=_timestamp(raw.get("completedAt")),
        duration_seconds=(
            round(duration_ms / 1_000, 3) if isinstance(duration_ms, int | float) else None
        ),
        user_text=user_text,
        agent_text=agent_text,
        evidence_sha256=hashlib.sha256(evidence).hexdigest(),
    )


def export_historical_tasks(
    client: CodexAppServer,
    *,
    archived: bool,
    task_ids: set[str],
) -> HistoricalTaskExport:
    tasks: list[ExportedTask] = []
    for summary in client.list_threads(archived=archived):
        task_id = str(summary.get("id", ""))
        title = str(summary.get("name") or summary.get("preview") or "")
        if task_id not in task_ids and not EXPLORATORY_TITLE.search(title):
            continue
        raw = client.read_thread(task_id)
        created = _timestamp(raw.get("createdAt"))
        updated = _timestamp(raw.get("updatedAt"))
        if created is None or updated is None:
            continue
        run_match = RUN_NUMBER.search(title)
        exploratory_match = EXPLORATORY_NUMBER.search(title)
        tasks.append(
            ExportedTask(
                id=task_id,
                title=title,
                created_at=created,
                updated_at=updated,
                cwd=str(raw.get("cwd", "")),
                codex_version=str(raw.get("cliVersion", "unknown")),
                campaign_hint=(f"Run{run_match.group(1)}" if run_match else None),
                exploratory_number_hint=(
                    int(exploratory_match.group(1)) if exploratory_match else None
                ),
                turns=[
                    _export_turn(turn)
                    for turn in raw.get("turns", [])
                    if isinstance(turn, dict)
                ],
            )
        )
    return HistoricalTaskExport(
        exported_at=datetime.now(UTC),
        archived=archived,
        tasks=tasks,
    )


def historical_observations(
    batch: HistoricalReviewBatch,
) -> list[PerformanceObservation]:
    accepted = [
        phase for phase in batch.phases if phase.decision == ReviewDecision.ACCEPTED
    ]
    grouped: dict[tuple[str, str, str], list[HistoricalPhaseReview]] = defaultdict(list)
    for phase in accepted:
        grouped[(phase.campaign_id, phase.source_task_id, phase.fixture_id)].append(phase)

    campaign_ranges: dict[str, tuple[datetime, datetime]] = {}
    for phase in accepted:
        current = campaign_ranges.get(phase.campaign_id)
        if current is None:
            campaign_ranges[phase.campaign_id] = (phase.started_at, phase.completed_at)
        else:
            campaign_ranges[phase.campaign_id] = (
                min(current[0], phase.started_at),
                max(current[1], phase.completed_at),
            )

    observations: list[PerformanceObservation] = []
    for (campaign_id, task_id, fixture_id), phases_for_task in sorted(grouped.items()):
        initial = next((item for item in phases_for_task if item.phase == "initial"), None)
        if initial is None:
            continue
        continuations = [
            item for item in phases_for_task if item.phase == "continuation"
        ]
        campaign_start, campaign_end = campaign_ranges[campaign_id]
        phase_measurements = PhaseMeasurements(
            initial=PhaseMeasurement(
                status=PhaseStatus.COMPLETED,
                duration_seconds=initial.duration_seconds,
            ),
            continuation=(
                PhaseMeasurement(
                    status=PhaseStatus.COMPLETED,
                    duration_seconds=round(
                        sum(item.duration_seconds for item in continuations),
                        3,
                    ),
                )
                if continuations
                else PhaseMeasurement(status=PhaseStatus.NOT_RUN)
            ),
        )
        measured = initial.duration_seconds + (
            sum(item.duration_seconds for item in continuations)
        )
        observations.append(
            build_performance_observation(
                campaign=CampaignMetadata(
                    id=campaign_id,
                    execution_mode=ExecutionMode.PARALLEL_CODEX_TASKS,
                    started_at=campaign_start,
                    completed_at=campaign_end,
                    wall_clock_seconds=round(
                        (campaign_end - campaign_start).total_seconds(),
                        3,
                    ),
                ),
                test=TestMetadata(
                    fixture_id=fixture_id,
                    fixture_revision=initial.fixture_revision,
                    workload_fingerprint=initial.workload_fingerprint,
                    task_name=initial.source_task_title,
                    task_id=task_id,
                ),
                runtime=RuntimeMetadata(
                    model=initial.model,
                    reasoning_effort=initial.reasoning_effort,
                    speed=initial.speed,
                    codex_version=initial.codex_version,
                    plugin_version=initial.plugin_version,
                    plugin_provenance=None,
                    git_commit=initial.git_commit,
                    host=initial.host,
                ),
                phases=phase_measurements,
                timing=TimingMetadata(measured_phase_seconds=round(measured, 3)),
                result=ResultMetadata(
                    outcome=EvaluationOutcome.MANUAL_REVIEW,
                    source=ObservationSource.CODEX_TASK_HISTORY,
                    measurement_quality=MeasurementQuality.RECONSTRUCTED,
                    notes=(
                        "Accepted through Codex-assisted review batch "
                        f"{batch.reviewer_session_id}."
                    ),
                ),
            )
        )
    return observations


def apply_historical_review(
    batch: HistoricalReviewBatch,
    ledger: Path,
) -> int:
    return append_performance_observations(ledger, historical_observations(batch))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    export = subparsers.add_parser("export")
    export.add_argument("--codex-command", type=Path, required=True)
    export.add_argument("--output", type=Path, required=True)
    export.add_argument("--task-id", action="append", default=[])
    export.add_argument("--active", action="store_true")
    draft = subparsers.add_parser("draft")
    draft.add_argument("--export", type=Path, required=True)
    draft.add_argument("--output", type=Path, required=True)
    draft.add_argument("--reviewer-session-id", required=True)
    apply = subparsers.add_parser("apply")
    apply.add_argument("--review", type=Path, required=True)
    apply.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "export":
            with CodexAppServer(args.codex_command) as client:
                exported = export_historical_tasks(
                    client,
                    archived=not args.active,
                    task_ids=set(args.task_id),
                )
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                exported.model_dump_json(indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            print(f"Exported {len(exported.tasks)} candidate task(s).")
            print(args.output)
            return 0
        if args.command == "draft":
            exported = HistoricalTaskExport.model_validate_json(
                args.export.read_text(encoding="utf-8")
            )
            draft = build_historical_review_draft(
                exported,
                reviewer_session_id=args.reviewer_session_id,
            )
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                draft.model_dump_json(indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            print(f"Drafted {len(draft.phases)} phase review(s).")
            print(args.output)
            return 0
        batch = HistoricalReviewBatch.model_validate_json(
            args.review.read_text(encoding="utf-8")
        )
        appended = apply_historical_review(batch, args.ledger)
        print(f"Applied {appended} new historical observation(s).")
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Historical evaluation review failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
