"""
main.py — AML Case Summary Script
Retrieves and displays a structured case summary for a given party ID.

Usage:
    python main.py --party-id P001
    python main.py --party-id P001 --from-date 2024-09-01 --to-date 2024-10-31
"""

import argparse
import logging
import sys
from datetime import datetime, timezone

from config import get_db_path, get_env_name
from formatter import format_case_summary
from loader import build_case_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("main")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AML Case Summary Script")
    parser.add_argument("--party-id", required=True, help="Party ID to investigate")
    parser.add_argument("--from-date", default=None, help="Filter transactions from date (YYYY-MM-DD)")
    parser.add_argument("--to-date", default=None, help="Filter transactions to date (YYYY-MM-DD)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        db_path = get_db_path()
    except (ValueError, FileNotFoundError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    env = get_env_name()
    as_of = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    logger.info("party_id=%s env=%s", args.party_id, env)

    data = build_case_data(db_path, args.party_id, args.from_date, args.to_date)

    # Abstain path — unknown party
    if data["party"] is None:
        print(f"UNABLE TO ASSESS — party '{args.party_id}' not found in {env} database.")
        sys.exit(2)

    # Abstain path — no usable data
    if not data["accounts"] and not data["transactions"] and not data["alerts"]:
        print(
            f"UNABLE TO ASSESS — party '{args.party_id}' has no account, transaction "
            f"or alert records. Insufficient data to produce a case summary."
        )
        sys.exit(2)

    output = format_case_summary(
        data, args.party_id, args.from_date, args.to_date, env, as_of
    )
    print(output)


if __name__ == "__main__":
    main()
