"""The lookup-settings file as seen from the CLI: --config, WEBLOGSTATS_CONFIG and the default."""

from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.fakes.fake_geo_ip import FakeGeoIp
from weblogstats import cli
from weblogstats.cli import (
    DEFAULT_CONFIG_PATH,
    USER_AGENT_DEFAULT_CACHE_SIZE,
    main,
    parse_args,
)
from weblogstats.contracts import GeoIpLookup
from weblogstats.lookups import UaParserLookup
from weblogstats.lookups.maxmind_geo_ip import DEFAULT_CACHE_SIZE

ONE_LINE = (
    '1.1.1.1 - - [17/May/2015:10:05:03 +0000] "GET / HTTP/1.1" 200 10 "-" '
    '"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/32.0.1700.107 Safari/537.36"'
)
SIZES = "[lookups.geoip]\ncache_size = 11\n\n[lookups.user_agent]\ncache_size = 22\n"


def _spies(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Records the cache sizes the CLI hands to the two lookups."""
    geoip_sizes: list[int] = []
    ua_kwargs: list[dict[str, int]] = []
    real_ua = UaParserLookup

    def geoip_factory(path: Path, cache_size: int) -> GeoIpLookup:
        geoip_sizes.append(cache_size)
        return FakeGeoIp({"1.1.1.1": "France"})

    def spy_ua(*args: object, **kwargs: int) -> UaParserLookup:
        ua_kwargs.append(kwargs)
        return real_ua(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(cli, "UaParserLookup", spy_ua)
    return SimpleNamespace(
        geoip_sizes=geoip_sizes, ua_kwargs=ua_kwargs, geoip_factory=geoip_factory
    )


def _setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[SimpleNamespace, list[str]]:
    """A one-line log, an isolated cwd and environment, and the spies."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("WEBLOGSTATS_CONFIG", raising=False)
    monkeypatch.delenv("WEBLOGSTATS_ERRORS_FILE", raising=False)
    log = tmp_path / "access.log"
    log.write_text(ONE_LINE + "\n", encoding="utf-8")
    return _spies(monkeypatch), [str(log), "--errors-file", str(tmp_path / "errors.log")]


class TestCliConfig:
    # --- resolution order -------------------------------------------------------------------

    def test_the_flag_is_the_first_choice(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        (tmp_path / "flag.toml").write_text(SIZES, encoding="utf-8")
        (tmp_path / "from-env.toml").write_text(SIZES, encoding="utf-8")
        monkeypatch.setenv("WEBLOGSTATS_CONFIG", "from-env.toml")
        assert parse_args(["a.log", "--config", "flag.toml"]).config_path == Path("flag.toml")

    def test_the_env_var_is_the_second_choice(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        (tmp_path / "config").mkdir()
        (tmp_path / DEFAULT_CONFIG_PATH).write_text(SIZES, encoding="utf-8")
        (tmp_path / "from-env.toml").write_text(SIZES, encoding="utf-8")
        monkeypatch.setenv("WEBLOGSTATS_CONFIG", "from-env.toml")
        assert parse_args(["a.log"]).config_path == Path("from-env.toml")

    def test_the_default_file_is_used_when_it_exists(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("WEBLOGSTATS_CONFIG", raising=False)
        (tmp_path / "config").mkdir()
        (tmp_path / DEFAULT_CONFIG_PATH).write_text(SIZES, encoding="utf-8")
        assert (
            parse_args(["a.log"]).config_path
            == DEFAULT_CONFIG_PATH
            == Path("config/weblogstats.toml")
        )

    def test_there_is_no_config_when_nothing_is_given_and_no_default_exists(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("WEBLOGSTATS_CONFIG", raising=False)
        assert parse_args(["a.log"]).config_path is None

    def test_an_empty_env_var_is_ignored(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("WEBLOGSTATS_CONFIG", "")
        assert parse_args(["a.log"]).config_path is None

    # --- sizes reach the lookups ------------------------------------------------------------

    def test_the_config_flag_sets_both_cache_sizes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        spies, argv = _setup(tmp_path, monkeypatch)
        (tmp_path / "my.toml").write_text(SIZES, encoding="utf-8")
        assert (
            main([*argv, "--config", str(tmp_path / "my.toml")], geoip_factory=spies.geoip_factory)
            == 0
        )
        assert spies.geoip_sizes == [11]
        assert spies.ua_kwargs == [{"cache_size": 22}]

    def test_the_env_var_sets_both_cache_sizes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        spies, argv = _setup(tmp_path, monkeypatch)
        (tmp_path / "env.toml").write_text(SIZES, encoding="utf-8")
        monkeypatch.setenv("WEBLOGSTATS_CONFIG", str(tmp_path / "env.toml"))
        assert main(argv, geoip_factory=spies.geoip_factory) == 0
        assert spies.geoip_sizes == [11]
        assert spies.ua_kwargs == [{"cache_size": 22}]

    def test_the_default_file_in_the_current_directory_is_honoured(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        spies, argv = _setup(tmp_path, monkeypatch)
        (tmp_path / "config").mkdir()
        (tmp_path / DEFAULT_CONFIG_PATH).write_text(SIZES, encoding="utf-8")
        assert main(argv, geoip_factory=spies.geoip_factory) == 0
        assert spies.geoip_sizes == [11]
        assert spies.ua_kwargs == [{"cache_size": 22}]

    def test_a_lookup_missing_from_the_file_keeps_its_own_default(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        spies, argv = _setup(tmp_path, monkeypatch)
        (tmp_path / "my.toml").write_text("[lookups.geoip]\ncache_size = 11\n", encoding="utf-8")
        assert (
            main([*argv, "--config", str(tmp_path / "my.toml")], geoip_factory=spies.geoip_factory)
            == 0
        )
        assert spies.geoip_sizes == [11]
        assert spies.ua_kwargs == [{"cache_size": USER_AGENT_DEFAULT_CACHE_SIZE}]

    def test_no_config_anywhere_keeps_the_lookup_defaults(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        spies, argv = _setup(tmp_path, monkeypatch)
        assert main(argv, geoip_factory=spies.geoip_factory) == 0
        assert spies.geoip_sizes == [DEFAULT_CACHE_SIZE]
        assert spies.ua_kwargs == [{"cache_size": USER_AGENT_DEFAULT_CACHE_SIZE}]

    def test_the_ua_default_matches_the_lookups_own_default(self) -> None:
        parameter = inspect.signature(UaParserLookup).parameters["cache_size"]
        assert USER_AGENT_DEFAULT_CACHE_SIZE == parameter.default

    # --- explicit but unusable config -------------------------------------------------------

    @pytest.mark.parametrize(
        ("content", "message"),
        [
            (None, "config file not found"),
            ("[lookups.geoip\n", "invalid TOML"),
            ("[lookups.geoip]\ncache_size = 0\n", "lookups.geoip.cache_size"),
            ("[lookups.geoip]\ncachesize = 5\n", "lookups.geoip.cachesize"),
        ],
    )
    @pytest.mark.parametrize("via", ["flag", "env"])
    def test_an_explicit_unusable_config_exits_1_and_touches_nothing(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        content: str | None,
        message: str,
        via: str,
    ) -> None:
        spies, argv = _setup(tmp_path, monkeypatch)
        config = tmp_path / "bad.toml"
        if content is not None:
            config.write_text(content, encoding="utf-8")
        errors = tmp_path / "errors.log"
        errors.write_text("entry from the previous run\n", encoding="utf-8")
        if via == "flag":
            argv = [*argv, "--config", str(config)]
        else:
            monkeypatch.setenv("WEBLOGSTATS_CONFIG", str(config))
        assert main(argv, geoip_factory=spies.geoip_factory) == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert message in captured.err
        assert str(config) in captured.err
        assert errors.read_text(encoding="utf-8") == "entry from the previous run\n"
        assert spies.geoip_sizes == []

    def test_an_invalid_default_file_also_exits_1(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        spies, argv = _setup(tmp_path, monkeypatch)
        (tmp_path / "config").mkdir()
        (tmp_path / DEFAULT_CONFIG_PATH).write_text("[lookups.geoip]\ncache_size = -1\n")
        assert main(argv, geoip_factory=spies.geoip_factory) == 1

    def test_help_lists_the_config_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit):
            main(["--help"])
        assert "--config" in capsys.readouterr().out
