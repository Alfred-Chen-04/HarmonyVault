from __future__ import annotations

import click
from tabulate import tabulate

from cli import db


@click.group()
def projects() -> None:
    """Commands that work with projects and collaborators."""


@projects.command("create")
@click.option("--name", required=True)
@click.option("--user", "username", required=True)
@click.option("--description", default="")
def create_project(name: str, username: str, description: str) -> None:
    affected = db.run_mutation(
        """
        INSERT INTO Projects (ownerUserID, name, description)
        SELECT userID, %(name)s, %(desc)s FROM Users WHERE username = %(user)s
        """,
        {"name": name, "desc": description, "user": username},
    )
    if affected == 0:
        raise click.ClickException(f"Unknown user: {username}")
    click.echo(f"Created project '{name}' for {username}.")


@projects.command("list-clips")
@click.option("--project", "project_name", required=True)
def list_clips(project_name: str) -> None:
    sql = """
        SELECT c.clipID, c.title, u.username AS owner,
               ma.musicalKey, ma.mode, ma.tempo
        FROM Projects p
        JOIN ProjectClips pc ON pc.projectID = p.projectID
        JOIN Clips c ON c.clipID = pc.clipID
        JOIN Users u ON u.userID = c.userID
        LEFT JOIN MusicalAttributes ma ON ma.clipID = c.clipID
        WHERE p.name = %(name)s
    """
    rows = db.run_query(sql, {"name": project_name})
    click.echo(tabulate(rows, headers="keys", tablefmt="github"))


@projects.command("invite")
@click.option("--project", "project_name", required=True)
@click.option("--user", "username", required=True)
@click.option("--role", type=click.Choice(["editor", "viewer"]), default="editor")
def invite_collaborator(project_name: str, username: str, role: str) -> None:
    affected = db.run_mutation(
        """
        INSERT IGNORE INTO ProjectCollaborators (projectID, userID, role)
        SELECT p.projectID, u.userID, %(role)s
        FROM Projects p, Users u
        WHERE p.name = %(name)s AND u.username = %(user)s
        """,
        {"role": role, "name": project_name, "user": username},
    )
    if affected == 0:
        click.echo("Invite failed (unknown project/user, or already invited).", err=True)
    else:
        click.echo(f"Added {username} as {role} on '{project_name}'.")
