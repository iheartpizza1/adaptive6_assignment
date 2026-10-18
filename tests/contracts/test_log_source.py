from __future__ import annotations

from types import SimpleNamespace

from weblogstats.contracts import LogSource


class TestLogSource:
    def test_object_with_the_members_satisfies_the_protocol(self) -> None:
        candidate = SimpleNamespace(lines=lambda: iter(()))
        assert isinstance(candidate, LogSource)

    def test_object_missing_the_members_does_not_satisfy_the_protocol(self) -> None:
        assert not isinstance(SimpleNamespace(), LogSource)
        assert not isinstance(object(), LogSource)
