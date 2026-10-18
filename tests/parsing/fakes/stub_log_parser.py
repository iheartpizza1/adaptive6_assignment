"""A LogParser that returns canned results and remembers the lines it was given."""

from __future__ import annotations

from weblogstats.contracts import LogRecord


class StubLogParser:
    def __init__(self, result: LogRecord | None) -> None:
        self._result = result
        self.lines: list[str] = []

    def parse(self, line: str) -> LogRecord | None:
        self.lines.append(line)
        return self._result
