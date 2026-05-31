from tools.tool_search import TransactionHistoryTool
from tools.tool_escalate import EscalationTool

TOOL_REGISTRY: dict = {
    "transaction_history_lookup": TransactionHistoryTool,
    "escalate_case": EscalationTool,
}


def get_tool(name: str):
    cls = TOOL_REGISTRY.get(name)
    if cls is None:
        raise KeyError(f"Tool '{name}' not found in registry. Available: {list(TOOL_REGISTRY)}")
    return cls()
