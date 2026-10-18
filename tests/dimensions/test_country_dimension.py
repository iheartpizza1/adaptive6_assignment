"""CountryDimension: the Country label comes from the GeoIpLookup, keyed by the record's IP."""

from __future__ import annotations

from tests.fakes import FakeGeoIp
from weblogstats.contracts import UNKNOWN, Dimension, LogRecord
from weblogstats.dimensions.country_dimension import CountryDimension


def _record(ip: str) -> LogRecord:
    return LogRecord(
        ip=ip,
        timestamp=None,
        method="GET",
        path="/",
        protocol="HTTP/1.1",
        status=200,
        bytes_sent=1,
        referer="-",
        user_agent="-",
        raw="",
    )


class _CountingGeoIp:
    """Records every lookup so a test can assert the lookup was not called."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def country_name(self, ip: str) -> str:
        self.calls.append(ip)
        return "Somewhere"


class TestCountryDimension:
    def test_name_is_country(self) -> None:
        assert CountryDimension(FakeGeoIp({})).name == "Country"

    def test_satisfies_dimension_protocol(self) -> None:
        assert isinstance(CountryDimension(FakeGeoIp({})), Dimension)

    def test_extract_returns_the_lookup_result(self) -> None:
        dimension = CountryDimension(FakeGeoIp({"83.149.9.216": "Russia"}))
        assert dimension.extract(_record("83.149.9.216")) == "Russia"

    def test_extract_returns_unknown_for_unmapped_ip(self) -> None:
        dimension = CountryDimension(FakeGeoIp({"83.149.9.216": "Russia"}))
        assert dimension.extract(_record("1.2.3.4")) == UNKNOWN

    def test_empty_ip_is_unknown_without_calling_the_lookup(self) -> None:
        geoip = _CountingGeoIp()
        dimension = CountryDimension(geoip)
        assert dimension.extract(LogRecord.unreadable("garbage")) == UNKNOWN
        assert geoip.calls == []
