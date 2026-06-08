"""
MCP client — sends JSON-RPC 2.0 tool-call requests via a pluggable transport.

Usage:
    from mcp.fraud_mcp_server import fraud_mcp_client
    result = fraud_mcp_client.call_tool("transaction_history_lookup", user_id="U001")
"""
import logging

logger = logging.getLogger(__name__)


class MCPClient:
    def __init__(self, transport) -> None:
        self._transport = transport
        self._req_id = 0

    # ── Public API ────────────────────────────────────────────────────────────

    def call_tool(self, tool_name: str, **arguments) -> str:
        """Call a named tool and return its text response.

        Raises RuntimeError if the server returns a JSON-RPC error.
        """
        self._req_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": str(self._req_id),
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }
        logger.debug("MCPClient calling tool '%s' (req_id=%s)", tool_name, self._req_id)
        response = self._transport.send(request)
        return self._extract_text(response, tool_name)

    def list_tools(self) -> list[dict]:
        """Return the list of tool schemas advertised by the server."""
        self._req_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": str(self._req_id),
            "method": "tools/list",
            "params": {},
        }
        response = self._transport.send(request)
        if "error" in response:
            raise RuntimeError(response["error"]["message"])
        return response.get("result", {}).get("tools", [])

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_text(response: dict, tool_name: str) -> str:
        if "error" in response:
            err = response["error"]
            raise RuntimeError(
                f"MCP error calling '{tool_name}' (code {err.get('code')}): {err.get('message')}"
            )
        content = response.get("result", {}).get("content", [])
        text_parts = [block["text"] for block in content if block.get("type") == "text"]
        return "\n".join(text_parts)
