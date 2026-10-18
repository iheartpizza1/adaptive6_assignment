from __future__ import annotations

from typing import Any

import pytest
import ua_parser

from weblogstats.contracts import UNKNOWN, UserAgentLookup
from weblogstats.lookups.label_normalizer import LabelNormalizer
from weblogstats.lookups.ua_parser_lookup import UaParserLookup

# User agents copied from tests/fixtures/sample.log.
CHROME_MAC = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_1) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/32.0.1700.77 Safari/537.36"
)
CHROME_WINDOWS = (
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/32.0.1700.107 Safari/537.36"
)
FIREFOX_UBUNTU = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:26.0) Gecko/20100101 Firefox/26.0"
IPHONE_SAFARI = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 6_1_3 like Mac OS X) AppleWebKit/536.26 "
    "(KHTML, like Gecko) Version/6.0 Mobile/10B329 Safari/8536.25"
)
IE6_WINDOWS_XP = "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)"
GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
FEED_PARSER = "UniversalFeedParser/4.2-pre-314-svn +http://feedparser.org/"


class TestUaParserLibraryApi:
    """Pins what we rely on from the real ua-parser 1.x, so an upgrade fails here first."""

    def test_parse_returns_result_with_os_and_user_agent_families(self) -> None:
        result = ua_parser.parse(CHROME_MAC)
        assert result.os is not None
        assert result.os.family == "Mac OS X"
        assert result.user_agent is not None
        assert result.user_agent.family == "Chrome"

    def test_os_is_none_when_nothing_matched(self) -> None:
        result = ua_parser.parse(GOOGLEBOT)
        assert result.os is None
        assert result.user_agent is not None
        assert result.user_agent.family == "Googlebot"

    def test_os_and_user_agent_are_both_none_for_an_unmatched_string(self) -> None:
        result = ua_parser.parse("-")
        assert result.os is None
        assert result.user_agent is None


class TestUaParserLookupLabels:
    def _lookup(self) -> UaParserLookup:
        return UaParserLookup(LabelNormalizer.for_os(), LabelNormalizer.for_browser())

    def test_satisfies_the_user_agent_lookup_protocol(self) -> None:
        assert isinstance(self._lookup(), UserAgentLookup)

    @pytest.mark.parametrize(
        ("user_agent", "os_label", "browser_label"),
        [
            pytest.param(CHROME_MAC, "Mac OS", "Chrome", id="chrome-mac"),
            pytest.param(CHROME_WINDOWS, "Windows", "Chrome", id="chrome-windows"),
            pytest.param(FIREFOX_UBUNTU, "Linux", "Firefox", id="firefox-ubuntu"),
            pytest.param(IPHONE_SAFARI, "iOS", "Mobile Safari", id="iphone"),
            pytest.param(IE6_WINDOWS_XP, "Windows", "IE", id="ie6-windows-xp"),
            pytest.param(GOOGLEBOT, UNKNOWN, "Googlebot", id="googlebot"),
            pytest.param("-", UNKNOWN, UNKNOWN, id="dash"),
            pytest.param("", UNKNOWN, UNKNOWN, id="empty"),
        ],
    )
    def test_labels_for_real_user_agents(
        self, user_agent: str, os_label: str, browser_label: str
    ) -> None:
        lookup = self._lookup()
        assert lookup.os_family(user_agent) == os_label
        assert lookup.browser_family(user_agent) == browser_label

    def test_feed_reader_is_never_labelled_other(self) -> None:
        lookup = self._lookup()
        assert lookup.os_family(FEED_PARSER) != "Other"
        assert lookup.browser_family(FEED_PARSER) != "Other"

    def test_uses_the_injected_normalizers(self) -> None:
        lookup = UaParserLookup(
            LabelNormalizer({"Mac OS X": "macOS"}), LabelNormalizer({"Chrome": "Chromium family"})
        )
        assert lookup.os_family(CHROME_MAC) == "macOS"
        assert lookup.browser_family(CHROME_MAC) == "Chromium family"


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
