from __future__ import annotations

from typing import Any

import pytest
import ua_parser

from weblogstats.contracts import UNKNOWN
from weblogstats.lookups.label_normalizer import LabelNormalizer
from weblogstats.lookups.ua_parser_lookup import UaParserLookup

# User agents copied from tests/fixtures/sample.log.
CHROME_MAC = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_1) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/32.0.1700.77 Safari/537.36"
)
GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"


class TestUaParserLookupCaching:
    @pytest.fixture
    def parse_calls(self, monkeypatch: pytest.MonkeyPatch) -> list[str]:
        calls: list[str] = []
        real_parse = ua_parser.parse

        def counting_parse(user_agent: str) -> Any:
            calls.append(user_agent)
            return real_parse(user_agent)

        monkeypatch.setattr("weblogstats.lookups.ua_parser_lookup.ua_parser.parse", counting_parse)
        return calls

    def _lookup(self, cache_size: int = 4096) -> UaParserLookup:
        return UaParserLookup(
            LabelNormalizer.for_os(), LabelNormalizer.for_browser(), cache_size=cache_size
        )

    def test_each_distinct_user_agent_is_parsed_once(self, parse_calls: list[str]) -> None:
        lookup = self._lookup()
        for _ in range(3):
            lookup.os_family(CHROME_MAC)
            lookup.browser_family(CHROME_MAC)
        lookup.os_family(GOOGLEBOT)
        assert parse_calls == [CHROME_MAC, GOOGLEBOT]

    def test_dash_and_empty_never_reach_the_parser(self, parse_calls: list[str]) -> None:
        lookup = self._lookup()
        assert lookup.os_family("-") == UNKNOWN
        assert lookup.browser_family("-") == UNKNOWN
        assert lookup.os_family("") == UNKNOWN
        assert lookup.browser_family("") == UNKNOWN
        assert parse_calls == []

    def test_cache_size_bounds_the_cache(self, parse_calls: list[str]) -> None:
        lookup = self._lookup(cache_size=1)
        lookup.os_family(CHROME_MAC)
        lookup.os_family(GOOGLEBOT)
        lookup.os_family(CHROME_MAC)
        assert parse_calls == [CHROME_MAC, GOOGLEBOT, CHROME_MAC]
