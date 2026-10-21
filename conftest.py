# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Apply explicit platform requirements to tests throughout the workspace."""

from __future__ import annotations

import sys

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    if sys.platform == "win32":
        return
    windows_only = pytest.mark.skip(reason="Windows-only integration test")
    for item in items:
        if item.get_closest_marker("windows") is not None:
            item.add_marker(windows_only)
