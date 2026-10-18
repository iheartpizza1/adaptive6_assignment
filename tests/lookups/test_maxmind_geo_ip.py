"""MaxMindGeoIp: unit tests use a stub reader; data tests use the real GeoLite2-Country MMDB."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from weblogstats.lookups.maxmind_geo_ip import MaxMindGeoIp


def _stub_reader(database_type: str = "GeoLite2-Country") -> Mock:
    reader = Mock()
    reader.metadata.return_value = SimpleNamespace(database_type=database_type)
    return reader


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
