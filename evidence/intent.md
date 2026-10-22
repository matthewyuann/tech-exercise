# Intent

## Problem Statement

L1 Transaction Monitoring analysts spend significant time manually gathering data from multiple
systems before they can begin reviewing a case. This script automates that data-gathering step.

Given a `party_id` and an optional date range, the script retrieves data directly from the
relevant data sources and produces a case summary the investigator can copy and paste directly
into their case or alert notes — reducing the manual effort at the start of an L1 investigation.

In production, data will be retrieved from governed databases. The current implementation reads
from CSV files that replicate the same schema and data quality characteristics.

---

## Intended Users

- **L1 Transaction Monitoring Analysts** — primary users, conducting initial case reviews
- **L2 TM Analysts** — reviewing escalated cases requiring deeper investigation
- **TM Team Leads** — overseeing case queues and reviewing analyst outputs

---

## Assumptions

- All users of this script already have authorised access to view the underlying data in the
  production environment. The script does not grant access beyond what the user already holds.
- Constrained PII access is essential in a regulated environment. The script defaults to the
  masked environment; unmasked data is only available where the user's access permits.
- The investigator provides a valid `party_id` — case assignment happens outside this tool.
- The underlying source data may contain quality issues. The script surfaces these where they
  affect completeness; it does not validate the correctness of the source data itself.

---

## Constraints

- The script makes no decisions. It collates and presents data only.
- No risk scores, recommendations or conclusions are produced — these remain with the investigator.
- The script must run without paid API keys or private credentials.
- Data is read-only. The script never writes back to any source system.
- Output is written to stdout or a plain text file, formatted for direct copy-paste into case
  or alert notes. No structured data formats (JSON, XML) are used in the investigator-facing output.
- PII is never written to logs, regardless of environment. Log entries reference record IDs only.

---

## Out of Scope

- **LLM summarisation** — layering a language model to interpret or narrate the output is a
  planned future stage, not part of this implementation.
- Risk scoring or automated decision-making of any kind.
- Case management, workflow routing or alert assignment.
- A web or desktop UI.
- Integration with live bank systems (current implementation uses CSV-based mock data).

---

## Success Criteria

- Given a valid `party_id`, the script produces a complete case summary in under 5 seconds.
- The output accurately reflects the source data as ingested — the script introduces no errors
  or omissions of its own. This is verified by tests that compare ingested mock data against
  script output directly.
- Date range filtering applies correctly to transaction data — only transactions within the
  specified window are included in the summary.
- The output header clearly shows when the underlying data was last refreshed (`data_as_of`),
  so the investigator can assess whether the data is current before relying on it.
- Every observation in the output cites the source file and record ID it came from.
- Data excluded due to quality issues is noted in the output so the investigator knows
  their summary may be incomplete.
- The script exits cleanly with a clear message and a nonzero exit code when the party is
  unknown or data is insufficient. This protects the investigator from making a decision
  based on a partial or empty summary without being aware of it.
- All checks pass via a single `./verify.sh` command from a clean checkout.
