#!/usr/bin/env python3
"""MCP server for scitex-clew."""

import asyncio


def get_tools_sync(mcp_server):
    """Get tool list from a FastMCP server (version-agnostic, synchronous).

    Handles API differences between FastMCP 2.x and 3.x.
    """
    # FastMCP 2.x: _tool_manager._tools (dict)
    try:
        return list(mcp_server._tool_manager._tools.values())
    except AttributeError:
        pass
    # FastMCP 2.x/3.x: async get_tools()
    if hasattr(mcp_server, "get_tools"):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(mcp_server.get_tools())
        finally:
            loop.close()
    # FastMCP 3.x: only get_tool(name) exists — no list method
    raise AttributeError(
        "Cannot enumerate tools from this FastMCP version. "
        "Consider upgrading or pinning fastmcp."
    )


# EOF
