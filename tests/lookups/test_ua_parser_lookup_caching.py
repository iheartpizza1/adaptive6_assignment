from __future__ import annotations

import inspect
from typing import Any

import pytest
import ua_parser

from weblogstats.contracts import UNKNOWN
from weblogstats.lookups.label_normalizer import LabelNormalizer
from weblogstats.lookups.ua_parser_lookup import DEFAULT_CACHE_SIZE, UaParserLookup

# User agents copied from tests/fixtures/sample.log.
CHROME_MAC = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_1) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/32.0.1700.77 Safari/537.36"
)
GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
FIREFOX_UBUNTU = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:26.0) Gecko/20100101 Firefox/26.0"


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

    def test_default_cache_size_is_twice_the_distinct_user_agents_in_the_log(self) -> None:
        assert DEFAULT_CACHE_SIZE == 2 * 558
        default = inspect.signature(UaParserLookup).parameters["cache_size"].default
        assert default == DEFAULT_CACHE_SIZE

    def test_least_recently_used_entry_is_evicted(self, parse_calls: list[str]) -> None:
        lookup = self._lookup(cache_size=2)
        a, b, c = CHROME_MAC, GOOGLEBOT, FIREFOX_UBUNTU
        for user_agent in (a, b, a, c):
            lookup.os_family(user_agent)
        assert parse_calls == [a, b, c]

        lookup.os_family(b)
        assert parse_calls == [a, b, c, b]

        lookup = self._lookup(cache_size=2)
        parse_calls.clear()
        for user_agent in (a, b, a, c):
            lookup.os_family(user_agent)
        lookup.os_family(a)
        assert parse_calls == [a, b, c]

    @pytest.mark.parametrize("cache_size", [0, -1])
    def test_cache_size_below_one_is_rejected(self, cache_size: int) -> None:
        with pytest.raises(ValueError, match="cache_size"):
            self._lookup(cache_size=cache_size)

    def test_instances_do_not_share_a_cache(self, parse_calls: list[str]) -> None:
        first = self._lookup()
        second = self._lookup()
        first.os_family(CHROME_MAC)
        second.os_family(CHROME_MAC)
        assert parse_calls == [CHROME_MAC, CHROME_MAC]

    def test_cache_size_bounds_the_cache(self, parse_calls: list[str]) -> None:
        lookup = self._lookup(cache_size=1)
        lookup.os_family(CHROME_MAC)
        lookup.os_family(GOOGLEBOT)
        lookup.os_family(CHROME_MAC)
        assert parse_calls == [CHROME_MAC, GOOGLEBOT, CHROME_MAC]
