Examples
========

Clew ships with three example scripts in the ``examples/`` directory.
Run them all at once with:

.. code-block:: bash

   cd examples/
   ./00_run_all.sh

Example 1: Basic Verification
------------------------------

Initialize example data, query verification status, and list tracked runs.

.. code-block:: python

   import scitex_clew as clew

   # Initialize bundled example pipeline
   examples = clew.init_examples("/tmp/clew_example")

   # Git-status-like overview
   status = clew.status()
   print(f"Total runs: {status['total_runs']}")

   # List recent runs
   runs = clew.list_runs(limit=5)

   # Database statistics
   stats = clew.stats()

Output is saved to ``examples/01_basic_verification_out/status_report.txt``.


Example 2: Chain Verification
------------------------------

Verify the full dependency DAG and trace provenance chains.

.. code-block:: python

   import scitex_clew as clew

   clew.init_examples("/tmp/clew_example")

   # Verify the full DAG with claims
   result = clew.dag(claims=True)
   print(f"Verified: {result.is_verified}")

Output is saved to ``examples/02_chain_verification_out/chain_report.txt``.


Example 3: Mermaid Diagram
---------------------------

Generate a Mermaid flowchart of the dependency DAG.

.. code-block:: python

   import scitex_clew as clew

   clew.init_examples("/tmp/clew_example")

   # Generate Mermaid code
   mermaid_code = clew.mermaid(claims=True)
   print(mermaid_code)

Output is saved to ``examples/03_mermaid_diagram_out/dag.mmd``.
The ``.mmd`` file can be rendered with `mermaid-cli <https://github.com/mermaid-js/mermaid-cli>`_
or pasted into `mermaid.live <https://mermaid.live>`_.
