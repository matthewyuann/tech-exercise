# Verify

## How to Run All Checks

```bash
bash verify.sh
```

This runs four steps in sequence, stopping immediately on any failure:

1. `python setup.py` — seeds the SQLite databases from the CSV source files
2. `python -m ruff check .` — lints all Python source files
3. `python -m ruff format --check .` — verifies consistent code formatting
4. `python -m pytest tests/ -v` — runs the full test suite

Requires: virtual environment activated, dependencies installed (`pip install -r requirements.txt`).

---

## Test Suite — 40 Tests Across 4 Files

| File | What it covers |
|---|---|
| `tests/test_formatter.py` | Helper functions, key signals in output (PEP flag, risk rating, footer), structuring indicator boundary conditions, high-risk country flag |
| `tests/test_loader.py` | DQ exclusion (invalid date, missing amount), warnings raised for excluded rows, valid rows pass through, unknown party returns `None` |
| `tests/test_config.py` | Invalid `DB_ENV` raises `ValueError`, missing `.db` file raises `FileNotFoundError` |
| `tests/test_data_quality.py` | CSV column headers match schema, masked/unmasked column parity, no blank primary keys |

All 40 tests pass. Manually verified by running `pytest tests/ -v` before committing the suite.

---

## Local vs CI

| Check | Local | CI pipeline |
|---|---|---|
| Database seed (`setup.py`) | Run once before script use; re-run via `verify.sh` | Run at start of every CI job — CI runners start clean |
| Lint (`ruff`) | `bash verify.sh` or `python -m ruff check .` | Same command in CI step |
| Format check (`ruff format`) | `bash verify.sh` or `python -m ruff format --check .` | Same command in CI step |
| Tests (`pytest`) | `bash verify.sh` or `pytest tests/ -v` | Same command in CI step |
| End-to-end smoke test | Manual — run `python main.py --party-id P001` and inspect output | Not yet automated — next step |
| Type checking | Not yet added | Would add `mypy` or `pyright` as a CI step |

`verify.sh` maps directly to a CI pipeline. A GitHub Actions workflow would be:

```yaml
- run: pip install -r requirements.txt
- run: bash verify.sh
```

No further configuration is needed — `verify.sh` is the single source of truth for what "passing" means.

---

## CI/CD Promotion Path

See `design.md` — Production and Cloud Shape for the full promotion path. In summary:

- **PR** → GitHub Actions runs `verify.sh` (lint + format check + tests). Must pass before merge.
- **Merge to main** → builds and pushes a versioned container image.
- **Promotion** → environment selection (`masked` → `unmasked`) is a configuration change, not a code change.

A GitHub Actions workflow file (`.github/workflows/ci.yml`) was not built in this timebox.
`verify.sh` is the direct equivalent — see `decisions.md` for the rationale.

---

## Known Gaps

| Gap | Notes |
|---|---|
| No automated end-to-end CLI test | `main.py` is tested by invoking it as a subprocess — not yet automated. Covered manually. |
| No type checking | `mypy` or `pyright` would be the next addition to `verify.sh` |
| No coverage report | `pytest --cov` would show which lines are exercised. Not required at this scope. |
| No contract tests against Cloud Spanner | Would be required before production promotion — validates schema and query compatibility against the real target database |
| GitHub Actions workflow not built | `verify.sh` satisfies the spec requirement. A workflow file is the straightforward next step — see `decisions.md`. |
