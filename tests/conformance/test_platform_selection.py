# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

from types import SimpleNamespace

import pytest

import conftest


@pytest.mark.parametrize("platform", ["win32", "darwin", "linux"])
def test_windows_requirement_skips_only_windows_tests_on_other_hosts(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch, platform: str,
) -> None:
    def example() -> None:
        pass

    windows = pytest.Function.from_parent(request.node.parent, name="windows", callobj=example)
    shared = pytest.Function.from_parent(request.node.parent, name="shared", callobj=example)
    windows.add_marker(pytest.mark.windows)
    # Change only the policy module's view, never the running interpreter's platform.
    monkeypatch.setattr(conftest, "sys", SimpleNamespace(platform=platform))
    conftest.pytest_collection_modifyitems([windows, shared])

    assert bool(list(windows.iter_markers("skip"))) == (platform != "win32")
    assert not list(shared.iter_markers("skip"))
