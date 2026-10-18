# Agent brief: compose (Wave 2)

- **Branch:** `dev/compose`
- **Runs:** alone, after all four Wave 1 PRs (parser, geoip, user-agent, report) are merged into `master`.
- **Read first:** [`00-common.md`](00-common.md), then HLD §6, §7 (flow), §9 (extensibility), §10, §11, §13.

You wire the existing pieces together and document them. **Do not change the internals of plugins.** If a Wave 1 class has a bug, write a failing test that shows it, mark it `xfail(strict=True, reason=...)`, and report it in the PR.

## You own

- `src/weblogstats/pipeline.py` → `Pipeline`
- `src/weblogstats/cli.py` (replace the stub)
- `tests/test_pipeline.py`, `tests/test_cli.py`, `tests/test_golden.py`, `tests/fixtures/sample.expected.txt`
- `README.md`: the **Usage** and **Extending** sections. Leave Requirements / Install / Development as they are, except to fix facts that are now wrong.

## Checklist (TDD each item)

### Pipeline(source, parser, dimensions, aggregator)

1. `run() -> RunStats`, in one streaming pass. For each line:
   - `stats.total += 1`
   - `parser.parse(line)`
   - `None` → `LogRecord.unreadable(line)` and `stats.unreadable += 1`
   - `partial` → `stats.partial += 1`
   - else `stats.strict += 1`
   - then `aggregator.observe(d.name, d.extract(record))` for each dimension
2. Every dimension observes exactly `stats.total` labels. Test this with fakes: a source over in-memory lines plus `FakeGeoIp` / `FakeUserAgentLookup`.
3. One dimension raising for one record must not abort the run. That record gets `Unknown` for that dimension. Test with a raising fake dimension.

### cli.main(argv) -> int (the composition root)

4. Builds:
   - `FileLogSource`
   - `ApacheCombinedParser`
   - `MaxMindGeoIp`, used as a context manager
   - `UaParserLookup(LabelNormalizer.for_os(), LabelNormalizer.for_browser())`
   - `[CountryDimension, OsDimension, BrowserDimension]`: a plain list, which is the documented registration point
   - `CountingAggregator`
   - `TextReportFormatter`

   It then runs the pipeline and prints the report to stdout and `stats.summary()` to stderr.
5. Exit codes: 0 on success; 1 with a clear stderr message for a missing log, a missing MMDB or a wrong DB edition. No partial report is printed on these errors.
6. `--other-below X` is passed to `snapshot`.
6a. **Bad-line log:**
   - Add `--errors-file PATH` (default `weblogstats-errors.log` in the current directory).
   - Wrap the parser as `LoggingParser(ApacheCombinedParser(), BadLineLog(path))`, opening `BadLineLog` as a context manager so it is closed on every exit path.
   - Open it only after the input checks (log exists, MMDB valid), so a failed start never truncates an earlier run's errors file.
   - After the stats summary, write a second stderr line: `bad lines: 1 warn, 0 error → weblogstats-errors.log`.
   - `AppConfig` has no field for the path, so pass it alongside the config without changing the contract, and note this in the PR as a candidate contract addition.
   - Add `weblogstats-errors.log` to `.gitignore` (one line; you may touch only this line of that file).
   - Tests:
     - The golden run writes exactly the two expected entries for the fixture (1 WARN, 1 ERROR).
     - A failed start (missing log) leaves a pre-existing errors file untouched.
     - The data test asserts the errors file has exactly one `WARN partial` line.
7. **Golden test:** run `main` on `tests/fixtures/sample.log` with `FakeGeoIp` injected. Give `main` an optional, test-only keyword argument (e.g. `geoip_factory`), or factor the wiring into a `build_pipeline(config, geoip)` function in `cli.py`. Compare stdout to `sample.expected.txt` exactly. Real ua-parser is fine here.
8. **Data test (`@pytest.mark.data`):** run the real CLI on the full log with the real MMDB. Assert:
   - stderr `total=10000 strict=9999 partial=1 unreadable=0`
   - three blocks in the order Country, OS, Browser
   - every percentage formatted with two decimals
   - each block sums to 100 ± 0.05
   - no label `Other` unless `--other-below` is set
   - `Unknown` appears in OS and Browser
9. Run it once by hand and paste the full stdout into the PR body.

### README

10. **Usage:** the command line (`weblogstats apache_log.txt --geoip data/GeoLite2-Country.mmdb`, plus `python -m weblogstats`), every flag, the env var `GEOIP_DB`, real sample output (the top lines of each block from the 10k run), the stderr summary, the exit codes, the **errors file** (location, the `--errors-file` flag, the entry format with a WARN and an ERROR example, and that it is truncated on every run), and how the denominator, Unknown and Other behave (one short paragraph each, linking the HLD).
11. **Extending**, as step-by-step recipes. Each names the file to create (one class per file), the test to write first, and the one line to register:
    - **New dimension:** a worked `StatusDimension` (status → `2xx`/`3xx`/`4xx`/`5xx`/`Unknown`). Show the full class and test code in the README. Add a temporary test in your worktree that follows the recipe literally, run it, then delete the test and the class before committing. The README is documentation and the shipped CLI keeps three dimensions. Mention in the PR that you verified the recipe.
    - **New output format:** e.g. `formatting/json_report_formatter.py`, plus the `--format` choice.
    - **New log dialect:** a new `LogParser`.
    - **Filtering records:** e.g. a `--exclude-bots` `RecordFilter`. Describe the design only; it is not built in v1.

## Done when

All the above pass, the full suite is green, and ruff is clean. The real 10k run works end to end. PR presented per `00-common.md`, with the 10k output in the body. Title: `Wave 2: pipeline, CLI wiring, golden tests and README usage/extending`.
