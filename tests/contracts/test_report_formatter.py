from __future__ import annotations

from types import SimpleNamespace

from weblogstats.contracts import ReportFormatter


class TestReportFormatter:
    def test_object_with_the_members_satisfies_the_protocol(self) -> None:
        candidate = SimpleNamespace(format=lambda reports: "")
        assert isinstance(candidate, ReportFormatter)

    def test_object_missing_the_members_does_not_satisfy_the_protocol(self) -> None:
        assert not isinstance(SimpleNamespace(), ReportFormatter)
        assert not isinstance(object(), ReportFormatter)
