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

Five Node Classes
-----------------

Every node in the DAG is classified into one of five semantic roles:

.. list-table:: **Table 1.** Five node classes. Classification is inferred automatically from file extensions and session roles, or set explicitly via ``set_node_class()``.
   :header-rows: 1
   :widths: 15 30 55

   * - Class
     - Role
     - Examples
   * - **Source**
     - Data acquisition scripts
     - ``01_download.py``, ``collect.sh``
   * - **Input**
     - Raw data and configuration
     - ``raw_data.csv``, ``config.yaml``
   * - **Processing**
     - Transform and analysis scripts
     - ``03_analyze.py``, ``train.R``
   * - **Output**
     - Intermediate and final data products
     - ``results.csv``, ``figure1.png``
   * - **Claim**
     - Manuscript assertions tied to evidence
     - ``"Fig 1 shows p<0.05"``, ``"Table 2"``

The key operation is **backpropagation from claims to sources**: starting from a
manuscript assertion (claim), Clew traces backward through outputs, processing
scripts, and inputs to the original raw data — verifying every hash along the way.

Three Verification Modes
------------------------

.. list-table:: **Table 2.** Three verification modes. Each supports both cache verification (millisecond hash comparison) and re-run verification (sandbox re-execution).
   :header-rows: 1
   :widths: 15 25 30 30

   * - Mode
     - Scope
     - API
     - Description
   * - **Project**
     - Entire pipeline
     - ``clew.dag()``
     - Verifies every session recorded in the database in topological order. A navigation map for ongoing project monitoring. *"Is the whole project intact?"*
   * - **Files**
     - Specific outputs
     - ``clew.dag(["output.csv"])``
     - Traces backward from target files through their dependency chain. *"Can I trust this specific file?"*
   * - **Claims**
     - Manuscript assertions
     - ``clew.verify_claim("Fig 1")``
     - Verifies individual claims linked to source sessions. *"Is this figure still backed by the data?"*

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
