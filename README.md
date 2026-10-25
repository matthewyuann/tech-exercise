# AML Case Summary Script

A deterministic CLI tool that automates the manual data-gathering step in an AML investigation.
Given a `party_id`, the script queries a local SQLite database (seeded from CSV files), retrieves
party profile, account, transaction and alert data, and produces a structured case summary for
the investigator to copy into their case notes.

The script does not score risk, make recommendations or reach conclusions.
All decisions remain with the investigator.

---

## Prerequisites

- Python 3.11+
- Git

No paid services, API keys or private credentials are required.

---

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/matthewyuann/tech-exercise.git
cd tech-exercise

# 2. Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# Mac / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy the environment config
cp .env.example .env

# 5. Seed the databases
python setup.py
```

`setup.py` creates `data/masked.db` and `data/unmasked.db` from the CSV seed files.
It is safe to re-run.

---

## Running the Script

```bash
# Basic usage — masked environment (default)
python main.py --party-id P001

# With transaction date range filter
python main.py --party-id P001 --from-date 2024-10-01 --to-date 2024-10-31

# Switch to unmasked environment
# Edit .env and set DB_ENV=unmasked, then:
python main.py --party-id P001
```

**Environment:**
- `masked` (default) — PII fields replaced, safe for non-production use
- `unmasked` — clearly fictional full data, set `DB_ENV=unmasked` in `.env`

---

## Running Tests and Verification

```bash
# Run all checks (lint + tests + schema validation)
./verify.sh

# Run tests only
pytest tests/
```

> Tests and `verify.sh` are in progress. This section will be updated as they are added.

---

## Example: P001 Investigation

**Input**
```bash
python main.py --party-id P001
```

**Output**
```
============================================================
AML CASE SUMMARY
============================================================
Party ID   : P001
As of      : 2026-10-25 02:13:34 UTC
Environment: masked
Date filter: none (all transactions)

--- RISK SIGNALS ---
Risk rating  : HIGH
PEP          : YES [!]
Sanctions    : No
Open alerts  : 2

--- PARTY PROFILE ---
Name         : J*** F***
Date of birth: 1975-**-**
Entity type  : INDIVIDUAL
Nationality  : Australian
Address      : ** **** ******* ****** *** ****

--- LINKED ACCOUNTS (2 records) ---
Account Number         Type            Status     Opened       Closed
---------------------------------------------------------------------
062000-10000001        TRANSACTION     ACTIVE     2018-03-01   —
062000-10000002        SAVINGS         ACTIVE     2020-07-15   —

--- TRANSACTIONS (10 records) ---
Total CREDIT : AUD    51,100.00
Total DEBIT  : AUD    29,150.00

By type:
  High-Risk Country Activity [!]   1 transaction    AUD    25,000.00
  Cash Deposit                     5 transactions   AUD    48,100.00
  Direct Credit                    1 transaction    AUD     3,000.00
  Direct Debit                     2 transactions   AUD     3,700.00
  Purchase                         1 transaction    AUD       450.00
  Telegraphic Transfer             1 transaction    AUD    25,000.00

[!] STRUCTURING INDICATOR: 4 cash deposits between AUD 9,500.00
    and AUD 10,000.00 (reporting threshold: AUD 10,000.00)

--- ALERTS (2 records) ---
Alert ID   Type       Date         Status   Description
------------------------------------------------------------------------
ALT001     STRUCTURING  2024-10-16  OPEN    Multiple cash deposits below threshold
ALT002     PEP_MATCH    2024-10-16  OPEN    Party matched against PEP register

============================================================
Decision reserved for the investigator.
============================================================
```

**Abstain path** — unknown party:
```bash
python main.py --party-id P999
# UNABLE TO ASSESS — party 'P999' not found in masked database.
# Exit code: 2
```

---

## Known Limitations

- **Synthetic data only** — 4 parties (P001–P004) covering high-risk, medium-risk, clean and DQ scenarios.
- **SQLite only** — production target is Cloud Spanner (see `evidence/design.md`).
- **No authentication or access control** — enforced at the environment/infrastructure layer in production.
- **Date filtering applies to transactions only** — alerts and accounts are always returned in full.
- **`:name` SQL parameter notation** — SQLite compatible; Spanner requires `@name` (find-replace only).

---

## Evidence Pack

Design decisions, architecture, AI tooling usage and operational notes are in `evidence/`:

| File | Contents |
|---|---|
| `evidence/intent.md` | Problem statement, users, assumptions, constraints, success criteria |
| `evidence/design.md` | Architecture, data flow, schema, trade-offs, security, production shape |
| `evidence/agentic-workflow.md` | AI tools used, steering moments, interventions, mistakes caught |
| `evidence/verify.md` | Tests, checks, known gaps *(in progress)* |
| `evidence/operate.md` | Run steps, exit codes, logs, failure modes *(in progress)* |
| `evidence/decisions.md` | 7 key decision records with rationale and trade-offs |

---

## Repository Structure

```
aml-case-summary/
  data/
    unmasked/        CSV seed files — clearly fictional, all fields populated
    masked/          CSV seed files — PII fields replaced
    *.db             Generated by setup.py — gitignored
  queries/           Parameterised SQL files, one per table
  evidence/          Design documentation and evidence pack
  main.py            CLI entry point
  formatter.py       Renders structured plain-text case summary
  setup.py           Seeds SQLite databases from CSV files
  config.py          Environment configuration
  db.py              Database connection and query execution
  loader.py          Data retrieval and DQ handling
  schema.sql         Cloud Spanner DDL (production schema reference)
  requirements.txt
  .env.example
```
