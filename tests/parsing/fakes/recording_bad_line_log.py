"""A stand-in for BadLineLog that records calls instead of writing a file."""

from __future__ import annotations


class RecordingBadLineLog:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def warn(self, raw: str) -> None:
        self.calls.append(("warn", raw))

    def error(self, raw: str) -> None:
        self.calls.append(("error", raw))
