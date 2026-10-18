"""The one streaming pass: source, parser, dimensions, aggregator."""

from __future__ import annotations

from collections.abc import Sequence

from weblogstats.contracts import (
    UNKNOWN,
    Aggregator,
    Dimension,
    LogParser,
    LogRecord,
    LogSource,
    RunStats,
)


class Pipeline:
    """Reads every line once, parses it and feeds each dimension's label to the aggregator."""

    def __init__(
        self,
        source: LogSource,
        parser: LogParser,
        dimensions: Sequence[Dimension],
        aggregator: Aggregator,
    ) -> None:
        self._source = source
        self._parser = parser
        self._dimensions = list(dimensions)
        self._aggregator = aggregator

    def run(self) -> RunStats:
        """Process every line and return the parse counters.

        Every dimension observes exactly one label per line, so all dimensions share one
        denominator. A dimension that raises for a record contributes ``Unknown`` for it and
        adds one to ``stats.extract_errors``.
        """
        stats = RunStats()
        for line in self._source.lines():
            record = self._parse(line, stats)
            for dimension in self._dimensions:
                self._aggregator.observe(dimension.name, self._label(dimension, record, stats))
        return stats

    def _parse(self, line: str, stats: RunStats) -> LogRecord:
        stats.total += 1
        record = self._parser.parse(line)
        if record is None:
            stats.unreadable += 1
            return LogRecord.unreadable(line)
        if record.partial:
            stats.partial += 1
        else:
            stats.strict += 1
        return record

    @staticmethod
    def _label(dimension: Dimension, record: LogRecord, stats: RunStats) -> str:
        # A plugin bug must cost one label, never the run; it is counted so it is not silent.
        try:
            return dimension.extract(record)
        except Exception:
            stats.extract_errors += 1
            return UNKNOWN
