#!/usr/bin/env python3
"""MCP tool registration for scitex-clew."""

from fastmcp import FastMCP


def register_all_tools(mcp: FastMCP) -> None:
    """Register all clew MCP tools with the server."""
    from . import verification

    verification.register_tools(mcp)


__all__ = ["register_all_tools"]

# EOF
