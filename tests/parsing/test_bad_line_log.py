from __future__ import annotations

import logging
import re
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from weblogstats.parsing.bad_line_log import BadLineLog

FIXED = datetime(2026, 10, 18, 10, 23, 3, 123000, tzinfo=UTC)
STAMP = "2026-10-18T10:23:03.123Z"
PARTIAL_LINE = (
    '46.118.127.106 - - [20/May/2015:12:05:17 +0000] "GET /scripts/grok-py-test/configlib.py '
    'HTTP/1.1" 200 235 "-" "Mozilla/5.0 (compatible; Googlebot/2.1; '
    "+http://www.google.com/bot.html"
)


def _fixed_clock() -> datetime:
    return FIXED


def _read(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


@pytest.fixture
def errors_path(tmp_path: Path) -> Path:
    return tmp_path / "errors.log"


class TestBadLineLog:
    def test_creates_the_file_empty_when_opened(self, errors_path: Path) -> None:
        with BadLineLog(errors_path, _fixed_clock):
            assert errors_path.is_file()
            assert errors_path.read_bytes() == b""

    def test_truncates_a_stale_file_when_opened(self, errors_path: Path) -> None:
        errors_path.write_text("stale entry from an earlier run\n", encoding="utf-8")
        with BadLineLog(errors_path, _fixed_clock):
            assert errors_path.read_bytes() == b""

    def test_warn_writes_a_warn_partial_entry(self, errors_path: Path) -> None:
        with BadLineLog(errors_path, _fixed_clock) as log:
            log.warn(PARTIAL_LINE)
        assert _read(errors_path) == f"{STAMP} WARN partial {PARTIAL_LINE}\n"

    def test_error_writes_an_error_unreadable_entry(self, errors_path: Path) -> None:
        with BadLineLog(errors_path, _fixed_clock) as log:
            log.error("this is not a log line")
        assert _read(errors_path) == f"{STAMP} ERROR unreadable this is not a log line\n"

    def test_entries_are_appended_in_order(self, errors_path: Path) -> None:
        with BadLineLog(errors_path, _fixed_clock) as log:
            log.warn("first")
            log.error("second")
            log.warn("third")
        assert _read(errors_path).splitlines() == [
            f"{STAMP} WARN partial first",
            f"{STAMP} ERROR unreadable second",
            f"{STAMP} WARN partial third",
        ]

    def test_split_on_the_first_three_spaces_gives_back_the_four_fields(
        self, errors_path: Path
    ) -> None:
        with BadLineLog(errors_path, _fixed_clock) as log:
            log.warn(PARTIAL_LINE)
            log.error("this is not a log line")
        warn_entry, error_entry = _read(errors_path).split("\n")[:2]
        assert warn_entry.split(" ", 3) == [STAMP, "WARN", "partial", PARTIAL_LINE]
        assert error_entry.split(" ", 3) == [
            STAMP,
            "ERROR",
            "unreadable",
            "this is not a log line",
        ]

    def test_the_full_line_is_never_truncated(self, errors_path: Path) -> None:
        long_line = "1.2.3.4 " + "x" * 100_000
        with BadLineLog(errors_path, _fixed_clock) as log:
            log.error(long_line)
        assert _read(errors_path).split(" ", 3)[3] == long_line + "\n"

    def test_timestamp_is_utc_with_milliseconds_and_z_suffix(self, errors_path: Path) -> None:
        plus_two = timezone(timedelta(hours=2))

        def clock() -> datetime:
            return datetime(2026, 10, 18, 12, 23, 3, 5000, tzinfo=plus_two)

        with BadLineLog(errors_path, clock) as log:
            log.warn("x")
        assert _read(errors_path).startswith("2026-10-18T10:23:03.005Z WARN partial x\n")

    def test_default_clock_is_the_current_utc_time(self, errors_path: Path) -> None:
        before = datetime.now(UTC).replace(microsecond=0)
        with BadLineLog(errors_path) as log:
            log.warn("x")
        stamp = _read(errors_path).split(" ", 1)[0]
        assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z", stamp)
        written = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        assert before <= written <= datetime.now(UTC)

    def test_counts_warnings_and_errors_separately(self, errors_path: Path) -> None:
        with BadLineLog(errors_path, _fixed_clock) as log:
            assert (log.warn_count, log.error_count) == (0, 0)
            log.warn("a")
            log.warn("b")
            log.error("c")
            assert (log.warn_count, log.error_count) == (2, 1)

    def test_context_manager_closes_the_file(self, errors_path: Path) -> None:
        with BadLineLog(errors_path, _fixed_clock) as log:
            log.warn("a")
        with pytest.raises(ValueError):
            log.warn("b")

    @pytest.mark.parametrize("method", ["warn", "error"])
    def test_writing_after_close_raises_value_error_and_is_not_counted(
        self, errors_path: Path, method: str
    ) -> None:
        log = BadLineLog(errors_path, _fixed_clock)
        log.close()
        with pytest.raises(ValueError):
            getattr(log, method)("late")
        assert (log.warn_count, log.error_count) == (0, 0)
        assert errors_path.read_bytes() == b""

    def test_close_can_be_called_twice(self, errors_path: Path) -> None:
        log = BadLineLog(errors_path, _fixed_clock)
        log.close()
        log.close()

    def test_entries_are_on_disk_after_close(self, errors_path: Path) -> None:
        log = BadLineLog(errors_path, _fixed_clock)
        log.warn("a")
        log.close()
        assert _read(errors_path) == f"{STAMP} WARN partial a\n"

    def test_carriage_return_tab_and_non_ascii_are_written_as_is(self, errors_path: Path) -> None:
        raw = "1.2.3.4\tcr\rend caf\u00e9 \u20ac bad\ufffdbyte"
        with BadLineLog(errors_path, _fixed_clock) as log:
            log.error(raw)
        assert errors_path.read_bytes() == f"{STAMP} ERROR unreadable {raw}\n".encode()

    def test_lines_end_in_a_bare_line_feed_on_every_platform(self, errors_path: Path) -> None:
        with BadLineLog(errors_path, _fixed_clock) as log:
            log.warn("a")
        assert errors_path.read_bytes().endswith(b"a\n")
        assert b"\r" not in errors_path.read_bytes()

    def test_does_not_touch_the_root_logger_or_global_logging_configuration(
        self, errors_path: Path
    ) -> None:
        root = logging.getLogger()
        handlers_before = list(root.handlers)
        level_before = root.level
        with BadLineLog(errors_path, _fixed_clock) as log:
            log.warn("a")
            log.error("b")
        assert root.handlers == handlers_before
        assert root.level == level_before
