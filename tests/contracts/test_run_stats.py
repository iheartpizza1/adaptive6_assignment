from __future__ import annotations

from weblogstats.contracts import RunStats


class TestRunStats:
    def test_counters_default_to_zero(self) -> None:
        stats = RunStats()
        assert (stats.total, stats.strict, stats.partial, stats.unreadable) == (0, 0, 0, 0)

    def test_summary_format(self) -> None:
        stats = RunStats(total=10000, strict=9999, partial=1, unreadable=0)
        assert stats.summary() == "total=10000 strict=9999 partial=1 unreadable=0"

    def test_summary_of_empty_stats(self) -> None:
        assert RunStats().summary() == "total=0 strict=0 partial=0 unreadable=0"

    def test_is_mutable_so_the_pipeline_can_count(self) -> None:
        stats = RunStats()
        stats.total += 1
        stats.strict += 1
        assert stats.summary() == "total=1 strict=1 partial=0 unreadable=0"
