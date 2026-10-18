"""One finished metric block: a name and its (label, percent) rows."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DimensionReport:
    """Rows are (label, percent), sorted by percent descending."""

    name: str
    rows: tuple[tuple[str, float], ...]
