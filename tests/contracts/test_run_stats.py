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

    def test_extract_errors_defaults_to_zero_and_is_left_out_of_the_summary(self) -> None:
        stats = RunStats(total=3, strict=3)
        assert stats.extract_errors == 0
        assert stats.summary() == "total=3 strict=3 partial=0 unreadable=0"

    def test_summary_appends_extract_errors_when_there_are_any(self) -> None:
        stats = RunStats(total=3, strict=3, extract_errors=2)
        assert stats.summary() == "total=3 strict=3 partial=0 unreadable=0 extract_errors=2"
