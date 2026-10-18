"""Settings the CLI hands to the pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    """Resolved command-line settings."""

    log_path: Path
    geoip_path: Path
    output_format: str = "text"
    other_below: float | None = None
