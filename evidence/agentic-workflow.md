# Agentic Workflow

This document describes how Claude Code (Claude Sonnet 4.6 via VSCode) was used during
development of this solution. It is updated incrementally as development progresses.

---

## Tool Used

**Claude Code — Claude Sonnet 4.6**, accessed via the VSCode extension throughout the session.
Used as the primary implementation tool for planning, design, code generation and documentation.

---

## Decomposition Approach

Work was broken down in this order:

1. **Identify the problem** — defined the problem statement and the intended user before any design work.
2. **Define the data model** — agreed on 4 CSV files (parties, accounts, transactions, alerts) in masked and unmasked variants before writing any code.
3. **Agree on the output contract** — defined exactly what the stdout output should and should not contain before writing any logic.
4. **Write evidence docs first** — `intent.md` and `agentic-workflow.md` committed before any code, to establish scope and goals upfront.
5. **Build incrementally** — data layer → SQL queries → config/db/loader → main.py → formatter → tests → verify script → remaining evidence docs → README.

---

## Representative Steering Moments

**1. Clarifying DQ visibility**
Claude Code initially proposed suppressing all DQ issues from the investigator output
("investigators don't need to see DQ noise"). I clarified the distinction: raw parsing errors
go to logs, but data excluded from the case summary must be visible to the investigator because
it affects completeness. Claude Code updated the output contract accordingly.

**2. Defining the tool's decision boundary**
Claude Code drafted an output section labelled "Case Recommendation" with escalation language.
I pushed back: the tool's sole purpose is automating data gathering. It does not assess risk,
score parties or recommend actions. This was corrected to "Observations" with a closing line
"Decision reserved for the investigator."

**3. Choosing the technology stack**
Claude Code initially proposed Google ADK and a FastAPI backend. I challenged both. The FastAPI
layer had no purpose without a custom frontend. ADK added framework complexity without clear
benefit for this scope. Both were removed. The final stack — plain Python, SQLite, `.sql` files —
was simpler, faster to deliver, and easier for reviewers to run.

**4. Requesting a plan before implementation**
Before building `formatter.py` — the most important user-facing component — I asked Claude Code
to present the design first: output sections, helper functions, structuring indicator logic, and
how it would wire into `main.py`. I reviewed and approved the design before any code was written.
This is deliberate: for components where the output contract matters (what the investigator actually
sees), reviewing the plan costs minutes and prevents the much more expensive rework of fixing
the wrong output structure after it is built.

---

## Where I Intervened

| Phase | Intervention |
|---|---|
| Scope | Confirmed no LLM in the product; directed Claude Code to record this as an explicit decision |
| Architecture | Removed FastAPI — no custom frontend, no need for a REST layer |
| Architecture | Removed Google ADK — plain Python agent pattern was sufficient and simpler |
| Data design | Introduced Cloud Spanner DDL as the production schema target — GCP ecosystem alignment |
| Data design | Chose 2 separate CSV sets (masked/unmasked) over a masking script — simpler, less to test |
| Data design | Introduced `transaction_code` and `transaction_code_desc` fields — realistic banking schema |
| Data design | Caught that `data/prod/` committed to git was poor practice even for synthetic data — renamed to `data/unmasked/` and documented the reasoning |
| Schema design | Corrected duplicate `alert_type` column in the original alerts table draft |
| SQL | Noted that `@party_id` (Spanner notation) differs from `:party_id` (SQLite notation) — clarified the migration path |

---

## AI Mistakes Caught

| Mistake | How caught | Resolution |
|---|---|---|
| "Case Recommendation" output language | Recognised it implied automated judgement | Replaced with "Observations" + investigator decision line |
| FastAPI included without justification | Questioned the assumption directly | Removed from architecture entirely |
| Duplicate `alert_type` column in alert schema | Reviewed the schema draft carefully | Removed duplicate, added `description` and `alert_source` |
| `data/prod/` named to suggest real production data | Noticed it was poor practice to commit anything labelled "prod" | Renamed to `data/unmasked/` with documented rationale in design.md |

---

## Verification Approach

- All generated code and documentation is reviewed before committing — nothing is accepted verbatim.
- After each build phase, I run the script myself end-to-end and verify the output matches the intended design — correct sections, correct data, correct flags. AI-generated output is not trusted until I have seen it produce the right result with my own eyes.
- Tests are written to verify behaviour, not just to pass. Edge cases and abstain paths are covered explicitly.
- End-to-end smoke test run after each major build phase before committing.
- The full test suite (`pytest tests/ -v`) was manually run and validated — 40 tests passing — before committing the tests to the branch.

_This document is updated as development progresses._
