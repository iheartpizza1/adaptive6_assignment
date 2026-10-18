from __future__ import annotations

import dataclasses

import pytest

from weblogstats.contracts import DimensionReport


class TestDimensionReport:
    def test_holds_name_and_rows(self) -> None:
        report = DimensionReport(name="OS", rows=(("Windows", 64.36), ("Linux", 3.0)))
        assert report.name == "OS"
        assert report.rows == (("Windows", 64.36), ("Linux", 3.0))

    def test_is_frozen(self) -> None:
        report = DimensionReport(name="OS", rows=())
        with pytest.raises(dataclasses.FrozenInstanceError):
            report.name = "Browser"  # type: ignore[misc]

    def test_equal_reports_hash_equal(self) -> None:
        a = DimensionReport(name="OS", rows=(("Windows", 1.0),))
        b = DimensionReport(name="OS", rows=(("Windows", 1.0),))
        assert a == b
        assert hash(a) == hash(b)
