"""Test double for UserAgentLookup."""

from __future__ import annotations

from weblogstats.contracts import UNKNOWN


class FakeUserAgentLookup:
    """Maps a User-Agent string to OS and browser from two dicts; any other UA is Unknown."""

    def __init__(self, os_map: dict[str, str], browser_map: dict[str, str]) -> None:
        self._os_map = dict(os_map)
        self._browser_map = dict(browser_map)

    def os_family(self, user_agent: str) -> str:
        return self._os_map.get(user_agent, UNKNOWN)

    def browser_family(self, user_agent: str) -> str:
        return self._browser_map.get(user_agent, UNKNOWN)
