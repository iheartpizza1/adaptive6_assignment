from __future__ import annotations

from weblogstats.contracts import UNKNOWN


class TestUnknown:
    def test_is_the_literal_string(self) -> None:
        assert UNKNOWN == "Unknown"
