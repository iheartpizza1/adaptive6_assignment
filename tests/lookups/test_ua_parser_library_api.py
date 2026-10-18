from __future__ import annotations

import ua_parser

CHROME_MAC = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_1) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/32.0.1700.77 Safari/537.36"
)
GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"


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
