Quickstart
==========

Python API
----------

.. code-block:: python

   import scitex_clew as clew

   # Check verification status
   status = clew.status()

   # List tracked runs
   runs = clew.list_runs(limit=10)

   # Verify a specific session
   result = clew.run("SESSION_ID")
   print(f"Verified: {result.is_verified}")

   # Trace provenance chain
   chain = clew.chain("/path/to/output.csv")

   # Full DAG verification
   dag = clew.dag(["/path/to/target.csv"])

CLI
---

.. code-block:: bash

   # Overview
   clew status

   # List runs
   clew list --limit 10

   # Verify a session
   clew verify SESSION_ID

   # Generate Mermaid diagram
   clew mermaid

   # List Python APIs
   clew list-python-apis -v

   # List MCP tools
   clew mcp list-tools -v

MCP Server
----------

.. code-block:: bash

   # Start standalone MCP server
   clew mcp start

   # Check MCP health
   clew mcp doctor
