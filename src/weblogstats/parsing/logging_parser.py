"""A LogParser decorator that reports unclean lines to a BadLineLog."""

from __future__ import annotations

from weblogstats.contracts.log_parser import LogParser
from weblogstats.contracts.log_record import LogRecord
from weblogstats.parsing.bad_line_log import BadLineLog


class LoggingParser:
    """Wraps any LogParser and returns its results unchanged.

    A partial record is logged as a warning and an unreadable line (``None``) as an error.
    Clean records are not logged.
    """

    def __init__(self, inner: LogParser, log: BadLineLog) -> None:
        self._inner = inner
        self._log = log

    def parse(self, line: str) -> LogRecord | None:
        record = self._inner.parse(line)
        if record is None:
            self._log.error(line)
        elif record.partial:
            self._log.warn(line)
        return record
