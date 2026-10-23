# Decisions

Five key decisions made during this build, including trade-offs and what was intentionally left out.

---

## 1. No LLM in the product

**Decision:** The script is fully deterministic — no language model is used anywhere in the solution.

**Why:** The exercise requires the solution to run without paid API keys or private credentials.
Any real LLM requires a credential of some kind. A deterministic pipeline satisfies every
requirement without that friction, and produces output that is auditable and reproducible:
the same input always produces the same output.

**What was ruled out:** Google ADK with Gemini, Anthropic SDK with Claude. Both were considered
early in planning. LLM-generated narrative summarisation is documented as the intended next stage.

---

## 2. SQLite as the local database over direct CSV reading

**Decision:** `setup.py` seeds two SQLite databases from CSV files. The script queries via SQL,
not by reading CSVs directly at runtime.

**Why:** SQL queries against a local SQLite file are structurally identical to queries against
Cloud Spanner in production. The migration path is a connection string change and a
parameter notation change (`:name` → `@name`) — nothing else. Direct CSV reading would mean
rewriting the data access layer entirely when moving to a real database.

**What was ruled out:** Reading CSVs directly with pandas at runtime. Simpler to build but
creates a false local/production equivalence.

---

## 3. Two separate CSV sets (masked / unmasked) over a masking script

**Decision:** `data/masked/` and `data/unmasked/` are maintained as separate manually-authored
CSV files. No masking logic is written or run.

**Why:** Writing and testing a masking function adds scope and complexity. For a demonstration
dataset with 4 parties, maintaining two CSV sets manually is simpler and less likely to
introduce errors. The trade-off — duplicated data that must be kept in sync — is acceptable
at this scale and is documented.

**What was ruled out:** A `mask.py` script that generates `masked/` from `unmasked/` at setup
time. Would be the right call at larger data volumes.

---

## 4. Plain Python over a framework (Google ADK, FastAPI)

**Decision:** The solution uses plain Python with no agent framework and no REST layer.

**Why:** An agent framework adds abstraction without benefit for a single-purpose script.
FastAPI was considered but had no purpose without a custom frontend. The JD's requirements —
bounded tool calls, evidence, human decision authority — are demonstrated through the code
structure and output design, not through a framework.

**What was ruled out:** Google ADK (would require Gemini credentials and adds framework
overhead), FastAPI (no consuming frontend exists in this scope).

---

## 5. Seed CSV files committed to the repository

**Decision:** The CSV seed files are committed to the repository under `data/masked/` and
`data/unmasked/`.

**Why:** The exercise requires the solution to run from a clean checkout without external
dependencies. Committing the seed data is the only way to satisfy this without requiring
reviewers to generate or source data themselves.

**Trade-off acknowledged:** In a real delivery, no data — synthetic or otherwise — would be
committed to source control. Data would live in a governed pipeline and be loaded into
controlled environments. The folder names (`masked/unmasked` rather than `prod/non_prod`)
were chosen deliberately to avoid implying these are real production datasets.
