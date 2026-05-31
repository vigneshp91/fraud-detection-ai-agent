"""
AI Fraud Detection Agent — CLI entry point.

Usage :
    python scripts/run_agent.py                        # runs built-in demo transactions
    python scripts/run_agent.py '{"user_id": "user_001", "amount": 4500, ...}'
"""
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from data.setup_db import setup_database
setup_database()

from agent.core_agent import build_crew

DEMO_TRANSACTIONS = {
    "low_risk": {
        "transaction_id": "txn_low_001",
        "user_id": "user_001",
        "amount": 45.50,
        "merchant": "Starbucks",
        "category": "restaurant",
        "location": "New York, NY",
        "timestamp": "2026-04-26 09:15:00",
    },
    "medium_risk": {
        "transaction_id": "txn_med_001",
        "user_id": "user_002",
        "amount": 380.00,
        "merchant": "Apple Store",
        "category": "electronics",
        "location": "Chicago, IL",
        "timestamp": "2026-04-26 14:30:00",
    },
    "high_risk": {
        "transaction_id": "txn_high_001",
        "user_id": "user_003",
        "amount": 2200.00,
        "merchant": "Unknown Merchant",
        "category": "online",
        "location": "Lagos, Nigeria",
        "timestamp": "2026-04-26 03:47:00",
    },
}


def run(transaction: dict) -> dict:
    print("\n" + "=" * 60)
    print("  AI FRAUD DETECTION AGENT")
    print("=" * 60)
    print(f"\nAnalyzing transaction:\n{json.dumps(transaction, indent=2)}\n")

    crew   = build_crew(transaction)
    result = crew.kickoff()

    raw = result.raw if hasattr(result, "raw") else str(result)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        report = json.loads(raw)
    except json.JSONDecodeError:
        report = {"raw_output": raw}

    print("\n" + "=" * 60)
    print("  FRAUD RISK REPORT")
    print("=" * 60)
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            tx = json.loads(sys.argv[1])
        except json.JSONDecodeError as e:
            print(f"Invalid JSON argument: {e}")
            sys.exit(1)
        run(tx)
    else:
        for label, tx in DEMO_TRANSACTIONS.items():
            print(f"\n{'#' * 60}")
            print(f"  DEMO: {label.upper().replace('_', ' ')}")
            print(f"{'#' * 60}")
            run(tx)
            input("\nPress Enter to continue to the next demo...\n")
