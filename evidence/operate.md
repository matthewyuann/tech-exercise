# Operate

## How to Run

**Prerequisites:** Python 3.11+, Git. No paid services, API keys or private credentials required.

```bash
# 1. Clone and enter the repo
git clone https://github.com/matthewyuann/tech-exercise.git
cd tech-exercise

# 2. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Mac / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment config
cp .env.example .env            # default: DB_ENV=masked

# 5. Seed the databases
python setup.py

# 6. Run a case summary
python main.py --party-id P001

# With date filter
python main.py --party-id P001 --from-date 2024-10-01 --to-date 2024-10-31

# Switch to unmasked environment
# Edit .env: set DB_ENV=unmasked
python main.py --party-id P001

# Run all checks
bash verify.sh
```

Output is written to stdout and saved to `output/YYYY-MM-DD/<party_id>_output_<date>.txt`.

---

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | Success — case summary produced |
| `1` | Configuration error — invalid `DB_ENV`, missing `.db` file, or unreadable config |
| `2` | Abstain — party not found, or insufficient data to produce a summary |

Exit code `2` is a safe, intentional path — not an error. It means the script found no usable
data and refused to produce an incomplete summary.

---

## Logs

Logs are written to **stderr only**. They never appear in the case summary output.

```
2026-10-25 02:13:34,123 INFO     main    — party_id=P001 env=masked
2026-10-25 02:13:34,145 INFO     db      — get_party.sql: 1 row(s)
2026-10-25 02:13:34,162 INFO     db      — get_accounts.sql: 2 row(s)
2026-10-25 02:13:34,178 WARNING  loader  — transaction_data — TXN022 excluded: invalid date '2024-13-45'
2026-10-25 02:13:34,190 INFO     db      — get_alerts.sql: 2 row(s)
2026-10-25 02:13:34,201 INFO     main    — output written to output/2026-10-25/P001_output_2026-10-25.txt
```

**Log rules:**
- Record IDs only — no names, dates of birth, addresses or amounts are logged
- PII is never written to logs, regardless of environment
- `WARNING` level indicates a row was excluded from the summary due to a data quality issue

To suppress log output and see only the case summary:
```bash
python main.py --party-id P001 2>$null    # Windows PowerShell
python main.py --party-id P001 2>/dev/null # Mac / Linux
```

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `DB_ENV` | `masked` | Which database to query — `masked` or `unmasked` |

Set in `.env` (gitignored, never committed). `.env.example` shows the required keys.

In production, `DB_ENV` and any database credentials would be injected at runtime by the
deployment pipeline — not stored in a file. The `.env` pattern maps directly to how secrets
are injected in CI/CD environments (GitHub Actions secrets, GCP Secret Manager, etc.).

---

## Failure Modes

| Failure | Symptom | Resolution |
|---|---|---|
| `.env` missing or `DB_ENV` not set | `ValueError: Invalid DB_ENV` on startup | Copy `.env.example` to `.env` |
| `setup.py` not run | `FileNotFoundError: Database not found` on startup | Run `python setup.py` |
| Invalid `DB_ENV` value | `ValueError: Invalid DB_ENV 'x'` | Set `DB_ENV=masked` or `DB_ENV=unmasked` in `.env` |
| Unknown `party_id` | `UNABLE TO ASSESS — party 'P999' not found`, exit code `2` | Verify the party ID exists in the source data |
| Party has no usable data | `UNABLE TO ASSESS — insufficient data`, exit code `2` | Check source data for the party |
| DQ issues in transaction data | Warning in logs; affected rows excluded, note in output | Investigate upstream data quality |
| CSV seed file missing | `FileNotFoundError: Seed file not found` during `setup.py` | Ensure `data/masked/` and `data/unmasked/` CSVs are present |

---

## Rollback and Degrade

**Re-seeding:** `setup.py` is fully idempotent — re-running it clears and reloads all tables.
If a database becomes corrupted or out of sync with the CSV source files, re-running
`python setup.py` restores it to a known state.

**Partial data:** The script degrades gracefully. If transactions contain DQ issues, valid rows
are still included and the DQ warnings section in the output tells the investigator what was
excluded. The script does not fail silently — it either produces a complete summary, a summary
with explicit gaps, or an explicit abstain.

**No writes:** The script is read-only. It cannot corrupt the database. Any failure can be
resolved by fixing the configuration and re-running.

---

## Local to Cloud

| Concern | Local | Production |
|---|---|---|
| Database | SQLite file (`data/masked.db`) | Cloud Spanner — change connection string and `:name` → `@name` in queries |
| Config / secrets | `.env` file | GCP Secret Manager or equivalent; injected at runtime |
| Credentials | None required | IAM-scoped service account; no credentials in code |
| Execution | `python main.py` on developer machine | Container task triggered by case management system or scheduled job |
| Logging | stderr to terminal | Structured log aggregation (Cloud Logging / Datadog) |
| Output files | Local `output/` directory | Written to a governed storage location (GCS bucket with access controls) |
| Data access | Unrestricted local file | Row-level security and audit logging enforced at database layer |
