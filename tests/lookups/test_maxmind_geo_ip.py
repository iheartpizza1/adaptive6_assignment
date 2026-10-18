"""MaxMindGeoIp: unit tests use a stub reader; data tests use the real GeoLite2-Country MMDB."""

from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from geoip2.errors import AddressNotFoundError  # the adapter's own test may name geoip2 errors

from weblogstats.contracts import UNKNOWN
from weblogstats.lookups import maxmind_geo_ip
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

    def test_default_cache_size_is_twice_the_logs_unique_ips(self) -> None:
        assert maxmind_geo_ip.DEFAULT_CACHE_SIZE == 2 * 1753 == 3506
        default = inspect.signature(MaxMindGeoIp).parameters["cache_size"].default
        assert default == maxmind_geo_ip.DEFAULT_CACHE_SIZE

    def test_least_recently_used_ip_is_evicted_when_the_cache_is_full(self, db_file: Path) -> None:
        reader = _stub_reader()
        reader.country.return_value = _response(country={"en": "Russia"})
        geoip = MaxMindGeoIp(db_file, reader_factory=Mock(return_value=reader), cache_size=2)
        a, b, c = "8.8.8.8", "1.1.1.1", "9.9.9.9"
        for ip in (a, b, a, c):  # the second A refreshes A, so B is now least recently used
            geoip.country_name(ip)
        assert reader.country.call_count == 3
        geoip.country_name(a)  # still cached
        assert reader.country.call_count == 3
        geoip.country_name(b)  # was evicted
        assert reader.country.call_count == 4

    @pytest.mark.parametrize("cache_size", [0, -1])
    def test_cache_size_below_one_raises_value_error(self, db_file: Path, cache_size: int) -> None:
        factory = Mock(return_value=_stub_reader())
        with pytest.raises(ValueError, match="cache_size"):
            MaxMindGeoIp(db_file, reader_factory=factory, cache_size=cache_size)
        factory.assert_not_called()

    def test_instances_do_not_share_a_cache(self, db_file: Path) -> None:
        first_reader, second_reader = _stub_reader(), _stub_reader()
        first_reader.country.return_value = _response(country={"en": "Russia"})
        second_reader.country.return_value = _response(country={"en": "Germany"})
        first = _geoip(db_file, first_reader)
        second = _geoip(db_file, second_reader)
        assert first.country_name("8.8.8.8") == "Russia"
        assert second.country_name("8.8.8.8") == "Germany"
        assert first_reader.country.call_count == 1
        assert second_reader.country.call_count == 1

    def test_close_closes_the_reader(self, db_file: Path) -> None:
        reader = _stub_reader()
        _geoip(db_file, reader).close()
        reader.close.assert_called_once()

    def test_context_manager_returns_itself_and_closes_on_exit(self, db_file: Path) -> None:
        reader = _stub_reader()
        geoip = _geoip(db_file, reader)
        with geoip as entered:
            assert entered is geoip
            reader.close.assert_not_called()
        reader.close.assert_called_once()

    def test_context_manager_closes_when_the_body_raises(self, db_file: Path) -> None:
        reader = _stub_reader()
        with pytest.raises(RuntimeError), _geoip(db_file, reader):
            raise RuntimeError("boom")
        reader.close.assert_called_once()

    @pytest.mark.data
    def test_real_db_resolves_the_first_fixture_ip_to_a_country(self, geoip_db_path: Path) -> None:
        with MaxMindGeoIp(geoip_db_path) as geoip:
            country = geoip.country_name("83.149.9.216")
        assert country
        assert country != UNKNOWN

    @pytest.mark.data
    def test_real_db_resolves_google_dns_to_united_states(self, geoip_db_path: Path) -> None:
        with MaxMindGeoIp(geoip_db_path) as geoip:
            assert geoip.country_name("8.8.8.8") == "United States"

    @pytest.mark.data
    def test_real_db_gives_unknown_for_private_and_empty_ips(self, geoip_db_path: Path) -> None:
        with MaxMindGeoIp(geoip_db_path) as geoip:
            assert geoip.country_name("10.0.0.1") == UNKNOWN
            assert geoip.country_name("") == UNKNOWN

    @pytest.mark.data
    def test_real_log_has_under_two_percent_unknown_countries(
        self, geoip_db_path: Path, apache_log_path: Path
    ) -> None:
        with apache_log_path.open(encoding="utf-8", errors="replace") as handle:
            ips = {line.split(" ", 1)[0] for line in handle if line.strip()}
        with MaxMindGeoIp(geoip_db_path) as geoip:
            unknown = sum(1 for ip in ips if geoip.country_name(ip) == UNKNOWN)
        assert len(ips) > 1000
        assert unknown / len(ips) < 0.02

    def test_different_ips_are_looked_up_separately(self, db_file: Path) -> None:
        reader = _stub_reader()
        reader.country.side_effect = [
            _response(country={"en": "Russia"}),
            _response(country={"en": "Germany"}),
        ]
        geoip = _geoip(db_file, reader)
        assert geoip.country_name("83.149.9.216") == "Russia"
        assert geoip.country_name("46.5.6.7") == "Germany"
