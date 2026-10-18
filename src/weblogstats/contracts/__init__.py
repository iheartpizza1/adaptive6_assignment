"""Shared contracts. Re-exports only; each class lives in its own module."""

from weblogstats.contracts.log_record import LogRecord
from weblogstats.contracts.unknown import UNKNOWN

__all__ = ["UNKNOWN", "LogRecord"]
