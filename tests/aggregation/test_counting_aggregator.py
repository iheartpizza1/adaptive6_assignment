from __future__ import annotations

import random

import pytest

from weblogstats.aggregation.counting_aggregator import CountingAggregator
from weblogstats.contracts import Aggregator, DimensionReport


def _observe(aggregator: CountingAggregator, dimension: str, counts: dict[str, int]) -> None:
    for label, count in counts.items():
        for _ in range(count):
            aggregator.observe(dimension, label)


def _country_aggregator() -> CountingAggregator:
    aggregator = CountingAggregator()
    _observe(aggregator, "Country", {"US": 60, "UK": 25, "France": 10, "Peru": 3, "Chad": 2})
    return aggregator


class TestCountingAggregator:
    def test_is_re_exported_from_the_package(self) -> None:
        from weblogstats.aggregation import CountingAggregator as Exported

        assert Exported is CountingAggregator

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

    def test_dimensions_are_reported_in_first_observed_order(self) -> None:
        aggregator = CountingAggregator()
        aggregator.observe("OS", "Windows")
        aggregator.observe("Country", "France")
        aggregator.observe("Browser", "Chrome")
        aggregator.observe("OS", "Linux")

        assert [report.name for report in aggregator.snapshot()] == ["OS", "Country", "Browser"]

    def test_empty_aggregator_gives_no_reports(self) -> None:
        assert CountingAggregator().snapshot() == []

    def test_labels_below_the_threshold_are_merged_into_one_other_row_last(self) -> None:
        (report,) = _country_aggregator().snapshot(other_below=5.0)

        assert [label for label, _ in report.rows] == ["US", "UK", "France", "Other"]
        assert dict(report.rows)["Other"] == pytest.approx(5.0)

    def test_a_label_exactly_at_the_threshold_is_kept(self) -> None:
        (report,) = _country_aggregator().snapshot(other_below=3.0)

        assert [label for label, _ in report.rows] == ["US", "UK", "France", "Peru", "Other"]
        assert dict(report.rows)["Other"] == pytest.approx(2.0)

    def test_no_other_row_when_nothing_is_below_the_threshold(self) -> None:
        (report,) = _country_aggregator().snapshot(other_below=1.0)

        assert "Other" not in dict(report.rows)
        assert len(report.rows) == 5

    def test_other_stays_last_even_when_it_is_larger_than_the_kept_rows(self) -> None:
        aggregator = CountingAggregator()
        _observe(aggregator, "Browser", {"Chrome": 50, "Opera": 20, "Midori": 15, "Lynx": 15})

        (report,) = aggregator.snapshot(other_below=21.0)

        assert [label for label, _ in report.rows] == ["Chrome", "Other"]
        assert dict(report.rows)["Other"] == pytest.approx(50.0)

    def test_an_existing_label_named_other_is_merged_into_the_other_row(self) -> None:
        aggregator = CountingAggregator()
        _observe(aggregator, "Country", {"US": 90, "Other": 4, "Peru": 3, "Chad": 3})

        (report,) = aggregator.snapshot(other_below=5.0)

        assert report.rows == (("US", 90.0), ("Other", pytest.approx(10.0)))

    def test_an_existing_other_label_above_the_threshold_still_comes_last(self) -> None:
        aggregator = CountingAggregator()
        _observe(aggregator, "Country", {"Other": 60, "US": 40})

        (report,) = aggregator.snapshot(other_below=5.0)

        assert report.rows == (("US", 40.0), ("Other", 60.0))

    def test_unknown_is_a_normal_label_and_is_merged_into_other_when_small(self) -> None:
        aggregator = CountingAggregator()
        _observe(aggregator, "OS", {"Windows": 98, "Unknown": 2})

        (report,) = aggregator.snapshot(other_below=5.0)

        assert report.rows == (("Windows", 98.0), ("Other", 2.0))

    def test_unknown_above_the_threshold_keeps_its_own_row(self) -> None:
        aggregator = CountingAggregator()
        _observe(aggregator, "OS", {"Windows": 90, "Unknown": 10})

        (report,) = aggregator.snapshot(other_below=5.0)

        assert report.rows == (("Windows", 90.0), ("Unknown", 10.0))

    def test_the_threshold_applies_to_each_dimension_separately(self) -> None:
        aggregator = CountingAggregator()
        _observe(aggregator, "OS", {"Windows": 96, "Linux": 4})
        _observe(aggregator, "Browser", {"Chrome": 50, "Firefox": 50})

        by_name = {report.name: report.rows for report in aggregator.snapshot(other_below=5.0)}

        assert by_name["OS"] == (("Windows", 96.0), ("Other", 4.0))
        assert by_name["Browser"] == (("Chrome", 50.0), ("Firefox", 50.0))

    def test_a_threshold_that_merges_everything_leaves_only_other(self) -> None:
        aggregator = CountingAggregator()
        _observe(aggregator, "OS", {"Windows": 1, "Linux": 1})

        (report,) = aggregator.snapshot(other_below=100.0)

        assert report.rows == (("Other", 100.0),)

    def test_a_label_at_the_threshold_is_kept_despite_float_rounding(self) -> None:
        # 29 / 100 * 100 is 28.999999999999996 in floating point.
        aggregator = CountingAggregator()
        _observe(aggregator, "OS", {"Windows": 71, "Linux": 29})

        (report,) = aggregator.snapshot(other_below=29.0)

        assert [label for label, _ in report.rows] == ["Windows", "Linux"]

    @pytest.mark.parametrize("other_below", [None, 1.0, 5.0, 20.0])
    def test_percentages_of_each_report_sum_to_one_hundred(self, other_below: float | None) -> None:
        rng = random.Random(20261018)
        for _ in range(25):
            aggregator = CountingAggregator()
            counts = {f"label{i}": rng.randint(1, 500) for i in range(rng.randint(1, 40))}
            _observe(aggregator, "Random", counts)

            (report,) = aggregator.snapshot(other_below=other_below)

            assert sum(percent for _, percent in report.rows) == pytest.approx(100.0, abs=1e-9)
