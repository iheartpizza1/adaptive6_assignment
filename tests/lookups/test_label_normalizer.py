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


def test_is_re_exported_from_the_lookups_package() -> None:
    from weblogstats.lookups import LabelNormalizer as Exported

    assert Exported is LabelNormalizer


class TestLabelNormalizerForOs:
    def test_mac_os_x_becomes_mac_os(self) -> None:
        assert LabelNormalizer.for_os().normalize("Mac OS X") == "Mac OS"

    @pytest.mark.parametrize(
        "family", ["Windows", "Windows 7", "Windows XP", "Windows Vista", "Windows 10"]
    )
    def test_any_windows_family_becomes_windows(self, family: str) -> None:
        assert LabelNormalizer.for_os().normalize(family) == "Windows"

    @pytest.mark.parametrize(
        "family",
        [
            "Ubuntu",
            "Debian",
            "Fedora",
            "Linux Mint",
            "Red Hat",
            "CentOS",
            "Gentoo",
            "Arch Linux",
            "openSUSE",
            "Slackware",
        ],
    )
    def test_linux_distributions_become_linux(self, family: str) -> None:
        assert LabelNormalizer.for_os().normalize(family) == "Linux"

    @pytest.mark.parametrize("family", ["Linux", "iOS", "Android", "Chrome OS"])
    def test_other_real_families_are_kept(self, family: str) -> None:
        assert LabelNormalizer.for_os().normalize(family) == family

    @pytest.mark.parametrize("family", [None, "", "Other", "-"])
    def test_unknown_rules_apply(self, family: str | None) -> None:
        assert LabelNormalizer.for_os().normalize(family) == UNKNOWN


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
