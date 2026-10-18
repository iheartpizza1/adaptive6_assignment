from __future__ import annotations

from types import SimpleNamespace

from weblogstats.contracts import Aggregator


class TestAggregator:
    def test_object_with_the_members_satisfies_the_protocol(self) -> None:
        candidate = SimpleNamespace(observe=lambda dimension, label: None, snapshot=lambda other_below=None: [])
        assert isinstance(candidate, Aggregator)

    def test_object_missing_the_members_does_not_satisfy_the_protocol(self) -> None:
        assert not isinstance(SimpleNamespace(), Aggregator)
        assert not isinstance(object(), Aggregator)

    def test_object_with_only_observe_is_not_an_aggregator(self) -> None:
        assert not isinstance(SimpleNamespace(observe=lambda d, label: None), Aggregator)
