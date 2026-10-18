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
        method, path, protocol = _split_request(match["request"])
        return LogRecord(
            ip=match["ip"],
            timestamp=_parse_time(match["time"]),
            method=method,
            path=path,
            protocol=protocol,
            status=_to_int(match["status"]),
            bytes_sent=_to_int(match["bytes"]),
            referer=match["referer"],
            user_agent=match["agent"],
            raw=line,
        )


def _split_request(request: str) -> tuple[str, str, str]:
    """Split ``METHOD PATH PROTOCOL``; missing parts become empty strings.

    Two tokens are METHOD and PATH, one token is a bare PATH, and ``-`` or empty is nothing.
    """
    if request in ("", "-"):
        return "", "", ""
    tokens = request.split(" ")
    if len(tokens) == 1:
        return "", tokens[0], ""
    if len(tokens) == 2:
        return tokens[0], tokens[1], ""
    return tokens[0], " ".join(tokens[1:-1]), tokens[-1]


def _parse_time(text: str) -> datetime | None:
    try:
        return datetime.strptime(text, _TIME_FORMAT)
    except ValueError:
        return None


def _to_int(token: str) -> int | None:
    return None if token == "-" else int(token)
