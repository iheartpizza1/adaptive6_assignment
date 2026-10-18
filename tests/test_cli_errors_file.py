"""Where the errors file goes: --errors-file > WEBLOGSTATS_ERRORS_FILE > config > default."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.fakes.fake_geo_ip import FakeGeoIp
from weblogstats.cli import main, parse_args
from weblogstats.contracts import GeoIpLookup

PARTIAL = '2.2.2.2 - - [17/May/2015:10:05:03 +0000] "GET / HTTP/1.1" 200 10 "-" "Mozilla/5.0 (Chr'
ENV_VAR = "WEBLOGSTATS_ERRORS_FILE"


def _geoip(path: Path, cache_size: int) -> GeoIpLookup:
    return FakeGeoIp({})


@pytest.fixture
def workdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An empty cwd with no config file and none of the env vars set."""
    monkeypatch.chdir(tmp_path)
    for name in (ENV_VAR, "WEBLOGSTATS_CONFIG"):
        monkeypatch.delenv(name, raising=False)
    (tmp_path / "access.log").write_text(PARTIAL + "\n", encoding="utf-8")
    return tmp_path


def _config(workdir: Path, errors_file: str) -> Path:
    path = workdir / "w.toml"
    path.write_text(f'[output]\nerrors_file = "{errors_file}"\n', encoding="utf-8")
    return path


def _only_entry(path: Path) -> str:
    (entry,) = path.read_text(encoding="utf-8").splitlines()
    return entry


class TestCliErrorsFile:
    def test_the_default_when_nothing_sets_it(self, workdir: Path) -> None:
        assert parse_args(["access.log"]).errors_file == Path("weblogstats-errors.log")
        assert main(["access.log"], geoip_factory=_geoip) == 0
        assert "WARN partial" in _only_entry(workdir / "weblogstats-errors.log")

    def test_the_config_file_beats_the_default(self, workdir: Path) -> None:
        config = _config(workdir, "from-config.log")
        argv = ["access.log", "--config", str(config)]
        assert parse_args(argv).errors_file == Path("from-config.log")
        assert main(argv, geoip_factory=_geoip) == 0
        assert "WARN partial" in _only_entry(workdir / "from-config.log")
        assert not (workdir / "weblogstats-errors.log").exists()

    def test_the_default_config_file_is_honoured_too(self, workdir: Path) -> None:
        (workdir / "config").mkdir()
        (workdir / "config" / "weblogstats.toml").write_text(
            '[output]\nerrors_file = "from-default-config.log"\n', encoding="utf-8"
        )
        assert main(["access.log"], geoip_factory=_geoip) == 0
        assert "WARN partial" in _only_entry(workdir / "from-default-config.log")

    def test_the_env_var_beats_the_config_file(
        self, workdir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        config = _config(workdir, "from-config.log")
        monkeypatch.setenv(ENV_VAR, "from-env.log")
        argv = ["access.log", "--config", str(config)]
        assert parse_args(argv).errors_file == Path("from-env.log")
        assert main(argv, geoip_factory=_geoip) == 0
        assert "WARN partial" in _only_entry(workdir / "from-env.log")
        assert not (workdir / "from-config.log").exists()

    def test_the_flag_beats_the_env_var_and_the_config_file(
        self, workdir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        config = _config(workdir, "from-config.log")
        monkeypatch.setenv(ENV_VAR, "from-env.log")
        argv = ["access.log", "--config", str(config), "--errors-file", "from-flag.log"]
        assert parse_args(argv).errors_file == Path("from-flag.log")
        assert main(argv, geoip_factory=_geoip) == 0
        assert "WARN partial" in _only_entry(workdir / "from-flag.log")
        assert not (workdir / "from-env.log").exists()
        assert not (workdir / "from-config.log").exists()

    def test_an_empty_env_var_is_ignored(
        self, workdir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(ENV_VAR, "")
        assert parse_args(["access.log"]).errors_file == Path("weblogstats-errors.log")

    def test_the_stderr_line_names_the_resolved_path(
        self,
        workdir: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setenv(ENV_VAR, "from-env.log")
        assert main(["access.log"], geoip_factory=_geoip) == 0
        assert capsys.readouterr().err.splitlines()[1] == (
            "bad lines: 1 warn, 0 error → from-env.log"
        )

    def test_an_invalid_output_table_exits_1_and_touches_nothing(
        self, workdir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        config = workdir / "w.toml"
        config.write_text("[output]\nerrors_file = 3\n", encoding="utf-8")
        previous = workdir / "weblogstats-errors.log"
        previous.write_text("entry from the previous run\n", encoding="utf-8")
        assert main(["access.log", "--config", str(config)], geoip_factory=_geoip) == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "output.errors_file" in captured.err
        assert previous.read_text(encoding="utf-8") == "entry from the previous run\n"
