"""Test double for GeoIpLookup."""

from __future__ import annotations

from weblogstats.contracts import UNKNOWN


class FakeGeoIp:
    """Maps IP to country from a dict; any other IP is Unknown."""

    def __init__(self, mapping: dict[str, str]) -> None:
        self._mapping = dict(mapping)

    def country_name(self, ip: str) -> str:
        return self._mapping.get(ip, UNKNOWN)
