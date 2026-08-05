# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Run shared exploratory fixtures through non-interactive Codex."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import threading
import time
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import yaml

from adapters.codex.evaluations.decision_observation import extract_decision_observation
from adapters.codex.evaluations.grading import grade_phase
from adapters.codex.evaluations.models import (
    AssertionStatus,
    CampaignReport,
    DecisionObservation,
    DeterministicAssertion,
    EvaluationFixture,
    EvaluationStatus,
    ExpectedDecision,
    FixtureResult,
    PhaseResult,
    PhaseTelemetry,
    ToolTimelineEvent,
    VerificationPolicy,
    load_fixture,
)
from adapters.codex.evaluations.performance_import import _report_observations
from adapters.codex.evaluations.performance_ledger import append_performance_observations
from adapters.codex.evaluations.performance_models import ObservationSource, SpeedMode

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MANIFEST = ROOT / "shared" / "evaluations" / "verification-manifest.yaml"
DEFAULT_PERFORMANCE_LEDGER = ROOT / "evaluation-data" / "exploratory-runs.jsonl"
INTERNAL_MARKER = "<!-- ai-architect-"
PLUGIN_NAME = "ai-software-architect"


@dataclass(frozen=True)
class InstalledPluginIdentity:
    plugin_id: str
    marketplace: str
    version: str
    provenance_sha256: str | None = None


@dataclass(frozen=True)
class _ProcessCapture:
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float
    stdout_lines: list[tuple[float, str]]


def _capture_process(
    command: list[str],
    *,
    workspace: Path,
    timeout_seconds: int,
) -> _ProcessCapture:
    """Capture Codex output while preserving runner-observed JSONL arrival times."""

    started = time.monotonic()
    process = subprocess.Popen(  # noqa: S603
        command,
        cwd=workspace,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if process.stdout is None or process.stderr is None:
        process.kill()
        raise OSError("Codex process streams were unavailable.")

    stdout_lines: list[tuple[float, str]] = []
    stderr_lines: list[str] = []

    def read_stdout() -> None:
        assert process.stdout is not None
        for line in process.stdout:
            stdout_lines.append((time.monotonic() - started, line))

    def read_stderr() -> None:
        assert process.stderr is not None
        stderr_lines.extend(process.stderr)

    stdout_thread = threading.Thread(target=read_stdout, daemon=True)
    stderr_thread = threading.Thread(target=read_stderr, daemon=True)
    stdout_thread.start()
    stderr_thread.start()
    try:
        returncode = process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        stdout_thread.join()
        stderr_thread.join()
        raise
    stdout_thread.join()
    stderr_thread.join()
    duration = time.monotonic() - started
    return _ProcessCapture(
        returncode=returncode,
        stdout="".join(line for _, line in stdout_lines),
        stderr="".join(stderr_lines),
        duration_seconds=duration,
        stdout_lines=stdout_lines,
    )


def _phase_telemetry(stdout_lines: Sequence[tuple[float, str]]) -> PhaseTelemetry:
    """Extract only telemetry explicitly exposed by Codex JSONL."""

    first_event: float | None = None
    agent_message_times: list[float] = []
    item_counts: dict[str, int] = {}
    started_tools: dict[str, tuple[float, str]] = {}
    tool_events: list[ToolTimelineEvent] = []
    previous_completion: float | None = None
    usage: dict[str, Any] | None = None
    for observed_seconds, line in stdout_lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        if first_event is None:
            first_event = observed_seconds
        candidate_usage = event.get("usage")
        if isinstance(candidate_usage, dict):
            usage = candidate_usage
        item = event.get("item")
        event_type = event.get("type")
        if not isinstance(item, dict):
            continue
        item_type = str(item.get("type", "unknown"))
        item_id = item.get("id")
        is_tool = (
            item_type in {"command_execution", "file_change", "mcp_tool_call"}
            or item_type.endswith("_tool_call")
        )
        if (
            event_type == "item.started"
            and is_tool
            and isinstance(item_id, str)
        ):
            started_tools[item_id] = (observed_seconds, item_type)
            continue
        if event_type != "item.completed":
            continue
        item_counts[item_type] = item_counts.get(item_type, 0) + 1
        if item_type == "agent_message":
            agent_message_times.append(observed_seconds)
        if is_tool and isinstance(item_id, str) and item_id in started_tools:
            started_seconds, started_type = started_tools.pop(item_id)
            duration = max(0.0, observed_seconds - started_seconds)
            gap = (
                None
                if previous_completion is None
                else max(0.0, started_seconds - previous_completion)
            )
            tool_events.append(
                ToolTimelineEvent(
                    ordinal=len(tool_events) + 1,
                    tool_type=started_type,
                    started_seconds=round(started_seconds, 3),
                    completed_seconds=round(observed_seconds, 3),
                    duration_seconds=round(duration, 3),
                    gap_from_previous_tool_seconds=(
                        round(gap, 3) if gap is not None else None
                    ),
                    status=str(item.get("status", "unknown")),
                )
            )
            previous_completion = observed_seconds

    tool_call_count = sum(
        count
        for item_type, count in item_counts.items()
        if item_type in {"command_execution", "file_change", "mcp_tool_call"}
        or item_type.endswith("_tool_call")
    )

    def token_value(name: str) -> int | None:
        value = usage.get(name) if usage is not None else None
        return value if isinstance(value, int) and value >= 0 else None

    unavailable = [
        "time_to_first_token_seconds",
        "user_prompt_submit_hook_seconds",
        "pre_tool_use_hook_seconds",
        "post_tool_use_hook_seconds",
        "stop_hook_seconds",
        "stop_hook_correction_count",
        "template_loading_seconds",
        "patch_creation_seconds",
        "durable_write_seconds",
        "subagent_duration_seconds",
    ]
    if usage is None:
        unavailable.append("token_usage")
    return PhaseTelemetry(
        first_event_seconds=round(first_event, 3) if first_event is not None else None,
        first_agent_message_seconds=(
            round(agent_message_times[0], 3) if agent_message_times else None
        ),
        last_agent_message_seconds=(
            round(agent_message_times[-1], 3) if agent_message_times else None
        ),
        agent_message_count=len(agent_message_times),
        tool_call_count=tool_call_count,
        item_counts=dict(sorted(item_counts.items())),
        input_tokens=token_value("input_tokens"),
        cached_input_tokens=token_value("cached_input_tokens"),
        output_tokens=token_value("output_tokens"),
        tool_events=tool_events,
        unavailable_metrics=unavailable,
    )


def _snapshot(root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.relative_to(root).parts:
            continue
        relative = path.relative_to(root).as_posix()
        snapshot[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snapshot


def _changes(before: dict[str, str], after: dict[str, str]) -> list[str]:
    return sorted(
        path
        for path in before.keys() | after.keys()
        if before.get(path) != after.get(path)
    )


def _prepare_workspace(fixture: EvaluationFixture, workspace: Path) -> None:
    workspace.mkdir(parents=True, exist_ok=False)
    for relative, content in fixture.repository.items():
        destination = workspace / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8", newline="\n")
    if not fixture.repository:
        (workspace / "README.md").write_text(
            f"# Isolated evaluation workspace: {fixture.id}\n",
            encoding="utf-8",
            newline="\n",
        )
    git = shutil.which("git")
    if git is None:
        raise OSError("Git was not found in PATH.")
    subprocess.run(  # noqa: S603
        [git, "init", "--quiet"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    )


def _parse_events(stdout: str) -> tuple[list[dict[str, Any]], set[str], str | None, str | None]:
    events: list[dict[str, Any]] = []
    event_types: set[str] = set()
    thread_id: str | None = None
    final_response: str | None = None
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            event_types.add("invalid-jsonl")
            continue
        if not isinstance(event, dict):
            event_types.add("invalid-jsonl")
            continue
        events.append(event)
        event_type = str(event.get("type", "unknown"))
        event_types.add(event_type)
        if event_type == "thread.started" and isinstance(event.get("thread_id"), str):
            thread_id = event["thread_id"]
        item = event.get("item")
        if isinstance(item, dict):
            item_type = str(item.get("type", "unknown"))
            event_types.add(item_type)
            if event_type == "item.completed" and item_type == "agent_message":
                text = item.get("text")
                if isinstance(text, str):
                    final_response = text
    return events, event_types, thread_id, final_response


def _codex_command(
    *,
    executable: str,
    model: str,
    reasoning_effort: str,
    prompt: str,
    sandbox: str,
    ephemeral: bool,
    speed: str = "standard",
    resume_thread: str | None = None,
) -> list[str]:
    command = [
        executable,
        "exec",
        "--json",
        "--sandbox",
        sandbox,
        "--model",
        model,
        "--config",
        f'model_reasoning_effort="{reasoning_effort}"',
    ]
    if speed == "fast":
        command.extend(["--config", 'service_tier="fast"'])
    if ephemeral:
        command.append("--ephemeral")
    if resume_thread:
        command.extend(["resume", resume_thread])
    command.append(prompt)
    return command


def _run_phase(
    *,
    name: Literal["initial", "continuation"],
    command: list[str],
    workspace: Path,
    evidence: Path,
    policy: VerificationPolicy,
    expected: list[str],
    forbidden_actions: list[str],
    timeout_seconds: int,
    observe_decision: bool = False,
    expected_decision: ExpectedDecision | None = None,
) -> PhaseResult:
    before = _snapshot(workspace)
    completed = _capture_process(
        command,
        workspace=workspace,
        timeout_seconds=timeout_seconds,
    )
    _, event_types, thread_id, final_response = _parse_events(completed.stdout)
    changed = _changes(before, _snapshot(workspace))

    evidence.mkdir(parents=True, exist_ok=True)
    event_file = evidence / f"{name}.jsonl"
    event_file.write_text(completed.stdout, encoding="utf-8", newline="\n")
    stderr_file = evidence / f"{name}.stderr.txt"
    stderr_file.write_text(completed.stderr, encoding="utf-8", newline="\n")
    response_file: Path | None = None
    if final_response is not None:
        response_file = evidence / f"{name}.response.md"
        response_file.write_text(final_response + "\n", encoding="utf-8", newline="\n")

    assertions = grade_phase(
        exit_code=completed.returncode,
        final_response=final_response,
        event_types=event_types,
        repository_changes=changed,
        policy=policy,
    )
    decision_observation: DecisionObservation | None = None
    if observe_decision:
        try:
            decision_observation = extract_decision_observation(final_response or "")
        except ValueError as exc:
            assertions.append(
                DeterministicAssertion(
                    name="decision-observation-captured",
                    status=AssertionStatus.FAIL,
                    evidence=f"Validated comparison outcome was unavailable: {exc}",
                )
            )
        else:
            assertions.append(
                DeterministicAssertion(
                    name="decision-observation-captured",
                    status=AssertionStatus.PASS,
                    evidence=(
                        "Captured a normalized public selection and a private "
                        "material-assumption fingerprint."
                    ),
                )
            )
            if expected_decision is not None:
                assertions.append(
                    _expected_decision_assertion(decision_observation, expected_decision)
                )
    return PhaseResult(
        name=name,
        exit_code=completed.returncode,
        duration_seconds=round(completed.duration_seconds, 3),
        thread_id=thread_id,
        final_response_file=response_file.name if response_file else None,
        event_log_file=event_file.name,
        stderr_file=stderr_file.name,
        event_types=sorted(event_types),
        repository_changes=changed,
        assertions=assertions,
        manual_review=[
            *(f"expected:{item}" for item in expected),
            *(f"forbidden:{item}" for item in forbidden_actions),
        ],
        telemetry=_phase_telemetry(completed.stdout_lines),
        decision_observation=decision_observation,
    )


def _expected_decision_assertion(
    observation: DecisionObservation,
    expected: ExpectedDecision,
) -> DeterministicAssertion:
    selection_matches = (
        observation.selected_category == expected.selected_category
        and observation.selected_name == expected.selected_name
    )
    return DeterministicAssertion(
        name="expected-decision-selected",
        status=AssertionStatus.PASS if selection_matches else AssertionStatus.FAIL,
        evidence=(
            "Selected the fixture's expected public decision identity."
            if selection_matches
            else (
                f"Expected {expected.selected_category}/{expected.selected_name}, "
                f"observed {observation.selected_category}/{observation.selected_name}."
            )
        ),
    )


def _continuation_sandbox(policy: VerificationPolicy) -> str:
    """Grant write access only when the fixture expects repository changes."""

    return "read-only" if policy.repository_changes == "forbid" else "workspace-write"


def _fixture_status(phases: list[PhaseResult]) -> EvaluationStatus:
    if any(phase.exit_code != 0 or "invalid-jsonl" in phase.event_types for phase in phases):
        return EvaluationStatus.INFRASTRUCTURE_ERROR
    if any(
        assertion.status == AssertionStatus.FAIL
        for phase in phases
        for assertion in phase.assertions
    ):
        return EvaluationStatus.DETERMINISTIC_FAILURE
    return EvaluationStatus.MANUAL_REVIEW


def _codex_version(executable: str) -> str:
    completed = subprocess.run(  # noqa: S603
        [executable, "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"exit code {completed.returncode}"
        raise OSError(f"Unable to execute Codex CLI: {detail}")
    return completed.stdout.strip()


def _git_commit() -> str:
    git = shutil.which("git")
    if git is None:
        return "unknown"
    completed = subprocess.run(  # noqa: S603
        [git, "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unknown"


def _provenance_digest(plugin: dict[str, Any]) -> str | None:
    source = plugin.get("source")
    source_path = source.get("path") if isinstance(source, dict) else None
    if not isinstance(source_path, str) or not source_path.strip():
        return None
    root = Path(source_path).expanduser()
    if not root.is_absolute():
        return None
    provenance_path = root / "provenance.json"
    manifest_path = root / ".codex-plugin" / "plugin.json"
    try:
        provenance_bytes = provenance_path.read_bytes()
        provenance = json.loads(provenance_bytes)
        manifest = json.loads(manifest_path.read_text("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(
            "The enabled AI Software Architect source could not be provenance-verified."
        ) from exc
    version = plugin.get("version")
    if (
        provenance.get("plugin_version") != version
        or manifest.get("version") != version
        or manifest.get("name") != PLUGIN_NAME
    ):
        raise ValueError(
            "The enabled AI Software Architect manifest, provenance, and Codex version disagree."
        )
    return hashlib.sha256(provenance_bytes).hexdigest()


def _installed_plugin_identity(executable: str) -> InstalledPluginIdentity:
    completed = subprocess.run(  # noqa: S603
        [executable, "plugin", "list", "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"exit code {completed.returncode}"
        raise OSError(f"Unable to inspect installed Codex plugins: {detail}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("Codex returned an invalid JSON plugin list.") from exc

    installed = payload.get("installed")
    if not isinstance(installed, list):
        raise ValueError("Codex plugin list did not contain an installed-plugin collection.")
    matches = [
        plugin
        for plugin in installed
        if isinstance(plugin, dict)
        and (
            plugin.get("name") == PLUGIN_NAME
            or str(plugin.get("pluginId", "")).partition("@")[0] == PLUGIN_NAME
        )
        and plugin.get("installed") is True
        and plugin.get("enabled") is True
    ]
    if len(matches) != 1:
        raise ValueError(
            "Expected exactly one installed and enabled AI Software Architect across "
            f"all marketplaces; found {len(matches)}. Disable or uninstall duplicates "
            "before spending evaluation credits."
        )
    plugin = matches[0]
    plugin_id = plugin.get("pluginId")
    if not isinstance(plugin_id, str) or not plugin_id.startswith(f"{PLUGIN_NAME}@"):
        raise ValueError("Codex did not report an unambiguous AI Software Architect plugin ID.")
    marketplace = plugin_id.partition("@")[2]
    version = plugin.get("version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError(f"Codex did not report a version for {plugin_id}.")
    return InstalledPluginIdentity(
        plugin_id=plugin_id,
        marketplace=marketplace,
        version=version.strip(),
        provenance_sha256=_provenance_digest(plugin),
    )


def _load_campaign(
    manifest: Path,
    selected: set[str],
    campaign: str = "default",
) -> list[tuple[Path, EvaluationFixture]]:
    raw = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    if campaign == "default":
        configured = raw.get("exploratory_campaign", [])
    else:
        configured = raw.get("additional_exploratory_campaigns", {}).get(campaign)
        if configured is None:
            available = sorted(raw.get("additional_exploratory_campaigns", {}))
            raise ValueError(
                f"Unknown exploratory campaign: {campaign}. Available: "
                + ", ".join(["default", *available])
            )
    fixtures: list[tuple[Path, EvaluationFixture]] = []
    for raw_path in configured:
        path = ROOT / str(raw_path)
        fixture = load_fixture(path)
        if not selected or fixture.id in selected:
            fixtures.append((path, fixture))
    missing = selected - {fixture.id for _, fixture in fixtures}
    if missing:
        raise ValueError("Unknown fixture identifiers: " + ", ".join(sorted(missing)))
    return fixtures


def _summary(report: CampaignReport) -> str:
    lines = [
        "# Codex Exploratory Evaluation Summary",
        "",
        f"- Model: `{report.model}`",
        f"- Reasoning effort: `{report.reasoning_effort}`",
        f"- Speed: `{report.speed}`",
        f"- Codex CLI: `{report.codex_version}`",
        f"- Installed plugin: `{report.installed_plugin_id or 'not-checked (dry run)'}`",
        f"- Installed marketplace: `{report.installed_plugin_marketplace or 'not-checked'}`",
        "- Installed plugin version: "
        f"`{report.installed_plugin_version or 'not-checked (dry run)'}`",
        "- Installed provenance SHA-256: "
        f"`{report.installed_plugin_provenance_sha256 or 'not-reported'}`",
        f"- Expected plugin version: `{report.expected_plugin_version or 'not-specified'}`",
        f"- Started: `{report.started_at.isoformat()}`",
        "- Campaign wall-clock duration: "
        f"`{report.campaign_wall_clock_seconds or 0.0:.3f}s`",
        "",
        "| Fixture | Scenario | Status | Phases |",
        "|---|---|---|---:|",
    ]
    for result in report.results:
        lines.append(
            f"| `{result.fixture_id}` | `{result.scenario}` | "
            f"{result.status.value} | {len(result.phases)} |"
        )
    decision_phases = [
        (result.fixture_id, phase)
        for result in report.results
        for phase in result.phases
        if phase.decision_observation is not None
    ]
    if decision_phases:
        lines.extend(
            [
                "",
                "## Privacy-preserving decision observations",
                "",
                "Free-form assumptions are not retained; only their normalized "
                "SHA-256 fingerprints are reported. Response content is not retained; "
                "only its visible word count is reported.",
                "",
                "| Fixture | Phase | Selected category | Selected name | "
                "Assumption fingerprint | Assumption words | Visible response words |",
                "|---|---|---|---|---|---:|---:|",
            ]
        )
        for fixture_id, phase in decision_phases:
            observation = phase.decision_observation
            assert observation is not None
            lines.append(
                f"| `{fixture_id}` | {phase.name} | "
                f"{observation.selected_category} | {observation.selected_name} | "
                f"`{observation.material_assumption_sha256[:12]}` | "
                f"{observation.material_assumption_word_count} | "
                f"{observation.visible_response_word_count or '—'} |"
            )
    telemetry_phases = [
        (result.fixture_id, phase)
        for result in report.results
        for phase in result.phases
        if phase.telemetry is not None
    ]
    if telemetry_phases:
        lines.extend(
            [
                "",
                "## Runner-observed telemetry",
                "",
                "| Fixture | Phase | Duration (s) | First event (s) | "
                "First agent message (s) | Last agent message (s) | "
                "Messages | Tool calls | Input tokens | Cached input | Output tokens |",
                "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for fixture_id, phase in telemetry_phases:
            telemetry = phase.telemetry
            assert telemetry is not None

            def value(raw: float | int | None) -> str:
                return "—" if raw is None else str(raw)

            lines.append(
                f"| `{fixture_id}` | {phase.name} | {phase.duration_seconds:.3f} | "
                f"{value(telemetry.first_event_seconds)} | "
                f"{value(telemetry.first_agent_message_seconds)} | "
                f"{value(telemetry.last_agent_message_seconds)} | "
                f"{telemetry.agent_message_count} | {telemetry.tool_call_count} | "
                f"{value(telemetry.input_tokens)} | "
                f"{value(telemetry.cached_input_tokens)} | "
                f"{value(telemetry.output_tokens)} |"
            )
    lines.extend(
        [
            "",
            "`manual-review` means deterministic safeguards passed; a human must still review",
            "the fixture's semantic expected and forbidden behaviors before approving the release.",
            "",
        ]
    )
    return "\n".join(lines)


def run_campaign(args: argparse.Namespace) -> CampaignReport:
    started = datetime.now(UTC)
    campaign_started = time.monotonic()
    selected = set(args.fixture or [])
    fixtures = _load_campaign(args.manifest, selected, args.campaign)
    if args.dry_run:
        codex_version = "not-checked (dry run)"
        installed_plugin = None
    else:
        codex_version = _codex_version(args.codex_command)
        installed_plugin = _installed_plugin_identity(args.codex_command)
        if (
            args.expected_plugin_version is not None
            and installed_plugin.version != args.expected_plugin_version
        ):
            raise ValueError(
                f"Expected AI Software Architect {args.expected_plugin_version}, but Codex has "
                f"{installed_plugin.version} installed and enabled. Install the intended release "
                "candidate before running the evaluations."
            )
    args.output_directory.mkdir(parents=True, exist_ok=False)
    results: list[FixtureResult] = []
    fixture_count = len(fixtures)

    print(f"Loaded {fixture_count} exploratory fixture(s).", flush=True)
    if installed_plugin is not None:
        print(
            f"Installed plugin: {installed_plugin.plugin_id} "
            f"({installed_plugin.version}).",
            flush=True,
        )

    for fixture_index, (_, fixture) in enumerate(fixtures, start=1):
        progress = f"[{fixture_index}/{fixture_count}] {fixture.id} ({fixture.scenario})"
        workspace = args.output_directory / "workspaces" / fixture.id
        evidence = args.output_directory / "evidence" / fixture.id
        if args.dry_run:
            print(f"{progress}: planned (dry run).", flush=True)
            results.append(
                FixtureResult(
                    fixture_id=fixture.id,
                    scenario=fixture.scenario,
                    status=EvaluationStatus.PLANNED,
                    workspace=str(workspace),
                    phases=[],
                )
            )
            continue
        try:
            _prepare_workspace(fixture, workspace)
            initial_prompt = f"{fixture.activation.skill_invocation} {fixture.prompt}"
            print(f"{progress}: running initial phase...", flush=True)
            initial = _run_phase(
                name="initial",
                command=_codex_command(
                    executable=args.codex_command,
                    model=args.model,
                    reasoning_effort=args.reasoning_effort,
                    prompt=initial_prompt,
                    sandbox="read-only",
                    ephemeral=fixture.continuation is None,
                    speed=args.speed,
                ),
                workspace=workspace,
                evidence=evidence,
                policy=fixture.verification,
                expected=fixture.expected,
                forbidden_actions=fixture.forbidden_actions,
                timeout_seconds=args.timeout_seconds,
                observe_decision=fixture.observe_decision,
                expected_decision=fixture.expected_decision,
            )
            print(
                f"{progress}: initial phase finished in "
                f"{initial.duration_seconds:.1f}s (exit {initial.exit_code}).",
                flush=True,
            )
            phases = [initial]
            if fixture.continuation is not None and initial.thread_id and initial.exit_code == 0:
                continuation = fixture.continuation
                continuation_sandbox = _continuation_sandbox(continuation.verification)
                print(f"{progress}: running continuation...", flush=True)
                continuation_result = _run_phase(
                    name="continuation",
                    command=_codex_command(
                        executable=args.codex_command,
                        model=args.model,
                        reasoning_effort=args.reasoning_effort,
                        prompt=continuation.prompt,
                        sandbox=continuation_sandbox,
                        ephemeral=False,
                        speed=args.speed,
                        resume_thread=initial.thread_id,
                    ),
                    workspace=workspace,
                    evidence=evidence,
                    policy=continuation.verification,
                    expected=continuation.expected,
                    forbidden_actions=continuation.forbidden_actions,
                    timeout_seconds=args.timeout_seconds,
                )
                phases.append(continuation_result)
                print(
                    f"{progress}: continuation finished in "
                    f"{continuation_result.duration_seconds:.1f}s "
                    f"(exit {continuation_result.exit_code}).",
                    flush=True,
                )
            missing_continuation = fixture.continuation is not None and not initial.thread_id
            status = (
                EvaluationStatus.INFRASTRUCTURE_ERROR
                if missing_continuation
                else _fixture_status(phases)
            )
            results.append(
                FixtureResult(
                    fixture_id=fixture.id,
                    scenario=fixture.scenario,
                    status=status,
                    workspace=str(workspace),
                    phases=phases,
                    error=(
                        "Continuation could not run because the initial phase "
                        "returned no thread ID."
                        if missing_continuation
                        else None
                    ),
                )
            )
            print(f"{progress}: {status.value}.", flush=True)
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            results.append(
                FixtureResult(
                    fixture_id=fixture.id,
                    scenario=fixture.scenario,
                    status=EvaluationStatus.INFRASTRUCTURE_ERROR,
                    workspace=str(workspace),
                    phases=[],
                    error=str(exc),
                )
            )
            print(f"{progress}: infrastructure-error: {exc}", file=sys.stderr, flush=True)
            if not args.continue_on_failure:
                break

    completed_at = datetime.now(UTC)
    elapsed = time.monotonic() - campaign_started
    git_commit = _git_commit()
    report = CampaignReport(
        started_at=started,
        completed_at=completed_at,
        codex_command=args.codex_command,
        codex_version=codex_version,
        installed_plugin_id=(installed_plugin.plugin_id if installed_plugin else None),
        installed_plugin_marketplace=(
            installed_plugin.marketplace if installed_plugin else None
        ),
        installed_plugin_version=(installed_plugin.version if installed_plugin else None),
        installed_plugin_provenance_sha256=(
            installed_plugin.provenance_sha256 if installed_plugin else None
        ),
        expected_plugin_version=args.expected_plugin_version,
        model=args.model,
        reasoning_effort=args.reasoning_effort,
        speed=args.speed,
        campaign_wall_clock_seconds=round(elapsed, 3),
        git_commit=git_commit,
        results=results,
    )
    report_path = args.output_directory / "report.json"
    report_path.write_text(
        report.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    (args.output_directory / "SUMMARY.md").write_text(
        _summary(report), encoding="utf-8", newline="\n"
    )
    if not args.dry_run:
        observations, exclusions = _report_observations(
            report_path=report_path,
            speed=SpeedMode(args.speed),
            git_commit=git_commit,
            host=f"{platform.system().lower()}-{platform.machine().lower()}",
            source=ObservationSource.CODEX_CLI_RUNNER,
        )
        appended = append_performance_observations(args.performance_ledger, observations)
        print(
            f"Performance history: {appended} new observation(s), "
            f"{len(exclusions)} exclusion(s).",
            flush=True,
        )
    print(f"Campaign finished in {elapsed:.1f}s.", flush=True)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--campaign",
        default="default",
        help="Named exploratory campaign from the verification manifest.",
    )
    parser.add_argument("--fixture", action="append", help="Run one fixture ID; repeat as needed")
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--codex-command", default="codex")
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument(
        "--speed",
        choices=("standard", "fast", "unknown"),
        default="standard",
    )
    parser.add_argument(
        "--performance-ledger",
        type=Path,
        default=DEFAULT_PERFORMANCE_LEDGER,
    )
    parser.add_argument(
        "--expected-plugin-version",
        "--plugin-version",
        dest="expected_plugin_version",
        help="Fail before evaluation if the one enabled plugin has another version.",
    )
    parser.add_argument(
        "--reasoning-effort",
        choices=("low", "medium", "high", "xhigh"),
        default="medium",
    )
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--continue-on-failure", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.timeout_seconds < 1:
        raise SystemExit("--timeout-seconds must be positive")
    try:
        report = run_campaign(args)
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        print(f"Evaluation runner error: {exc}", file=sys.stderr)
        return 2
    print(args.output_directory / "SUMMARY.md")
    failing = {
        EvaluationStatus.DETERMINISTIC_FAILURE,
        EvaluationStatus.INFRASTRUCTURE_ERROR,
    }
    return 1 if any(result.status in failing for result in report.results) else 0


if __name__ == "__main__":
    sys.exit(main())
