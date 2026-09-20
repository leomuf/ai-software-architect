# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

from pathlib import Path

import pytest

from adapters.codex.runtime_targets import target_for_name
from scripts.package_codex_release import package_release


def test_release_rejects_symlinked_plugin_files(tmp_path: Path) -> None:
    plugin = tmp_path / "plugin"
    plugin.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("untrusted", encoding="utf-8")
    linked = plugin / "linked.txt"
    try:
        linked.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation is unavailable on this host")

    with pytest.raises(ValueError, match=r"must not contain symlink: linked\.txt"):
        package_release(
            plugin,
            tmp_path / "release",
            target=target_for_name("aarch64-darwin"),
            plugin_version="0.2.3",
        )
