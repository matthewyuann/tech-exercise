# Design

## Architecture Overview

A single-purpose CLI script that reads from a local SQLite database, executes parameterised
SQL queries, and writes a structured case summary to stdout.

The database is seeded from CSV files at setup time. Two environments are provided —
`unmasked` (clearly fictional full data) and `masked` (PII replaced) — controlled by a `.env` file.
In production, the SQLite file is replaced by a governed database; the queries and application
code are unchanged.

```
CSV seed files  →  setup.py  →  unmasked.db / masked.db
                                       ↓
                             .env (DB_ENV=masked)
                                       ↓
                    main.py --party-id P001
                         ↓
                    config.py  →  resolves environment
                    db.py      →  opens SQLite connection
                    loader.py  →  executes 4 SQL queries
                    formatter.py →  builds case summary
                         ↓
                      stdout
```

---

## Data Flow

1. Investigator runs `python main.py --party-id <id> [--from-date YYYY-MM-DD] [--to-date YYYY-MM-DD]`
2. `config.py` reads `.env`, resolves which database to connect to
3. `db.py` opens a connection to `data/unmasked.db` or `data/masked.db`
4. `loader.py` executes 4 parameterised queries in sequence:
   - `get_party.sql` — party profile and account list
   - `get_accounts.sql` — account details for the party
   - `get_transactions.sql` — transactions filtered by account and date range
   - `get_alerts.sql` — open and historical alerts for the party
5. Each query result is logged (row count only, no PII)
6. `formatter.py` assembles the results into a plain-text case summary
7. Summary is written to stdout; investigator copies into their case notes

---

## Component Boundaries

```
main.py           CLI entry point — argument parsing, orchestration
config.py         Loads .env, exposes DB path and environment name
db.py             SQLite connection, parameterised query execution, row count logging
queries/
  get_party.sql
  get_accounts.sql
  get_transactions.sql
  get_alerts.sql
loader.py         Calls db.py for each query, returns structured dicts
formatter.py      Renders the case summary as plain text for stdout
logger.py         Structured logging — record IDs and counts only, never PII
setup.py          Seeds unmasked.db and masked.db from data/unmasked/ and data/masked/ CSVs
data/
  unmasked/       Clearly fictional CSV source files, all fields populated
  masked/         Same data with PII fields replaced
  unmasked.db     Generated at setup — gitignored
  masked.db       Generated at setup — gitignored
tests/            pytest — tool functions, output schema, abstain paths, golden output
evidence/         Design documentation
```

---

## Key Trade-offs

**SQLite over direct CSV reading**
Using SQLite as a mock database means queries are SQL — the same language used against
production databases. The trade-off is an extra setup step (`python setup.py`). This was
chosen because it more accurately represents the production integration pattern and makes
the path to a real database explicit: change the connection string, not the queries.

**Two CSV sets instead of a masking script**
Maintaining separate `unmasked/` and `masked/` CSV folders avoids writing and testing a
masking function. The trade-off is duplicated data that must be kept in sync manually.
For this scope, the simplicity benefit outweighs the maintenance risk.

**stdout and dated text file**
Output goes to stdout and is also written to `output/YYYY-MM-DD/<party_id>_output_<date>.txt`.
stdout allows direct copy-paste into case notes; the dated file provides a lightweight audit
trail. The `output/` directory is gitignored — investigator outputs are never committed.
PDF generation was considered and deferred — see `decisions.md` #7.

**No LLM in the product**
The script is fully deterministic — no language model is used. This keeps the solution
credential-free, auditable and reproducible: the same input always produces the same output.
LLM-generated narrative summarisation is documented as a future stage.

**requirements.txt over uv**
`pip` and `requirements.txt` ship with Python and require no additional tooling from the
reviewer. uv would be the preferred local development toolchain but adds friction for
external setup.

---

## Security and Privacy

- **Environment separation** — `masked` is the default. Unmasked data requires an explicit
  `DB_ENV=unmasked` in `.env`. This mirrors the production pattern where full-detail data access
  is constrained and audited.
- **No PII in logs** — log entries contain record IDs and row counts only. No names, dates
  of birth, addresses or account numbers are written to any log file.
- **Read-only access** — the script never writes to the database. All queries are `SELECT`.
- **Parameterised queries** — all SQL is parameterised. No user input is interpolated into
  query strings, preventing SQL injection.
- **No credentials in code** — database path and environment are resolved from `.env`,
  which is gitignored and never committed.

---

## Technology Choices

| Component | Choice | Reason |
|---|---|---|
| Language | Python 3.11+ | Standard for data and scripting; assessors can run without additional tooling |
| Database (local) | SQLite | Zero-dependency, file-based; allows credential-free local development and CI |
| Database (production) | Cloud Spanner | Google-native, horizontally scalable, strongly consistent; aligns with GCP as the target cloud ecosystem. Positions the solution to leverage Vertex AI and Google ADK for future LLM/agent runtime integration without cross-cloud complexity. `schema.sql` is written in Spanner DDL. |
| SQL | `.sql` files | Readable, testable independently, mirrors how queries are managed in production. Note: local SQLite queries use `:name` parameter notation; Cloud Spanner uses `@name`. A find-replace in the query files is the only change needed when migrating. |
| Config | python-dotenv | Standard `.env` pattern; maps directly to how secrets are injected in CI/CD |
| Logging | Python stdlib `logging` | No extra dependency; structured enough for future log aggregation |
| Testing | pytest | Standard; integrates with GitHub Actions without configuration |
| Linting | ruff | Fast, zero-config, catches common issues |

---

## Production and Cloud Shape

**Local (current)**
- SQLite file-based databases seeded from CSV files
- `.env` file controls environment selection
- All credentials are illustrative (no real credentials exist)

**Production path**
- SQLite replaced by Cloud Spanner — connection string and `:name` → `@name` parameter notation change; queries and application code are unchanged
- `.env` replaced by GCP Secret Manager — credentials injected at runtime by the pipeline
- `db.py` connection driver swapped (`sqlite3` → Cloud Spanner client library) — queries unchanged
- Script packaged as a container image; run as a task or job, not a long-running service
- Access to production data gated by IAM roles and network controls, not application-level logic

---

## Database Schema (DDL)

Schema is written in Cloud Spanner DDL. Locally, `setup.py` creates equivalent SQLite tables
from the same column definitions. Full DDL is in `data/schema.sql`.

```sql
CREATE TABLE party_data (
    party_id            STRING(36)      NOT NULL,
    full_name           STRING(255),
    date_of_birth       DATE,
    address             STRING(500),
    nationality         STRING(100),
    entity_type         STRING(20)      NOT NULL,   -- INDIVIDUAL | ENTITY
    acn                 STRING(20),
    abn                 STRING(20),
    risk_rating         STRING(10)      NOT NULL,   -- LOW | MEDIUM | HIGH
    pep_flag            STRING(1)       NOT NULL,   -- Y | N
    sanctions_flag      STRING(1)       NOT NULL,   -- Y | N
) PRIMARY KEY (party_id);

CREATE TABLE account_data (
    account_id          STRING(36)      NOT NULL,
    party_id            STRING(36)      NOT NULL,
    account_type        STRING(20)      NOT NULL,   -- SAVINGS | TRANSACTION | BUSINESS
    account_number      STRING(50)      NOT NULL,
    account_status      STRING(20)      NOT NULL,   -- ACTIVE | DORMANT | CLOSED
    open_date           DATE            NOT NULL,
    close_date          DATE,
) PRIMARY KEY (account_id);

CREATE TABLE transaction_data (
    transaction_id          STRING(36)      NOT NULL,
    account_number          STRING(50)      NOT NULL,
    transaction_date        DATE            NOT NULL,
    transaction_amount      FLOAT64         NOT NULL,
    transaction_type        STRING(10)      NOT NULL,   -- CREDIT | DEBIT
    transaction_narrative   STRING(500),
    transaction_code        STRING(10)      NOT NULL,
    transaction_code_desc   STRING(100)     NOT NULL,
    counterparty_bsb        STRING(10),
    counterparty_name       STRING(255),
    counterparty_country    STRING(100),
) PRIMARY KEY (transaction_id);

CREATE TABLE alert_data (
    alert_id            STRING(36)      NOT NULL,
    party_id            STRING(36)      NOT NULL,
    alert_type          STRING(50)      NOT NULL,
    alert_date          DATE            NOT NULL,
    alert_status        STRING(20)      NOT NULL,   -- OPEN | CLOSED | ESCALATED
    alert_source        STRING(100)     NOT NULL,
    description         STRING(1000),
) PRIMARY KEY (alert_id);
```

---

**CI/CD promotion**
- Pull request triggers GitHub Actions: `ruff` lint → `pytest` → golden output test
- Merge to `main` builds and pushes a versioned container image
- Environment promotion (`masked` → `unmasked`) is a configuration change, not a code change
- No deployment to cloud is required for this exercise — the container and pipeline shape
  is described here as the intended next step
