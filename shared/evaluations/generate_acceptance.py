# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Extract the normative Gherkin block from the approved specification."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "specs" / "AISoftwareArchitect.md"
OUTPUT = Path(__file__).with_name("acceptance.feature")


def main() -> None:
    text = SPEC.read_text(encoding="utf-8")
    marker = "```gherkin\n"
    if text.count(marker) != 1:
        raise ValueError("specification must contain exactly one normative Gherkin block")
    block = text.split(marker, 1)[1].split("\n```", 1)[0].rstrip() + "\n"
    OUTPUT.write_text(block, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()

