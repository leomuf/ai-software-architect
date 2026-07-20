# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Typed, token-matched access to the generated canonical reference catalog."""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReferenceSpec:
    name: str
    category: str
    filename: str
    aliases: tuple[str, ...]


def _tokens(value: str) -> tuple[str, ...]:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    tokens: list[str] = []
    current: list[str] = []
    for character in normalized:
        if character.isalnum():
            current.append(character)
        elif current:
            tokens.append("".join(current))
            current.clear()
    if current:
        tokens.append("".join(current))
    return tuple(tokens)


class ReferenceCatalog:
    def __init__(self, entries: tuple[ReferenceSpec, ...]) -> None:
        self.entries = entries
        by_name: dict[str, ReferenceSpec] = {}
        aliases: dict[tuple[str, ...], ReferenceSpec] = {}
        for entry in entries:
            normalized_name = " ".join(_tokens(entry.name))
            if normalized_name in by_name:
                raise ValueError(f"duplicate reference name: {entry.name}")
            by_name[normalized_name] = entry
            for alias in (entry.name, *entry.aliases):
                token_alias = _tokens(alias)
                existing = aliases.get(token_alias)
                if existing is not None and existing != entry:
                    raise ValueError(f"conflicting reference alias: {alias}")
                aliases[token_alias] = entry
        self._by_name = by_name
        self._aliases = aliases

    def named(self, name: str) -> ReferenceSpec | None:
        return self._by_name.get(" ".join(_tokens(name)))

    def explicitly_named(self, prompt: str) -> tuple[ReferenceSpec, ...]:
        prompt_tokens = _tokens(prompt)
        resolved: list[tuple[int, ReferenceSpec]] = []
        seen: set[str] = set()
        aliases = sorted(self._aliases.items(), key=lambda item: len(item[0]), reverse=True)
        for alias, entry in aliases:
            if len(alias) == 1 and alias != ("mvc",):
                positions = tuple(
                    index
                    for index in range(len(prompt_tokens) - len(alias))
                    if prompt_tokens[index : index + len(alias) + 1]
                    in ((*alias, "pattern"), ("pattern", *alias))
                )
            else:
                positions = tuple(
                    index
                    for index in range(len(prompt_tokens) - len(alias) + 1)
                    if prompt_tokens[index : index + len(alias)] == alias
                )
            if positions and entry.filename not in seen:
                resolved.append((positions[0], entry))
                seen.add(entry.filename)
        return tuple(entry for _, entry in sorted(resolved, key=lambda item: item[0]))

    def compact_index(self) -> str:
        """Render stable name/category/filename metadata without loading reference bodies."""

        return "; ".join(
            f"[{entry.category}] {entry.name}=references/{entry.filename}"
            for entry in self.entries
        )


def load_reference_catalog(path: Path | None = None) -> ReferenceCatalog:
    source = path or Path(__file__).with_name("reference_catalog.json")
    payload = json.loads(source.read_text(encoding="utf-8"))
    return ReferenceCatalog(
        tuple(
            ReferenceSpec(
                name=item["name"],
                category=item["category"],
                filename=item["filename"],
                aliases=tuple(item.get("aliases", ())),
            )
            for item in payload["references"]
        )
    )


REFERENCE_CATALOG = load_reference_catalog()
