"""Counts labels per dimension and turns the counts into percentages."""

from __future__ import annotations

from collections import Counter

from weblogstats.contracts import DimensionReport


class CountingAggregator:
    """Dimension-agnostic Aggregator backed by one Counter per dimension."""

    def __init__(self) -> None:
        # dicts keep insertion order, so dimensions report in first-observed order.
        self._counts: dict[str, Counter[str]] = {}

    def observe(self, dimension: str, label: str) -> None:
        self._counts.setdefault(dimension, Counter())[label] += 1

    def snapshot(self, other_below: float | None = None) -> list[DimensionReport]:
        return [self._report(name, counts) for name, counts in self._counts.items()]

    @staticmethod
    def _report(name: str, counts: Counter[str]) -> DimensionReport:
        total = sum(counts.values())
        ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        rows = tuple((label, count / total * 100) for label, count in ordered)
        return DimensionReport(name=name, rows=rows)
