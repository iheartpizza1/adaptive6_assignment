"""Streams raw lines from a log file."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path


class FileLogSource:
    """A LogSource backed by a file on disk.

    A missing file raises ``FileNotFoundError`` from the constructor, so the caller fails before
    any output is produced.
    """

    def __init__(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"log file not found: {path}")
        self._path = path

    def lines(self) -> Iterator[str]:
        # newline="\n" so only "\n" ends a line; a stray "\r" inside a line is kept as data.
        with self._path.open(encoding="utf-8", errors="replace", newline="\n") as handle:
            for line in handle:
                line = line.removesuffix("\n").removesuffix("\r")
                if line.strip():
                    yield line
