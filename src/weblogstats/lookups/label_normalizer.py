"""Data-driven cleanup of ua-parser family names."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from weblogstats.contracts import UNKNOWN

# What ua-parser (and the log) say when nothing matched.
_UNKNOWN_FAMILIES = frozenset({"", "Other", "-"})


_LINUX_DISTRIBUTIONS = (
    "Ubuntu",
    "Debian",
    "Fedora",
    "Linux Mint",
    "Red Hat",
    "CentOS",
    "Gentoo",
    "Arch Linux",
    "openSUSE",
    "Slackware",
)
_OS_ALIASES = {"Mac OS X": "Mac OS", **dict.fromkeys(_LINUX_DISTRIBUTIONS, "Linux")}
_OS_PREFIX_ALIASES = (("Windows", "Windows"),)


class LabelNormalizer:
    """Maps a raw family to a display label using alias tables."""

    def __init__(
        self,
        aliases: Mapping[str, str],
        prefix_aliases: Sequence[tuple[str, str]] = (),
    ) -> None:
        self._aliases = dict(aliases)
        self._prefix_aliases = tuple(prefix_aliases)

    @classmethod
    def for_os(cls) -> LabelNormalizer:
        """The default OS table: Mac OS X, every Windows version and Linux distributions."""
        return cls(_OS_ALIASES, _OS_PREFIX_ALIASES)

    @classmethod
    def for_browser(cls) -> LabelNormalizer:
        """Browser families are kept as ua-parser reports them; only Unknown rules apply."""
        return cls({})

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
