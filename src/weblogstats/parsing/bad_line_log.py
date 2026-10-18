"""Writes the lines the parser could not read cleanly to an errors file."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType


def _utc_now() -> datetime:
    return datetime.now(UTC)


class BadLineLog:
    """An errors-file writer: ``<UTC timestamp> <LEVEL> <kind> <full line>`` per bad line.

    The file is created and truncated when the log is opened, so an empty file means that this
    run had no bad lines. It is a plain file writer and never touches the ``logging`` module.
    """

    def __init__(self, path: Path, clock: Callable[[], datetime] = _utc_now) -> None:
        self._clock = clock
        self._warn_count = 0
        self._error_count = 0
        # newline="\n": entries end in a bare line feed and a "\r" inside a line is not rewritten.
        self._file = path.open("w", encoding="utf-8", errors="replace", newline="\n")

    @property
    def warn_count(self) -> int:
        return self._warn_count

    @property
    def error_count(self) -> int:
        return self._error_count

    def warn(self, raw: str) -> None:
        """Record a line the lenient fallback had to rescue."""
        self._write("WARN", "partial", raw)
        self._warn_count += 1

    def error(self, raw: str) -> None:
        """Record a line the parser could not read at all."""
        self._write("ERROR", "unreadable", raw)
        self._error_count += 1

    def close(self) -> None:
        self._file.close()

    def __enter__(self) -> BadLineLog:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def _write(self, level: str, kind: str, raw: str) -> None:
        if self._file.closed:
            raise ValueError("cannot write to a closed BadLineLog")
        stamp = self._timestamp()
        self._file.write(f"{stamp} {level} {kind} {raw}\n")
        self._file.flush()

    def _timestamp(self) -> str:
        moment = self._clock()
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=UTC)
        return moment.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
