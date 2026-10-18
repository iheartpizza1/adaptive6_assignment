"""The OS metric."""

from __future__ import annotations

from weblogstats.contracts import LogRecord, UserAgentLookup


class OsDimension:
    """Labels each record with the operating system from its User-Agent."""

    name = "OS"

    def __init__(self, ua: UserAgentLookup) -> None:
        self._ua = ua

    def extract(self, record: LogRecord) -> str:
        return self._ua.os_family(record.user_agent)
