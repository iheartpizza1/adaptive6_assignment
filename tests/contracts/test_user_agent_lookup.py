from __future__ import annotations

from types import SimpleNamespace

from weblogstats.contracts import UserAgentLookup


class TestUserAgentLookup:
    def test_object_with_the_members_satisfies_the_protocol(self) -> None:
        candidate = SimpleNamespace(
            os_family=lambda ua: "Unknown", browser_family=lambda ua: "Unknown"
        )
        assert isinstance(candidate, UserAgentLookup)

    def test_object_missing_the_members_does_not_satisfy_the_protocol(self) -> None:
        assert not isinstance(SimpleNamespace(), UserAgentLookup)
        assert not isinstance(object(), UserAgentLookup)

    def test_object_with_only_os_family_is_not_a_lookup(self) -> None:
        assert not isinstance(SimpleNamespace(os_family=lambda ua: "x"), UserAgentLookup)
