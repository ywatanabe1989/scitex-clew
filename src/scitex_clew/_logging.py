#!/usr/bin/env python3
"""Logging with optional scitex.logging enhancement.

When scitex is installed, uses scitex.logging (richer formatting).
Otherwise, falls back to stdlib logging.
"""

try:
    import scitex.logging as _logging

    getLogger = _logging.getLogger
except ImportError:
    import logging

    getLogger = logging.getLogger


# EOF
