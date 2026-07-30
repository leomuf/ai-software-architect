# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Atomic, idempotent JSONL storage for performance observations."""

from __future__ import annotations

import os
import time
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile

from adapters.codex.evaluations.performance_models import PerformanceObservation


class LedgerConflictError(ValueError):
    """Raised when one record ID maps to different canonical content."""


class LedgerLockTimeoutError(TimeoutError):
    """Raised when another process keeps the ledger lock beyond the timeout."""


def load_performance_ledger(path: Path) -> list[PerformanceObservation]:
    if not path.exists():
        return []
    records: list[PerformanceObservation] = []
    seen: dict[str, PerformanceObservation] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            record = PerformanceObservation.model_validate_json(line)
        except ValueError as exc:
            raise ValueError(f"Invalid performance ledger line {line_number}: {exc}") from exc
        previous = seen.get(record.record_id)
        if previous is not None:
            if previous != record:
                raise LedgerConflictError(
                    f"Conflicting performance record ID on line {line_number}: "
                    f"{record.record_id}"
                )
            raise ValueError(
                f"Duplicate performance record ID on line {line_number}: {record.record_id}"
            )
        seen[record.record_id] = record
        records.append(record)
    return records


@contextmanager
def _ledger_lock(path: Path, *, timeout_seconds: float = 10.0) -> Iterator[None]:
    lock_path = path.with_suffix(path.suffix + ".lock")
    deadline = time.monotonic() + timeout_seconds
    while True:
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(descriptor)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise LedgerLockTimeoutError(
                    f"Timed out waiting for ledger lock: {lock_path}"
                ) from None
            time.sleep(0.05)
    try:
        yield
    finally:
        lock_path.unlink(missing_ok=True)


def append_performance_observations(
    path: Path,
    observations: Sequence[PerformanceObservation],
) -> int:
    """Append new observations atomically and return the number actually added."""

    if not observations:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with _ledger_lock(path):
        existing = load_performance_ledger(path)
        by_id = {record.record_id: record for record in existing}
        additions: list[PerformanceObservation] = []
        for observation in observations:
            previous = by_id.get(observation.record_id)
            if previous is not None:
                if previous != observation:
                    raise LedgerConflictError(
                        f"Record ID {observation.record_id} has conflicting content"
                    )
                continue
            by_id[observation.record_id] = observation
            additions.append(observation)
        if not additions:
            return 0

        serialized = "".join(
            record.model_dump_json() + "\n" for record in (*existing, *additions)
        )
        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(serialized)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        try:
            os.replace(temporary_path, path)
        finally:
            temporary_path.unlink(missing_ok=True)
        return len(additions)
