# Agent brief: parser (Wave 1)

- **Branch:** `dev/parser`
- **Runs:** in parallel with geoip, ua and report, after `dev/bootstrap` is merged.
- **Read first:** [`00-common.md`](00-common.md), then HLD §3 (input profile), §4 (log format and denominator rows), §11.

## You own

- `src/weblogstats/sources/file_log_source.py` → `FileLogSource`
- `src/weblogstats/parsing/apache_combined_parser.py` → `ApacheCombinedParser`
- `src/weblogstats/parsing/bad_line_log.py` → `BadLineLog`
- `src/weblogstats/parsing/logging_parser.py` → `LoggingParser`
- Re-exports in `sources/__init__.py` and `parsing/__init__.py`
- `tests/sources/test_file_log_source.py`, `tests/parsing/test_apache_combined_parser.py`, `tests/parsing/test_bad_line_log.py`, `tests/parsing/test_logging_parser.py`

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

### Bad-line log (build on the parser; HLD §11)

Every line the parser could not read cleanly is written to an errors file, so nobody has to search the input for it. Do this **without changing any contract**. `LoggingParser` is a decorator that itself implements `LogParser`, so the pipeline and CLI see an ordinary parser.

**Output format (this is the contract with users):** one entry per bad line, UTF-8, `\n`-terminated, four space-separated fields. The last field is the full original line, unmodified and never truncated:

```
<timestamp> <LEVEL> <kind> <full line>
2026-10-18T10:23:03.123Z WARN partial 46.118.127.106 - - [20/May/2015:12:05:17 +0000] "GET /scripts/grok-py-test/configlib.py HTTP/1.1" 200 235 "-" "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html
2026-10-18T10:23:03.124Z ERROR unreadable this is not a log line
```

- `timestamp`: when the entry was written, UTC, ISO 8601 with milliseconds and a `Z` suffix. (The request's own time is already inside the full line.)
- `LEVEL` / `kind`: `WARN partial` when the lenient fallback produced the record (`record.partial is True`), `ERROR unreadable` when the parser returned `None`. Clean lines are never written.
- `line.split(" ", 3)` gives back the four fields. Write a test for exactly that.

#### BadLineLog(path: Path, clock: Callable[[], datetime] = <utc now>)

13. The file is created and **truncated when the log is opened**, at the start of each run. An empty file therefore means "no bad lines this run", and a stale file from an earlier run can never be mistaken for this one.
14. `warn(raw: str)` writes a `WARN partial` entry. `error(raw: str)` writes an `ERROR unreadable` entry. Both follow the format above exactly. Test with an injected fixed clock and `tmp_path`.
15. `warn_count` and `error_count` properties. `close()`, plus context-manager support. Writing after `close()` raises `ValueError`.
16. A raw line containing `\r`, a tab or non-ASCII text (from `errors="replace"`) is written as-is. The parser never sees `\n` inside a line, because the source splits on it.
17. You may build it on stdlib `logging` (a dedicated, non-propagating logger with its own `FileHandler`, opened with `mode="w"`) or as a plain file writer. Either way it must not touch the root logger or global logging configuration. Assert in a test that `logging.getLogger().handlers` is unchanged.

#### LoggingParser(inner: LogParser, log: BadLineLog)

18. `isinstance(LoggingParser(...), LogParser)` is True. `parse(line)` returns exactly what `inner.parse(line)` returned, the same object, for clean, partial and `None` results.
19. It calls `log.warn(line)` when the result is partial and `log.error(line)` when it is `None`, and calls nothing for a clean record. Test with a stub inner parser and a recording fake log, kept local to the test module or in `tests/parsing/fakes/`, one class per file.
20. **Fixture test:** wrap the real `ApacheCombinedParser` and run every line of `tests/fixtures/sample.log` through `FileLogSource`. The errors file then holds exactly 1 `WARN partial` entry (the line-8899 copy) and 1 `ERROR unreadable` entry (the garbage line), each with its full line.
21. **Data test (`@pytest.mark.data`):** run the full 10k log through it. The errors file has exactly one line: `WARN partial`, whose 4th field equals line 8899 of the log byte for byte.

`--errors-file` and the stderr mention belong to the compose agent. You only provide these two classes.

## Done when

All the above pass, the full suite is green, and ruff is clean. PR presented per `00-common.md`. Title: `Wave 1: Apache combined parser with lenient fallback, file source and bad-line log`.
