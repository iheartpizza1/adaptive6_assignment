"""User-Agent string to OS and browser labels."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class UserAgentLookup(Protocol):
    """Both methods return "Unknown" when the family cannot be determined."""

    def os_family(self, user_agent: str) -> str: ...

    def browser_family(self, user_agent: str) -> str: ...
