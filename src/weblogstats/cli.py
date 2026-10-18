"""Command-line entry point. Stub: parses arguments only; Wave 2 wires the pipeline."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from weblogstats.contracts import AppConfig

DEFAULT_GEOIP_PATH = Path("data/GeoLite2-Country.mmdb")
OUTPUT_FORMATS = ("text",)


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
    return parser


def parse_args(argv: list[str] | None = None) -> AppConfig:
    """Parse the command line into an AppConfig. Exits with status 2 on a usage error."""
    namespace = _build_parser().parse_args(argv)
    return AppConfig(
        log_path=namespace.log,
        geoip_path=namespace.geoip,
        output_format=namespace.output_format,
        other_below=namespace.other_below,
    )


def main(argv: list[str] | None = None) -> int:
    """Composition root. Not wired yet: builds the config, then reports that and returns 2."""
    parse_args(argv)
    print("pipeline not wired", file=sys.stderr)
    return 2
