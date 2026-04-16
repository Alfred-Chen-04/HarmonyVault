from __future__ import annotations

import click
from tabulate import tabulate

from cli import db


@click.group()
def admin() -> None:
    """Administrative aggregate queries across all users."""


@admin.command("top-tags")
@click.option("--limit", default=10, show_default=True)
def top_tags(limit: int) -> None:
    """Most popular tag names across every user's vocabulary."""
    rows = db.run_query(
        """
        SELECT t.tagName, COUNT(*) AS uses
        FROM Tags t
        JOIN ClipTags ct ON ct.tagID = t.tagID
        GROUP BY t.tagName
        ORDER BY uses DESC
        LIMIT %(limit)s
        """,
        {"limit": limit},
    )
    click.echo(tabulate(rows, headers="keys", tablefmt="github"))


@admin.command("user-stats")
@click.option("--limit", default=10, show_default=True)
def user_stats(limit: int) -> None:
    """Per-user clip, project, and collaborator counts."""
    rows = db.run_query(
        """
        SELECT u.username,
               (SELECT COUNT(*) FROM Clips c WHERE c.userID = u.userID) AS clips,
               (SELECT COUNT(*) FROM Projects p WHERE p.ownerUserID = u.userID) AS projects,
               (SELECT COUNT(*) FROM ProjectCollaborators pc
                WHERE pc.userID = u.userID) AS memberships
        FROM Users u
        ORDER BY clips DESC
        LIMIT %(limit)s
        """,
        {"limit": limit},
    )
    click.echo(tabulate(rows, headers="keys", tablefmt="github"))


@admin.command("tempo-histogram")
def tempo_histogram() -> None:
    """Distribution of clips across standard tempo buckets."""
    rows = db.run_query(
        """
        SELECT CASE
                   WHEN tempo < 80  THEN '<80'
                   WHEN tempo < 100 THEN '80-99'
                   WHEN tempo < 120 THEN '100-119'
                   WHEN tempo < 140 THEN '120-139'
                   ELSE '>=140'
               END AS bucket,
               COUNT(*) AS clips
        FROM MusicalAttributes
        GROUP BY bucket
        ORDER BY MIN(tempo)
        """,
    )
    click.echo(tabulate(rows, headers="keys", tablefmt="github"))
