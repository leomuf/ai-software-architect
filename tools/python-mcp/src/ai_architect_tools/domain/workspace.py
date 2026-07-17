# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Workspace-bound, read-only file access with strict path and size budgets."""

from __future__ import annotations

import ctypes
import os
import stat
from collections.abc import Iterable, Iterator
from contextlib import closing
from pathlib import Path, PurePosixPath
from typing import BinaryIO

MAX_FILES = 500
MAX_TOTAL_BYTES = 5_000_000
MAX_SINGLE_FILE_BYTES = 500_000
FILE_ATTRIBUTE_REPARSE_POINT = 0x400

PROTECTED_PATTERNS = (
    ".git/**",
    ".env",
    ".env.*",
    ".npmrc",
    ".pypirc",
    "**/*.pem",
    "**/*.key",
    "**/*.p12",
    "**/*.pfx",
    "**/credentials*",
    "**/secrets.*",
    "**/service-account*.json",
    "**/id_rsa*",
    "**/.ssh/**",
    "**/.aws/**",
    "**/.azure/**",
    "**/.config/gcloud/**",
)


class WorkspaceAccessError(Exception):
    def __init__(self, code: str, message: str, relative_path: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.relative_path = relative_path


def _normalized_relative(path: str) -> PurePosixPath:
    if not path or "\x00" in path:
        raise WorkspaceAccessError("invalid-input", "relative path is empty or invalid")
    normalized = path.replace("\\", "/")
    candidate = PurePosixPath(normalized)
    if candidate.is_absolute() or candidate.drive or any(part == ".." for part in candidate.parts):
        raise WorkspaceAccessError(
            "boundary-violation", "path must remain workspace-relative", path
        )
    if any(part in {"", "."} for part in candidate.parts):
        candidate = PurePosixPath(*(part for part in candidate.parts if part not in {"", "."}))
    return candidate


def _is_protected(path: PurePosixPath) -> bool:
    text = path.as_posix()
    return any(
        path.match(pattern) or PurePosixPath(text).match(pattern)
        for pattern in PROTECTED_PATTERNS
    )


def _is_reparse_point(path: Path) -> bool:
    try:
        attributes = path.lstat().st_file_attributes
    except AttributeError:
        return path.is_symlink()
    return bool(attributes & FILE_ATTRIBUTE_REPARSE_POINT)


def _final_windows_path(handle: BinaryIO) -> Path:
    import msvcrt

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    function = kernel32.GetFinalPathNameByHandleW
    function.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32]
    function.restype = ctypes.c_uint32
    os_handle = msvcrt.get_osfhandle(handle.fileno())
    size = function(os_handle, None, 0, 0)
    if size == 0:
        raise OSError(ctypes.get_last_error(), "GetFinalPathNameByHandleW failed")
    buffer = ctypes.create_unicode_buffer(size + 1)
    written = function(os_handle, buffer, len(buffer), 0)
    if written == 0 or written >= len(buffer):
        raise OSError(ctypes.get_last_error(), "GetFinalPathNameByHandleW failed")
    value = buffer.value
    if value.startswith("\\\\?\\UNC\\"):
        value = "\\\\" + value[8:]
    elif value.startswith("\\\\?\\"):
        value = value[4:]
    return Path(value).resolve(strict=True)


class WorkspaceReader:
    """Read supported files without allowing the caller to select an absolute root."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve(strict=True)
        if not self.root.is_dir():
            raise WorkspaceAccessError("workspace-unavailable", "workspace root is not a directory")

    def _candidate(self, relative_path: str) -> tuple[PurePosixPath, Path]:
        relative = _normalized_relative(relative_path)
        if _is_protected(relative):
            raise WorkspaceAccessError(
                "protected-path", "protected path is not readable", relative.as_posix()
            )
        candidate = self.root.joinpath(*relative.parts)
        current = self.root
        for part in relative.parts:
            current = current / part
            if current.exists() and _is_reparse_point(current):
                raise WorkspaceAccessError(
                    "boundary-violation",
                    "filesystem indirection is not allowed",
                    relative.as_posix(),
                )
        try:
            resolved = candidate.resolve(strict=True)
        except FileNotFoundError as exc:
            raise WorkspaceAccessError(
                "not-found", "requested path does not exist", relative.as_posix()
            ) from exc
        if os.path.commonpath((str(self.root), str(resolved))) != str(self.root):
            raise WorkspaceAccessError(
                "boundary-violation", "resolved path escapes workspace", relative.as_posix()
            )
        return relative, resolved

    def read_text(self, relative_path: str, allowed_suffixes: set[str]) -> str:
        relative, resolved = self._candidate(relative_path)
        if resolved.suffix.casefold() not in allowed_suffixes:
            raise WorkspaceAccessError(
                "unsupported-format", "file type is not supported", relative.as_posix()
            )
        with closing(resolved.open("rb")) as handle:
            final = (
                _final_windows_path(handle)
                if os.name == "nt"
                else resolved.resolve(strict=True)
            )
            if os.path.commonpath((str(self.root), str(final))) != str(self.root):
                raise WorkspaceAccessError(
                    "boundary-violation", "opened file escapes workspace", relative.as_posix()
                )
            file_stat = os.fstat(handle.fileno())
            if not stat.S_ISREG(file_stat.st_mode):
                raise WorkspaceAccessError("unsupported-format", "path is not a regular file")
            if file_stat.st_size > MAX_SINGLE_FILE_BYTES:
                raise WorkspaceAccessError(
                    "budget-exhausted", "file exceeds the single-file budget", relative.as_posix()
                )
            content = handle.read(MAX_SINGLE_FILE_BYTES + 1)
        if len(content) > MAX_SINGLE_FILE_BYTES:
            raise WorkspaceAccessError(
                "budget-exhausted", "file exceeds the single-file budget", relative.as_posix()
            )
        if b"\x00" in content:
            raise WorkspaceAccessError("unsupported-format", "binary file is not supported")
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise WorkspaceAccessError(
                "unsupported-format", "file is not valid UTF-8", relative.as_posix()
            ) from exc

    def iter_files(self, relative_roots: list[str], suffixes: set[str]) -> Iterator[str]:
        seen: set[str] = set()
        for root_text in relative_roots:
            _, resolved = self._candidate(root_text)
            if resolved.is_file():
                candidates: Iterable[Path] = [resolved]
            elif resolved.is_dir():
                candidates = self._walk(resolved)
            else:
                continue
            for candidate in candidates:
                if candidate.suffix.casefold() not in suffixes:
                    continue
                candidate_relative = candidate.relative_to(self.root).as_posix()
                if candidate_relative in seen or _is_protected(PurePosixPath(candidate_relative)):
                    continue
                seen.add(candidate_relative)
                yield candidate_relative
                if len(seen) >= MAX_FILES:
                    return

    def _walk(self, directory: Path) -> Iterator[Path]:
        pending = [directory]
        while pending:
            current = pending.pop()
            with os.scandir(current) as entries:
                for entry in entries:
                    if entry.name.startswith(".") or entry.is_symlink():
                        continue
                    path = Path(entry.path)
                    if _is_reparse_point(path):
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        pending.append(path)
                    elif entry.is_file(follow_symlinks=False):
                        yield path
