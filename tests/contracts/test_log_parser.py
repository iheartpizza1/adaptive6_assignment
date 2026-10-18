from __future__ import annotations

from types import SimpleNamespace

from weblogstats.contracts import LogParser


class TestLogParser:
    def test_object_with_the_members_satisfies_the_protocol(self) -> None:
        candidate = SimpleNamespace(parse=lambda line: None)
        assert isinstance(candidate, LogParser)

    def test_object_missing_the_members_does_not_satisfy_the_protocol(self) -> None:
        assert not isinstance(SimpleNamespace(), LogParser)
        assert not isinstance(object(), LogParser)
