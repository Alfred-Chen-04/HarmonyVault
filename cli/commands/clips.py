from __future__ import annotations

import click
from tabulate import tabulate

from cli import db


@click.group()
def clips() -> None:
    """Commands that work with audio clips."""


@clips.command("list")
@click.option("--user", "username", help="Filter to one user's clips.")
@click.option("--limit", default=20, show_default=True)
def list_clips(username: str | None, limit: int) -> None:
    sql = """
        SELECT c.clipID, c.title, u.username AS owner, c.duration,
               ma.musicalKey, ma.mode, ma.tempo
        FROM Clips c
        JOIN Users u ON u.userID = c.userID
        LEFT JOIN MusicalAttributes ma ON ma.clipID = c.clipID
        WHERE (%(username)s IS NULL OR u.username = %(username)s)
        ORDER BY c.dateCreated DESC
        LIMIT %(limit)s
    """
    rows = db.run_query(sql, {"username": username, "limit": limit})
    click.echo(tabulate(rows, headers="keys", tablefmt="github"))


@clips.command("search")
@click.option("--key", "musical_key", help="Pitch class, e.g. C, C#, Db.")
@click.option("--mode", type=click.Choice(["major", "minor"]))
@click.option("--tempo-min", type=float, default=0.0)
@click.option("--tempo-max", type=float, default=300.0)
@click.option("--limit", default=20, show_default=True)
def search_clips(
    musical_key: str | None,
    mode: str | None,
    tempo_min: float,
    tempo_max: float,
    limit: int,
) -> None:
    rows = db.run_named(
        "cli_search_clips.sql",
        {
            "key": musical_key,
            "mode": mode,
            "tempo_min": tempo_min,
            "tempo_max": tempo_max,
            "limit": limit,
        },
    )
    click.echo(tabulate(rows, headers="keys", tablefmt="github"))


@clips.command("assign")
@click.option("--clip-id", type=int, required=True)
@click.option("--project", "project_name", required=True)
def assign_clip(clip_id: int, project_name: str) -> None:
    """Add an existing clip to an existing project (by name)."""
    affected = db.run_mutation(
        """
        INSERT IGNORE INTO ProjectClips (projectID, clipID)
        SELECT p.projectID, %(clip)s FROM Projects p
        WHERE p.name = %(name)s
        """,
        {"clip": clip_id, "name": project_name},
    )
    if affected == 0:
        click.echo("No matching project, or clip already assigned.", err=True)
    else:
        click.echo(f"Assigned clip {clip_id} to project '{project_name}'.")
