"""Guards tests/fixtures/sample.log so edits to it are noticed."""

from __future__ import annotations

from pathlib import Path

EXPECTED_NON_BLANK_LINES = 19
EXPECTED_BLANK_LINES = 1


class TestSampleLog:
    def _lines(self, path: Path) -> list[str]:
        return path.read_text(encoding="ascii").splitlines()

    def test_has_expected_number_of_non_blank_lines(self, sample_log_path: Path) -> None:
        lines = self._lines(sample_log_path)
        assert sum(1 for line in lines if line.strip()) == EXPECTED_NON_BLANK_LINES

    def test_has_expected_number_of_blank_lines(self, sample_log_path: Path) -> None:
        lines = self._lines(sample_log_path)
        assert sum(1 for line in lines if not line.strip()) == EXPECTED_BLANK_LINES

    def test_covers_the_cases_from_the_hld(self, sample_log_path: Path) -> None:
        text = sample_log_path.read_text(encoding="ascii")
        for needle in (
            "Chrome/32.0.1700.77",  # brief sample shape
            "Googlebot/2.1; +http://www.google.com/bot.html\n",  # truncated UA (no closing quote)
            '"-" "-"',  # UA is "-"
            '" 304 - ',  # bytes is "-"
            r"\xe4\xe5",  # escapes in the referer
            "MSIE 6.0; Windows NT 5.1",  # IE 6 / Windows XP
            "UniversalFeedParser",
            "LAVA.KKT35",
            "Ubuntu; Linux x86_64; rv:26.0",
            "iPhone; CPU iPhone OS 6_1_3",
            "X11; Linux x86_64) AppleWebKit",
            "10.0.0.1 ",
            "this is not a log line",
        ):
            assert needle in text, needle
