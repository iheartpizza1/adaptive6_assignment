"""MaxMindGeoIp: unit tests use a stub reader; data tests use the real GeoLite2-Country MMDB."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from geoip2.errors import AddressNotFoundError  # the adapter's own test may name geoip2 errors

from weblogstats.contracts import UNKNOWN
from weblogstats.lookups.maxmind_geo_ip import MaxMindGeoIp


def _stub_reader(database_type: str = "GeoLite2-Country") -> Mock:
    reader = Mock()
    reader.metadata.return_value = SimpleNamespace(database_type=database_type)
    return reader


def _response(country: dict[str, str], registered: dict[str, str] | None = None) -> SimpleNamespace:
    """The two fields of a geoip2 country response that the adapter reads."""
    return SimpleNamespace(
        country=SimpleNamespace(names=country),
        registered_country=SimpleNamespace(names=registered or {}),
    )


def _geoip(db_file: Path, reader: Mock) -> MaxMindGeoIp:
    return MaxMindGeoIp(db_file, reader_factory=Mock(return_value=reader))


@pytest.fixture
def db_file(tmp_path: Path) -> Path:
    """An existing file the stub factory never actually reads."""
    path = tmp_path / "GeoLite2-Country.mmdb"
    path.write_bytes(b"")
    return path


class TestMaxMindGeoIp:
    def test_missing_file_raises_file_not_found_naming_path_and_env_var(
        self, tmp_path: Path
    ) -> None:
        missing = tmp_path / "nope.mmdb"
        with pytest.raises(FileNotFoundError) as excinfo:
            MaxMindGeoIp(missing)
        assert str(missing) in str(excinfo.value)
        assert "GEOIP_DB" in str(excinfo.value)

    def test_missing_file_does_not_call_the_reader_factory(self, tmp_path: Path) -> None:
        factory = Mock()
        with pytest.raises(FileNotFoundError):
            MaxMindGeoIp(tmp_path / "nope.mmdb", reader_factory=factory)
        factory.assert_not_called()

    def test_opens_the_database_once_at_construction(self, db_file: Path) -> None:
        factory = Mock(return_value=_stub_reader())
        geoip = MaxMindGeoIp(db_file, reader_factory=factory)
        factory.assert_called_once_with(str(db_file))
        geoip.close()

    @pytest.mark.parametrize("database_type", ["GeoLite2-Country", "GeoLite2-City", "GeoIP2-City"])
    def test_accepts_country_and_city_editions(self, db_file: Path, database_type: str) -> None:
        reader = _stub_reader(database_type)
        MaxMindGeoIp(db_file, reader_factory=Mock(return_value=reader))

    def test_rejects_an_asn_database_and_closes_the_reader(self, db_file: Path) -> None:
        reader = _stub_reader("GeoLite2-ASN")
        with pytest.raises(ValueError, match=r"GeoLite2-Country") as excinfo:
            MaxMindGeoIp(db_file, reader_factory=Mock(return_value=reader))
        assert "GeoLite2-ASN" in str(excinfo.value)
        reader.close.assert_called_once()

    def test_country_name_uses_the_english_country_name(self, db_file: Path) -> None:
        reader = _stub_reader()
        reader.country.return_value = _response(country={"en": "Russia", "de": "Russland"})
        geoip = _geoip(db_file, reader)
        assert geoip.country_name("83.149.9.216") == "Russia"
        reader.country.assert_called_once_with("83.149.9.216")

    def test_country_name_falls_back_to_registered_country(self, db_file: Path) -> None:
        reader = _stub_reader()
        reader.country.return_value = _response(country={}, registered={"en": "Australia"})
        assert _geoip(db_file, reader).country_name("1.1.1.1") == "Australia"

    def test_country_name_prefers_country_over_registered_country(self, db_file: Path) -> None:
        reader = _stub_reader()
        reader.country.return_value = _response(
            country={"en": "Spain"}, registered={"en": "France"}
        )
        assert _geoip(db_file, reader).country_name("5.5.5.5") == "Spain"

    def test_country_name_is_unknown_when_no_english_name_exists(self, db_file: Path) -> None:
        reader = _stub_reader()
        reader.country.return_value = _response(country={"de": "Russland"}, registered={})
        assert _geoip(db_file, reader).country_name("5.5.5.5") == UNKNOWN

    def test_address_not_found_is_unknown(self, db_file: Path) -> None:
        reader = _stub_reader()
        reader.country.side_effect = AddressNotFoundError("not in database")
        assert _geoip(db_file, reader).country_name("8.8.8.8") == UNKNOWN

    def test_reader_value_error_is_unknown(self, db_file: Path) -> None:
        reader = _stub_reader()
        reader.country.side_effect = ValueError("IPv6 address in an IPv4-only database")
        assert _geoip(db_file, reader).country_name("2001:db8::1") == UNKNOWN

    @pytest.mark.parametrize(
        "ip",
        ["", "not-an-ip", "999.1.1.1", "1.2.3", "10.0.0.1", "192.168.1.5", "127.0.0.1", "::1"],
    )
    def test_invalid_private_and_loopback_ips_are_unknown_without_calling_the_reader(
        self, db_file: Path, ip: str
    ) -> None:
        reader = _stub_reader()
        assert _geoip(db_file, reader).country_name(ip) == UNKNOWN
        reader.country.assert_not_called()

    def test_second_lookup_of_the_same_ip_is_served_from_the_cache(self, db_file: Path) -> None:
        reader = _stub_reader()
        reader.country.return_value = _response(country={"en": "Russia"})
        geoip = _geoip(db_file, reader)
        assert geoip.country_name("83.149.9.216") == "Russia"
        assert geoip.country_name("83.149.9.216") == "Russia"
        assert reader.country.call_count == 1

    def test_unmapped_ips_are_cached_too(self, db_file: Path) -> None:
        reader = _stub_reader()
        reader.country.side_effect = AddressNotFoundError("not in database")
        geoip = _geoip(db_file, reader)
        assert geoip.country_name("8.8.8.8") == UNKNOWN
        assert geoip.country_name("8.8.8.8") == UNKNOWN
        assert reader.country.call_count == 1

    def test_different_ips_are_looked_up_separately(self, db_file: Path) -> None:
        reader = _stub_reader()
        reader.country.side_effect = [
            _response(country={"en": "Russia"}),
            _response(country={"en": "Germany"}),
        ]
        geoip = _geoip(db_file, reader)
        assert geoip.country_name("83.149.9.216") == "Russia"
        assert geoip.country_name("46.5.6.7") == "Germany"
