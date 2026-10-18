from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from weblogstats.contracts import AppConfig


class TestAppConfig:
    def test_defaults(self) -> None:
        config = AppConfig(log_path=Path("a.log"), geoip_path=Path("g.mmdb"))
        assert config.output_format == "text"
        assert config.other_below is None

    def test_explicit_values(self) -> None:
        config = AppConfig(
            log_path=Path("a.log"),
            geoip_path=Path("g.mmdb"),
            output_format="text",
            other_below=1.5,
        )
        assert config.other_below == 1.5
        assert config.log_path == Path("a.log")
        assert config.geoip_path == Path("g.mmdb")

    def test_is_frozen(self) -> None:
        config = AppConfig(log_path=Path("a.log"), geoip_path=Path("g.mmdb"))
        with pytest.raises(dataclasses.FrozenInstanceError):
            config.output_format = "json"  # type: ignore[misc]

    def test_errors_file_defaults_to_the_current_directory(self) -> None:
        config = AppConfig(log_path=Path("a.log"), geoip_path=Path("g.mmdb"))
        assert config.errors_file == Path("weblogstats-errors.log")

    def test_config_path_defaults_to_none(self) -> None:
        assert AppConfig(log_path=Path("a.log"), geoip_path=Path("g.mmdb")).config_path is None

    def test_errors_file_and_config_path_can_be_set(self) -> None:
        config = AppConfig(
            log_path=Path("a.log"),
            geoip_path=Path("g.mmdb"),
            errors_file=Path("bad.log"),
            config_path=Path("w.toml"),
        )
        assert (config.errors_file, config.config_path) == (Path("bad.log"), Path("w.toml"))
