from __future__ import annotations

import pytest

from weblogstats.aggregation.counting_aggregator import CountingAggregator
from weblogstats.contracts import Aggregator, DimensionReport


def _observe(aggregator: CountingAggregator, dimension: str, counts: dict[str, int]) -> None:
    for label, count in counts.items():
        for _ in range(count):
            aggregator.observe(dimension, label)


class TestCountingAggregator:
    def test_satisfies_the_aggregator_protocol(self) -> None:
        assert isinstance(CountingAggregator(), Aggregator)

    def test_snapshot_gives_one_report_with_percent_of_the_dimension_total(self) -> None:
        aggregator = CountingAggregator()
        _observe(aggregator, "OS", {"Windows": 3, "Linux": 1})

        assert aggregator.snapshot() == [
            DimensionReport(name="OS", rows=(("Windows", 75.0), ("Linux", 25.0)))
        ]

    def test_rows_are_sorted_by_count_descending_then_label_ascending(self) -> None:
        aggregator = CountingAggregator()
        _observe(aggregator, "Browser", {"Opera": 2, "Firefox": 2, "Chrome": 5, "Safari": 1})

        (report,) = aggregator.snapshot()

        assert [label for label, _ in report.rows] == ["Chrome", "Firefox", "Opera", "Safari"]

    def test_rows_keep_full_float_precision(self) -> None:
        aggregator = CountingAggregator()
        _observe(aggregator, "OS", {"Windows": 2, "Linux": 1})

        (report,) = aggregator.snapshot()

        assert dict(report.rows) == {"Windows": 2 / 3 * 100, "Linux": 1 / 3 * 100}
        assert report.rows[0][1] != round(report.rows[0][1], 2)

    def test_each_dimension_uses_its_own_total(self) -> None:
        aggregator = CountingAggregator()
        _observe(aggregator, "OS", {"Windows": 1, "Linux": 1})
        _observe(aggregator, "Browser", {"Chrome": 3, "Firefox": 1})

        by_name = {report.name: dict(report.rows) for report in aggregator.snapshot()}

        assert by_name == {
            "OS": {"Windows": 50.0, "Linux": 50.0},
            "Browser": {"Chrome": 75.0, "Firefox": 25.0},
        }

    @pytest.mark.parametrize("calls", [1, 2])
    def test_snapshot_does_not_change_the_counts(self, calls: int) -> None:
        aggregator = CountingAggregator()
        _observe(aggregator, "OS", {"Windows": 1})

        for _ in range(calls):
            snapshot = aggregator.snapshot()

        assert snapshot == [DimensionReport(name="OS", rows=(("Windows", 100.0),))]
