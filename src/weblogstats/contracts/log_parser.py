"""Turns one raw line into a LogRecord."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from weblogstats.contracts.log_record import LogRecord


@runtime_checkable
class LogParser(Protocol):
    """Returns None only when no record can be recovered from the line."""

    def parse(self, line: str) -> LogRecord | None: ...
