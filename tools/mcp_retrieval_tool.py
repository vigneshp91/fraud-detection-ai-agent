"""
CrewAI tool: retrieve_knowledge via MCP.

The risk_score_agent uses this to look up fraud detection policy rules and
risk scoring guidelines from the FAISS knowledge base before calculating a score.
"""
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from mcp.fraud_mcp_server import fraud_mcp_client


class _Input(BaseModel):
    query: str = Field(description="The search query to retrieve relevant fraud policy chunks")
    top_k: int = Field(default=3, description="Number of document chunks to retrieve")


class MCPRetrievalTool(BaseTool):
    name: str = "retrieve_knowledge"
    description: str = (
        "Searches the fraud detection policy knowledge base using semantic search. "
        "Use this to look up risk scoring rules, high-risk indicators, escalation thresholds, "
        "and known false positive patterns before calculating a risk score."
    )
    args_schema: type[BaseModel] = _Input

    def _run(self, query: str, top_k: int = 3) -> str:
        return fraud_mcp_client.call_tool("retrieve_knowledge", query=query, top_k=top_k)
