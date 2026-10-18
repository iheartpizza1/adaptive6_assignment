from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from weblogstats.contracts import LogParser, LogRecord
from weblogstats.parsing.apache_combined_parser import ApacheCombinedParser

# 1-based fixture line numbers, see tests/fixtures/README.md (blank line 19 is dropped here).
CLEAN_LINE = 1
TRUNCATED_LINE = 2
UA_DASH_LINE = 3
BYTES_DASH_LINE = 4
ESCAPED_REFERER_LINE = 5
GARBAGE_LINE = 19  # fixture line 20, shifted by the dropped blank line


@pytest.fixture
def sample_lines(sample_log_path: Path) -> list[str]:
    text = sample_log_path.read_text(encoding="ascii")
    return [line for line in text.splitlines() if line.strip()]


@pytest.fixture
def parser() -> ApacheCombinedParser:
    return ApacheCombinedParser()


def _line(request: str = "GET /a HTTP/1.1", *, status: str = "200", size: str = "10") -> str:
    return f'1.2.3.4 - - [17/May/2015:10:05:03 +0000] "{request}" {status} {size} "-" "Agent/1.0"'


class TestApacheCombinedParser:
    def test_satisfies_the_log_parser_protocol(self, parser: ApacheCombinedParser) -> None:
        assert isinstance(parser, LogParser)

    def test_strict_fields_of_the_brief_sample_line(
        self, parser: ApacheCombinedParser, sample_lines: list[str]
    ) -> None:
        line = sample_lines[CLEAN_LINE - 1]
        record = parser.parse(line)
        assert isinstance(record, LogRecord)
        assert record.ip == "83.149.9.216"
        assert record.timestamp == datetime(2015, 5, 17, 10, 5, 3, tzinfo=UTC)
        assert record.timestamp is not None
        assert record.timestamp.utcoffset() == timedelta(0)
        assert record.method == "GET"
        assert record.path == "/presentations/logstash-monitorama-2013/images/kibana-search.png"
        assert record.protocol == "HTTP/1.1"
        assert record.status == 200
        assert record.bytes_sent == 203023
        assert record.referer == "http://semicomplete.com/presentations/logstash-monitorama-2013/"
        assert record.user_agent.startswith("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_1)")
        assert record.user_agent.endswith("Chrome/32.0.1700.77 Safari/537.36")
        assert record.raw == line
        assert record.partial is False

    def test_timestamp_keeps_a_non_utc_offset(self, parser: ApacheCombinedParser) -> None:
        record = parser.parse(_line().replace("+0000", "+0200"))
        assert record is not None
        assert record.timestamp == datetime(2015, 5, 17, 8, 5, 3, tzinfo=UTC)
        assert record.timestamp is not None
        assert record.timestamp.utcoffset() == timedelta(hours=2)

    def test_dash_bytes_is_none(
        self, parser: ApacheCombinedParser, sample_lines: list[str]
    ) -> None:
        record = parser.parse(sample_lines[BYTES_DASH_LINE - 1])
        assert record is not None
        assert record.status == 304
        assert record.bytes_sent is None
        assert record.partial is False

    def test_dash_status_is_none(self, parser: ApacheCombinedParser) -> None:
        record = parser.parse(_line(status="-"))
        assert record is not None
        assert record.status is None
        assert record.bytes_sent == 10
        assert record.partial is False

    def test_dash_user_agent_is_a_valid_strict_record(
        self, parser: ApacheCombinedParser, sample_lines: list[str]
    ) -> None:
        record = parser.parse(sample_lines[UA_DASH_LINE - 1])
        assert record is not None
        assert record.user_agent == "-"
        assert record.partial is False

    @pytest.mark.parametrize(
        ("request_field", "expected"),
        [
            ("GET /a HTTP/1.1", ("GET", "/a", "HTTP/1.1")),
            ("GET /a b HTTP/1.1", ("GET", "/a b", "HTTP/1.1")),
            ("GET /a", ("GET", "/a", "")),
            ("/a", ("", "/a", "")),
            ("-", ("", "", "")),
            ("", ("", "", "")),
        ],
    )
    def test_request_field_that_is_not_three_tokens_still_parses(
        self,
        parser: ApacheCombinedParser,
        request_field: str,
        expected: tuple[str, str, str],
    ) -> None:
        record = parser.parse(_line(request_field))
        assert record is not None
        assert (record.method, record.path, record.protocol) == expected
        assert record.partial is False

    def test_escaped_referer_parses_strictly_and_keeps_the_escapes_literal(
        self, parser: ApacheCombinedParser, sample_lines: list[str]
    ) -> None:
        record = parser.parse(sample_lines[ESCAPED_REFERER_LINE - 1])
        assert record is not None
        assert record.partial is False
        assert (
            record.referer
            == r"http://\xe4\xe5\xe3\xf2\xff\xf0\xed\xee\xe5-\xec\xfb\xeb\xee.\xf0\xf4/"
        )
        assert (
            record.user_agent == "Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0"
        )

    def test_escaped_quote_inside_a_field_does_not_end_it(
        self, parser: ApacheCombinedParser
    ) -> None:
        line = (
            r'1.2.3.4 - - [17/May/2015:10:05:03 +0000] "GET / HTTP/1.1" 200 1 "-" "A \"quoted\" UA"'
        )
        record = parser.parse(line)
        assert record is not None
        assert record.partial is False
        assert record.user_agent == r"A \"quoted\" UA"

    def test_bad_timestamp_gives_none_and_does_not_raise(
        self, parser: ApacheCombinedParser
    ) -> None:
        for bad in ("99/Foo/2015:10:05:03 +0000", "garbage", ""):
            record = parser.parse(_line().replace("17/May/2015:10:05:03 +0000", bad))
            assert record is not None, bad
            assert record.timestamp is None, bad
            assert record.ip == "1.2.3.4", bad
            assert record.partial is False, bad
