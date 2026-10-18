# Agent brief: user-agent (Wave 1)

- **Branch:** `dev/user-agent`
- **Runs:** in parallel with parser, geoip and report, after `dev/bootstrap` is merged.
- **Read first:** [`00-common.md`](00-common.md), then HLD §3 (bots, long-tail UAs), §4 (UA label normalization, bots).

## You own

- `src/weblogstats/lookups/ua_parser_lookup.py` → `UaParserLookup` (the only module that imports `ua_parser`)
- `src/weblogstats/lookups/label_normalizer.py` → `LabelNormalizer`
- `src/weblogstats/dimensions/os_dimension.py` → `OsDimension`
- `src/weblogstats/dimensions/browser_dimension.py` → `BrowserDimension`
- Re-exports for these classes in `lookups/__init__.py` and `dimensions/__init__.py`. The geoip agent also adds lines to these two `__init__.py` files. Keep your additions to separate, alphabetically sorted import lines.
- Tests: `tests/lookups/test_ua_parser_lookup.py`, `tests/lookups/test_label_normalizer.py`, `tests/dimensions/test_os_dimension.py`, `tests/dimensions/test_browser_dimension.py`

## Checklist (TDD each item)

### LabelNormalizer(aliases: Mapping[str, str], prefix_aliases: Sequence[tuple[str, str]] = ())

The rules are data-driven, never `if` chains.

1. `normalize(family: str | None) -> str`:
   - `None`, `""`, `"Other"` and `"-"` → `Unknown`
   - exact alias match next
   - then the first matching prefix alias
   - else the family unchanged
2. Class-level factory methods `for_os()` and `for_browser()` hold the default tables from HLD §4:
   - **OS:** `Mac OS X` → `Mac OS`; any family starting with `Windows` → `Windows`; `Ubuntu`, `Debian`, `Fedora`, `Linux Mint`, `Red Hat`, `CentOS`, `Gentoo`, `Arch Linux`, `openSUSE`, `Slackware` → `Linux`.
   - **Browser:** no renames by default, only the Unknown rules. Real families stay as they are (`Chrome`, `Firefox`, `Mobile Safari`, `IE`, `Googlebot`…). Never map IE to Edge.

### UaParserLookup(os_normalizer, browser_normalizer, cache_size: int = 4096)

3. Uses ua-parser 1.x. Verify the API with a quick test first: `ua_parser.parse(ua)` returns a result whose `.os` / `.user_agent` may be `None` when nothing matched, with `.family` otherwise. Pin your understanding in a test.
4. Parses each distinct UA string once (`functools.lru_cache` on a private method, or an explicit dict). Prove it with a counting test: wrap or monkeypatch the parse function.
5. `os_family(ua)` and `browser_family(ua)` → normalized labels. `"-"`, `""` → `Unknown` without calling the parser.

   Data-free tests against real ua-parser, using UAs copied from `tests/fixtures/sample.log`:

   | UA | OS | Browser |
   |---|---|---|
   | Brief sample (Mac + Chrome 32) | `Mac OS` | `Chrome` |
   | `Windows NT 6.1; WOW64` + Chrome | `Windows` | `Chrome` |
   | Ubuntu + Firefox 27 | `Linux` | `Firefox` |
   | iPhone OS 6 (pick one **without** `Googlebot-Mobile` in it) | `iOS` | `Mobile Safari` |
   | `MSIE 6.0; Windows NT 5.1` | `Windows` | `IE` |
   | Googlebot | `Unknown` | `Googlebot` |
   | `UniversalFeedParser/4.2…` | whatever ua-parser gives, normalized (assert it is not `Other`) | |
   | `"-"` | `Unknown` | `Unknown` |

### OsDimension(ua: UserAgentLookup) / BrowserDimension(ua: UserAgentLookup)

6. `name == "OS"` / `name == "Browser"`.
7. `extract(record)` delegates to `ua.os_family(record.user_agent)` / `ua.browser_family(...)`. Test with `FakeUserAgentLookup`.
8. **Data test (`@pytest.mark.data`):** over the full 10k log's user agents (parse each line with a simple regex in the test; do not import the parser agent's module), assert that no OS or browser label equals `Other`, and that `Unknown` OS ≥ 190 (the `"-"` UAs).

## Done when

All the above pass, the full suite is green, and ruff is clean. PR presented per `00-common.md`. Title: `Wave 1: ua-parser adapter, label normalizer, OS and Browser dimensions`.
