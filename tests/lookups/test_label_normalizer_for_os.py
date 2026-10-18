from __future__ import annotations

import pytest

from weblogstats.contracts import UNKNOWN
from weblogstats.lookups.label_normalizer import LabelNormalizer


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
