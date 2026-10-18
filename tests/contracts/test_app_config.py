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
