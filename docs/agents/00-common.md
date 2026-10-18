# Common rules for every implementation agent

Read this file before your own brief. Your brief (`01-…` to `06-…`) says *what* to build; this file says *how*.

The design source of truth is [`docs/hld.html`](../hld.html) (v1.4.0). Read §3 (input profile), §4 (assumptions), §8 (abstractions and module layout), §11 (errors / Unknown / Other) and §13 (testing) before writing code. If your brief and the HLD disagree, follow your brief and say so in the PR description.

## Repository and data

- Remote: `https://github.com/iheartpizza1/adaptive6_assignment`, base branch `master`.
- Python: `python` on PATH is 3.14. The package must support `>=3.12`.
- Real input files live in the **main checkout**, not in your worktree, and are not committed:
  - Log: `C:\Users\Avi\Documents\Dev\Adaptive6_Assignment\adaptive6_assignment\apache_log.txt`
  - GeoIP DB: `C:\Users\Avi\Documents\Dev\Adaptive6_Assignment\adaptive6_assignment\data\GeoLite2-Country.mmdb`
- Tests that need either file read them from the env vars `APACHE_LOG` and `GEOIP_DB`, fall back to `apache_log.txt` / `data/GeoLite2-Country.mmdb` under the repo root, and are marked `@pytest.mark.data` and skipped when the file is missing. Set both env vars in your shell before running the suite so these tests actually run for you.
- Never commit `*.mmdb`, MaxMind archives, `apache_log.txt` or `.venv/`.

## Branch and worktree

1. You run in your own git worktree. First, run:
   ```
   git fetch origin
   git switch -c <your-branch> origin/master
   ```
   Your branch name is in your brief (`dev/...`).
2. Create a venv in the worktree and install: `python -m venv .venv`, then `.venv\Scripts\python -m pip install -e .[dev]` (Wave 0 creates `pyproject.toml`; until then, follow the bootstrap brief).
3. Touch **only the paths your brief says you own**. Do not edit `contracts/`, `tests/fakes/`, `tests/fixtures/`, `pyproject.toml` or the README unless your brief owns them. If you need a contract change, stop and describe it in your PR description instead of making it.
4. Never merge, rebase onto, or push to `master`. Never force-push. Never delete branches.

## Code rules

- **One class per file.** Each class (Protocol, dataclass, adapter, fake, test class) gets its own module named after it in snake_case. `__init__.py` only re-exports. Module-level constants and helper functions live in the file of the one class that uses them.
- Depend on the Protocols in `weblogstats.contracts`, never on another Wave 1 agent's module.
- Only the adapter module may import a third-party library (`geoip2` in `maxmind_geo_ip.py`, `ua_parser` in `ua_parser_lookup.py`).
- Type hints everywhere. Short docstrings on public classes. Comments only where the *why* is not obvious.
- Unknown values are the literal string `"Unknown"`. Never raise for a single bad record.

## TDD loop (mandatory)

For every behaviour in your brief's checklist:

1. **Red:** write the test first, run it, and confirm it fails for the expected reason (an assertion, not an `ImportError` from a typo).
2. **Green:** write the minimum production code that passes it.
3. **Refactor**, keeping the suite green.
4. **Commit** the test and code together, with a message describing the behaviour (e.g. `parser: recover IP and UA from truncated line`).

Tests mirror `src/`: one test module per production class, e.g. `tests/parsing/test_apache_combined_parser.py`. Use the fixtures in `tests/fixtures/` and the fakes in `tests/fakes/`. Do not hit the network.

## Before presenting the PR (gate)

Run all three from the worktree root, with `APACHE_LOG` and `GEOIP_DB` set:

```
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m ruff check .
.venv\Scripts\python -m ruff format --check .
```

All must pass, on the **full** suite, not only your tests. Fix failures in your own files. If a failure is in a file you do not own, do not fix it: report it.

Then:

1. Push: `git push -u origin <your-branch>`.
2. Open the PR into `master`:
   - If `gh` is installed and authenticated, run `gh pr create --base master --head <your-branch> --title "<title>" --body-file <file>`.
   - Otherwise (the current state of this machine), do not open it yourself. Return the compare URL `https://github.com/iheartpizza1/adaptive6_assignment/compare/master...<your-branch>?expand=1` together with the title and body.
3. The PR body must contain:
   - **Summary:** what was built, mapped to the brief's checklist.
   - **Files:** the files added, one class each.
   - **Test evidence:** the pasted tail of the pytest output (pass/skip counts) and the ruff output. Name any skipped tests and say why they were skipped.
   - **Deviations / contract change requests:** if none, say "none".

## Your final report (back to the orchestrator)

Keep it short and factual: the branch, the head commit SHA, the PR URL or compare URL, the PR title and body, the test counts, and anything blocked or deviating. Do not claim tests pass unless you ran them in this session and saw them pass.
