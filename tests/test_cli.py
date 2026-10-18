"""cli.main: argument parsing, composition, exit codes, --other-below and the errors file."""

from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tests.fakes.fake_geo_ip import FakeGeoIp
from weblogstats.cli import DEFAULT_ERRORS_FILE, DEFAULT_GEOIP_PATH, main, parse_args
from weblogstats.contracts import AppConfig, GeoIpLookup

ONE_LINE = (
    '1.1.1.1 - - [17/May/2015:10:05:03 +0000] "GET / HTTP/1.1" 200 10 "-" '
    '"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/32.0.1700.107 Safari/537.36"'
)
PARTIAL = '2.2.2.2 - - [17/May/2015:10:05:03 +0000] "GET / HTTP/1.1" 200 10 "-" "Mozilla/5.0 (Chr'
GARBAGE = "this is not a log line"


def _geoip(path: Path) -> GeoIpLookup:
    return FakeGeoIp({"1.1.1.1": "France", "2.2.2.2": "Spain"})


def _write_log(tmp_path: Path, *lines: str) -> Path:
    log = tmp_path / "access.log"
    log.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return log


class TestCli:
    # --- argument parsing -------------------------------------------------------------------

    def test_parse_args_builds_an_app_config_and_the_errors_file(self) -> None:
        config, errors_file = parse_args(
            [
                "access.log",
                "--geoip",
                "g.mmdb",
                "--format",
                "text",
                "--other-below",
                "1.5",
                "--errors-file",
                "bad.log",
            ]
        )
        assert config == AppConfig(
            log_path=Path("access.log"),
            geoip_path=Path("g.mmdb"),
            output_format="text",
            other_below=1.5,
        )
        assert errors_file == Path("bad.log")

    def test_parse_args_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GEOIP_DB", raising=False)
        config, errors_file = parse_args(["access.log"])
        assert config.output_format == "text"
        assert config.other_below is None
        assert config.geoip_path == DEFAULT_GEOIP_PATH == Path("data/GeoLite2-Country.mmdb")
        assert errors_file == DEFAULT_ERRORS_FILE == Path("weblogstats-errors.log")

    def test_geoip_defaults_to_the_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GEOIP_DB", "from-env.mmdb")
        assert parse_args(["access.log"])[0].geoip_path == Path("from-env.mmdb")

    def test_geoip_flag_beats_the_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GEOIP_DB", "from-env.mmdb")
        assert parse_args(["a.log", "--geoip", "flag.mmdb"])[0].geoip_path == Path("flag.mmdb")

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
        for flag in ("log", "--geoip", "--format", "--other-below", "--errors-file"):
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

    # --- composition ------------------------------------------------------------------------

    def test_success_prints_the_report_to_stdout_and_the_summary_to_stderr(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        log = _write_log(tmp_path, ONE_LINE)
        errors = tmp_path / "errors.log"
        argv = [str(log), "--geoip", "unused.mmdb", "--errors-file", str(errors)]
        assert main(argv, geoip_factory=_geoip) == 0
        captured = capsys.readouterr()
        assert captured.out == (
            "Country:\nFrance 100.00%\n\nOS:\nWindows 100.00%\n\nBrowser:\nChrome 100.00%\n"
        )
        assert captured.err.splitlines()[0] == "total=1 strict=1 partial=0 unreadable=0"

    def test_the_geoip_factory_receives_the_geoip_path(self, tmp_path: Path) -> None:
        seen: list[Path] = []

        def factory(path: Path) -> GeoIpLookup:
            seen.append(path)
            return _geoip(path)

        log = _write_log(tmp_path, ONE_LINE)
        errors = tmp_path / "errors.log"
        main([str(log), "--geoip", "the.mmdb", "--errors-file", str(errors)], geoip_factory=factory)
        assert seen == [Path("the.mmdb")]

    def test_a_closeable_geoip_is_closed_after_the_run(self, tmp_path: Path) -> None:
        geoip = MagicMock()
        geoip.__enter__.return_value = geoip
        geoip.country_name.return_value = "France"
        log = _write_log(tmp_path, ONE_LINE)
        errors = tmp_path / "errors.log"
        main([str(log), "--errors-file", str(errors)], geoip_factory=lambda path: geoip)
        geoip.__enter__.assert_called_once()
        geoip.__exit__.assert_called_once()
        geoip.country_name.assert_called_once_with("1.1.1.1")

    def test_output_is_utf8_even_when_the_streams_default_to_another_encoding(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        out_bytes, err_bytes = io.BytesIO(), io.BytesIO()
        out = io.TextIOWrapper(out_bytes, encoding="cp1252", newline="\n")
        err = io.TextIOWrapper(err_bytes, encoding="cp1252", newline="\n")
        monkeypatch.setattr(sys, "stdout", out)
        monkeypatch.setattr(sys, "stderr", err)
        log = _write_log(tmp_path, ONE_LINE)
        errors = tmp_path / "errors.log"
        argv = [str(log), "--errors-file", str(errors)]
        assert main(argv, geoip_factory=lambda path: FakeGeoIp({"1.1.1.1": "Сай"})) == 0
        out.flush()
        err.flush()
        assert "Сай 100.00%" in out_bytes.getvalue().decode("utf-8")
        assert f" → {errors}" in err_bytes.getvalue().decode("utf-8")

    # --- exit codes -------------------------------------------------------------------------

    def test_missing_log_exits_1_with_a_message_and_no_report(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        missing = tmp_path / "nope.log"
        errors = tmp_path / "errors.log"
        argv = [str(missing), "--errors-file", str(errors)]
        assert main(argv, geoip_factory=_geoip) == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "log file not found" in captured.err
        assert str(missing) in captured.err
        assert not errors.exists()

    def test_missing_mmdb_exits_1_with_a_message_and_no_report(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        log = _write_log(tmp_path, ONE_LINE)
        missing = tmp_path / "missing.mmdb"
        errors = tmp_path / "errors.log"
        argv = [str(log), "--geoip", str(missing), "--errors-file", str(errors)]
        assert main(argv) == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "GeoIP database not found" in captured.err
        assert not errors.exists()

    def test_wrong_database_edition_exits_1_with_the_message(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        def asn_factory(path: Path) -> GeoIpLookup:
            raise ValueError("x.mmdb is a 'GeoLite2-ASN' database. The Country edition is required")

        log = _write_log(tmp_path, ONE_LINE)
        errors = tmp_path / "errors.log"
        argv = [str(log), "--errors-file", str(errors)]
        assert main(argv, geoip_factory=asn_factory) == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "GeoLite2-ASN" in captured.err
        assert not errors.exists()

    def test_a_file_that_is_not_an_mmdb_exits_1(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        log = _write_log(tmp_path, ONE_LINE)
        fake_db = tmp_path / "fake.mmdb"
        fake_db.write_text("not a database", encoding="utf-8")
        errors = tmp_path / "errors.log"
        argv = [str(log), "--geoip", str(fake_db), "--errors-file", str(errors)]
        assert main(argv) == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "fake.mmdb" in captured.err

    def test_an_unwritable_errors_file_exits_1(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        log = _write_log(tmp_path, ONE_LINE)
        argv = [str(log), "--errors-file", str(tmp_path / "no-such-dir" / "errors.log")]
        assert main(argv, geoip_factory=_geoip) == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "errors.log" in captured.err

    # --- --other-below ----------------------------------------------------------------------

    def test_other_below_rolls_small_rows_into_other(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        log = _write_log(tmp_path, ONE_LINE, ONE_LINE, ONE_LINE, PARTIAL)
        errors = tmp_path / "errors.log"
        argv = [str(log), "--other-below", "30", "--errors-file", str(errors)]
        assert main(argv, geoip_factory=_geoip) == 0
        out = capsys.readouterr().out
        assert out.startswith("Country:\nFrance 75.00%\nOther 25.00%\n")

    def test_without_other_below_there_is_no_other_row(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        log = _write_log(tmp_path, ONE_LINE, ONE_LINE, ONE_LINE, PARTIAL)
        errors = tmp_path / "errors.log"
        assert main([str(log), "--errors-file", str(errors)], geoip_factory=_geoip) == 0
        out = capsys.readouterr().out
        assert "Other" not in out
        assert out.startswith("Country:\nFrance 75.00%\nSpain 25.00%\n")

    # --- the errors file --------------------------------------------------------------------

    def test_partial_and_unreadable_lines_are_written_to_the_errors_file(
        self, tmp_path: Path
    ) -> None:
        log = _write_log(tmp_path, ONE_LINE, PARTIAL, GARBAGE)
        errors = tmp_path / "errors.log"
        main([str(log), "--errors-file", str(errors)], geoip_factory=_geoip)
        warn, error = errors.read_text(encoding="utf-8").splitlines()
        assert warn.endswith(f"Z WARN partial {PARTIAL}")
        assert error.endswith(f"Z ERROR unreadable {GARBAGE}")

    def test_a_clean_run_leaves_an_empty_errors_file(self, tmp_path: Path) -> None:
        log = _write_log(tmp_path, ONE_LINE)
        errors = tmp_path / "errors.log"
        errors.write_text("stale entry from an earlier run\n", encoding="utf-8")
        main([str(log), "--errors-file", str(errors)], geoip_factory=_geoip)
        assert errors.read_text(encoding="utf-8") == ""

    def test_stderr_has_a_bad_lines_line_after_the_summary(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        log = _write_log(tmp_path, ONE_LINE, PARTIAL, GARBAGE)
        errors = tmp_path / "errors.log"
        main([str(log), "--errors-file", str(errors)], geoip_factory=_geoip)
        lines = capsys.readouterr().err.splitlines()
        assert lines == [
            "total=3 strict=1 partial=1 unreadable=1",
            f"bad lines: 1 warn, 1 error → {errors}",
        ]

    def test_the_errors_file_defaults_to_the_current_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        log = _write_log(tmp_path, ONE_LINE, PARTIAL)
        monkeypatch.chdir(tmp_path)
        main([str(log)], geoip_factory=_geoip)
        assert (tmp_path / "weblogstats-errors.log").read_text(encoding="utf-8").count("\n") == 1

    def test_a_failed_start_leaves_an_existing_errors_file_untouched(self, tmp_path: Path) -> None:
        errors = tmp_path / "errors.log"
        errors.write_text("entry from the previous run\n", encoding="utf-8")
        argv = [str(tmp_path / "nope.log"), "--errors-file", str(errors)]
        assert main(argv, geoip_factory=_geoip) == 1
        assert errors.read_text(encoding="utf-8") == "entry from the previous run\n"

    def test_a_bad_mmdb_leaves_an_existing_errors_file_untouched(self, tmp_path: Path) -> None:
        log = _write_log(tmp_path, ONE_LINE)
        errors = tmp_path / "errors.log"
        errors.write_text("entry from the previous run\n", encoding="utf-8")
        argv = [str(log), "--geoip", str(tmp_path / "missing.mmdb"), "--errors-file", str(errors)]
        assert main(argv) == 1
        assert errors.read_text(encoding="utf-8") == "entry from the previous run\n"
