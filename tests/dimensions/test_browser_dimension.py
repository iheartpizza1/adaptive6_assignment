from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.fakes.fake_user_agent_lookup import FakeUserAgentLookup
from weblogstats.contracts import UNKNOWN, Dimension, LogRecord
from weblogstats.dimensions.browser_dimension import BrowserDimension
from weblogstats.lookups.label_normalizer import LabelNormalizer
from weblogstats.lookups.ua_parser_lookup import UaParserLookup

CHROME_MAC = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_1) Chrome/32.0.1700.77 Safari/537.36"


def _record(user_agent: str) -> LogRecord:
    return LogRecord(
        ip="1.2.3.4",
        timestamp=None,
        method="GET",
        path="/",
        protocol="HTTP/1.1",
        status=200,
        bytes_sent=1,
        referer="-",
        user_agent=user_agent,
        raw="",
    )


class TestBrowserDimension:
    def _dimension(self) -> BrowserDimension:
        fake = FakeUserAgentLookup(
            os_map={CHROME_MAC: "Mac OS"}, browser_map={CHROME_MAC: "Chrome"}
        )
        return BrowserDimension(fake)

    def test_name_is_the_printed_heading(self) -> None:
        assert self._dimension().name == "Browser"

    def test_satisfies_the_dimension_protocol(self) -> None:
        assert isinstance(self._dimension(), Dimension)

    def test_extract_returns_the_browser_family_of_the_user_agent(self) -> None:
        assert self._dimension().extract(_record(CHROME_MAC)) == "Chrome"

    def test_extract_does_not_return_the_os(self) -> None:
        assert self._dimension().extract(_record(CHROME_MAC)) != "Mac OS"

    def test_unmapped_user_agent_is_unknown(self) -> None:
        assert self._dimension().extract(_record("something else")) == UNKNOWN


# The combined format ends with the quoted User-Agent. A truncated line (no closing quote) is
# matched too, so its UA is still read. This regex is deliberately local: the parser agent's
# module is not imported.
_USER_AGENT_AT_END = re.compile(r'"([^"]*)"?\s*$')


def _user_agents(path: Path) -> list[str]:
    agents: list[str] = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                match = _USER_AGENT_AT_END.search(line.rstrip("\n"))
                agents.append(match.group(1) if match else "")
    return agents


class TestBrowserDimensionOnRealLog:
    @pytest.mark.data
    def test_no_other_label_and_enough_unknown(self, apache_log_path: Path) -> None:
        lookup = UaParserLookup(LabelNormalizer.for_os(), LabelNormalizer.for_browser())
        dimension = BrowserDimension(lookup)
        labels = [dimension.extract(_record(agent)) for agent in _user_agents(apache_log_path)]
        assert len(labels) == 10_000
        assert "Other" not in labels
        assert labels.count(UNKNOWN) >= 190
