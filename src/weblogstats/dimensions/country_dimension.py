"""Country dimension."""

from __future__ import annotations

from weblogstats.contracts import UNKNOWN, GeoIpLookup, LogRecord


class CountryDimension:
    """Labels each request with the country of its client IP."""

    name = "Country"

    def __init__(self, geoip: GeoIpLookup) -> None:
        self._geoip = geoip

    def extract(self, record: LogRecord) -> str:
        if not record.ip:
            return UNKNOWN
        return self._geoip.country_name(record.ip)
