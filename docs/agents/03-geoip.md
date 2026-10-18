# Agent brief: geoip (Wave 1)

- **Branch:** `dev/geoip`
- **Runs:** in parallel with parser, ua and report, after `dev/bootstrap` is merged.
- **Read first:** [`00-common.md`](00-common.md), then HLD §3 (GeoIP note), §4 (GeoIP misses, DB distribution), §6 (GeoIP lookup paragraph), §11.

## You own

- `src/weblogstats/lookups/maxmind_geo_ip.py` → `MaxMindGeoIp` (the only module that imports `geoip2`)
- `src/weblogstats/dimensions/country_dimension.py` → `CountryDimension`
- Re-exports for these two classes in `lookups/__init__.py` and `dimensions/__init__.py`. The ua agent also adds lines to these two `__init__.py` files. Keep your additions to separate, alphabetically sorted import lines so the merge is trivial.
- `tests/lookups/test_maxmind_geo_ip.py`, `tests/dimensions/test_country_dimension.py`

## Checklist (TDD each item)

### CountryDimension(geoip: GeoIpLookup)

1. `name == "Country"`.
2. `extract(record)` returns `geoip.country_name(record.ip)`. Test with `FakeGeoIp`.
3. Empty IP (from `LogRecord.unreadable`) → `Unknown`, without calling the lookup.

### MaxMindGeoIp(db_path: Path)

4. Missing file → `FileNotFoundError`, with a message naming the path and the `GEOIP_DB` env var.
5. Opens the DB once (`geoip2.database.Reader`; the default mode is fine).
6. Validates `reader.metadata().database_type`: it must contain `Country` or `City`. Otherwise raise `ValueError`, with a message saying the GeoLite2-Country edition is required (e.g. when given an ASN DB). Unit-test this with a stub reader injected through an optional constructor parameter, a small factory argument, or a `classmethod` for tests. Do not ship a fake MMDB file.
7. `country_name(ip)`:
   - returns `response.country.names["en"]`
   - falls back to `response.registered_country.names["en"]`
   - else `Unknown`
8. `AddressNotFoundError`, `ValueError` (invalid IP), empty string and private / loopback IPs (check with `ipaddress` first, without calling the reader) → `Unknown`.
9. Per-IP cache: a second lookup of the same IP does not hit the reader (assert with a counting stub).
10. `close()` plus context-manager support, so the CLI can release the file.
11. **Data tests (`@pytest.mark.data`, using `geoip_db_path`):**
    - `83.149.9.216` (fixture line 1) resolves to a non-Unknown country name (assert it is a non-empty string other than `Unknown`, without hard-coding which country).
    - `8.8.8.8` → `United States`.
    - Over the full 10k log's distinct IPs, Unknown makes up less than 2% (sanity check).

## Done when

All the above pass, the full suite is green, and ruff is clean. PR presented per `00-common.md`. Title: `Wave 1: MaxMind GeoIP adapter and Country dimension`.
