"""Parses Apache combined-format access-log lines."""

from __future__ import annotations

import re
from datetime import datetime

from weblogstats.contracts.log_record import LogRecord


def _quoted(name: str) -> str:
    """A quoted field. It may hold \\" and \\xNN escapes, which stay as literal text."""
    return r'"(?P<' + name + r'>(?:[^"\\]|\\.)*)"'


_STRICT = re.compile(
    r"^(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]*)\] " + _quoted("request") + " "
    r"(?P<status>\d+|-) (?P<bytes>\d+|-) " + _quoted("referer") + " " + _quoted("agent") + r"\s*$"
)

_TIME_FORMAT = "%d/%b/%Y:%H:%M:%S %z"


class ApacheCombinedParser:
    """A LogParser for the Apache combined format, with a lenient fallback."""

    def parse(self, line: str) -> LogRecord | None:
        match = _STRICT.match(line)
        if match is None:
            return None
        method, path, protocol = match["request"].split(" ")
        return LogRecord(
            ip=match["ip"],
            timestamp=datetime.strptime(match["time"], _TIME_FORMAT),
            method=method,
            path=path,
            protocol=protocol,
            status=_to_int(match["status"]),
            bytes_sent=_to_int(match["bytes"]),
            referer=match["referer"],
            user_agent=match["agent"],
            raw=line,
        )


def _to_int(token: str) -> int | None:
    return None if token == "-" else int(token)
