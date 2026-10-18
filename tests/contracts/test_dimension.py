from __future__ import annotations

from types import SimpleNamespace

from weblogstats.contracts import Dimension


class TestDimension:
    def test_object_with_the_members_satisfies_the_protocol(self) -> None:
        candidate = SimpleNamespace(name="Country", extract=lambda record: "Unknown")
        assert isinstance(candidate, Dimension)

    def test_object_missing_the_members_does_not_satisfy_the_protocol(self) -> None:
        assert not isinstance(SimpleNamespace(), Dimension)
        assert not isinstance(object(), Dimension)

    def test_object_with_only_extract_is_not_a_dimension(self) -> None:
        assert not isinstance(SimpleNamespace(extract=lambda record: "x"), Dimension)
