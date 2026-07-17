# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Generate a deterministic runtime dependency notice from installed metadata."""

from __future__ import annotations

import re
from collections import deque
from importlib import metadata
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "THIRD_PARTY_NOTICES.md"
ROOT_PACKAGES = ("ai-architect-tools", "ai-architect-schemas")
BUILD_COMPONENTS = ("pyinstaller", "pyinstaller-hooks-contrib")
LOCAL_PACKAGES = {canonicalize_name(name) for name in ROOT_PACKAGES}


def runtime_distributions() -> list[metadata.Distribution]:
    available = {
        canonicalize_name(distribution.metadata["Name"]): distribution
        for distribution in metadata.distributions()
        if distribution.metadata["Name"]
    }
    queue = deque(canonicalize_name(name) for name in ROOT_PACKAGES)
    visited: set[str] = set()
    result: list[metadata.Distribution] = []
    while queue:
        name = queue.popleft()
        if name in visited:
            continue
        visited.add(name)
        distribution = available.get(name)
        if distribution is None:
            raise RuntimeError(f"installed distribution is missing: {name}")
        if name not in LOCAL_PACKAGES:
            result.append(distribution)
        for requirement_text in distribution.requires or []:
            requirement = Requirement(requirement_text)
            if requirement.marker and not requirement.marker.evaluate({"extra": ""}):
                continue
            queue.append(canonicalize_name(requirement.name))
    for name in BUILD_COMPONENTS:
        distribution = available[canonicalize_name(name)]
        if distribution not in result:
            result.append(distribution)
    return sorted(result, key=lambda item: canonicalize_name(item.metadata["Name"]))


def license_name(distribution: metadata.Distribution) -> str:
    expression = distribution.metadata.get("License-Expression")
    if expression:
        return expression
    classifiers = distribution.metadata.get_all("Classifier") or []
    license_classifiers = [
        item.rsplit("::", 1)[-1].strip() for item in classifiers if "License ::" in item
    ]
    if license_classifiers:
        return ", ".join(sorted(set(license_classifiers)))
    value = (distribution.metadata.get("License") or "Not declared in package metadata").strip()
    return re.sub(r"\s+", " ", value)[:500]


def main() -> None:
    lines = [
        "<!--",
        "SPDX-FileCopyrightText: 2026 Leonardo Muffato "
        "(AUTOSOFT Engineering - www.autosoft-engineering.de)",
        "SPDX-License-Identifier: MIT",
        "-->",
        "",
        "# Third-Party Notices",
        "",
        "The Windows executable bundles the runtime dependencies below. Copyright remains "
        "with each package's authors. Complete license texts are provided by their respective "
        "distributions and must be included in release archives when required.",
        "",
        "| Package | Version | Declared license | Project URL |",
        "| --- | --- | --- | --- |",
        "| CPython | 3.13.12 | PSF-2.0 | https://www.python.org/ |",
    ]
    for distribution in runtime_distributions():
        name = distribution.metadata["Name"]
        url = distribution.metadata.get("Home-page") or ""
        if not url:
            project_urls = distribution.metadata.get_all("Project-URL") or []
            url = project_urls[0].split(",", 1)[-1].strip() if project_urls else ""
        lines.append(
            f"| {name} | {distribution.version} | {license_name(distribution)} | {url} |"
        )
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
