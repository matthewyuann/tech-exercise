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
5. **Build incrementally** — data layer → normalisation → observations → formatter → CLI → tests → verify script → remaining evidence docs → README.

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

---

## Where I Intervened

| Phase | Intervention |
|---|---|
| Scope | Confirmed no LLM in the product; directed Claude Code to record this as an explicit decision |
| Data design | Specified prod/non-prod should be `unmasked`/`masked` with clearly fictional data |

---

## AI Mistakes Caught

_This section is updated as development progresses._

| Mistake | How caught | Resolution |
|---|---|---|
| "Case Recommendation" output language | Recognised it implied automated judgement | Replaced with "Observations" + investigator decision line |

---

## Verification Approach

- All generated code and documentation is reviewed before committing — nothing is accepted verbatim.
- Tests are written to verify behaviour, not just to pass. Edge cases and abstain paths are covered explicitly.

_This document is updated as development progresses._
