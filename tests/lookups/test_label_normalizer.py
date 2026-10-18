from __future__ import annotations

import pytest

from weblogstats.contracts import UNKNOWN
from weblogstats.lookups.label_normalizer import LabelNormalizer


class TestLabelNormalizerRules:
    @pytest.mark.parametrize("family", [None, "", "Other", "-"])
    def test_empty_like_families_become_unknown(self, family: str | None) -> None:
        assert LabelNormalizer({}).normalize(family) == UNKNOWN

    def test_unknown_rule_wins_over_an_alias_for_the_same_key(self) -> None:
        assert LabelNormalizer({"Other": "Something"}).normalize("Other") == UNKNOWN

    def test_exact_alias_is_applied(self) -> None:
        normalizer = LabelNormalizer({"Mac OS X": "Mac OS"})
        assert normalizer.normalize("Mac OS X") == "Mac OS"

    def test_family_without_a_rule_is_unchanged(self) -> None:
        assert LabelNormalizer({"Mac OS X": "Mac OS"}).normalize("Chrome") == "Chrome"

    def test_prefix_alias_is_applied(self) -> None:
        normalizer = LabelNormalizer({}, [("Windows", "Windows")])
        assert normalizer.normalize("Windows 7") == "Windows"

    def test_first_matching_prefix_wins(self) -> None:
        normalizer = LabelNormalizer({}, [("Win", "First"), ("Windows", "Second")])
        assert normalizer.normalize("Windows 7") == "First"

    def test_exact_alias_beats_prefix_alias(self) -> None:
        normalizer = LabelNormalizer({"Windows Phone": "Windows Phone"}, [("Windows", "Windows")])
        assert normalizer.normalize("Windows Phone") == "Windows Phone"

    def test_prefix_match_is_case_sensitive_and_anchored_at_the_start(self) -> None:
        normalizer = LabelNormalizer({}, [("Windows", "Windows")])
        assert normalizer.normalize("Not Windows") == "Not Windows"
        assert normalizer.normalize("windows 7") == "windows 7"
