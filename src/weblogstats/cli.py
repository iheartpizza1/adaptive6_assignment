"""Command-line entry point and composition root. No parsing or percentage logic lives here."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable
from contextlib import AbstractContextManager, ExitStack
from pathlib import Path

from weblogstats.aggregation import CountingAggregator
from weblogstats.config import LookupSettings, OutputSettings
from weblogstats.contracts import AppConfig, Dimension, GeoIpLookup, ReportFormatter
from weblogstats.dimensions import BrowserDimension, CountryDimension, OsDimension
from weblogstats.formatting import TextReportFormatter
from weblogstats.lookups import LabelNormalizer, MaxMindGeoIp, UaParserLookup
from weblogstats.lookups.maxmind_geo_ip import DEFAULT_CACHE_SIZE as GEOIP_DEFAULT_CACHE_SIZE
from weblogstats.lookups.ua_parser_lookup import (
    DEFAULT_CACHE_SIZE as USER_AGENT_DEFAULT_CACHE_SIZE,
)
from weblogstats.parsing import ApacheCombinedParser, BadLineLog, LoggingParser
from weblogstats.pipeline import Pipeline
from weblogstats.sources import FileLogSource

DEFAULT_GEOIP_PATH = Path("data/GeoLite2-Country.mmdb")
DEFAULT_ERRORS_FILE = Path("weblogstats-errors.log")
DEFAULT_CONFIG_PATH = Path("config/weblogstats.toml")
CONFIG_ENV_VAR = "WEBLOGSTATS_CONFIG"
ERRORS_FILE_ENV_VAR = "WEBLOGSTATS_ERRORS_FILE"

# The names of the [lookups.<name>] tables in the config file.
GEOIP_LOOKUP = "geoip"
USER_AGENT_LOOKUP = "user_agent"

# One entry per --format choice; a new ReportFormatter is registered here.
_FORMATTERS: dict[str, Callable[[], ReportFormatter]] = {"text": TextReportFormatter}
OUTPUT_FORMATS = tuple(_FORMATTERS)

# (MMDB path, cache size) -> lookup. Tests inject a fake here.
GeoIpFactory = Callable[[Path, int], GeoIpLookup]


def _open_maxmind(path: Path, cache_size: int) -> GeoIpLookup:
    return MaxMindGeoIp(path, cache_size=cache_size)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="weblogstats",
        description="Report request share by Country, OS and Browser from an Apache log.",
    )
    parser.add_argument("log", type=Path, help="path to an Apache combined-format log file")
    parser.add_argument(
        "--geoip",
        type=Path,
        default=Path(os.environ.get("GEOIP_DB") or DEFAULT_GEOIP_PATH),
        help="path to GeoLite2-Country.mmdb (default: $GEOIP_DB, else %(default)s)",
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=OUTPUT_FORMATS,
        default="text",
        help="output format (default: %(default)s)",
    )
    parser.add_argument(
        "--other-below",
        type=float,
        default=None,
        metavar="FLOAT",
        help="roll rows below this percentage into an Other row",
    )
    parser.add_argument(
        "--errors-file",
        type=Path,
        default=None,
        metavar="PATH",
        help="where partial and unreadable lines are logged; truncated on every run "
        f"(default: ${ERRORS_FILE_ENV_VAR}, else [output] errors_file in the config file, "
        f"else {DEFAULT_ERRORS_FILE})",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        metavar="PATH",
        help=f"TOML file with per-lookup settings (default: ${CONFIG_ENV_VAR}, else "
        f"{DEFAULT_CONFIG_PATH} if it exists)",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> AppConfig:
    """Parse the command line, the environment and the config file into an AppConfig.

    The config file is the --config flag, else $WEBLOGSTATS_CONFIG, else the default file if it
    exists, else none. The errors file is the --errors-file flag, else $WEBLOGSTATS_ERRORS_FILE,
    else the config file's ``[output] errors_file``, else the default. Exits with status 2 on a
    usage error. Raises FileNotFoundError or ValueError for an unusable config file.
    """
    namespace = _build_parser().parse_args(argv)
    config_path = _resolve_settings_path(namespace.config)
    return AppConfig(
        log_path=namespace.log,
        geoip_path=namespace.geoip,
        output_format=namespace.output_format,
        other_below=namespace.other_below,
        errors_file=_resolve_errors_file(namespace.errors_file, config_path),
        config_path=config_path,
    )


def _resolve_errors_file(flag: Path | None, config_path: Path | None) -> Path:
    if flag is not None:
        return flag
    if os.environ.get(ERRORS_FILE_ENV_VAR):
        return Path(os.environ[ERRORS_FILE_ENV_VAR])
    if config_path is not None:
        from_file = OutputSettings.load(config_path).errors_file
        if from_file is not None:
            return from_file
    return DEFAULT_ERRORS_FILE


def _resolve_settings_path(flag: Path | None) -> Path | None:
    if flag is not None:
        return flag
    if os.environ.get(CONFIG_ENV_VAR):
        return Path(os.environ[CONFIG_ENV_VAR])
    return DEFAULT_CONFIG_PATH if DEFAULT_CONFIG_PATH.is_file() else None


def build_dimensions(geoip: GeoIpLookup, settings: LookupSettings) -> list[Dimension]:
    """The registration point: a new Dimension is one more entry in this list."""
    ua = UaParserLookup(
        LabelNormalizer.for_os(),
        LabelNormalizer.for_browser(),
        cache_size=settings.cache_size(USER_AGENT_LOOKUP, USER_AGENT_DEFAULT_CACHE_SIZE),
    )
    return [CountryDimension(geoip), OsDimension(ua), BrowserDimension(ua)]


def main(argv: list[str] | None = None, *, geoip_factory: GeoIpFactory = _open_maxmind) -> int:
    """Run the report. Returns 0, or 1 after printing a message to stderr for a bad input.

    ``geoip_factory`` exists so tests can inject a fake instead of opening the real MMDB.
    """
    _use_utf8_output()
    with ExitStack() as stack:
        try:
            # Every input is checked before BadLineLog opens, because opening truncates the file.
            config = parse_args(argv)
            settings = (
                LookupSettings.defaults()
                if config.config_path is None
                else LookupSettings.load(config.config_path)
            )
            source = FileLogSource(config.log_path)
            geoip = geoip_factory(
                config.geoip_path, settings.cache_size(GEOIP_LOOKUP, GEOIP_DEFAULT_CACHE_SIZE)
            )
            if isinstance(geoip, AbstractContextManager):
                stack.enter_context(geoip)
            bad_lines = stack.enter_context(BadLineLog(config.errors_file))
        except (OSError, ValueError, RuntimeError) as error:
            return _fail(error)
        aggregator = CountingAggregator()
        pipeline = Pipeline(
            source,
            LoggingParser(ApacheCombinedParser(), bad_lines),
            build_dimensions(geoip, settings),
            aggregator,
        )
        formatter = _FORMATTERS[config.output_format]()
        try:
            stats = pipeline.run()
        except OSError as error:
            return _fail(error)
        sys.stdout.write(formatter.format(aggregator.snapshot(config.other_below)))
        print()
        print(stats.summary(), file=sys.stderr)
        print(
            f"bad lines: {bad_lines.warn_count} warn, {bad_lines.error_count} error"
            f" → {config.errors_file}",
            file=sys.stderr,
        )
    return 0


def _use_utf8_output() -> None:
    """Print UTF-8 whatever the locale says, like the errors file.

    Accented country names on stdout, or the arrow in the stderr summary, would otherwise raise
    or turn into escapes on a legacy code page.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def _fail(error: Exception) -> int:
    print(f"weblogstats: error: {error}", file=sys.stderr)
    return 1
