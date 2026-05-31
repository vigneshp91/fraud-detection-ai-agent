"""
MCP client — sends tool-call requests to the MCP server.
"""
import json
import logging

logger = logging.getLogger(__name__)


class MCPClient:
    def __init__(self, host: str = "localhost", port: int = 9000):
        self.host = host
        self.port = port

    def call_tool(self, tool_name: str, **params) -> dict:
        # TODO: implement actual MCP transport (stdio / SSE)
        payload = {"tool": tool_name, "params": params}
        logger.debug("MCP call: %s", json.dumps(payload))
        raise NotImplementedError("MCP client transport not yet implemented.")
