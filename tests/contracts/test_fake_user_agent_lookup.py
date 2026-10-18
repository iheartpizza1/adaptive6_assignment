from __future__ import annotations

from tests.fakes.fake_user_agent_lookup import FakeUserAgentLookup
from weblogstats.contracts import UNKNOWN, UserAgentLookup

CHROME_MAC = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_1) Chrome/32.0.1700.77 Safari/537.36"


class TestFakeUserAgentLookup:
    def _fake(self) -> FakeUserAgentLookup:
        return FakeUserAgentLookup(
            os_map={CHROME_MAC: "Mac OS"}, browser_map={CHROME_MAC: "Chrome"}
        )

    def test_satisfies_the_user_agent_lookup_protocol(self) -> None:
        assert isinstance(self._fake(), UserAgentLookup)

    def test_returns_the_mapped_os_and_browser(self) -> None:
        fake = self._fake()
        assert fake.os_family(CHROME_MAC) == "Mac OS"
        assert fake.browser_family(CHROME_MAC) == "Chrome"

    def test_returns_unknown_for_an_unmapped_user_agent(self) -> None:
        fake = self._fake()
        assert fake.os_family("curl/7.0") == UNKNOWN
        assert fake.browser_family("curl/7.0") == UNKNOWN

    def test_maps_are_independent(self) -> None:
        fake = FakeUserAgentLookup(os_map={"ua": "Linux"}, browser_map={})
        assert fake.os_family("ua") == "Linux"
        assert fake.browser_family("ua") == UNKNOWN

    def test_returns_unknown_for_dash_and_empty_user_agent(self) -> None:
        fake = self._fake()
        assert fake.os_family("-") == UNKNOWN
        assert fake.browser_family("") == UNKNOWN
