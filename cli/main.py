"""Top-level click group that wires every subcommand together.

Owner: Sky Zhou (sxz903).

Run ``python -m cli --help`` to see everything. Each subcommand module
registers its own click group; this file just imports and aggregates.
"""

from __future__ import annotations

import click

from cli.commands import admin, clips, projects, search, tags


@click.group()
def cli() -> None:
    """HarmonyVault command-line interface."""


cli.add_command(clips.clips)
cli.add_command(projects.projects)
cli.add_command(tags.tags)
cli.add_command(search.search)
cli.add_command(admin.admin)


if __name__ == "__main__":
    cli()
