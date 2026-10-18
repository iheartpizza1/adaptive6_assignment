from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

from weblogstats.contracts import LogRecord


def _record(**overrides: object) -> LogRecord:
    fields: dict[str, object] = {
        "ip": "83.149.9.216",
        "timestamp": datetime(2015, 5, 17, 10, 5, 3, tzinfo=UTC),
        "method": "GET",
        "path": "/index.html",
        "protocol": "HTTP/1.1",
        "status": 200,
        "bytes_sent": 203023,
        "referer": "-",
        "user_agent": "Mozilla/5.0",
        "raw": "raw line",
    }
    fields.update(overrides)
    return LogRecord(**fields)  # type: ignore[arg-type]


class TestLogRecord:
    def test_partial_defaults_to_false(self) -> None:
        assert _record().partial is False

    def test_is_frozen(self) -> None:
        record = _record()
        with pytest.raises(dataclasses.FrozenInstanceError):
            record.ip = "1.2.3.4"  # type: ignore[misc]

    def test_is_hashable_and_comparable(self) -> None:
        assert _record() == _record()
        assert hash(_record()) == hash(_record())

    def test_optional_fields_accept_none(self) -> None:
        record = _record(timestamp=None, status=None, bytes_sent=None)
        assert record.timestamp is None
        assert record.status is None
        assert record.bytes_sent is None

    def test_unreadable_keeps_raw_and_blanks_everything_else(self) -> None:
        record = LogRecord.unreadable("this is not a log line")
        assert record.raw == "this is not a log line"
        assert record.ip == ""
        assert record.method == ""
        assert record.path == ""
        assert record.protocol == ""
        assert record.referer == ""
        assert record.user_agent == ""
        assert record.timestamp is None
        assert record.status is None
        assert record.bytes_sent is None

    def test_unreadable_is_not_marked_partial(self) -> None:
        assert LogRecord.unreadable("x").partial is False
