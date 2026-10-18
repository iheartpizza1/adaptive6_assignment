"""Renders finished reports as text."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from weblogstats.contracts.dimension_report import DimensionReport


@runtime_checkable
class ReportFormatter(Protocol):
    """One implementation per output format."""

    def format(self, reports: list[DimensionReport]) -> str: ...
