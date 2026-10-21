# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Collect completed platform builds into one publication set and checksum file."""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import stat
import sys
import tempfile
import zipfile
from pathlib import Path


def _is_link(path: Path) -> bool:
    if path.is_symlink():
        return True
    if sys.platform == "win32":
        return bool(path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    return False


def collect_release_assets(
    source: Path, output: Path, *, version: str, targets: list[str],
) -> Path:
    """Reject missing, duplicate, unexpected or linked ZIPs before publishing any files."""
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)*", version):
        raise ValueError("invalid release version")
    if (
        not targets or len(set(targets)) != len(targets)
        or any(not re.fullmatch(r"[a-z0-9]+(?:[-_][a-z0-9]+)*", t) for t in targets)
    ):
        raise ValueError("provide distinct expected runtime targets")
    if any(_is_link(p) for p in (source, *source.parents)):
        raise ValueError("release source must not use links")
    source = source.resolve(strict=True)
    output = output.absolute()
    if output.exists():
        raise ValueError("publication output must not already exist")
    expected = {f"ai-software-architect-v{version}-{target}.zip" for target in targets}
    archives: dict[str, Path] = {}
    for path in source.rglob("*.zip"):
        if any(_is_link(p) for p in (path, *path.parents)):
            raise ValueError("release archives must not use links")
        if path.name not in expected:
            raise ValueError(f"unexpected release archive: {path.name}")
        if path.name in archives:
            raise ValueError(f"duplicate release archive: {path.name}")
        if not path.is_file() or not zipfile.is_zipfile(path):
            raise ValueError(f"invalid release archive: {path.name}")
        archives[path.name] = path
    if missing := expected - archives.keys():
        raise ValueError(f"missing release archives: {sorted(missing)}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        staged = Path(temporary) / "assets"
        staged.mkdir()
        lines = []
        for name, archive in sorted(archives.items()):
            destination = staged / name
            shutil.copyfile(archive, destination)
            with destination.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            lines.append(f"{digest}  {name}\n")
        (staged / "SHA256SUMS.txt").write_text("".join(lines), encoding="ascii", newline="\n")
        staged.rename(output)
    return output / "SHA256SUMS.txt"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--target", action="append", required=True)
    args = parser.parse_args()
    print(collect_release_assets(
        args.source, args.output, version=args.version, targets=args.target,
    ))


if __name__ == "__main__":
    main()
