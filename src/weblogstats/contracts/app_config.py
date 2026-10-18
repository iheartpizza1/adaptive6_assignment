"""Settings the CLI hands to the pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    """Resolved settings from the command line, the environment and the config file.

    ``errors_file`` is where partial and unreadable lines are logged. ``config_path`` is the TOML
    settings file in use, or None when there is none.
    """

    log_path: Path
    geoip_path: Path
    output_format: str = "text"
    other_below: float | None = None
    errors_file: Path = Path("weblogstats-errors.log")
    config_path: Path | None = None
