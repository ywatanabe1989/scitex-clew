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

    # Try async methods: get_tools (2.x) then list_tools (3.x)
    for method_name in ("get_tools", "list_tools"):
        method = getattr(mcp_server, method_name, None)
        if method is not None and callable(method):
            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(method())
                if isinstance(result, dict):
                    return list(result.values())
                return list(result)
            finally:
                loop.close()

    raise AttributeError(
        "Cannot enumerate tools from this FastMCP version. "
        "Consider upgrading or pinning fastmcp."
    )


# EOF
