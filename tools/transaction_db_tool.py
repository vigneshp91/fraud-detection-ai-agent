import json
import sqlite3
import os
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "transactions.db")


class TransactionQueryInput(BaseModel):
    user_id: str = Field(description="The user ID to look up transaction history for")


class TransactionHistoryTool(BaseTool):
    name: str = "transaction_history_lookup"
    description: str = (
        "Fetches the past 30 transactions for a given user from the database. "
        "Returns aggregated stats: avg amount, max amount, fraud count, common locations, "
        "common categories, and recent transaction list."
    )
    args_schema: type[BaseModel] = TransactionQueryInput

    def _run(self, user_id: str) -> str:
        db_path = os.path.abspath(DB_PATH)
        if not os.path.exists(db_path):
            return json.dumps({"error": "Database not found. Run: python data/setup_db.py"})

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT amount, merchant, category, location, timestamp, is_fraud
            FROM transactions
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 30
        """, (user_id,))
        rows = cursor.fetchall()

        if not rows:
            conn.close()
            return json.dumps({"error": f"No transaction history found for user '{user_id}'"})

        amounts      = [r["amount"] for r in rows]
        fraud_count  = sum(r["is_fraud"] for r in rows)
        locations    = [r["location"] for r in rows]
        categories   = [r["category"] for r in rows]
        transactions = [dict(r) for r in rows]

        cursor.execute("SELECT COUNT(*) as total FROM transactions WHERE user_id = ?", (user_id,))
        total = cursor.fetchone()["total"]
        conn.close()

        summary = {
            "user_id":               user_id,
            "total_transactions":    total,
            "last_30_transactions":  len(transactions),
            "avg_amount":            round(sum(amounts) / len(amounts), 2),
            "max_amount":            max(amounts),
            "min_amount":            min(amounts),
            "fraud_count_in_last30": fraud_count,
            "fraud_rate_pct":        round(fraud_count / len(transactions) * 100, 1),
            "unique_locations":      list(set(locations)),
            "category_breakdown":    {c: categories.count(c) for c in set(categories)},
            "recent_transactions":   transactions[:10],
        }
        return json.dumps(summary, indent=2)
