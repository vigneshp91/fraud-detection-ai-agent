"""
CrewAI tool: transaction_history_lookup via MCP.

The analyst_agent uses this instead of calling SQLite directly.
All data access is routed through the MCP server so the transport
(in-process today, stdio/SSE tomorrow) is transparent to the agent.
"""
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from mcp.fraud_mcp_server import fraud_mcp_client


class _Input(BaseModel):
    user_id: str = Field(description="The user ID to look up transaction history for")


class MCPTransactionHistoryTool(BaseTool):
    name: str = "transaction_history_lookup"
    description: str = (
        "Fetches the past 30 transactions for a given user from the database via MCP. "
        "Returns aggregated stats: avg amount, max amount, fraud count, common locations, "
        "common categories, and recent transaction list."
    )
    args_schema: type[BaseModel] = _Input

    def _run(self, user_id: str) -> str:
        return fraud_mcp_client.call_tool("transaction_history_lookup", user_id=user_id)
