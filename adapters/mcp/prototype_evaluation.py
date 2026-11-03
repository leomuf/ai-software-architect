# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Dedicated deterministic cohort; never writes the legacy exploratory ledger."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ai_architect_tools.workflow_server import PROTOCOL_VERSION, TOOL_CONTRACTS

from .build_instructions import ROOT, build


def schema_risks(value: Any, path: str = "$") -> list[str]:
    risks = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"anyOf", "allOf", "oneOf"} or (key == "type" and isinstance(child, list)):
                risks.append(f"{path}.{key}")
            risks.extend(schema_risks(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            risks.extend(schema_risks(child, f"{path}[{index}]"))
    return risks


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run only the synthetic deterministic MCP cohort")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error("choose a new empty output directory to preserve prior evidence")
    output.mkdir(parents=True, exist_ok=True)
    package = build(output / "instruction-package")
    schemas = {name: model.model_json_schema() for name, (model, _) in TOOL_CONTRACTS.items()}
    (output / "tool-input-schemas.json").write_text(
        json.dumps(schemas, indent=2) + "\n", encoding="utf-8"
    )
    started = time.monotonic()
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tools/python-mcp/tests/test_workflow_prototype.py",
        "tests/adapters/mcp/test_prototype_packaging.py",
        "-q",
        "--basetemp",
        str(output / "pytest-workspaces"),
        "--junitxml",
        str(output / "junit.xml"),
    ]
    completed = subprocess.run(command, cwd=ROOT, check=False)  # noqa: S603
    durations = []
    counts = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    if (output / "junit.xml").is_file():
        # Only our just-generated synthetic pytest report, never customer-supplied XML.
        tree = ET.parse(output / "junit.xml")  # noqa: S314
        for suite in tree.getroot().iter("testsuite"):
            for category in counts:
                counts[category] += int(suite.attrib.get(category, "0"))
        durations = [float(test.attrib["time"]) for test in tree.getroot().iter("testcase")]
    report = dict(
        cohort="mcp-phase-0-anonymous-stateless-deterministic",
        timestamp=datetime.now(UTC).isoformat(),
        exit_code=completed.returncode,
        counts=counts,
        duration_seconds=time.monotonic() - started,
        python=platform.python_version(),
        os=platform.platform(),
        sdk=importlib.metadata.version("mcp"),
        protocol=PROTOCOL_VERSION,
        reference_version=package["reference_version"],
        test_case_latency_seconds={
            "p50": percentile(durations, 0.5),
            "p90": percentile(durations, 0.9),
        }
        if durations
        else {},
        latency_scope="deterministic test cases, not host-model or tool-call latency",
        host_model_runs="not-run",
        migration_gate="no-go-pending-real-host-evidence",
        acceptance="draft-only; independent human confirmation unavailable",
        foundry={
            "status": "not-run",
            "schema_risks": schema_risks(schemas),
            "authentication": "none; needs a provisioned agent and reachable HTTPS endpoint",
        },
    )
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (output / "SUMMARY.md").write_text(
        "# MCP phase 0 deterministic evidence\n\n"
        f"Exit code: {completed.returncode}; tests: {counts['tests']}; "
        f"failures: {counts['failures']}; errors: {counts['errors']}.\n\n"
        "Synthetic protocol/security tests only. Actual HTTPS is exercised. "
        "No model or live host is scored. Legacy hooks and performance history are not used.\n\n"
        "Migration gate: **no-go pending real-host evidence**. "
        "Draft export only; human acceptance and customer-local persistence are unverified.\n\n"
        "Codex/Claude continuation cohorts, Foundry discovery/auth/schema probe, "
        "latency budgets and all advertised OS/surface cells remain unverified.\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Prototype evidence: {output}")
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
