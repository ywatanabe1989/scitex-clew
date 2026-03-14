CLI Reference
=============

Clew provides a command-line interface via the ``clew`` command (requires ``pip install scitex-clew[cli]``).

Overview
--------

.. code-block:: bash

   clew --help-recursive    # Show all commands and subcommands

Core Commands
-------------

.. code-block:: bash

   clew status              # Git-status-like verification overview
   clew verify SESSION_ID   # Verify a specific session run
   clew list                # List tracked runs
   clew stats               # Database statistics
   clew mermaid             # Generate Mermaid DAG diagram

Introspection
-------------

.. code-block:: bash

   clew list-python-apis         # List all Python API functions
   clew list-python-apis -v      # With signatures
   clew list-python-apis -vv     # With descriptions
   clew list-python-apis -vvv    # Full details

MCP Subcommands
---------------

.. code-block:: bash

   clew mcp start           # Start MCP server
   clew mcp doctor          # Check MCP dependencies
   clew mcp installation    # Show installation instructions
   clew mcp list-tools      # List available MCP tools
   clew mcp list-tools -v   # With signatures
