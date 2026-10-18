# Test fixtures

`sample.log` has 20 lines: 19 non-blank and 1 blank. Lines 1 to 17 are copied verbatim from the
real `apache_log.txt` (10,000 lines, May 2015). Lines 18 to 20 are synthetic. Do not edit the file
without updating this table and the counts in `test_sample_log.py`.

| Fixture line | Source | Case covered |
|---|---|---|
| 1 | `apache_log.txt` line 1 | Chrome 32 / Mac OS X, the sample line shape from the brief |
| 2 | `apache_log.txt` line 8899 | Truncated line: the UA has no closing quote (lenient fallback, `partial=True`) |
| 3 | `apache_log.txt` line 44 | User-Agent is `"-"` (Unknown OS and browser, not a parse error) |
| 4 | `apache_log.txt` line 86 | Bytes is `-` on a 304 (`bytes_sent` is `None`); Sogou spider UA |
| 5 | `apache_log.txt` line 5851 | `\x` escapes in the referer; Firefox 11 / Windows |
| 6 | `apache_log.txt` line 5860 | IE 6 / Windows XP |
| 7 | `apache_log.txt` line 33 | Googlebot (a bot counted like any other request) |
| 8 | `apache_log.txt` line 35 | UniversalFeedParser (feed reader) |
| 9 | `apache_log.txt` line 7421 | `LAVA.KKT35` J2ME phone (odd, non-Mozilla UA) |
| 10 | `apache_log.txt` line 34 | Firefox 28 / Windows (long Google referer) |
| 11 | `apache_log.txt` line 24 | Firefox 26 / Ubuntu |
| 12 | `apache_log.txt` line 430 | iPhone, Mobile Safari |
| 13 | `apache_log.txt` line 208 | Chrome 32 / Linux |
| 14 | `apache_log.txt` line 63 | 404 status (Googlebot) |
| 15 | `apache_log.txt` line 189 | Chrome 32 / Windows 7 (the most common UA in the log) |
| 16 | `apache_log.txt` line 688 | HEAD request with bytes `-`, Firefox 24 / Windows |
| 17 | `apache_log.txt` line 5009 | POST request, Chrome 23 / Windows |
| 18 | synthetic | Valid line from private IP `10.0.0.1` (GeoIP gives Unknown) |
| 19 | synthetic | Blank line (skipped, not counted) |
| 20 | synthetic | Garbage line `this is not a log line` (unreadable, no IP recoverable) |

Expected parser outcomes for the whole file: `total=19 strict=17 partial=1 unreadable=1`. Strict
are lines 1 and 3 to 18, partial is line 2, unreadable is line 20, and the blank line 19 is skipped
and not counted.
