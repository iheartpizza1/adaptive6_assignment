"""Counts labels per dimension and turns the counts into percentages."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from weblogstats.contracts.dimension_report import DimensionReport


@runtime_checkable
class Aggregator(Protocol):
    """Dimension-agnostic: it only sees dimension names and labels."""

    def observe(self, dimension: str, label: str) -> None: ...

    def snapshot(self, other_below: float | None = None) -> list[DimensionReport]: ...
