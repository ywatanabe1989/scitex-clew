#!/bin/bash
# -*- coding: utf-8 -*-
# Runs all numbered example scripts in this directory.
#
# Usage: ./00_run_all.sh [OPTIONS]
#
# Options:
#   -h, --help    Show this help message and exit

set -euo pipefail

THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    head -8 "${BASH_SOURCE[0]}" | tail -5 | sed 's/^# //'
}

case "${1:-}" in
-h | --help)
    usage
    exit 0
    ;;
esac

for script in "$THIS_DIR"/[0-9][0-9]_*.py; do
    [ -f "$script" ] || continue
    echo "=== Running: $(basename "$script") ==="
    python "$script"
    echo
done

echo "All examples completed."
