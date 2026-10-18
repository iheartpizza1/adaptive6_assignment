"""Renders reports in the plain-text shape of the assignment sample."""

from __future__ import annotations

from weblogstats.contracts import DimensionReport


class TextReportFormatter:
    """ReportFormatter that prints ``Name:`` blocks of ``label pct%`` rows."""

    def format(self, reports: list[DimensionReport]) -> str:
        blocks = [self._block(report) for report in reports]
        return "\n".join(blocks)

    @staticmethod
    def _block(report: DimensionReport) -> str:
        lines = [f"{report.name}:"]
        lines.extend(f"{label} {percent:.2f}%" for label, percent in report.rows)
        return "\n".join(lines) + "\n"
