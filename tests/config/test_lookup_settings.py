"""LookupSettings: the TOML loader and its validation."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from weblogstats.config import LookupSettings


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "weblogstats.toml"
    path.write_text(text, encoding="utf-8")
    return path


class TestLookupSettings:
    def test_defaults_use_the_callers_default(self) -> None:
        assert LookupSettings.defaults().cache_size("geoip", 99) == 99

    def test_loads_a_valid_file(self, tmp_path: Path) -> None:
        path = _write(
            tmp_path,
            "[lookups.geoip]\ncache_size = 10\n\n[lookups.user_agent]\ncache_size = 20  # note\n",
        )
        settings = LookupSettings.load(path)
        assert settings.cache_size("geoip", 99) == 10
        assert settings.cache_size("user_agent", 99) == 20

    def test_a_lookup_missing_from_the_file_uses_the_default(self, tmp_path: Path) -> None:
        settings = LookupSettings.load(_write(tmp_path, "[lookups.geoip]\ncache_size = 10\n"))
        assert settings.cache_size("user_agent", 99) == 99

    def test_a_lookup_table_without_cache_size_uses_the_default(self, tmp_path: Path) -> None:
        settings = LookupSettings.load(_write(tmp_path, "[lookups.geoip]\n"))
        assert settings.cache_size("geoip", 99) == 99

    def test_an_empty_file_is_all_defaults(self, tmp_path: Path) -> None:
        assert LookupSettings.load(_write(tmp_path, "")).cache_size("geoip", 99) == 99

    def test_an_unknown_lookup_name_is_tolerated(self, tmp_path: Path) -> None:
        settings = LookupSettings.load(_write(tmp_path, "[lookups.future]\ncache_size = 5\n"))
        assert settings.cache_size("future", 99) == 5
        assert settings.cache_size("geoip", 99) == 99

    @pytest.mark.parametrize("value", ["0", "-1", '"10"', "true", "1.5", "[1]"])
    def test_a_bad_cache_size_is_rejected_naming_the_file_and_key(
        self, tmp_path: Path, value: str
    ) -> None:
        path = _write(tmp_path, f"[lookups.geoip]\ncache_size = {value}\n")
        with pytest.raises(ValueError) as error:
            LookupSettings.load(path)
        assert str(path) in str(error.value)
        assert "lookups.geoip.cache_size" in str(error.value)

    def test_an_unknown_key_in_a_lookup_table_is_rejected(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "[lookups.geoip]\ncahce_size = 10\n")
        with pytest.raises(ValueError) as error:
            LookupSettings.load(path)
        assert str(path) in str(error.value)
        assert "lookups.geoip.cahce_size" in str(error.value)

    def test_a_lookup_that_is_not_a_table_is_rejected(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "[lookups]\ngeoip = 10\n")
        with pytest.raises(ValueError) as error:
            LookupSettings.load(path)
        assert str(path) in str(error.value)
        assert "lookups.geoip" in str(error.value)

    def test_lookups_that_is_not_a_table_is_rejected(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "lookups = 3\n")
        with pytest.raises(ValueError, match="lookups"):
            LookupSettings.load(path)

    def test_invalid_toml_is_a_value_error_naming_the_file(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "[lookups.geoip\ncache_size = \n")
        with pytest.raises(ValueError) as error:
            LookupSettings.load(path)
        assert str(path) in str(error.value)

    def test_a_missing_file_is_file_not_found_naming_the_path(self, tmp_path: Path) -> None:
        missing = tmp_path / "nope.toml"
        with pytest.raises(FileNotFoundError, match="nope.toml"):
            LookupSettings.load(missing)

    def test_the_settings_are_immutable(self) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            LookupSettings.defaults().lookups = {}  # type: ignore[misc]

    def test_the_shipped_config_file_loads_with_the_documented_sizes(self) -> None:
        shipped = Path(__file__).resolve().parents[2] / "config" / "weblogstats.toml"
        settings = LookupSettings.load(shipped)
        assert settings.cache_size("geoip", 0) == 3506
        assert settings.cache_size("user_agent", 0) == 1116
