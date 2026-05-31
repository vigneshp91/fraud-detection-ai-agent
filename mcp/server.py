"""
MCP (Model Context Protocol) server — exposes agent tools over the MCP transport.
"""
import json
import logging

logger = logging.getLogger(__name__)


class MCPServer:
    def __init__(self, host: str = "localhost", port: int = 9000):
        self.host = host
        self.port = port
        self._tools: dict = {}

    def register_tool(self, name: str, handler) -> None:
        self._tools[name] = handler
        logger.info("Registered MCP tool: %s", name)

    def run(self) -> None:
        logger.info("MCP server listening on %s:%s", self.host, self.port)
        # TODO: replace with actual MCP transport (stdio / SSE)
        raise NotImplementedError("MCP server transport not yet implemented.")

    def dispatch(self, request: dict) -> dict:
        tool_name = request.get("tool")
        params    = request.get("params", {})
        handler   = self._tools.get(tool_name)
        if handler is None:
            return {"error": f"Unknown tool: {tool_name}"}
        try:
            result = handler(**params)
            return {"result": result}
        except Exception as exc:
            logger.exception("Tool %s raised an error", tool_name)
            return {"error": str(exc)}
