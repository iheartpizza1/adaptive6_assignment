"""Configuration. Re-exports only; each class lives in its own module."""

from weblogstats.config.lookup_settings import LookupSettings
from weblogstats.config.output_settings import OutputSettings

__all__ = ["LookupSettings", "OutputSettings"]
