"""Counters behind the stderr summary line."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RunStats:
    """How many lines were seen, how each one was parsed, and how many extractions failed.

    ``extract_errors`` counts the times a dimension raised for a record (that record got
    "Unknown" for that dimension). The summary only shows it when it is above zero.
    """

    total: int = 0
    strict: int = 0
    partial: int = 0
    unreadable: int = 0
    extract_errors: int = 0

    def summary(self) -> str:
        text = (
            f"total={self.total} strict={self.strict} "
            f"partial={self.partial} unreadable={self.unreadable}"
        )
        if self.extract_errors:
            text += f" extract_errors={self.extract_errors}"
        return text
