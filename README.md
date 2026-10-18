# adaptive6_assignment

Home Assignment from Adaptive6.

`weblogstats` reads an Apache combined-format access log and prints the share of requests by
Country, OS and Browser. See [docs/hld.html](docs/hld.html) for the design.

## Requirements

- Python 3.12 or newer (developed and tested on 3.14).
- Runtime dependencies: `geoip2` (5.x or newer) and `ua-parser` (1.x or newer). Both are installed
  by `pip`.
- Development dependencies: `pytest` and `ruff`.
- The MaxMind **GeoLite2-Country** database (`GeoLite2-Country.mmdb`), downloaded free from a
  [MaxMind account](https://www.maxmind.com/en/geolite2/signup). The GeoLite2 **ASN** edition will
  not work: it has no country data, and the tool rejects it at startup.
- The Apache log file to analyze (`apache_log.txt` for this assignment).

The MMDB and the log are not redistributable and are not committed; both are git-ignored.

## Install

Run these from the repository root in PowerShell. Create the virtual environment and install the
package into it:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

PowerShell does not run a relative path such as `.venv\Scripts\python` without the leading `.\`,
so always write `.\.venv\Scripts\...` as above. On macOS or Linux use `.venv/bin/python` instead.

Put `GeoLite2-Country.mmdb` in the `data/` folder, or point the `GEOIP_DB` environment variable (or
the `--geoip` flag) at it wherever it lives. Check the install with:

```powershell
.\.venv\Scripts\weblogstats.exe --help
```

## Usage

Installing the package does not add `weblogstats` to your PATH. Use one of the two ways below.

**Option A: no activation (recommended).** Call the executable in the venv directly:

```powershell
.\.venv\Scripts\weblogstats.exe apache_log.txt --geoip data\GeoLite2-Country.mmdb --other-below 2
```

**Option B: activate the venv for this PowerShell window.** Then `weblogstats` works by its short
name, and the prompt shows `(.venv)`:

```powershell
.\.venv\Scripts\Activate.ps1
weblogstats apache_log.txt --geoip data\GeoLite2-Country.mmdb --other-below 2
deactivate
```

Activation lasts only for the current window, so activate again in each new one. If PowerShell
reports that running scripts is disabled, allow local scripts once for your user account, then
activate again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

You can also run it as a module, with no activation and no executable:

```powershell
.\.venv\Scripts\python.exe -m weblogstats apache_log.txt --geoip data\GeoLite2-Country.mmdb --other-below 2
```

For this assignment, the full command that writes the report to a file is:

```powershell
.\.venv\Scripts\weblogstats.exe apache_log.txt --geoip data\GeoLite2-Country.mmdb > report.txt
```

The report goes to **stdout** and the run summary to **stderr**, so `> report.txt` keeps the two
apart. Both streams are written as UTF-8.

### Flags

| Flag | Default | Meaning |
|---|---|---|
| `log` (positional) | required | Path to an Apache combined-format log file. |
| `--geoip PATH` | `$GEOIP_DB`, else `data/GeoLite2-Country.mmdb` | The MaxMind GeoLite2 **Country** (or City) MMDB. |
| `--format {text}` | `text` | Output format. Only `text` exists today; see [Extending](#extending). |
| `--other-below FLOAT` | off | Roll every row below this percentage into one `Other` row at the end of its block, reducing output lines for small dimention counts. |
| `--errors-file PATH` | `$WEBLOGSTATS_ERRORS_FILE`, else `[output] errors_file` in the config file, else `weblogstats-errors.log` | Where partial and unreadable lines are logged. See [The errors file](#the-errors-file). |
| `--config PATH` | `$WEBLOGSTATS_CONFIG`, else `config/weblogstats.toml` if it exists | TOML settings file: lookup cache sizes and the errors file. See [The config file](#the-config-file). |
| `-h`, `--help` | | Show the usage and exit. |

Environment variables set defaults for flags, and the flag wins when both are given: `GEOIP_DB`
for `--geoip`, `WEBLOGSTATS_CONFIG` for `--config` and `WEBLOGSTATS_ERRORS_FILE` for
`--errors-file`. An empty variable counts as unset.

### The config file

Lookup cache sizes (per lookup) and the errors-file path are set in a TOML file, read with the
standard library's `tomllib`. The repository ships
[`config/weblogstats.toml`](config/weblogstats.toml):

```toml
# Per-lookup settings. Add a [lookups.<name>] table for a new lookup.
[lookups.geoip]
cache_size = 3506   # 2 x 1,753 unique client IPs in apache_log.txt

[lookups.user_agent]
cache_size = 1116   # 2 x 558 distinct User-Agent strings reaching the cache in apache_log.txt

# Run outputs. Relative paths are relative to the current directory.
# --errors-file and WEBLOGSTATS_ERRORS_FILE both override this.
[output]
errors_file = "weblogstats-errors.log"
```

`cache_size` is the number of entries the lookup's LRU cache holds, an integer of at least 1.
A lookup with no table (or no `cache_size`) keeps the default built into its constructor.
`[output] errors_file` is a non-empty path string; a relative path is relative to the current
directory, not to the config file. Every table and key is optional.

The file is found in this order: the `--config` flag, then the `WEBLOGSTATS_CONFIG` environment
variable, then `config/weblogstats.toml` relative to the current directory if it exists, and
otherwise no file at all (every lookup uses its own default). A file that is missing, is not valid
TOML, has a bad value (zero, negative, a string, a boolean, an empty `errors_file`), has a
misspelled key inside a lookup table or `[output]`, or has a `lookups.<name>` or `output` that is
not a table stops the run with exit code 1 and a message
naming the file and the key. An unknown lookup *name* is allowed, for forward compatibility.

### Sample output

This is the top of each block from a run over the real 10,000-line `apache_log.txt` (the full
output has 95 countries, 11 operating systems and 98 browsers):

```
Country:
United States 39.10%
France 8.66%
Germany 5.73%
Sweden 4.38%
India 4.26%
China 4.16%
...

OS:
Windows 33.17%
Unknown 24.50%
Linux 21.37%
Mac OS 14.44%
iOS 4.29%
Android 2.04%
...

Browser:
Chrome 28.92%
Firefox 26.07%
Unknown 11.34%
Googlebot 5.10%
IE 4.86%
Safari 2.62%
...
```

Each block is `Name:` followed by `label percent%` rows, sorted by share descending and then by label.
Percentages always have two decimals. They are rounded one by one, so a block may sum to 99.99 or
100.01 rather than exactly 100.00. See the [output contract](docs/hld.html#output).

The stderr summary for that run:

```
total=10000 strict=9999 partial=1 unreadable=0
bad lines: 1 warn, 0 error → weblogstats-errors.log
```

`total` is the number of non-empty lines. `strict` lines matched the Apache combined format,
`partial` lines were truncated or damaged but still yielded an IP and a User-Agent, and
`unreadable` lines yielded nothing. The three parts always add up to `total`.

If a dimension raises for a record (a plugin bug), that record is counted as `Unknown` in that
dimension, the run carries on, and the summary gains a field at the end, for example
`total=10000 strict=9999 partial=1 unreadable=0 extract_errors=3`. The field counts failed
extractions, not lines, and is left out entirely when it is zero, as in the run above.

### Exit codes

| Code | Meaning |
|---|---|
| `0` | The report was printed. |
| `1` | The log file is missing, the MMDB is missing or unreadable, the MMDB is the wrong edition (for example GeoLite2-ASN), the config file is missing or invalid, or the errors file cannot be written. A one-line `weblogstats: error: ...` goes to stderr and **no report is printed**. |
| `2` | Usage error, such as a missing `log` argument or a non-numeric `--other-below`. |

### The errors file

Every line that is not a clean match is also written, in full, to the errors file. Its path is
the first of these that is set:

1. the `--errors-file PATH` flag
2. the `WEBLOGSTATS_ERRORS_FILE` environment variable
3. `errors_file` in the `[output]` table of the [config file](#the-config-file)
4. the default, `weblogstats-errors.log` in the current directory

The second stderr line always names the path that was used. One entry per line:

```
<UTC timestamp> <LEVEL> <kind> <the full original line>
```

- `WARN partial` marks a line the lenient fallback had to rescue. The real log has one:

  ```
  2026-10-18T11:02:14.518Z WARN partial 46.118.127.106 - - [20/May/2015:12:05:17 +0000] "GET /scripts/grok-py-test/configlib.py HTTP/1.1" 200 235 "-" "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html
  ```

- `ERROR unreadable` marks a line from which nothing could be recovered:

  ```
  2026-10-18T11:02:14.519Z ERROR unreadable this is not a log line
  ```

The file is **truncated at the start of every run**, so an empty file means that run had no bad
lines. It is opened only after the log and the MMDB have been checked, so a run that fails to
start (including one with an unusable config file) leaves the previous file alone. Add the file to your own `.gitignore` if you run the tool
inside a repository; this repository already ignores `weblogstats-errors.log`.

### Denominator, Unknown and Other

**Denominator.** Percentages are shares of *all non-empty lines*, 10,000 for the sample log. A
line that cannot be parsed still counts, as `Unknown` in every dimension, so every block sums to
about 100% over the same base. Blank lines are skipped and not counted. See
[HLD section 4](docs/hld.html#assumptions).

**Unknown.** `Unknown` is an ordinary row, never an error. It is what a dimension returns when it
cannot classify a record: a private or unmapped IP, a User-Agent of `-`, an unknown OS or browser
family, or an unreadable line. See [HLD section 11](docs/hld.html#errors).

**Other.** Without `--other-below` no row is ever called `Other`. With `--other-below 1`, each
block's rows under 1% (including a small `Unknown`) are merged into one `Other` row, which is
always last. See [HLD section 11](docs/hld.html#errors).

## Extending

The pipeline is `LogSource` → `LogParser` → `Dimension`s → `Aggregator` → `ReportFormatter`
([HLD section 6](docs/hld.html#architecture) and [section 9](docs/hld.html#extensibility)). The
composition root is `src/weblogstats/cli.py`; every extension below registers in it. Keep to the
repository rules: **one class per file** (the test class too), test first, and never edit a
contract in `src/weblogstats/contracts/` to make an extension fit.

### New dimension: a worked `StatusDimension`

Goal: a fourth block, `Status:`, that groups requests into `2xx`, `3xx`, `4xx` and `5xx`.

**1. Write the test first**, in `tests/dimensions/test_status_dimension.py`, and watch it fail:

```python
from __future__ import annotations

from dataclasses import replace

import pytest

from weblogstats.contracts import UNKNOWN, Dimension, LogRecord
from weblogstats.dimensions.status_dimension import StatusDimension


def _record(status: int | None) -> LogRecord:
    return replace(LogRecord.unreadable(""), status=status)


class TestStatusDimension:
    def test_satisfies_the_dimension_protocol(self) -> None:
        assert isinstance(StatusDimension(), Dimension)

    def test_name_is_the_printed_heading(self) -> None:
        assert StatusDimension().name == "Status"

    @pytest.mark.parametrize(
        ("status", "label"),
        [(200, "2xx"), (204, "2xx"), (301, "3xx"), (304, "3xx"), (404, "4xx"), (503, "5xx")],
    )
    def test_labels_the_status_class(self, status: int, label: str) -> None:
        assert StatusDimension().extract(_record(status)) == label

    @pytest.mark.parametrize("status", [None, 0, 99, 600, 999])
    def test_anything_else_is_unknown(self, status: int | None) -> None:
        assert StatusDimension().extract(_record(status)) == UNKNOWN
```

**2. Write the class**, in `src/weblogstats/dimensions/status_dimension.py`, until the test passes:

```python
"""The Status metric."""

from __future__ import annotations

from weblogstats.contracts import UNKNOWN, LogRecord


class StatusDimension:
    """Labels each record with its HTTP status class: 2xx, 3xx, 4xx or 5xx."""

    name = "Status"

    def extract(self, record: LogRecord) -> str:
        if record.status is None or not 200 <= record.status < 600:
            return UNKNOWN
        return f"{record.status // 100}xx"
```

`name` is the heading the report prints. `extract` must return a label and use `UNKNOWN` when it
cannot classify; an unreadable line arrives as a record with `status=None`, so it lands in
`Unknown` without special handling. Constructor arguments are for lookups the dimension needs
(see `CountryDimension(geoip)`); this one needs none.

**3. Register it.** In `src/weblogstats/cli.py`, add the import and one entry to the list in
`build_dimensions`:

```python
from weblogstats.dimensions.status_dimension import StatusDimension
...
    return [CountryDimension(geoip), OsDimension(ua), BrowserDimension(ua), StatusDimension()]
```

The aggregator and the formatter know nothing about dimensions, so nothing else changes. On
`tests/fixtures/sample.log` the new block reads `2xx 84.21%`, `3xx 5.26%`, `4xx 5.26%`,
`Unknown 5.26%`. Update `tests/fixtures/sample.expected.txt` for the golden test when you
register a real dimension.

### Configuring a new lookup

Goal: give a new lookup (say `geo_city`, built in `cli.py`) its own cache size from the config file.

1. **Test first**, in `tests/test_cli_config.py` style: write a TOML file with a `[lookups.geo_city]`
   table, run `main` with `--config`, and assert the size reaches the lookup (see how the existing
   tests spy on the geoip factory and on `UaParserLookup`).
2. **Add the table** to `config/weblogstats.toml`:

   ```toml
   [lookups.geo_city]
   cache_size = 2000
   ```

3. **Read it where the lookup is built**, in `cli.py`, with a module constant for the name next to
   the other two (`GEOIP_LOOKUP`, `USER_AGENT_LOOKUP`):

   ```python
   GEO_CITY_LOOKUP = "geo_city"
   ...
   GeoCityLookup(cache_size=settings.cache_size(GEO_CITY_LOOKUP, GeoCityLookup.DEFAULT_CACHE_SIZE))
   ```

`LookupSettings` itself does not change: it holds a generic name to settings mapping, so a new
lookup only adds a section to the file and the one line above.

### New output format

Goal: `--format json`.

1. **Test first**, in `tests/formatting/test_json_report_formatter.py`: build a list of
   `DimensionReport` objects, call `JsonReportFormatter().format(reports)`, and assert on the
   parsed JSON. Also assert `isinstance(JsonReportFormatter(), ReportFormatter)`.
2. **Class**, in `src/weblogstats/formatting/json_report_formatter.py`, with one method,
   `format(self, reports: list[DimensionReport]) -> str`. `DimensionReport` has `name` and
   `rows`, a tuple of `(label, percent)`.
3. **Re-export** it in `formatting/__init__.py`.
4. **Register** it with one entry in `_FORMATTERS` in `cli.py`; the `--format` choices are
   built from that dict:

   ```python
   _FORMATTERS = {"text": TextReportFormatter, "json": JsonReportFormatter}
   ```

### New log dialect

Goal: read another access-log format (CLF without the User-Agent, JSON lines, nginx).

1. **Test first**, in `tests/parsing/test_<your_parser>.py`, with a few real lines of that
   dialect: assert the `LogRecord` fields, and `None` for a line with no recoverable IP.
2. **Class**, in `src/weblogstats/parsing/<your_parser>.py`, implementing
   `parse(self, line: str) -> LogRecord | None`. Keep `LogRecord` as it is and leave the fields
   the dialect lacks empty (`""`, `None`). Return `None` only when nothing can be recovered, and
   set `partial=True` on a record rebuilt by a fallback.
3. **Register** it by replacing `ApacheCombinedParser()` in the `LoggingParser(...)` call in
   `cli.py` (or choosing between them with a new flag). Keep the `LoggingParser` wrapper, which
   is what feeds the errors file.

### Filtering records (design only, not built in v1)

An `--exclude-bots` flag would be a `RecordFilter` Protocol in `contracts/`:
`def keep(self, record: LogRecord) -> bool`. `Pipeline` would take a list of filters and skip a
record that any filter rejects, before the dimensions see it. A `BotFilter` would implement it
using ua-parser's device family `Spider` plus a small regex for feed readers. Filtered records
would leave the denominator, and the stderr summary would gain a `filtered=N` count. Dimensions
and the aggregator stay unchanged. See [HLD section 9](docs/hld.html#extensibility).

## Development

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```

Tests marked `@pytest.mark.data` need the real log or the MMDB and are skipped when the file is
missing. They read `APACHE_LOG` and `GEOIP_DB` from the environment, falling back to
`apache_log.txt` and `data/GeoLite2-Country.mmdb` under the repo root. Set both so they run:

```powershell
$env:APACHE_LOG = "C:\path\to\apache_log.txt"
$env:GEOIP_DB = "C:\path\to\GeoLite2-Country.mmdb"
```

### Layout

```
src/weblogstats/
  __init__.py  __main__.py
  cli.py                              # main(argv) composition root, no class
  pipeline.py                         # Pipeline (one pass: parse, extract, observe)
  config/lookup_settings.py           # LookupSettings (per-lookup settings from TOML)
  config/output_settings.py           # OutputSettings ([output] errors_file from TOML)
  contracts/                          # Protocols and dataclasses shared by every module
    log_record.py  log_source.py  log_parser.py  dimension.py
    geo_ip_lookup.py  user_agent_lookup.py  dimension_report.py
    aggregator.py  report_formatter.py  run_stats.py  app_config.py  unknown.py
  sources/file_log_source.py          # FileLogSource
  parsing/apache_combined_parser.py   # ApacheCombinedParser (strict + lenient)
  parsing/logging_parser.py           # LoggingParser (decorator: reports bad lines)
  parsing/bad_line_log.py             # BadLineLog (the errors-file writer)
  lookups/maxmind_geo_ip.py           # MaxMindGeoIp
  lookups/ua_parser_lookup.py         # UaParserLookup
  lookups/label_normalizer.py         # LabelNormalizer (alias tables)
  dimensions/country_dimension.py     # CountryDimension
  dimensions/os_dimension.py          # OsDimension
  dimensions/browser_dimension.py     # BrowserDimension
  aggregation/counting_aggregator.py  # CountingAggregator
  formatting/text_report_formatter.py # TextReportFormatter
config/weblogstats.toml               # default settings (cache sizes, errors file)
tests/
  conftest.py                         # sample_log_path, apache_log_path, geoip_db_path
  fakes/                              # FakeGeoIp, FakeUserAgentLookup
  fixtures/sample.log                 # 20 lines, see tests/fixtures/README.md
  fixtures/sample.expected.txt        # exact stdout of the golden test on sample.log
  <mirrors src/: one test module per production class>
```

### Conventions

- **One class per file.** Every class (Protocol, dataclass, adapter, fake, test class) lives in its
  own module named after it in snake_case. `__init__.py` files only re-export.
- **Only the adapter modules import third-party libraries**: `geoip2` in `maxmind_geo_ip.py` and
  `ua_parser` in `ua_parser_lookup.py`.
- **Unknown values are the literal string `"Unknown"`.** A single bad record never raises.
- **Test first.** Write the failing test, make it pass with the minimum code, refactor, commit.
- **Branches and PRs.** Work happens on a `dev/*` branch, one per area. Run the full pytest suite,
  `ruff check` and `ruff format --check`, then open a PR into `master`. Nobody merges their own PR.
  The full rules are in [docs/agents/00-common.md](docs/agents/00-common.md).

## GeoIP database (MySQL)

IP → country lookups run against a local MySQL 8.4 database named `geoip`, built from the
MaxMind GeoLite2 **Country** CSVs following
[MaxMind's MySQL import guide](https://dev.maxmind.com/geoip/importing-databases/mysql/)
(adapted from the City columns it shows to the Country ones).

### Prerequisites

- MySQL Server 8.4 (`winget install Oracle.MySQL`), installed at `C:\Program Files\MySQL\MySQL Server 8.4`
- Python 3 (used by the CIDR → hex-range converter)
- `GeoLite2-Country-CSV_<date>.zip` in the repo root (update the default `-Zip` path in `db/setup.ps1` if the date differs)

### One-time setup

The winget package installs the binaries but no service or data directory:

```powershell
$bin = 'C:\Program Files\MySQL\MySQL Server 8.4\bin'
& "$bin\mysqld.exe" --initialize-insecure --datadir="$env:USERPROFILE\mysql-data"   # root has an empty password
.\db\server.ps1 start
.\db\setup.ps1 -MysqlBin "$bin\mysql.exe"     # converts the CSVs, creates the schema, loads ~1M ranges
```

The server listens on `127.0.0.1:3306` only. `root` has no password, so this is for local development only.

### Start / stop

```powershell
.\db\server.ps1 start    # also: stop, status
```

In Claude Code the same thing is available as `/db start`, `/db stop` and `/db status`.
The server is a plain background process, not a Windows service, so start it again after a reboot.

### Looking up an IP

```powershell
mysql -u root geoip -e "SET @ip='8.8.8.8'; source db/lookup.sql"
```

or run [db/lookup.sql](db/lookup.sql) with the `@ip` of your choice. It works for IPv4 and IPv6 and returns no row for
private or unknown addresses. From application code, connect with `root@127.0.0.1:3306/geoip` and run the same query
with the IP as a parameter in place of `@ip`.

### Layout

| File | Purpose |
|---|---|
| `db/schema.sql` | Creates the `geoip` database and the `geoip2_network` / `geoip2_location` tables |
| `db/load.sql` | `LOAD DATA LOCAL INFILE` for the IPv4, IPv6 and English locations CSVs |
| `db/lookup.sql` | IP → country query |
| `db/scripts/convert_blocks.py` | CIDR → hex start/end converter (replaces MaxMind's `geoip2-csv-converter`) |
| `db/setup.ps1` | Rebuilds the database from the zip |
| `db/server.ps1` | Start / stop / status for the server |

Generated import files land in `db/generated/` (git-ignored).
