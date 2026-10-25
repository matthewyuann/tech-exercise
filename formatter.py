"""
formatter.py — renders a structured plain-text case summary for AML investigators.
Output is designed for copy-paste into case notes — no colour, no rich formatting.
"""

from typing import Any

CASH_REPORTING_THRESHOLD = 10_000.00
STRUCTURING_WINDOW = 500.00
CASH_DEPOSIT_CODE = "003"
LINE_WIDTH = 60

# Illustrative list — in production, source from FATF/AUSTRAC guidance and maintain as config.
# Covers FATF blacklist, common offshore secrecy jurisdictions, and high-risk jurisdictions.
HIGH_RISK_COUNTRIES: frozenset[str] = frozenset({
    # FATF blacklist
    "north korea", "iran", "myanmar",
    # FATF grey list (selected)
    "syria", "afghanistan", "yemen", "somalia", "sudan", "south sudan",
    "iraq", "libya", "mali", "nigeria",
    # Offshore / secrecy jurisdictions
    "cayman islands", "british virgin islands", "panama", "seychelles",
    "vanuatu", "belize", "marshall islands", "nauru",
})


def _section(title: str) -> str:
    return f"\n--- {title} ---"


def _divider() -> str:
    return "=" * LINE_WIDTH


def _fmt_amount(v: Any) -> str:
    if v is None:
        return "—"
    return f"AUD {float(v):>12,.2f}"


def _fmt_date(v: Any) -> str:
    if not v:
        return "—"
    return str(v)


def _flag(v: Any) -> str:
    return "YES [!]" if str(v).upper() == "Y" else "No"


def _render_header(
    party_id: str,
    from_date: str | None,
    to_date: str | None,
    env: str,
    as_of: str,
) -> str:
    lines = [
        _divider(),
        "AML CASE SUMMARY",
        _divider(),
        f"Party ID   : {party_id}",
        f"As of      : {as_of}",
        f"Environment: {env}",
    ]
    if from_date or to_date:
        lines.append(f"Date filter: {from_date or 'start'} to {to_date or 'end'}")
    else:
        lines.append("Date filter: none (all transactions)")
    return "\n".join(lines)


def _render_risk_signals(party: dict, alerts: list[dict]) -> str:
    open_count = sum(1 for a in alerts if a.get("alert_status") == "OPEN")
    lines = [_section("RISK SIGNALS")]
    lines.append(f"Risk rating  : {party.get('risk_rating', '—')}")
    lines.append(f"PEP          : {_flag(party.get('pep_flag'))}")
    lines.append(f"Sanctions    : {_flag(party.get('sanctions_flag'))}")
    lines.append(f"Open alerts  : {open_count}")
    return "\n".join(lines)


def _render_party_profile(party: dict) -> str:
    lines = [_section("PARTY PROFILE")]
    lines.append(f"Name         : {party.get('full_name', '—')}")
    lines.append(f"Date of birth: {_fmt_date(party.get('date_of_birth'))}")
    lines.append(f"Entity type  : {party.get('entity_type', '—')}")
    if party.get("entity_type") == "ENTITY":
        lines.append(f"ACN          : {party.get('acn') or '—'}")
        lines.append(f"ABN          : {party.get('abn') or '—'}")
    lines.append(f"Nationality  : {party.get('nationality', '—')}")
    lines.append(f"Address      : {party.get('address', '—')}")
    return "\n".join(lines)


def _render_accounts(accounts: list[dict]) -> str:
    count = len(accounts)
    label = "record" if count == 1 else "records"
    lines = [_section(f"LINKED ACCOUNTS ({count} {label})")]
    if not accounts:
        lines.append("No account records found.")
        return "\n".join(lines)

    header = f"{'Account Number':<22} {'Type':<15} {'Status':<10} {'Opened':<12} Closed"
    lines.append(header)
    lines.append("-" * len(header))
    for a in accounts:
        lines.append(
            f"{a.get('account_number', '—'):<22}"
            f"{a.get('account_type', '—'):<15}"
            f"{a.get('account_status', '—'):<10}"
            f"{_fmt_date(a.get('open_date')):<12}"
            f"{_fmt_date(a.get('close_date'))}"
        )
    return "\n".join(lines)


def _render_transactions(
    transactions: list[dict],
    from_date: str | None,
    to_date: str | None,
) -> str:
    date_range = (
        f" | {from_date or 'start'} to {to_date or 'end'}"
        if (from_date or to_date)
        else ""
    )
    lines = [_section(f"TRANSACTIONS ({len(transactions)} records{date_range})")]

    if not transactions:
        lines.append("No transaction records found for this period.")
        return "\n".join(lines)

    credits = [t for t in transactions if t.get("transaction_type") == "CREDIT"]
    debits  = [t for t in transactions if t.get("transaction_type") == "DEBIT"]
    total_credit = sum(t["transaction_amount"] for t in credits if t.get("transaction_amount") is not None)
    total_debit  = sum(t["transaction_amount"] for t in debits  if t.get("transaction_amount") is not None)

    lines.append(f"Total CREDIT : {_fmt_amount(total_credit)}")
    lines.append(f"Total DEBIT  : {_fmt_amount(total_debit)}")

    # Breakdown by transaction type — high-risk country activity shown first as a key red flag
    offshore = [
        t for t in transactions
        if t.get("counterparty_country")
        and t["counterparty_country"].lower() in HIGH_RISK_COUNTRIES
    ]

    type_totals: dict[str, dict] = {}
    for t in transactions:
        desc = t.get("transaction_code_desc") or "Other"
        if desc not in type_totals:
            type_totals[desc] = {"count": 0, "total": 0.0}
        type_totals[desc]["count"] += 1
        type_totals[desc]["total"] += t.get("transaction_amount") or 0.0

    lines.append("\nBy type:")
    if offshore:
        offshore_total = sum(t.get("transaction_amount") or 0.0 for t in offshore)
        word = "transaction" if len(offshore) == 1 else "transactions"
        lines.append(
            f"  {'High-Risk Country Activity [!]':<30} {len(offshore):>3} {word:<14} {_fmt_amount(offshore_total)}"
        )
    for desc, stats in sorted(type_totals.items()):
        word = "transaction" if stats["count"] == 1 else "transactions"
        lines.append(
            f"  {desc:<30} {stats['count']:>3} {word:<14} {_fmt_amount(stats['total'])}"
        )

    # Structuring indicator
    near_threshold = [
        t for t in transactions
        if t.get("transaction_code") == CASH_DEPOSIT_CODE
        and t.get("transaction_amount") is not None
        and (CASH_REPORTING_THRESHOLD - STRUCTURING_WINDOW)
        <= t["transaction_amount"]
        < CASH_REPORTING_THRESHOLD
    ]
    if len(near_threshold) >= 2:
        low = CASH_REPORTING_THRESHOLD - STRUCTURING_WINDOW
        lines.append(
            f"\n[!] STRUCTURING INDICATOR: {len(near_threshold)} cash deposits between "
            f"AUD {low:,.2f} and AUD {CASH_REPORTING_THRESHOLD:,.2f} "
            f"(reporting threshold: AUD {CASH_REPORTING_THRESHOLD:,.2f})"
        )

    return "\n".join(lines)


def _render_alerts(alerts: list[dict]) -> str:
    count = len(alerts)
    label = "record" if count == 1 else "records"
    lines = [_section(f"ALERTS ({count} {label})")]
    if not alerts:
        lines.append("No alert records found.")
        return "\n".join(lines)

    header = f"{'Alert ID':<10} {'Type':<22} {'Date':<12} {'Status':<12} Description"
    lines.append(header)
    lines.append("-" * 72)
    for a in alerts:
        lines.append(
            f"{a.get('alert_id', '—'):<10}"
            f"{a.get('alert_type', '—'):<22}"
            f"{_fmt_date(a.get('alert_date')):<12}"
            f"{a.get('alert_status', '—'):<12}"
            f"{a.get('description') or '—'}"
        )
    return "\n".join(lines)


def _render_dq_warnings(dq_warnings: list[str]) -> str:
    if not dq_warnings:
        return ""
    lines = [_section("DATA QUALITY WARNINGS")]
    lines.append(
        f"{len(dq_warnings)} record(s) excluded from this summary due to data quality issues:"
    )
    for w in dq_warnings:
        lines.append(f"  - {w}")
    return "\n".join(lines)


def _render_footer() -> str:
    return f"\n{_divider()}\nDecision reserved for the investigator.\n{_divider()}"


def format_case_summary(
    case_data: dict,
    party_id: str,
    from_date: str | None,
    to_date: str | None,
    env: str,
    as_of: str,
) -> str:
    """Render a structured plain-text case summary from loaded case data."""
    party        = case_data["party"]
    accounts     = case_data["accounts"]
    transactions = case_data["transactions"]
    alerts       = case_data["alerts"]
    dq_warnings  = case_data["dq_warnings"]

    sections = [
        _render_header(party_id, from_date, to_date, env, as_of),
        _render_risk_signals(party, alerts),
        _render_party_profile(party),
        _render_accounts(accounts),
        _render_transactions(transactions, from_date, to_date),
        _render_alerts(alerts),
        _render_dq_warnings(dq_warnings),
        _render_footer(),
    ]
    return "\n".join(s for s in sections if s)
