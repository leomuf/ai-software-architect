# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Deterministic grading that never pretends to replace semantic review."""

from __future__ import annotations

from pathlib import PurePosixPath

from adapters.codex.evaluations.models import (
    AssertionStatus,
    DeterministicAssertion,
    VerificationPolicy,
)


def _architecture_artifact(path: str) -> bool:
    normalized = PurePosixPath(path.replace("\\", "/"))
    return bool(normalized.parts) and normalized.parts[0] == ".ai-architect"


def grade_phase(
    *,
    exit_code: int,
    final_response: str | None,
    event_types: set[str],
    repository_changes: list[str],
    policy: VerificationPolicy,
) -> list[DeterministicAssertion]:
    assertions = [
        DeterministicAssertion(
            name="codex-exit-success",
            status=AssertionStatus.PASS if exit_code == 0 else AssertionStatus.FAIL,
            evidence=f"Codex exited with code {exit_code}.",
        ),
        DeterministicAssertion(
            name="final-response-present",
            status=AssertionStatus.PASS if final_response else AssertionStatus.FAIL,
            evidence="A final agent response was captured."
            if final_response
            else "No final agent response was captured.",
        ),
    ]

    for marker in policy.forbidden_response_markers:
        exposed = marker in (final_response or "")
        assertions.append(
            DeterministicAssertion(
                name=f"response-marker-absent:{marker}",
                status=AssertionStatus.FAIL if exposed else AssertionStatus.PASS,
                evidence=f"Forbidden response marker {marker!r} "
                + ("was exposed." if exposed else "was not exposed."),
            )
        )

    for event_type in policy.forbidden_event_types:
        observed = event_type in event_types
        assertions.append(
            DeterministicAssertion(
                name=f"event-type-absent:{event_type}",
                status=AssertionStatus.FAIL if observed else AssertionStatus.PASS,
                evidence=f"Event type {event_type!r} "
                + ("was observed." if observed else "was not observed."),
            )
        )

    if policy.repository_changes == "forbid":
        invalid_changes = repository_changes
    elif policy.repository_changes == "architecture-artifacts-only":
        invalid_changes = [path for path in repository_changes if not _architecture_artifact(path)]
    else:
        invalid_changes = []
    assertions.append(
        DeterministicAssertion(
            name="repository-change-policy",
            status=AssertionStatus.FAIL if invalid_changes else AssertionStatus.PASS,
            evidence=(
                "Repository changes satisfy the configured policy."
                if not invalid_changes
                else "Disallowed repository changes: " + ", ".join(invalid_changes)
            ),
        )
    )
    return assertions
