from __future__ import annotations

import pytest

from weblogstats.contracts import UNKNOWN
from weblogstats.lookups.label_normalizer import LabelNormalizer


class TestLabelNormalizerForBrowser:
    @pytest.mark.parametrize(
        "family", ["Chrome", "Firefox", "Mobile Safari", "IE", "Googlebot", "Edge"]
    )
    def test_real_families_are_kept(self, family: str) -> None:
        assert LabelNormalizer.for_browser().normalize(family) == family

    def test_ie_is_never_mapped_to_edge(self) -> None:
        assert LabelNormalizer.for_browser().normalize("IE") != "Edge"

    @pytest.mark.parametrize("family", [None, "", "Other", "-"])
    def test_unknown_rules_apply(self, family: str | None) -> None:
        assert LabelNormalizer.for_browser().normalize(family) == UNKNOWN
