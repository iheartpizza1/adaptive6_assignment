"""The parsed form of one access-log line."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class LogRecord:
    """One log line as fields. ``partial`` is True when the lenient fallback produced it."""

    ip: str
    timestamp: datetime | None
    method: str
    path: str
    protocol: str
    status: int | None
    bytes_sent: int | None
    referer: str
    user_agent: str
    raw: str
    partial: bool = False

    @classmethod
    def unreadable(cls, raw: str) -> LogRecord:
        """A record for a line the parser cannot read at all; every dimension yields Unknown."""
        return cls(
            ip="",
            timestamp=None,
            method="",
            path="",
            protocol="",
            status=None,
            bytes_sent=None,
            referer="",
            user_agent="",
            raw=raw,
        )
