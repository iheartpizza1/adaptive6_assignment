# Agent brief: parser (Wave 1)

- **Branch:** `dev/parser`
- **Runs:** in parallel with geoip, ua and report, after `dev/bootstrap` is merged.
- **Read first:** [`00-common.md`](00-common.md), then HLD §3 (input profile), §4 (log format and denominator rows), §11.

## You own

- `src/weblogstats/sources/file_log_source.py` → `FileLogSource`
- `src/weblogstats/parsing/apache_combined_parser.py` → `ApacheCombinedParser`
- Re-exports in `sources/__init__.py` and `parsing/__init__.py`
- `tests/sources/test_file_log_source.py`, `tests/parsing/test_apache_combined_parser.py`

You do not depend on GeoIP or ua-parser.

## Checklist (TDD each item)

### FileLogSource(path: Path)

1. `lines()` streams lazily, without reading the whole file into memory (test with a generator check, e.g. `next()` before the file is exhausted).
2. Opens the file as UTF-8 with `errors="replace"` and strips the trailing `\n` / `\r\n`.
3. Skips lines that are blank after stripping.
4. A missing file raises `FileNotFoundError` from the constructor or the first `lines()` call (document which). The CLI turns it into an exit code later.

### ApacheCombinedParser

5. **Strict path:** a compiled regex for Apache combined format, where quoted fields use `"((?:[^"\\]|\\.)*)"` so `\x..` and `\"` escapes are allowed. On a match it returns a `LogRecord` with `partial=False`. Field checks on fixture line 1:
   - `ip`
   - `timestamp` (timezone-aware `datetime`)
   - `method`, `path`, `protocol`
   - `status: int`, `bytes_sent: int`
   - `referer`, `user_agent`
   - `raw`
6. Bytes `-` → `bytes_sent=None`. Status `-` → `status=None`.
7. A request field that is not three tokens (e.g. `"-"` or a bare path) still parses: `method` / `path` / `protocol` get the best effort, with empty strings for the missing parts.
8. Escaped referer (fixture line from log 5851) parses strictly, and the escapes stay as literal text.
9. **Lenient fallback:** when the strict regex fails but the line starts with an IP-looking token:
   - `ip` = first whitespace token
   - `user_agent` = text after the last ` "`, without a trailing `"`
   - other fields best effort or empty / `None`
   - `partial=True`

   Must pass on fixture line 8899 (truncated Googlebot UA).
10. Lines that are not readable at all (the garbage fixture line) → `None`.
11. A bad timestamp never raises: `timestamp=None`.
12. **Data test (`@pytest.mark.data`):** parse the full 10k log; assert 10,000 records with exactly 9,999 strict, 1 partial and 0 `None`.

## Done when

All the above pass, the full suite is green, and ruff is clean. PR presented per `00-common.md`. Title: `Wave 1: Apache combined parser with lenient fallback and file source`.
