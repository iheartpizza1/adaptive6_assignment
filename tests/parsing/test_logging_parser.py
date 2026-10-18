from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest

from tests.parsing.fakes.recording_bad_line_log import RecordingBadLineLog
from tests.parsing.fakes.stub_log_parser import StubLogParser
from weblogstats.contracts import LogParser, LogRecord
from weblogstats.parsing.apache_combined_parser import ApacheCombinedParser
from weblogstats.parsing.bad_line_log import BadLineLog
from weblogstats.parsing.logging_parser import LoggingParser
from weblogstats.sources.file_log_source import FileLogSource

CLEAN = LogRecord.unreadable("clean line")
PARTIAL = replace(CLEAN, raw="partial line", partial=True)


def _wrap(result: LogRecord | None) -> tuple[LoggingParser, StubLogParser, RecordingBadLineLog]:
    inner = StubLogParser(result)
    log = RecordingBadLineLog()
    return LoggingParser(inner, cast(BadLineLog, log)), inner, log


class TestLoggingParser:
    def test_satisfies_the_log_parser_protocol(self) -> None:
        parser, _, _ = _wrap(CLEAN)
        assert isinstance(parser, LogParser)

    @pytest.mark.parametrize("result", [CLEAN, PARTIAL, None])
    def test_returns_exactly_what_the_inner_parser_returned(self, result: LogRecord | None) -> None:
        parser, inner, _ = _wrap(result)
        assert parser.parse("some line") is result
        assert inner.lines == ["some line"]

    def test_a_clean_record_logs_nothing(self) -> None:
        parser, _, log = _wrap(CLEAN)
        parser.parse("clean line")
        assert log.calls == []

    def test_a_partial_record_is_logged_as_a_warning_with_the_line(self) -> None:
        parser, _, log = _wrap(PARTIAL)
        parser.parse("partial line")
        assert log.calls == [("warn", "partial line")]

    def test_an_unreadable_line_is_logged_as_an_error_with_the_line(self) -> None:
        parser, _, log = _wrap(None)
        parser.parse("garbage")
        assert log.calls == [("error", "garbage")]

    def test_sample_log_yields_one_warning_and_one_error_with_the_full_lines(
        self, sample_log_path: Path, tmp_path: Path
    ) -> None:
        errors_path = tmp_path / "errors.log"
        lines = list(FileLogSource(sample_log_path).lines())
        with BadLineLog(errors_path) as log:
            parser = LoggingParser(ApacheCombinedParser(), log)
            for line in lines:
                parser.parse(line)
            assert (log.warn_count, log.error_count) == (1, 1)
        entries = errors_path.read_bytes().decode("utf-8").splitlines()
        assert len(entries) == 2
        warn, error = (entry.split(" ", 3) for entry in entries)
        assert warn[1:3] == ["WARN", "partial"]
        assert warn[3] == lines[1]  # fixture line 2 is the truncated line-8899 copy
        assert error[1:3] == ["ERROR", "unreadable"]
        assert error[3] == "this is not a log line"

    @pytest.mark.data
    def test_full_log_leaves_one_warning_equal_to_line_8899_byte_for_byte(
        self, apache_log_path: Path, tmp_path: Path
    ) -> None:
        errors_path = tmp_path / "errors.log"
        with BadLineLog(errors_path) as log:
            parser = LoggingParser(ApacheCombinedParser(), log)
            for line in FileLogSource(apache_log_path).lines():
                parser.parse(line)
        entries = errors_path.read_bytes().split(b"\n")
        assert entries[-1] == b""
        assert len(entries) == 2  # exactly one entry plus the empty tail after the final newline
        stamp, level, kind, full_line = entries[0].split(b" ", 3)
        assert (level, kind) == (b"WARN", b"partial")
        assert stamp.endswith(b"Z")
        expected = apache_log_path.read_bytes().split(b"\n")[8898].rstrip(b"\r")
        assert full_line == expected
