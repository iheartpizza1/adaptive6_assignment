"""IP address to country name."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class GeoIpLookup(Protocol):
    """Returns "Unknown" for private, invalid or unmapped addresses."""

    def country_name(self, ip: str) -> str: ...
