"""One reported metric, such as Country, OS or Browser."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from weblogstats.contracts.log_record import LogRecord


@runtime_checkable
class Dimension(Protocol):
    """``name`` is the printed heading. ``extract`` returns a label, or "Unknown"."""

    name: str

    def extract(self, record: LogRecord) -> str: ...
