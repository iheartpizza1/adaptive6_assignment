"""The data-path fixtures in conftest: env var first, repo default second, otherwise skip."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import _data_path


class TestDataPaths:
    def test_env_var_wins_over_default(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from_env = tmp_path / "env.txt"
        from_env.write_text("x")
        default = tmp_path / "default.txt"
        default.write_text("y")
        monkeypatch.setenv("SOME_VAR", str(from_env))
        assert _data_path("SOME_VAR", default, "thing") == from_env

    def test_default_used_when_env_unset(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        default = tmp_path / "default.txt"
        default.write_text("y")
        monkeypatch.delenv("SOME_VAR", raising=False)
        assert _data_path("SOME_VAR", default, "thing") == default

    def test_default_used_when_env_points_to_missing_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        default = tmp_path / "default.txt"
        default.write_text("y")
        monkeypatch.setenv("SOME_VAR", str(tmp_path / "nope.txt"))
        assert _data_path("SOME_VAR", default, "thing") == default

    def test_skips_when_nothing_exists(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("SOME_VAR", raising=False)
        with pytest.raises(pytest.skip.Exception):
            _data_path("SOME_VAR", tmp_path / "missing.txt", "thing")

    @pytest.mark.data
    def test_real_apache_log_is_10000_lines(self, apache_log_path: Path) -> None:
        with apache_log_path.open(encoding="utf-8", errors="replace") as handle:
            assert sum(1 for _ in handle) == 10_000

    @pytest.mark.data
    def test_real_geoip_db_is_a_country_edition(self, geoip_db_path: Path) -> None:
        assert geoip_db_path.suffix == ".mmdb"
        assert geoip_db_path.stat().st_size > 0
