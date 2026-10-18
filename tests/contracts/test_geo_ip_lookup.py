from __future__ import annotations

from types import SimpleNamespace

from weblogstats.contracts import GeoIpLookup


class TestGeoIpLookup:
    def test_object_with_the_members_satisfies_the_protocol(self) -> None:
        candidate = SimpleNamespace(country_name=lambda ip: "Unknown")
        assert isinstance(candidate, GeoIpLookup)

    def test_object_missing_the_members_does_not_satisfy_the_protocol(self) -> None:
        assert not isinstance(SimpleNamespace(), GeoIpLookup)
        assert not isinstance(object(), GeoIpLookup)
