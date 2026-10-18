"""Where raw log lines come from."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol, runtime_checkable


@runtime_checkable
class LogSource(Protocol):
    """Yields raw lines, without the trailing newline."""

    def lines(self) -> Iterator[str]: ...
