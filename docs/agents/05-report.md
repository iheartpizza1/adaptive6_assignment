# Agent brief: report (Wave 1)

- **Branch:** `dev/report`
- **Runs:** in parallel with parser, geoip and ua, after `dev/bootstrap` is merged.
- **Read first:** [`00-common.md`](00-common.md), then HLD §4 (denominator, Other, rounding), §10 (output contract), §11.

## You own

- `src/weblogstats/aggregation/counting_aggregator.py` → `CountingAggregator`
- `src/weblogstats/formatting/text_report_formatter.py` → `TextReportFormatter`
- Re-exports in `aggregation/__init__.py` and `formatting/__init__.py`
- `tests/aggregation/test_counting_aggregator.py`, `tests/formatting/test_text_report_formatter.py`

You depend only on `contracts` (`DimensionReport`, `UNKNOWN`).

## Checklist (TDD each item)

### CountingAggregator

1. `observe(dimension, label)` counts per dimension (a `Counter` per dimension name).
2. `snapshot()` returns one `DimensionReport` per dimension, in **first-observed dimension order** (the CLI registration order decides the print order).
3. Percent = `count / dimension_total * 100`, where the dimension total is the sum of that dimension's counts. Rows are sorted by count descending, then label ascending.
4. Rows keep full float precision. Rounding is the formatter's job.
5. `snapshot(other_below=X)`: labels with percent `< X` are merged into a single `Other` row, which is **always last**. An existing label literally named `Other` is merged into it too. If nothing is below the threshold, there is no `Other` row. `Unknown` is a normal label: it can be merged into Other if small (document this choice in a test name).
6. A dimension with zero observations produces no report. An empty aggregator → `[]`.
7. Percentages of each report sum to 100 within 1e-9 (property-style test over a few random count sets, with a fixed seed).

### TextReportFormatter

8. Output contract (HLD §10):
   - heading `Name:`
   - one `label pct%` row per line, with `f"{pct:.2f}"` (two decimals, always)
   - one blank line between dimension blocks
   - a trailing newline at the end
   - no trailing spaces
9. A golden string test with three dimensions, matching the shape of the assignment sample exactly (use the sample's labels and percentages as input rows).
10. Labels containing spaces (`United States`, `Mobile Safari`) are printed unchanged.
11. An empty report list → an empty string.

## Done when

All the above pass, the full suite is green, and ruff is clean. PR presented per `00-common.md`. Title: `Wave 1: counting aggregator and text report formatter`.
