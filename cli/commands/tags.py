from __future__ import annotations

import click
from tabulate import tabulate

from cli import db


@click.group()
def tags() -> None:
    """Commands that work with tags."""


@tags.command("list")
@click.option("--user", "username", required=True)
def list_tags(username: str) -> None:
    rows = db.run_query(
        """
        SELECT t.tagID, t.tagName, COUNT(ct.clipID) AS clips
        FROM Users u
        JOIN Tags t ON t.userID = u.userID
        LEFT JOIN ClipTags ct ON ct.tagID = t.tagID
        WHERE u.username = %(user)s
        GROUP BY t.tagID, t.tagName
        ORDER BY clips DESC, t.tagName ASC
        """,
        {"user": username},
    )
    click.echo(tabulate(rows, headers="keys", tablefmt="github"))


@tags.command("create")
@click.option("--user", "username", required=True)
@click.option("--name", required=True)
def create_tag(username: str, name: str) -> None:
    affected = db.run_mutation(
        """
        INSERT IGNORE INTO Tags (userID, tagName)
        SELECT userID, %(name)s FROM Users WHERE username = %(user)s
        """,
        {"user": username, "name": name.strip().lower()},
    )
    if affected == 0:
        click.echo("Tag already exists or unknown user.", err=True)
    else:
        click.echo(f"Created tag '{name}' for {username}.")
