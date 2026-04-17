from __future__ import annotations

import click
from tabulate import tabulate

from cli import db


@click.group()
def search() -> None:
    """Cross-cutting search commands."""


@search.command("orphans")
@click.option("--user", "username", required=True)
def orphan_clips(username: str) -> None:
    """Clips owned by the user that are not in any project."""
    rows = db.run_query(
        """
        SELECT c.clipID, c.title, ma.musicalKey, ma.mode, ma.tempo
        FROM Clips c
        JOIN Users u ON u.userID = c.userID
        LEFT JOIN MusicalAttributes ma ON ma.clipID = c.clipID
        WHERE u.username = %(user)s
          AND NOT EXISTS (
              SELECT 1 FROM ProjectClips pc WHERE pc.clipID = c.clipID
          )
        """,
        {"user": username},
    )
    click.echo(tabulate(rows, headers="keys", tablefmt="github"))


@search.command("by-tag")
@click.option("--tag", "tag_name", required=True)
@click.option("--limit", default=20, show_default=True)
def clips_by_tag(tag_name: str, limit: int) -> None:
    rows = db.run_query(
        """
        SELECT c.clipID, c.title, u.username AS owner,
               ma.musicalKey, ma.mode, ma.tempo
        FROM Clips c
        JOIN Users u ON u.userID = c.userID
        JOIN ClipTags ct ON ct.clipID = c.clipID
        JOIN Tags t ON t.tagID = ct.tagID
        LEFT JOIN MusicalAttributes ma ON ma.clipID = c.clipID
        WHERE t.tagName = %(tag)s
        LIMIT %(limit)s
        """,
        {"tag": tag_name.strip().lower(), "limit": limit},
    )
    click.echo(tabulate(rows, headers="keys", tablefmt="github"))
