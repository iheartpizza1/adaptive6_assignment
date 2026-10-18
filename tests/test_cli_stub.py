from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from weblogstats.cli import DEFAULT_GEOIP_PATH, main, parse_args
from weblogstats.contracts import AppConfig


class TestCliStub:
    def test_main_reports_pipeline_not_wired_and_returns_2(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert main(["access.log"]) == 2
        captured = capsys.readouterr()
        assert "pipeline not wired" in captured.err
        assert captured.out == ""

    def test_main_accepts_all_flags(self) -> None:
        argv = ["access.log", "--geoip", "g.mmdb", "--format", "text", "--other-below", "1.5"]
        assert main(argv) == 2

    def test_parse_args_builds_an_app_config(self) -> None:
        config = parse_args(
            ["access.log", "--geoip", "g.mmdb", "--format", "text", "--other-below", "1.5"]
        )
        assert config == AppConfig(
            log_path=Path("access.log"),
            geoip_path=Path("g.mmdb"),
            output_format="text",
            other_below=1.5,
        )

    def test_parse_args_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GEOIP_DB", raising=False)
        config = parse_args(["access.log"])
        assert config.output_format == "text"
        assert config.other_below is None
        assert config.geoip_path == DEFAULT_GEOIP_PATH == Path("data/GeoLite2-Country.mmdb")

    def test_geoip_defaults_to_the_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GEOIP_DB", "from-env.mmdb")
        assert parse_args(["access.log"]).geoip_path == Path("from-env.mmdb")

    def test_geoip_flag_beats_the_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GEOIP_DB", "from-env.mmdb")
        assert parse_args(["a.log", "--geoip", "flag.mmdb"]).geoip_path == Path("flag.mmdb")

    def test_missing_log_argument_is_a_usage_error(self) -> None:
        with pytest.raises(SystemExit) as exc:
            main([])
        assert exc.value.code == 2

    def test_unsupported_format_is_a_usage_error(self) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["access.log", "--format", "xml"])
        assert exc.value.code == 2

    def test_non_numeric_other_below_is_a_usage_error(self) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["access.log", "--other-below", "lots"])
        assert exc.value.code == 2

    def test_help_exits_zero_and_lists_the_flags(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["--help"])
        assert exc.value.code == 0
        out = capsys.readouterr().out
        for flag in ("log", "--geoip", "--format", "--other-below"):
            assert flag in out

    def test_python_dash_m_help_exits_zero(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "weblogstats", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "--geoip" in result.stdout
