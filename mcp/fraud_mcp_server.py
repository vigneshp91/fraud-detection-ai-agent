"""
Fraud-domain MCP server.

Registers two tools:
  - transaction_history_lookup  (reads SQLite)
  - escalate_case               (routes to fraud review team)

Exposes a module-level `fraud_mcp_client` that CrewAI tools import to make
MCP calls without caring about the transport underneath.
"""
import json
import logging
import os
import sqlite3

from mcp.server import MCPServer
from mcp.transport import InProcessTransport
from mcp.client import MCPClient

logger = logging.getLogger(__name__)

_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "transactions.db")
)


# ── Tool handlers (pure functions — no CrewAI dependency) ─────────────────────

def _transaction_history_lookup(user_id: str) -> str:
    if not os.path.exists(_DB_PATH):
        return json.dumps({"error": "Database not found. Run: python data/setup_db.py"})

    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT amount, merchant, category, location, timestamp, is_fraud
        FROM transactions
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT 30
        """,
        (user_id,),
    )
    rows = cursor.fetchall()

    if not rows:
        conn.close()
        return json.dumps({"error": f"No transaction history found for user '{user_id}'"})

    amounts      = [r["amount"] for r in rows]
    fraud_count  = sum(r["is_fraud"] for r in rows)
    locations    = [r["location"] for r in rows]
    categories   = [r["category"] for r in rows]
    transactions = [dict(r) for r in rows]

    cursor.execute(
        "SELECT COUNT(*) as total FROM transactions WHERE user_id = ?", (user_id,)
    )
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


def _escalate_case(transaction_id: str, reason: str, risk_score: int) -> str:
    payload = {
        "transaction_id": transaction_id,
        "risk_score":     risk_score,
        "reason":         reason,
        "status":         "ESCALATED",
    }
    logger.warning("MCP ESCALATION: %s", json.dumps(payload))
    return json.dumps({
        "escalated":      True,
        "transaction_id": transaction_id,
        "message":        "Case routed to fraud review team.",
    })


# ── Server bootstrap ──────────────────────────────────────────────────────────

def _build_server() -> MCPServer:
    server = MCPServer()

    server.register_tool(
        name="transaction_history_lookup",
        handler=_transaction_history_lookup,
        description=(
            "Fetches the past 30 transactions for a given user from the database. "
            "Returns aggregated stats: avg amount, max amount, fraud count, "
            "common locations, category breakdown, and recent transaction list."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The user ID to look up transaction history for",
                }
            },
            "required": ["user_id"],
        },
    )

    server.register_tool(
        name="escalate_case",
        handler=_escalate_case,
        description=(
            "Escalates a high-risk transaction to the human fraud review team. "
            "Use when risk_score >= 61 or when automated analysis is inconclusive."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "transaction_id": {
                    "type": "string",
                    "description": "The transaction ID to escalate",
                },
                "reason": {
                    "type": "string",
                    "description": "Why this transaction is being escalated",
                },
                "risk_score": {
                    "type": "integer",
                    "description": "The assessed risk score (0-100)",
                    "minimum": 0,
                    "maximum": 100,
                },
            },
            "required": ["transaction_id", "reason", "risk_score"],
        },
    )

    return server


# Module-level singletons — import these in tool files
_server = _build_server()
_transport = InProcessTransport(_server)
fraud_mcp_client = MCPClient(_transport)
