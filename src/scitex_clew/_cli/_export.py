#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`clew export-claims` — regenerate the claims.json artifact.

Default emits the per-claim v1.3 artifact (``export_claims_json``); ``--unified``
emits the compile-time UNIFIED render feed (value + citation + figure, in
scitex-writer's frozen schema) via ``export_manuscript_claims``.
"""

from __future__ import annotations

import json as _json

import click


@click.command(
    "export-claims",
    epilog=(
        "Example:\n"
        "  $ scitex-clew export-claims\n"
        "  $ scitex-clew export-claims --unified\n"
        "  $ scitex-clew export-claims --unified --path build/claims.json --json"
    ),
)
@click.option(
    "--unified",
    is_flag=True,
    help=(
        "Emit the UNIFIED render feed (value + citation + figure) in "
        "scitex-writer's frozen schema, for the compile-time Clew Render "
        "pre-flight. Default emits the per-claim v1.3 artifact."
    ),
)
@click.option(
    "--path",
    "path",
    default=None,
    help="Output path (default: canonical .scitex/clew/runtime/claims.json).",
)
@click.option(
    "--read-only/--no-read-only",
    "read_only",
    default=True,
    help="chmod 0o444 the output after writing (default: read-only).",
)
@click.option(
    "-y",
    "--yes",
    "yes",
    is_flag=True,
    help="Confirmation flag retained for §2 audit-cli compliance (no-op here).",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Emit JSON (also accepted at top level).",
)
@click.pass_context
def export_claims(
    ctx: click.Context, unified: bool, path, read_only: bool, yes: bool, as_json: bool
) -> None:
    """Regenerate the claims.json artifact (per-claim, or --unified render feed)."""
    del yes  # accepted for §2 compliance
    if unified:
        from scitex_clew import export_manuscript_claims

        out = export_manuscript_claims(path=path, read_only=read_only)
    else:
        from scitex_clew import export_claims_json

        out = export_claims_json(path=path, read_only=read_only)

    payload = {"path": str(out), "unified": unified}
    if as_json or (ctx.obj and ctx.obj.get("json")):
        click.echo(_json.dumps(payload, indent=2))
    else:
        kind = "unified render feed" if unified else "per-claim v1.3"
        click.echo(f"[EXPORTED] {kind} -> {out}")


# EOF
