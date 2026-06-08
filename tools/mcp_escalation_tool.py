"""
CrewAI tool: escalate_case via MCP.

The fraud_detection_agent uses this to route high-risk transactions to the
human review team. The call travels through the MCP server so the escalation
sink (log today, webhook/queue tomorrow) is transparent to the agent.
"""
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from mcp.fraud_mcp_server import fraud_mcp_client


class _Input(BaseModel):
    transaction_id: str = Field(description="The transaction ID to escalate")
    reason: str = Field(description="Why this transaction is being escalated")
    risk_score: int = Field(description="The assessed risk score (0-100)", ge=0, le=100)


class MCPEscalationTool(BaseTool):
    name: str = "escalate_case"
    description: str = (
        "Escalates a high-risk transaction to the human fraud review team via MCP. "
        "Use when risk_score >= 61 or when automated analysis is inconclusive."
    )
    args_schema: type[BaseModel] = _Input

    def _run(self, transaction_id: str, reason: str, risk_score: int) -> str:
        return fraud_mcp_client.call_tool(
            "escalate_case",
            transaction_id=transaction_id,
            reason=reason,
            risk_score=risk_score,
        )
