# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pytest
import yaml

from scripts.collect_release_assets import collect_release_assets

ROOT = Path(__file__).resolve().parents[2]


def _archive(source: Path, target: str) -> Path:
    directory = source / target
    directory.mkdir(parents=True, exist_ok=True)
    archive = directory / f"ai-software-architect-v0.2.4-{target}.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("VERSION.txt", f"0.2.4 {target}\n")
    # Job-local manifests must never overwrite or become the combined manifest.
    (directory / "SHA256SUMS.txt").write_text("stale job-local hash\n", encoding="ascii")
    return archive


@pytest.mark.parametrize("targets", [
    ["windows-x86_64"],
    ["windows-x86_64", "aarch64-darwin"],
    ["windows-x86_64", "aarch64-darwin", "linux-x86_64"],
])
def test_collects_all_platforms_with_independently_verified_hashes(
    tmp_path: Path, targets: list[str],
) -> None:
    source = tmp_path / "jobs"
    archives = [_archive(source, target) for target in targets]
    output = tmp_path / "publication"
    manifest = collect_release_assets(source, output, version="0.2.4", targets=targets)
    expected = {
        archive.name: hashlib.sha256(archive.read_bytes()).hexdigest() for archive in archives
    }
    lines = manifest.read_text("ascii").splitlines()
    assert lines == [f"{expected[name]}  {name}" for name in sorted(expected)]
    assert {path.name for path in output.iterdir()} == {*expected, "SHA256SUMS.txt"}
    for archive in archives:
        assert (output / archive.name).read_bytes() == archive.read_bytes()


@pytest.mark.parametrize("problem", ["missing", "duplicate", "unexpected", "corrupt"])
def test_collection_rejects_incomplete_or_ambiguous_inputs(tmp_path: Path, problem: str) -> None:
    source = tmp_path / "jobs"
    archive = _archive(source, "windows-x86_64")
    targets = ["windows-x86_64"]
    if problem == "missing":
        targets.append("aarch64-darwin")
    elif problem == "duplicate":
        (source / archive.name).write_bytes(archive.read_bytes())
    elif problem == "unexpected":
        _archive(source, "aarch64-darwin")
    else:
        archive.write_bytes(b"not a ZIP")
    output = tmp_path / "publication"
    with pytest.raises(ValueError, match=r"missing|duplicate|unexpected|invalid"):
        collect_release_assets(source, output, version="0.2.4", targets=targets)
    assert not output.exists()


def test_collection_refuses_to_overwrite_previous_publication(tmp_path: Path) -> None:
    source = tmp_path / "jobs"
    _archive(source, "windows-x86_64")
    output = tmp_path / "publication"
    output.mkdir()
    sentinel = output / "SHA256SUMS.txt"
    sentinel.write_text("previous release\n", encoding="ascii")
    with pytest.raises(ValueError, match="must not already exist"):
        collect_release_assets(source, output, version="0.2.4", targets=["windows-x86_64"])
    assert sentinel.read_text("ascii") == "previous release\n"


def test_release_collection_waits_for_every_declared_platform() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text("utf-8"))
    jobs = workflow["jobs"]
    collector = jobs["collect-release-assets"]
    builds = {name: job for name, job in jobs.items() if name.startswith("build")}
    assert set(builds) <= set(collector["needs"])
    command = next(step["run"] for step in collector["steps"] if "run" in step)
    for job in builds.values():
        upload = next(step for step in job["steps"] if "upload-artifact@" in step.get("uses", ""))
        prefix = "ai-software-architect-${{ github.ref_name }}-"
        assert upload["with"]["name"].startswith(prefix)
        target = upload["with"]["name"].removeprefix(prefix)
        assert f"--target {target}" in command
    download = next(
        step for step in collector["steps"] if "download-artifact@" in step.get("uses", "")
    )
    assert download["with"]["merge-multiple"] is False
