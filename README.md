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

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e .[dev]
```

On macOS or Linux use `.venv/bin/python` instead of `.venv\Scripts\python`.

Put `GeoLite2-Country.mmdb` in the `data/` folder, or point the `GEOIP_DB` environment variable (or
the `--geoip` flag) at it wherever it lives. `weblogstats --help` should now run.

## Usage

_Filled in by Wave 2._

## Extending

_Filled in by Wave 2._

## Development

```powershell
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m ruff check .
.venv\Scripts\python -m ruff format --check .
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
  pipeline.py                         # Pipeline
  contracts/                          # Protocols and dataclasses shared by every module
    log_record.py  log_source.py  log_parser.py  dimension.py
    geo_ip_lookup.py  user_agent_lookup.py  dimension_report.py
    aggregator.py  report_formatter.py  run_stats.py  app_config.py  unknown.py
  sources/file_log_source.py          # FileLogSource
  parsing/apache_combined_parser.py   # ApacheCombinedParser (strict + lenient)
  lookups/maxmind_geo_ip.py           # MaxMindGeoIp
  lookups/ua_parser_lookup.py         # UaParserLookup
  lookups/label_normalizer.py         # LabelNormalizer (alias tables)
  dimensions/country_dimension.py     # CountryDimension
  dimensions/os_dimension.py          # OsDimension
  dimensions/browser_dimension.py     # BrowserDimension
  aggregation/counting_aggregator.py  # CountingAggregator
  formatting/text_report_formatter.py # TextReportFormatter
tests/
  conftest.py                         # sample_log_path, apache_log_path, geoip_db_path
  fakes/                              # FakeGeoIp, FakeUserAgentLookup
  fixtures/sample.log                 # 20 lines, see tests/fixtures/README.md
  <mirrors src/: one test module per production class>
```

After the bootstrap only `contracts/`, the stub `cli.py` and empty sub-packages exist. The other
modules and `pipeline.py` are added by later waves.

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
