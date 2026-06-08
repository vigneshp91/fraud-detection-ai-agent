"""
MCP server — implements the JSON-RPC 2.0 MCP protocol.

Supported methods:
  tools/list  — returns all registered tool schemas
  tools/call  — invokes a named tool with arguments
"""
import json
import logging

logger = logging.getLogger(__name__)


class MCPServer:
    def __init__(self) -> None:
        # name → {handler, description, inputSchema}
        self._tools: dict[str, dict] = {}

    def register_tool(
        self,
        name: str,
        handler,
        description: str,
        input_schema: dict,
    ) -> None:
        self._tools[name] = {
            "handler": handler,
            "description": description,
            "inputSchema": input_schema,
        }
        logger.info("MCP server: registered tool '%s'", name)

    # ── JSON-RPC 2.0 entry point ──────────────────────────────────────────────

    def handle(self, message: dict) -> dict:
        msg_id = message.get("id")
        method = message.get("method")

        if method == "tools/list":
            return self._handle_tools_list(msg_id)
        if method == "tools/call":
            return self._handle_tools_call(msg_id, message.get("params", {}))

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }

    # ── Method handlers ───────────────────────────────────────────────────────

    def _handle_tools_list(self, msg_id) -> dict:
        tools = [
            {
                "name": name,
                "description": meta["description"],
                "inputSchema": meta["inputSchema"],
            }
            for name, meta in self._tools.items()
        ]
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": tools}}

    def _handle_tools_call(self, msg_id, params: dict) -> dict:
        name = params.get("name")
        arguments = params.get("arguments", {})
        meta = self._tools.get(name)

        if meta is None:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32602, "message": f"Unknown tool: {name}"},
            }

        try:
            raw = meta["handler"](**arguments)
            text = raw if isinstance(raw, str) else json.dumps(raw)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"content": [{"type": "text", "text": text}]},
            }
        except Exception as exc:
            logger.exception("MCP tool '%s' raised an error", name)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32000, "message": str(exc)},
            }
