"""The Browser metric."""

from __future__ import annotations

from weblogstats.contracts import LogRecord, UserAgentLookup


class BrowserDimension:
    """Labels each record with the browser family from its User-Agent."""

    name = "Browser"

    def __init__(self, ua: UserAgentLookup) -> None:
        self._ua = ua

    def extract(self, record: LogRecord) -> str:
        return self._ua.browser_family(record.user_agent)
