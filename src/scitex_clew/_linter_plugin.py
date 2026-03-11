"""Linter plugin for scitex-clew: provenance/verification rules.

Registered via entry point 'scitex_linter.plugins' so scitex-linter
discovers these rules automatically when scitex-clew is installed.

NOTE: No clew-specific lint rules have been defined yet in scitex-linter.
      This file is a placeholder that registers a no-op plugin so the
      entry-point machinery is exercised.

Candidate rules for a future CW (Clew) category:
  CW001 — file written without stx.io.save() → no provenance record created
  CW002 — clew.run() / clew.chain() called but result not checked (ignored)
  CW003 — add_claim() without a backing session_id → unverifiable claim
  CW004 — hash_file() result assigned but never stored in DB
  CW005 — rerun() called inside a tracked @stx.session → infinite loop risk
"""


def get_plugin():
    """Return scitex-clew linter rules (currently empty placeholder)."""
    # No clew-specific Rule objects exist in scitex-linter yet.
    # Return a valid but empty plugin dict so the entry-point is exercised.
    return {
        "rules": [],
        "call_rules": {},
        "axes_hints": {},
        "checkers": [],
    }
