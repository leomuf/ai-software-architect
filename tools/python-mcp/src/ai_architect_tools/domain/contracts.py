# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Safe architecture-contract validation and generated-artifact secret scanning."""

from __future__ import annotations

import re
from collections.abc import Hashable
from typing import Any

import yaml
from ai_architect_schemas import (
    ArchitectureContract,
    ArtifactSecretScanInput,
    ArtifactSecretScanResult,
    ContractValidationInput,
    ContractValidationResult,
    SecretFinding,
)
from pydantic import ValidationError
from yaml.events import AliasEvent
from yaml.nodes import MappingNode, Node

MAX_ERRORS = 100
MAX_NESTING_DEPTH = 50


class SafeArchitectureLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects aliases and duplicate mapping keys."""

    def compose_node(self, parent: Node | None, index: int) -> Node | None:
        if self.check_event(AliasEvent):  # type: ignore[no-untyped-call]
            raise yaml.constructor.ConstructorError(None, None, "YAML aliases are not allowed")
        return super().compose_node(parent, index)

    def construct_mapping(self, node: MappingNode, deep: bool = False) -> dict[Any, Any]:
        self.flatten_mapping(node)
        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, Hashable):
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    "found an unhashable key",
                    key_node.start_mark,
                )
            if key in mapping:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"found duplicate key {key!r}",
                    key_node.start_mark,
                )
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def _validate_depth(value: Any, depth: int = 0) -> None:
    if depth > MAX_NESTING_DEPTH:
        raise ValueError(f"YAML nesting exceeds {MAX_NESTING_DEPTH}")
    if isinstance(value, dict):
        for key, nested in value.items():
            _validate_depth(key, depth + 1)
            _validate_depth(nested, depth + 1)
    elif isinstance(value, list):
        for nested in value:
            _validate_depth(nested, depth + 1)


def load_safe_yaml(content: str) -> Any:
    """Parse bounded YAML without object construction, aliases, or duplicate keys."""

    value = yaml.load(content, Loader=SafeArchitectureLoader)  # noqa: S506
    _validate_depth(value)
    return value


def validate_architecture_contract(
    request: ContractValidationInput,
) -> ContractValidationResult:
    try:
        raw = load_safe_yaml(request.yaml_content)
        if not isinstance(raw, dict):
            raise ValueError("architecture contract must be a YAML mapping")
        contract = ArchitectureContract.model_validate(raw)
    except (yaml.YAMLError, ValueError, ValidationError) as exc:
        if isinstance(exc, ValidationError):
            messages = [
                f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
                for error in exc.errors(include_url=False)
            ]
        else:
            messages = [str(exc)]
        truncated = len(messages) > MAX_ERRORS
        return ContractValidationResult(
            valid=False,
            errors=messages[:MAX_ERRORS],
            truncated=truncated,
        )
    return ContractValidationResult(valid=True, schema_version=contract.schema_version)


_PRIVATE_KEY = re.compile(r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----")
_TOKEN_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
)
_CREDENTIAL_ASSIGNMENT = re.compile(
    r"(?i)\b(?:password|passwd|api[_-]?key|client[_-]?secret|access[_-]?token)\b"
    r"\s*[:=]\s*[\"']?([^\s\"'#,;]{12,})"
)
_SAFE_MARKERS = ("example", "placeholder", "changeme", "not-a-real", "${", "{{", "<")


def scan_generated_artifact(request: ArtifactSecretScanInput) -> ArtifactSecretScanResult:
    findings: list[SecretFinding] = []
    for line_number, line in enumerate(request.content.splitlines(), start=1):
        if _PRIVATE_KEY.search(line):
            findings.append(SecretFinding(category="private-key", line=line_number))
        if any(pattern.search(line) for pattern in _TOKEN_PATTERNS):
            findings.append(SecretFinding(category="token", line=line_number))
        credential = _CREDENTIAL_ASSIGNMENT.search(line)
        if credential and not any(
            marker in credential.group(1).casefold() for marker in _SAFE_MARKERS
        ):
            findings.append(SecretFinding(category="credential", line=line_number))
        if len(findings) >= 100:
            return ArtifactSecretScanResult(
                safe_to_write=False, findings=findings, truncated=True
            )
    return ArtifactSecretScanResult(safe_to_write=not findings, findings=findings)
