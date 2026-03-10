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

Three Verification Modes
------------------------

.. list-table::
   :header-rows: 1
   :widths: 15 25 30 30

   * - Mode
     - Scope
     - API
     - Description
   * - **Project**
     - Entire pipeline
     - ``clew.dag(claims=True)``
     - Builds the full DAG from all registered claims and verifies every session. *"Is the whole project intact?"*
   * - **Files**
     - Specific outputs
     - ``clew.dag(["output.csv"])``
     - Traces backward from target files through their dependency chain. *"Can I trust this specific file?"*
   * - **Claims**
     - Manuscript assertions
     - ``clew.verify_claim("Fig 1")``
     - Verifies individual claims linked to source sessions. *"Is this figure still backed by the data?"*

Each mode supports both **cache verification** (millisecond hash comparison) and
**re-run verification** (sandbox re-execution via ``rerun_dag`` / ``rerun_claims``).

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
