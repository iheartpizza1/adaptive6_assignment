from __future__ import annotations

from tests.fakes.fake_geo_ip import FakeGeoIp
from weblogstats.contracts import UNKNOWN, GeoIpLookup


class TestFakeGeoIp:
    def test_satisfies_the_geo_ip_lookup_protocol(self) -> None:
        assert isinstance(FakeGeoIp({}), GeoIpLookup)

    def test_returns_the_mapped_country(self) -> None:
        fake = FakeGeoIp({"83.149.9.216": "Russia"})
        assert fake.country_name("83.149.9.216") == "Russia"

    def test_returns_unknown_for_an_unmapped_ip(self) -> None:
        assert FakeGeoIp({"1.1.1.1": "Australia"}).country_name("2.2.2.2") == UNKNOWN

    def test_returns_unknown_for_empty_ip(self) -> None:
        assert FakeGeoIp({}).country_name("") == UNKNOWN
