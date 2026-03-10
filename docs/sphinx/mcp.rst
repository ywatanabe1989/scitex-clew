MCP Server
==========

Clew provides a `Model Context Protocol <https://modelcontextprotocol.io/>`_ (MCP)
server, enabling AI agents to verify reproducibility and trace provenance autonomously.

Installation
------------

.. code-block:: bash

   pip install scitex-clew[mcp]

Starting the Server
-------------------

.. code-block:: bash

   clew mcp start

MCP Client Configuration
-------------------------

Add to your MCP client configuration (e.g., Claude Desktop, Cursor):

.. code-block:: json

   {
     "mcpServers": {
       "scitex-clew": {
         "command": "clew",
         "args": ["mcp", "start"]
       }
     }
   }

Available Tools
---------------

.. list-table:: **Table 3.** Nine MCP tools for AI-assisted verification. All tools accept JSON parameters and return JSON results.
   :header-rows: 1
   :widths: 25 75

   * - Tool
     - Description
   * - ``clew_status``
     - Git-status-like verification overview
   * - ``clew_run``
     - Verify a specific session run
   * - ``clew_chain``
     - Trace file provenance chain
   * - ``clew_dag``
     - Verify full DAG
   * - ``clew_list``
     - List tracked runs
   * - ``clew_stats``
     - Database statistics
   * - ``clew_mermaid``
     - Generate Mermaid DAG diagram
   * - ``clew_rerun_dag``
     - Rerun full DAG in sandbox
   * - ``clew_rerun_claims``
     - Rerun all claim-backing sessions

Diagnostics
-----------

.. code-block:: bash

   clew mcp doctor          # Check dependencies and server health
   clew mcp list-tools -vv  # List tools with descriptions
