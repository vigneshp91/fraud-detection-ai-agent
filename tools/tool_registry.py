from tools.tool_search import TransactionHistoryTool
from tools.tool_escalate import EscalationTool
from tools.mcp_transaction_tool import MCPTransactionHistoryTool
from tools.mcp_escalation_tool import MCPEscalationTool

# Direct tools — bypass MCP, call data sources directly
TOOL_REGISTRY: dict = {
    "transaction_history_lookup": TransactionHistoryTool,
    "escalate_case": EscalationTool,
}

# MCP-backed tools — all calls routed through the MCP server
MCP_TOOL_REGISTRY: dict = {
    "transaction_history_lookup": MCPTransactionHistoryTool,
    "escalate_case": MCPEscalationTool,
}


def get_tool(name: str, use_mcp: bool = True):
    registry = MCP_TOOL_REGISTRY if use_mcp else TOOL_REGISTRY
    cls = registry.get(name)
    if cls is None:
        raise KeyError(f"Tool '{name}' not found in registry. Available: {list(registry)}")
    return cls()
