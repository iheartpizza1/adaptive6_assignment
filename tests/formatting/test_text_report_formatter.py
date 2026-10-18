from __future__ import annotations

from weblogstats.contracts import DimensionReport, ReportFormatter
from weblogstats.formatting.text_report_formatter import TextReportFormatter

SAMPLE_REPORTS = [
    DimensionReport(
        name="Country",
        rows=(
            ("United States", 35.10),
            ("United Kingdom", 27.55),
            ("Ukraine", 20.33),
            ("China", 10.34),
            ("Bolivia", 4.38),
            ("Other", 2.30),
        ),
    ),
    DimensionReport(
        name="OS",
        rows=(("Windows", 64.36), ("Mac OS", 22.15), ("Linux", 12.38), ("Unknown", 1.11)),
    ),
    DimensionReport(
        name="Browser",
        rows=(("Chrome", 35.45), ("Safari", 29.28), ("Edge", 23.17), ("Unknown", 12.10)),
    ),
]

SAMPLE_OUTPUT = """\
Country:
United States 35.10%
United Kingdom 27.55%
Ukraine 20.33%
China 10.34%
Bolivia 4.38%
Other 2.30%

OS:
Windows 64.36%
Mac OS 22.15%
Linux 12.38%
Unknown 1.11%

Browser:
Chrome 35.45%
Safari 29.28%
Edge 23.17%
Unknown 12.10%
"""


class TestTextReportFormatter:
    def test_satisfies_the_report_formatter_protocol(self) -> None:
        assert isinstance(TextReportFormatter(), ReportFormatter)

    def test_is_re_exported_from_the_package(self) -> None:
        from weblogstats.formatting import TextReportFormatter as Exported

        assert Exported is TextReportFormatter

    def test_three_dimensions_match_the_assignment_sample_exactly(self) -> None:
        assert TextReportFormatter().format(SAMPLE_REPORTS) == SAMPLE_OUTPUT

    def test_a_single_block_has_a_heading_rows_and_one_trailing_newline(self) -> None:
        report = DimensionReport(name="OS", rows=(("Windows", 60.0), ("Linux", 40.0)))

        assert TextReportFormatter().format([report]) == "OS:\nWindows 60.00%\nLinux 40.00%\n"

    def test_percentages_always_show_two_decimals(self) -> None:
        report = DimensionReport(name="OS", rows=(("A", 100.0), ("B", 12.5), ("C", 0.0)))

        assert TextReportFormatter().format([report]) == "OS:\nA 100.00%\nB 12.50%\nC 0.00%\n"

    def test_full_precision_percentages_are_rounded_to_two_decimals(self) -> None:
        report = DimensionReport(name="OS", rows=(("A", 200 / 3), ("B", 100 / 3)))

        assert TextReportFormatter().format([report]) == "OS:\nA 66.67%\nB 33.33%\n"

    def test_labels_with_spaces_are_printed_unchanged(self) -> None:
        reports = [
            DimensionReport(name="Country", rows=(("United States", 70.0),)),
            DimensionReport(name="Browser", rows=(("Mobile Safari", 30.0),)),
        ]

        output = TextReportFormatter().format(reports)

        assert "United States 70.00%\n" in output
        assert "Mobile Safari 30.00%\n" in output

    def test_no_line_has_trailing_spaces_and_blocks_are_separated_by_one_blank_line(self) -> None:
        output = TextReportFormatter().format(SAMPLE_REPORTS)

        assert all(line == line.rstrip() for line in output.splitlines())
        assert output.endswith("%\n")
        assert not output.endswith("\n\n")
        assert "\n\n\n" not in output
        assert output.count("\n\n") == len(SAMPLE_REPORTS) - 1

    def test_an_empty_report_list_gives_an_empty_string(self) -> None:
        assert TextReportFormatter().format([]) == ""
