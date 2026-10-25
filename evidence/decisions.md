# Decisions

Nine key decisions made during this build, including trade-offs and what was intentionally left out.

---

## High Priority Decisions

The five decisions most central to the architecture, product design and regulatory alignment of this solution.

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

## 5. No per-transaction table in the case summary output

**Decision:** The formatter renders aggregated statistics, a type breakdown, and indicator flags —
not a row-per-transaction table.

**Why:** In production, a single party may hold many accounts each with hundreds of transactions.
A full transaction table would make the summary unusable for copy-paste into case notes and would
bury the key signals (offshore activity, structuring pattern) in raw data. The formatter surfaces
what an L1 investigator needs: volume, value, channel breakdown, offshore activity flagged at the
top as a red flag, and a structuring indicator when the pattern is present.

**What was ruled out:** A full transaction table. Appropriate for an audit export or a data
extract tool — not for an investigator case summary.

---

## Lower Priority Decisions

Implementation, tooling and timebox decisions that are documented for completeness.

---

## 6. Seed CSV files committed to the repository

**Decision:** The CSV seed files are committed to the repository under `data/masked/` and
`data/unmasked/`.

**Why:** The exercise requires the solution to run from a clean checkout without external
dependencies. Committing the seed data is the only way to satisfy this without requiring
reviewers to generate or source data themselves.

**Trade-off acknowledged:** In a real delivery, no data — synthetic or otherwise — would be
committed to source control. Data would live in a governed pipeline and be loaded into
controlled environments. The folder names (`masked/unmasked` rather than `prod/non_prod`)
were chosen deliberately to avoid implying these are real production datasets.

---

## 7. Plain text file output over PDF

**Decision:** The script writes output to a dated `.txt` file under `output/YYYY-MM-DD/`
in addition to stdout. No PDF generation.

**Why:** PDF was considered on the basis that investigators could not accidentally edit an
immutable file.

PDF generation (via `reportlab` or `weasyprint`) adds meaningful dependency weight and
complexity with no material integrity benefit at this scope.

The dated file path (`P001_output_2026-10-25.txt`) provides a lightweight audit trail.
The `output/` directory is gitignored — investigator outputs are never committed.

**What was ruled out:** PDF generation. Appropriate for a V2 where a locked, distributable
summary is required — deferred, not dismissed.

---

## 8. No GitHub Actions workflow in this timebox

**Decision:** A `.github/workflows/ci.yml` file was not built. `verify.sh` is the
verification artefact for this submission.

**Why:** `verify.sh` runs exactly the checks a CI pipeline would run — seed, lint, test —
in the same order, with the same failure behaviour (`set -euo pipefail`). A GitHub Actions
workflow file would automate triggering `verify.sh` on push and PR, but adds no new
verification capability. The spec requires "a command or script that runs the main checks
you would expect to run in CI" — `verify.sh` satisfies this directly.

**What was ruled out:** `.github/workflows/ci.yml`. The workflow would be a single step:
`pip install -r requirements.txt && bash verify.sh`. Straightforward to add as the
immediate next step after submission.

---

## 9. Format check via ruff over pre-commit hooks

**Decision:** `verify.sh` runs `ruff format --check .` to enforce consistent code formatting.
No pre-commit hook framework is configured.

**Why:** Pre-commit hooks (`pre-commit` framework with a `.pre-commit-config.yaml`) were
considered as a way to block unformatted or non-linting code at commit time. However, they
require every contributor to run `pre-commit install` after cloning — an undocumented setup
step that adds friction for reviewers and increases onboarding complexity.

`ruff format --check` in `verify.sh` provides the same protection in CI without any
additional tooling or install steps. It fails if code is not formatted, enforcing the same
standard without the setup overhead.

**What was ruled out:** Pre-commit hooks with `black` + `ruff`. Pre-commit is the right
choice for a team working on a shared codebase — it prevents bad commits from entering the
history in the first place. Deferred as a required next step before team onboarding.
