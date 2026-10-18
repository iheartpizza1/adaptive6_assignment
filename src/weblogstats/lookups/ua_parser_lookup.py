"""ua-parser adapter. The only module that imports ua_parser."""

from __future__ import annotations

from functools import lru_cache

import ua_parser

from weblogstats.contracts import UNKNOWN
from weblogstats.lookups.label_normalizer import LabelNormalizer

# A missing user agent is valid input, not something to hand to the regex engine.
_NO_USER_AGENT = frozenset({"", "-"})

# 2 x 557 unique user-agent strings in apache_log.txt
DEFAULT_CACHE_SIZE = 1114


class UaParserLookup:
    """UserAgentLookup backed by ua-parser, with normalized labels and a per-UA cache."""

    def __init__(
        self,
        os_normalizer: LabelNormalizer,
        browser_normalizer: LabelNormalizer,
        cache_size: int = DEFAULT_CACHE_SIZE,
    ) -> None:
        if cache_size < 1:
            raise ValueError(f"cache_size must be at least 1, got {cache_size}")
        self._os_normalizer = os_normalizer
        self._browser_normalizer = browser_normalizer
        self._labels = lru_cache(maxsize=cache_size)(self._parse_labels)

    def os_family(self, user_agent: str) -> str:
        return self._lookup(user_agent)[0]

    def browser_family(self, user_agent: str) -> str:
        return self._lookup(user_agent)[1]

    def _lookup(self, user_agent: str) -> tuple[str, str]:
        """Return (os, browser) labels; one parse serves both."""
        if user_agent in _NO_USER_AGENT:
            return UNKNOWN, UNKNOWN
        return self._labels(user_agent)

    def _parse_labels(self, user_agent: str) -> tuple[str, str]:
        result = ua_parser.parse(user_agent)
        # ua-parser leaves .os / .user_agent as None when no regex matched.
        os_family = result.os.family if result.os is not None else None
        browser_family = result.user_agent.family if result.user_agent is not None else None
        return (
            self._os_normalizer.normalize(os_family),
            self._browser_normalizer.normalize(browser_family),
        )
