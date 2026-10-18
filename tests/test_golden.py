"""Golden runs: the whole CLI over tests/fixtures/sample.log, and over the real 10k log."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.fakes.fake_geo_ip import FakeGeoIp
from weblogstats.cli import main
from weblogstats.contracts import GeoIpLookup

EXPECTED = Path(__file__).resolve().parent / "fixtures" / "sample.expected.txt"

# Countries for the public IPs in sample.log. 10.0.0.1 is private and so is left out: Unknown.
SAMPLE_COUNTRIES = {
    "83.149.9.216": "Russia",
    "46.118.127.106": "Ukraine",
    "200.49.190.101": "Argentina",
    "218.30.103.62": "China",
    "201.242.142.135": "Venezuela",
    "186.93.16.149": "Venezuela",
    "66.249.73.185": "United States",
    "46.105.14.53": "France",
    "106.78.19.160": "India",
    "110.136.166.128": "Indonesia",
    "24.236.252.67": "United States",
    "50.195.216.83": "United States",
    "212.201.44.247": "Germany",
    "36.38.8.174": "South Korea",
    "89.170.74.95": "Russia",
    "37.115.186.244": "Ukraine",
}

PERCENT_ROW = re.compile(r"^.+ (\d+\.\d{2})%$")


def _fake_geoip(path: Path, cache_size: int) -> GeoIpLookup:
    return FakeGeoIp(SAMPLE_COUNTRIES)


def _blocks(stdout: str) -> dict[str, list[tuple[str, float]]]:
    """Parse a report into {heading: [(label, percent)]}, keeping the heading order."""
    blocks: dict[str, list[tuple[str, float]]] = {}
    for block in stdout.strip().split("\n\n"):
        heading, *rows = block.splitlines()
        parsed = []
        for row in rows:
            match = PERCENT_ROW.match(row)
            assert match, f"percentage without two decimals: {row!r}"
            parsed.append((row.rsplit(" ", 1)[0], float(match.group(1))))
        blocks[heading.removesuffix(":")] = parsed
    return blocks


class TestGolden:
    def test_sample_log_matches_the_expected_report_exactly(
        self, sample_log_path: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        errors = tmp_path / "errors.log"
        assert (
            main([str(sample_log_path), "--errors-file", str(errors)], geoip_factory=_fake_geoip)
            == 0
        )
        captured = capsys.readouterr()
        assert captured.out == EXPECTED.read_text(encoding="utf-8")
        assert captured.err.splitlines() == [
            "total=19 strict=17 partial=1 unreadable=1",
            f"bad lines: 1 warn, 1 error → {errors}",
        ]

    def test_sample_log_writes_exactly_the_two_expected_errors_file_entries(
        self, sample_log_path: Path, tmp_path: Path
    ) -> None:
        errors = tmp_path / "errors.log"
        main([str(sample_log_path), "--errors-file", str(errors)], geoip_factory=_fake_geoip)
        lines = sample_log_path.read_text(encoding="ascii").splitlines()
        truncated, garbage = lines[1], lines[19]
        warn_entry, error_entry = errors.read_text(encoding="utf-8").splitlines()
        stamp = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z"
        assert re.fullmatch(f"{stamp} WARN partial {re.escape(truncated)}", warn_entry)
        assert re.fullmatch(f"{stamp} ERROR unreadable {re.escape(garbage)}", error_entry)

    def test_every_block_of_the_sample_sums_to_100(
        self, sample_log_path: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        errors = tmp_path / "errors.log"
        main([str(sample_log_path), "--errors-file", str(errors)], geoip_factory=_fake_geoip)
        blocks = _blocks(capsys.readouterr().out)
        assert list(blocks) == ["Country", "OS", "Browser"]
        for rows in blocks.values():
            assert sum(percent for _, percent in rows) == pytest.approx(100, abs=0.05)

    @pytest.mark.data
    def test_full_log_with_the_real_mmdb(
        self,
        apache_log_path: Path,
        geoip_db_path: Path,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        errors = tmp_path / "errors.log"
        argv = [str(apache_log_path), "--geoip", str(geoip_db_path), "--errors-file", str(errors)]
        assert main(argv) == 0
        captured = capsys.readouterr()
        assert captured.err.splitlines()[0] == "total=10000 strict=9999 partial=1 unreadable=0"
        blocks = _blocks(captured.out)
        assert list(blocks) == ["Country", "OS", "Browser"]
        for rows in blocks.values():
            assert sum(percent for _, percent in rows) == pytest.approx(100, abs=0.05)
            assert "Other" not in [label for label, _ in rows]
        assert "Unknown" in [label for label, _ in blocks["OS"]]
        assert "Unknown" in [label for label, _ in blocks["Browser"]]
        entries = errors.read_text(encoding="utf-8").splitlines()
        assert len(entries) == 1
        assert re.search(r"Z WARN partial ", entries[0])
        assert captured.err.splitlines()[1].startswith("bad lines: 1 warn, 0 error")

    @pytest.mark.data
    def test_full_log_with_other_below_ends_each_block_in_other(
        self,
        apache_log_path: Path,
        geoip_db_path: Path,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        errors = tmp_path / "errors.log"
        argv = [
            str(apache_log_path),
            "--geoip",
            str(geoip_db_path),
            "--other-below",
            "1",
            "--errors-file",
            str(errors),
        ]
        assert main(argv) == 0
        blocks = _blocks(capsys.readouterr().out)
        for rows in blocks.values():
            assert rows[-1][0] == "Other"
