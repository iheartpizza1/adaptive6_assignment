"""Command-line entry point and composition root. No parsing or percentage logic lives here."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable
from contextlib import AbstractContextManager, ExitStack
from pathlib import Path

from weblogstats.aggregation import CountingAggregator
from weblogstats.contracts import AppConfig, Dimension, GeoIpLookup, ReportFormatter
from weblogstats.dimensions import BrowserDimension, CountryDimension, OsDimension
from weblogstats.formatting import TextReportFormatter
from weblogstats.lookups import LabelNormalizer, MaxMindGeoIp, UaParserLookup
from weblogstats.parsing import ApacheCombinedParser, BadLineLog, LoggingParser
from weblogstats.pipeline import Pipeline
from weblogstats.sources import FileLogSource

DEFAULT_GEOIP_PATH = Path("data/GeoLite2-Country.mmdb")
DEFAULT_ERRORS_FILE = Path("weblogstats-errors.log")

# One entry per --format choice; a new ReportFormatter is registered here.
_FORMATTERS: dict[str, Callable[[], ReportFormatter]] = {"text": TextReportFormatter}
OUTPUT_FORMATS = tuple(_FORMATTERS)

GeoIpFactory = Callable[[Path], GeoIpLookup]


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
        default=DEFAULT_ERRORS_FILE,
        metavar="PATH",
        help="where partial and unreadable lines are logged; truncated on every run "
        "(default: %(default)s)",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> tuple[AppConfig, Path]:
    """Parse the command line into an AppConfig and the errors-file path.

    The path travels beside the config because AppConfig has no field for it. Exits with
    status 2 on a usage error.
    """
    namespace = _build_parser().parse_args(argv)
    config = AppConfig(
        log_path=namespace.log,
        geoip_path=namespace.geoip,
        output_format=namespace.output_format,
        other_below=namespace.other_below,
    )
    return config, namespace.errors_file


def build_dimensions(geoip: GeoIpLookup) -> list[Dimension]:
    """The registration point: a new Dimension is one more entry in this list."""
    ua = UaParserLookup(LabelNormalizer.for_os(), LabelNormalizer.for_browser())
    return [CountryDimension(geoip), OsDimension(ua), BrowserDimension(ua)]


def main(argv: list[str] | None = None, *, geoip_factory: GeoIpFactory = MaxMindGeoIp) -> int:
    """Run the report. Returns 0, or 1 after printing a message to stderr for a bad input.

    ``geoip_factory`` exists so tests can inject a fake instead of opening the real MMDB.
    """
    config, errors_file = parse_args(argv)
    with ExitStack() as stack:
        try:
            # Every input is checked before BadLineLog opens, because opening truncates the file.
            source = FileLogSource(config.log_path)
            geoip = geoip_factory(config.geoip_path)
            if isinstance(geoip, AbstractContextManager):
                stack.enter_context(geoip)
            bad_lines = stack.enter_context(BadLineLog(errors_file))
        except (OSError, ValueError, RuntimeError) as error:
            return _fail(error)
        aggregator = CountingAggregator()
        pipeline = Pipeline(
            source,
            LoggingParser(ApacheCombinedParser(), bad_lines),
            build_dimensions(geoip),
            aggregator,
        )
        formatter = _FORMATTERS[config.output_format]()
        try:
            stats = pipeline.run()
        except OSError as error:
            return _fail(error)
        sys.stdout.write(formatter.format(aggregator.snapshot(config.other_below)))
        print(stats.summary(), file=sys.stderr)
        print(
            f"bad lines: {bad_lines.warn_count} warn, {bad_lines.error_count} error"
            f" → {errors_file}",
            file=sys.stderr,
        )
    return 0


def _fail(error: Exception) -> int:
    print(f"weblogstats: error: {error}", file=sys.stderr)
    return 1
