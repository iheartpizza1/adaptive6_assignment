# Agent brief: bootstrap (Wave 0)

- **Branch:** `dev/bootstrap`
- **Runs:** alone. Wave 1 waits until this PR is merged into `master`.
- **Read first:** [`00-common.md`](00-common.md), then HLD §5, §8, §11, §13.

Goal: deliver a green, installable skeleton with every contract in place, so the four Wave 1 agents can work in parallel without touching shared files.

## You own

- `pyproject.toml`, `.gitignore` (append Python entries; keep the existing lines)
- `src/weblogstats/__init__.py`, `__main__.py`, `cli.py` (stub only), and the empty sub-packages `sources/`, `parsing/`, `lookups/`, `dimensions/`, `aggregation/`, `formatting/` (each with an `__init__.py` only)
- `src/weblogstats/contracts/` (all files)
- `tests/conftest.py`, `tests/fakes/`, `tests/fixtures/`, `tests/contracts/`, `tests/test_cli_stub.py`
- `README.md`: the **Requirements**, **Install** and **Development** sections, plus placeholder headings `## Usage` and `## Extending` containing only `_Filled in by Wave 2._`

## Checklist (TDD each item)

1. **pyproject.toml**
   - Project `weblogstats`, `requires-python = ">=3.12"`, src layout.
   - Runtime deps: `geoip2>=5`, `ua-parser>=1.0`. Extra `dev`: `pytest`, `ruff`.
   - Console script `weblogstats = "weblogstats.cli:main"`.
   - pytest config: `testpaths = ["tests"]`, register marker `data: needs apache_log.txt or the GeoLite2 MMDB`.
   - ruff: line-length 100, rules `E,F,I,B,UP`.
2. **`.gitignore` additions:** `.venv/`, `__pycache__/`, `*.egg-info/`, `.pytest_cache/`, `.ruff_cache/` (the data entries `data/`, `*.mmdb`, `GeoLite2-*`, `apache_log.txt`, `Assignment_instructions.md` are already there; keep them).
3. **contracts/**, one file each, re-exported from `contracts/__init__.py`. All Protocols are `@runtime_checkable`.
   - `log_record.py`: frozen dataclass `LogRecord`, with the fields from HLD §8 (`ip, timestamp, method, path, protocol, status, bytes_sent, referer, user_agent, raw, partial=False`). Add `@classmethod unreadable(cls, raw: str) -> LogRecord`, which returns a record with empty strings and `None`s. The pipeline uses it for lines the parser cannot read; every dimension then yields `Unknown`.
   - `log_source.py` → `LogSource` (`lines() -> Iterator[str]`)
   - `log_parser.py` → `LogParser` (`parse(line) -> LogRecord | None`)
   - `dimension.py` → `Dimension` (`name: str`, `extract(record) -> str`)
   - `geo_ip_lookup.py` → `GeoIpLookup` (`country_name(ip) -> str`)
   - `user_agent_lookup.py` → `UserAgentLookup` (`os_family(ua) -> str`, `browser_family(ua) -> str`)
   - `dimension_report.py` → frozen dataclass `DimensionReport` (`name`, `rows: tuple[tuple[str, float], ...]`)
   - `aggregator.py` → `Aggregator` (`observe(dimension, label)`, `snapshot(other_below: float | None = None) -> list[DimensionReport]`)
   - `report_formatter.py` → `ReportFormatter` (`format(reports) -> str`)
   - `run_stats.py` → dataclass `RunStats` (`total, strict, partial, unreadable`, all default 0) with `summary() -> str` returning e.g. `total=10000 strict=9999 partial=1 unreadable=0`
   - `app_config.py` → frozen dataclass `AppConfig` (`log_path: Path`, `geoip_path: Path`, `output_format: str = "text"`, `other_below: float | None = None`)
   - `__init__.py` also exports the constant `UNKNOWN = "Unknown"`.
4. **tests/fakes/**, one class per file:
   - `fake_geo_ip.py` → `FakeGeoIp(mapping: dict[str, str])`, which returns `UNKNOWN` when the IP is missing.
   - `fake_user_agent_lookup.py` → `FakeUserAgentLookup(os_map, browser_map)`, same behaviour.
   - Contract tests in `tests/contracts/` assert `isinstance(fake, Protocol)` and the Unknown behaviour, plus `LogRecord.unreadable`, `RunStats.summary` and the dataclass frozenness.
5. **tests/fixtures/sample.log:** about 20 lines. Copy them verbatim from the real log (path in `00-common.md`), covering every case in HLD §3:
   - line 1 (Chrome / Mac, the brief's sample shape)
   - line 8899 (truncated UA, no closing quote)
   - one line with UA `"-"`
   - one line with bytes `-` (a 304)
   - line 5851 (`\x` escapes in the referer)
   - line 5860 (IE 6 / Windows XP)
   - one each of: Googlebot, `UniversalFeedParser`, the `LAVA.KKT35` J2ME phone, Firefox on Windows, Firefox on Ubuntu, iPhone Mobile Safari, Chrome on Linux
   - plus synthetic lines: a valid line from private IP `10.0.0.1`, one blank line, and one garbage line (`this is not a log line`)

   Add `tests/fixtures/README.md` listing each line number and the case it covers. Add a test that the fixture has the expected count of non-blank lines, so later edits are noticed.
6. **tests/conftest.py:** fixtures `sample_log_path`, `apache_log_path` (env `APACHE_LOG` → repo-root `apache_log.txt` → `pytest.skip`) and `geoip_db_path` (env `GEOIP_DB` → `data/GeoLite2-Country.mmdb` → skip).
7. **Stub CLI (`cli.py`):** `main(argv: list[str] | None = None) -> int`, with argparse:
   - positional `log`
   - `--geoip` (default: env `GEOIP_DB`, else `data/GeoLite2-Country.mmdb`)
   - `--format {text}` (default `text`)
   - `--other-below FLOAT`

   It builds an `AppConfig`, prints `pipeline not wired` to stderr and returns 2. `__main__.py` calls it. Test it via `main([...])` and `--help`.
8. **README.md:**
   - **Requirements:** Python ≥ 3.12, runtime and dev deps, the GeoLite2-Country MMDB (free MaxMind account; the ASN edition will not work), the Apache log.
   - **Install:** venv, `pip install -e .[dev]`, put the MMDB in `data/` or set `GEOIP_DB`.
   - **Development:** pytest, ruff, the `data` marker and its env vars, the layout tree from HLD §8, one class per file, and the TDD + `dev/*` branch + PR flow (link `docs/agents/00-common.md`).

## Done when

- `pip install -e .[dev]` works in a fresh venv.
- `weblogstats --help` exits 0.
- The full pytest suite passes, and ruff check and format are clean.
- Every contract has a test.
- PR presented per `00-common.md`. Title: `Wave 0: bootstrap contracts, fakes, fixture and stub CLI`.
