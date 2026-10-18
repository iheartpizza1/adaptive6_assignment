"""Pipeline: one pass over in-memory lines with fakes, no files and no network."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from types import SimpleNamespace

import pytest

from tests.fakes.fake_geo_ip import FakeGeoIp
from tests.fakes.fake_user_agent_lookup import FakeUserAgentLookup
from weblogstats.aggregation.counting_aggregator import CountingAggregator
from weblogstats.contracts import UNKNOWN, Dimension, DimensionReport, LogRecord
from weblogstats.dimensions import BrowserDimension, CountryDimension, OsDimension
from weblogstats.parsing.apache_combined_parser import ApacheCombinedParser
from weblogstats.pipeline import Pipeline

CHROME = "Mozilla/5.0 Chrome"
FIREFOX = "Mozilla/5.0 Firefox"


def _line(ip: str, agent: str) -> str:
    return f'{ip} - - [17/May/2015:10:05:03 +0000] "GET / HTTP/1.1" 200 10 "-" "{agent}"'


STRICT_FR = _line("1.1.1.1", CHROME)
STRICT_US = _line("2.2.2.2", FIREFOX)
# Cut off inside the user agent: the strict regex rejects it, the lenient fallback keeps it.
PARTIAL = '3.3.3.3 - - [17/May/2015:10:05:03 +0000] "GET / HTTP/1.1" 200 10 "-" "Mozilla/5.0 Chr'
GARBAGE = "this is not a log line"


def _source(lines: Iterable[str]) -> SimpleNamespace:
    """An in-memory LogSource."""
    return SimpleNamespace(lines=lambda: iter(list(lines)))


def _dimensions() -> list[Dimension]:
    geoip = FakeGeoIp({"1.1.1.1": "France", "2.2.2.2": "United States"})
    ua = FakeUserAgentLookup(
        os_map={CHROME: "Windows", FIREFOX: "Linux"},
        browser_map={CHROME: "Chrome", FIREFOX: "Firefox"},
    )
    return [CountryDimension(geoip), OsDimension(ua), BrowserDimension(ua)]


def _run(
    lines: Iterable[str], dimensions: list[Dimension] | None = None
) -> tuple[Pipeline, CountingAggregator]:
    aggregator = CountingAggregator()
    pipeline = Pipeline(
        _source(lines),
        ApacheCombinedParser(),
        dimensions if dimensions is not None else _dimensions(),
        aggregator,
    )
    return pipeline, aggregator


def _rows(reports: list[DimensionReport], name: str) -> dict[str, float]:
    return dict(next(report for report in reports if report.name == name).rows)


class TestPipeline:
    def test_counts_strict_partial_and_unreadable_lines(self) -> None:
        pipeline, _ = _run([STRICT_FR, STRICT_US, PARTIAL, GARBAGE])
        stats = pipeline.run()
        assert (stats.total, stats.strict, stats.partial, stats.unreadable) == (4, 2, 1, 1)

    def test_summary_matches_the_counters(self) -> None:
        pipeline, _ = _run([STRICT_FR, PARTIAL, GARBAGE])
        assert pipeline.run().summary() == "total=3 strict=1 partial=1 unreadable=1"

    def test_empty_source_gives_zero_stats_and_no_reports(self) -> None:
        pipeline, aggregator = _run([])
        assert pipeline.run().total == 0
        assert aggregator.snapshot() == []

    def test_every_dimension_observes_exactly_total_labels(self) -> None:
        observed: list[tuple[str, str]] = []
        recorder = SimpleNamespace(
            observe=lambda dimension, label: observed.append((dimension, label)),
            snapshot=lambda other_below=None: [],
        )
        lines = [STRICT_FR, STRICT_US, PARTIAL, GARBAGE, STRICT_FR]
        stats = Pipeline(_source(lines), ApacheCombinedParser(), _dimensions(), recorder).run()
        assert stats.total == 5
        for name in ("Country", "OS", "Browser"):
            assert sum(1 for dimension, _ in observed if dimension == name) == stats.total

    def test_unreadable_line_is_unknown_in_every_dimension(self) -> None:
        pipeline, aggregator = _run([GARBAGE])
        pipeline.run()
        reports = aggregator.snapshot()
        assert [(report.name, report.rows) for report in reports] == [
            ("Country", ((UNKNOWN, 100.0),)),
            ("OS", ((UNKNOWN, 100.0),)),
            ("Browser", ((UNKNOWN, 100.0),)),
        ]

    def test_labels_come_from_the_dimensions_in_registration_order(self) -> None:
        pipeline, aggregator = _run([STRICT_FR, STRICT_US, STRICT_FR])
        pipeline.run()
        reports = aggregator.snapshot()
        assert [report.name for report in reports] == ["Country", "OS", "Browser"]
        assert _rows(reports, "Country") == pytest.approx(
            {"France": 200 / 3, "United States": 100 / 3}
        )
        assert _rows(reports, "OS") == pytest.approx({"Windows": 200 / 3, "Linux": 100 / 3})

    def test_partial_line_is_classified_by_its_recovered_fields(self) -> None:
        pipeline, aggregator = _run([PARTIAL])
        pipeline.run()
        # 3.3.3.3 and the truncated user agent are not in the fakes.
        assert _rows(aggregator.snapshot(), "Country") == {UNKNOWN: 100.0}

    def test_a_raising_dimension_does_not_abort_the_run(self) -> None:
        def explode(record: LogRecord) -> str:
            if record.ip == "2.2.2.2":
                raise RuntimeError("boom")
            return "ok"

        flaky = SimpleNamespace(name="Flaky", extract=explode)
        pipeline, aggregator = _run([STRICT_FR, STRICT_US, STRICT_FR], [flaky, *_dimensions()])
        stats = pipeline.run()
        assert stats.total == 3
        assert _rows(aggregator.snapshot(), "Flaky") == pytest.approx(
            {"ok": 200 / 3, UNKNOWN: 100 / 3}
        )

    def test_a_raising_dimension_does_not_affect_the_other_dimensions(self) -> None:
        def always_fails(record: LogRecord) -> str:
            raise ValueError("nope")

        broken = SimpleNamespace(name="Broken", extract=always_fails)
        pipeline, aggregator = _run([STRICT_FR, STRICT_US], [broken, *_dimensions()])
        pipeline.run()
        reports = aggregator.snapshot()
        assert _rows(reports, "Broken") == {UNKNOWN: 100.0}
        assert _rows(reports, "Country") == {"France": 50.0, "United States": 50.0}

    def test_each_dimension_failure_is_counted_in_extract_errors(self) -> None:
        def explode(record: LogRecord) -> str:
            if record.ip == "2.2.2.2":
                raise RuntimeError("boom")
            return "ok"

        def always_fails(record: LogRecord) -> str:
            raise ValueError("nope")

        flaky = SimpleNamespace(name="Flaky", extract=explode)
        broken = SimpleNamespace(name="Broken", extract=always_fails)
        pipeline, _ = _run([STRICT_FR, STRICT_US, STRICT_FR], [flaky, broken, *_dimensions()])
        stats = pipeline.run()
        # Flaky fails once, Broken three times; the real dimensions never.
        assert stats.extract_errors == 4
        assert stats.summary().endswith(" extract_errors=4")

    def test_a_clean_run_has_no_extract_errors(self) -> None:
        pipeline, _ = _run([STRICT_FR, STRICT_US, PARTIAL, GARBAGE])
        stats = pipeline.run()
        assert stats.extract_errors == 0
        assert "extract_errors" not in stats.summary()

    def test_the_source_is_read_once(self) -> None:
        calls: list[int] = []

        def lines() -> Iterator[str]:
            calls.append(1)
            return iter([STRICT_FR, STRICT_US])

        pipeline = Pipeline(
            SimpleNamespace(lines=lines),
            ApacheCombinedParser(),
            _dimensions(),
            CountingAggregator(),
        )
        pipeline.run()
        assert len(calls) == 1
