"""Data-driven cleanup of ua-parser family names."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from weblogstats.contracts import UNKNOWN

# What ua-parser (and the log) say when nothing matched.
_UNKNOWN_FAMILIES = frozenset({"", "Other", "-"})


class LabelNormalizer:
    """Maps a raw family to a display label using alias tables."""

    def __init__(
        self,
        aliases: Mapping[str, str],
        prefix_aliases: Sequence[tuple[str, str]] = (),
    ) -> None:
        self._aliases = dict(aliases)
        self._prefix_aliases = tuple(prefix_aliases)

    def normalize(self, family: str | None) -> str:
        """Unknown rules first, then an exact alias, then the first prefix alias."""
        if family is None or family in _UNKNOWN_FAMILIES:
            return UNKNOWN
        if family in self._aliases:
            return self._aliases[family]
        for prefix, label in self._prefix_aliases:
            if family.startswith(prefix):
                return label
        return family
