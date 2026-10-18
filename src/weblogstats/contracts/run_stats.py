"""Counters behind the stderr summary line."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RunStats:
    """How many lines were seen and how each one was parsed."""

    total: int = 0
    strict: int = 0
    partial: int = 0
    unreadable: int = 0

    def summary(self) -> str:
        return (
            f"total={self.total} strict={self.strict} "
            f"partial={self.partial} unreadable={self.unreadable}"
        )
