SciTeX CLEW - Hash-Based Reproducibility Verification
======================================================

**SciTeX CLEW** provides hash-based reproducibility verification for scientific pipelines.
As LLM-assisted writing accelerates publication volumes, the gap between what is published
and what is verifiable widens. Clew tracks file hashes across computational sessions and
builds a **DAG — a structured, machine-readable logic representation of an entire research
project** — enabling both human reviewers and AI agents to verify reproducibility programmatically.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   quickstart

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/scitex_clew

Key Features
------------

- **Hash Verification**: Track and verify file hashes across sessions
- **DAG Provenance**: Build and verify dependency graphs
- **Chain Verification**: Trace file lineage through processing chains
- **Claim Tracking**: Link manuscript claims to source sessions
- **MCP Integration**: FastMCP server for AI-assisted verification
- **CLI**: Command-line interface for verification workflows

Quick Example
-------------

.. code-block:: python

   import scitex_clew as clew

   # Verify a session
   result = clew.run("2025Y-11M-18D-09h12m03s_HmH5")
   print(result.is_verified)

   # Trace provenance chain
   chain_result = clew.chain("/path/to/output.csv")
   print(chain_result.status)

   # Full DAG verification
   dag_result = clew.dag(["/path/to/final_output.csv"])
   print(dag_result.is_verified)

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
