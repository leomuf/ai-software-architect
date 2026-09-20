# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Create a target-specific, installable Codex marketplace bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import stat
import sys
import zipfile
from pathlib import Path
from zipfile import ZipInfo

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_NAME = "ai-software-architect"
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.codex import validate_plugin  # noqa: E402
from adapters.codex.runtime_targets import (  # noqa: E402
    RUNTIME_TARGETS,
    RuntimeTarget,
    target_for_name,
)


def _resolve_repository_path(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _target_install_guide(target: RuntimeTarget, version: str) -> str:
    text = (ROOT / "docs" / "INSTALL_CODEX_PLUGIN.md").read_text(encoding="utf-8")
    text = text.replace("v0.1.0", f"v{version}")
    if target.name == "aarch64-darwin":
        text = text.replace(
            "On Windows:\n\n"
            "```powershell\n"
            f"Get-FileHash .\\ai-software-architect-v{version}-windows-x86_64.zip "
            "-Algorithm SHA256\n"
            "```\n\n",
            "",
        )
    text = text.replace("windows-x86_64", target.archive_suffix)
    return text


def _write_zip(source: Path, archive: Path) -> None:
    with zipfile.ZipFile(
        archive,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as handle:
        for path in sorted(source.rglob("*")):
            if not path.is_file():
                continue
            info = ZipInfo(path.relative_to(source.parent).as_posix(), ZIP_EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (stat.S_IMODE(path.stat().st_mode) & 0xFFFF) << 16
            handle.writestr(info, path.read_bytes())


def _reject_symlinks(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_symlink():
            relative = path.relative_to(root).as_posix()
            raise ValueError(f"plugin package must not contain symlink: {relative}")


def package_release(
    plugin_path: Path,
    output_directory: Path,
    *,
    target: RuntimeTarget,
    plugin_version: str | None = None,
) -> tuple[Path, Path]:
    plugin_path = plugin_path.resolve(strict=True)
    _reject_symlinks(plugin_path)
    manifest_path = plugin_path / ".codex-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("name") != PLUGIN_NAME:
        raise ValueError(f"unexpected plugin name: {manifest.get('name')!r}")
    version = plugin_version or manifest["version"]
    if manifest["version"] != version:
        raise ValueError(
            f"built manifest version {manifest['version']!r} does not match {version!r}"
        )
    validate_plugin.validate(plugin_path, target=target)

    output_directory = output_directory.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    bundle_name = f"{PLUGIN_NAME}-v{version}-{target.archive_suffix}"
    bundle_root = output_directory / bundle_name
    archive = output_directory / f"{bundle_name}.zip"
    checksum = output_directory / "SHA256SUMS.txt"
    for path in (bundle_root, archive, checksum):
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

    plugin_target = bundle_root / "plugins" / PLUGIN_NAME
    plugin_target.parent.mkdir(parents=True)
    marketplace_target = bundle_root / ".agents" / "plugins" / "marketplace.json"
    marketplace_target.parent.mkdir(parents=True)
    shutil.copyfile(
        ROOT / "adapters" / "codex" / "templates" / "marketplace.json",
        marketplace_target,
    )
    shutil.copytree(plugin_path, plugin_target)
    (bundle_root / "INSTALL.md").write_text(
        _target_install_guide(target, version),
        encoding="utf-8",
        newline="\n",
    )
    (bundle_root / "VERSION.txt").write_text(f"{version}\n", encoding="ascii")
    _write_zip(bundle_root, archive)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="ascii")
    return archive, checksum


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plugin-path", default="dist/codex/ai-software-architect")
    parser.add_argument("--output-directory", default="dist/release")
    parser.add_argument("--plugin-version")
    parser.add_argument("--target", choices=sorted(RUNTIME_TARGETS), required=True)
    args = parser.parse_args()
    archive, checksum = package_release(
        _resolve_repository_path(args.plugin_path),
        _resolve_repository_path(args.output_directory),
        target=target_for_name(args.target),
        plugin_version=args.plugin_version,
    )
    print(f"Archive: {archive}")
    print(f"Checksum: {checksum}")


if __name__ == "__main__":
    main()
