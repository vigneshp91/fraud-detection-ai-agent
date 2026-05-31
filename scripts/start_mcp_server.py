"""
Start the MCP (Model Context Protocol) server.

Usage :
    python scripts/start_mcp_server.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import MCPServer


def main():
    server = MCPServer()
    print("Starting MCP server...")
    server.run()


if __name__ == "__main__":
    main()
