"""
MCP transport layer.

InProcessTransport wires a client directly to an MCPServer in the same process.
To go multi-process, swap it for StdioTransport or SSETransport without touching
the client or server code.
"""
import logging

logger = logging.getLogger(__name__)


class InProcessTransport:
    """Routes JSON-RPC 2.0 messages directly to an MCPServer instance (no network hop)."""

    def __init__(self, server) -> None:
        self._server = server

    def send(self, message: dict) -> dict:
        method = message.get("method", "")
        tool = message.get("params", {}).get("name", "")
        logger.debug("MCP → server | method=%s tool=%s", method, tool or "-")
        response = self._server.handle(message)
        status = "ok" if "result" in response else "error"
        logger.debug("MCP ← server | status=%s", status)
        return response
