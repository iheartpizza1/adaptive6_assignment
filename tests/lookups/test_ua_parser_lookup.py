from __future__ import annotations

import pytest

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


class TestUaParserLookup:
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


def test_is_re_exported_from_the_lookups_package() -> None:
    from weblogstats.lookups import UaParserLookup as Exported

    assert Exported is UaParserLookup
