#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Main CLI entry point for scitex-clew."""

import json
import sys

try:
    import click
except ImportError:
    # Graceful fallback: if click is not installed, print a helpful message
    # and fall back to the minimal argparse behavior.
    def main(argv=None):
        print(
            "ERROR: click is not installed. Install with: pip install scitex-clew[cli]",
            file=sys.stderr,
        )
        raise SystemExit(1)

else:
    from ._introspect import list_python_apis
    from ._mcp import mcp

    CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}

    COMMAND_CATEGORIES = [
        ("Verification", ["status", "list", "verify", "stats"]),
        ("Visualization", ["mermaid"]),
        ("Integration", ["mcp", "list-python-apis", "completion"]),
    ]

    class CategorizedGroup(click.Group):
        """Custom Click group that displays commands organized by category."""

        def format_commands(self, ctx, formatter):
            """Write categorized commands to the formatter."""
            commands = {}
            for subcommand in self.list_commands(ctx):
                cmd = self.get_command(ctx, subcommand)
                if cmd is not None and not cmd.hidden:
                    commands[subcommand] = cmd

            if not commands:
                return

            displayed = set()

            for category_name, category_commands in COMMAND_CATEGORIES:
                category_items = []
                for name in category_commands:
                    if name in commands and name not in displayed:
                        cmd = commands[name]
                        help_text = cmd.get_short_help_str(limit=formatter.width)
                        category_items.append((name, help_text))
                        displayed.add(name)

                if category_items:
                    with formatter.section(category_name):
                        formatter.write_dl(category_items)

            uncategorized = [
                (name, commands[name].get_short_help_str(limit=formatter.width))
                for name in sorted(commands.keys())
                if name not in displayed
            ]
            if uncategorized:
                with formatter.section("Other"):
                    formatter.write_dl(uncategorized)

    def _show_recursive_help(ctx: click.Context) -> None:
        """Recursively show help for all commands."""
        click.echo(ctx.get_help())
        click.echo()
        group = ctx.command
        if isinstance(group, click.Group):
            for name in sorted(group.list_commands(ctx)):
                cmd = group.get_command(ctx, name)
                sub_ctx = click.Context(cmd, parent=ctx, info_name=name)
                click.echo(f"{'=' * 60}")
                click.echo(f"Command: {name}")
                click.echo(f"{'=' * 60}")
                click.echo(sub_ctx.get_help())
                click.echo()
                if isinstance(cmd, click.Group):
                    for sub_name in sorted(cmd.list_commands(sub_ctx)):
                        sub_cmd = cmd.get_command(sub_ctx, sub_name)
                        sub_sub_ctx = click.Context(
                            sub_cmd, parent=sub_ctx, info_name=sub_name
                        )
                        click.echo(f"  {'─' * 56}")
                        click.echo(f"  Subcommand: {name} {sub_name}")
                        click.echo(f"  {'─' * 56}")
                        click.echo(sub_sub_ctx.get_help())
                        click.echo()

    def _get_version() -> str:
        """Read version from importlib.metadata."""
        try:
            from importlib.metadata import version

            return version("scitex-clew")
        except Exception:
            return "0.0.0-unknown"

    @click.group(
        cls=CategorizedGroup,
        invoke_without_command=True,
        context_settings=CONTEXT_SETTINGS,
    )
    @click.option("--version", "-V", is_flag=True, help="Show version and exit.")
    @click.option("--help-recursive", is_flag=True, help="Show help for all commands.")
    @click.pass_context
    def main(ctx: click.Context, version: bool, help_recursive: bool) -> None:
        """clew - Hash-based reproducibility verification for scientific pipelines."""
        if version:
            click.echo(f"scitex-clew {_get_version()}")
            ctx.exit(0)

        if help_recursive:
            _show_recursive_help(ctx)
            ctx.exit(0)

        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())

    # -----------------------------------------------------------------------
    # Subcommands: status, list, verify, stats, mermaid
    # -----------------------------------------------------------------------

    @main.command()
    def status():
        """Git-status-like overview of verification state."""
        import scitex_clew as clew

        result = clew.status()
        click.echo(json.dumps(result, indent=2, default=str))

    @main.command("list")
    @click.option("--limit", type=int, default=50, help="Maximum number of runs.")
    def list_runs(limit: int):
        """List tracked runs."""
        import scitex_clew as clew

        runs = clew.list_runs(limit=limit)
        for r in runs:
            sid = r["session_id"]
            run_status = r.get("status", "?")
            script = r.get("script_path", "")
            click.echo(f"  {run_status:<8} {sid}  {script}")

    @main.command()
    @click.argument("session_id")
    def verify(session_id: str):
        """Verify a specific run by session ID."""
        import scitex_clew as clew

        result = clew.run(session_id)
        icon = "OK" if result.is_verified else "FAIL"
        click.echo(f"[{icon}] {result.session_id} ({result.status.value})")
        for f in result.files:
            ficon = "OK" if f.is_verified else "!!"
            click.echo(f"  [{ficon}] {f.role:<6} {f.path}")

    @main.command()
    def stats():
        """Database statistics."""
        import scitex_clew as clew

        result = clew.stats()
        click.echo(json.dumps(result, indent=2, default=str))

    @main.command()
    @click.option("--claims", is_flag=True, help="Build DAG from registered claims.")
    def mermaid(claims: bool):
        """Generate Mermaid DAG diagram."""
        import scitex_clew as clew

        code = clew.mermaid(claims=claims)
        click.echo(code)

    @main.command("completion")
    @click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
    def completion(shell: str):
        """Generate shell completion script.

        \b
        Usage:
          eval "$(clew completion bash)"
          eval "$(clew completion zsh)"
          clew completion fish | source
        """
        import os
        import subprocess

        env = os.environ.copy()
        env["_CLEW_COMPLETE"] = f"{shell}_source"
        result = subprocess.run(
            ["clew"],
            env=env,
            capture_output=True,
            text=True,
        )
        click.echo(result.stdout)

    # -----------------------------------------------------------------------
    # Register integration commands
    # -----------------------------------------------------------------------

    main.add_command(list_python_apis)
    main.add_command(mcp)
