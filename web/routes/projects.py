from __future__ import annotations

from flask import Blueprint, render_template

from cli import db

bp = Blueprint("projects", __name__, url_prefix="/projects")


@bp.get("/")
def list_projects():
    rows = db.run_query(
        """
        SELECT p.projectID, p.name, u.username AS owner,
               COUNT(pc.clipID) AS clip_count
        FROM Projects p
        JOIN Users u ON u.userID = p.ownerUserID
        LEFT JOIN ProjectClips pc ON pc.projectID = p.projectID
        GROUP BY p.projectID, p.name, u.username
        ORDER BY clip_count DESC, p.name
        """
    )
    return render_template("projects_list.html", projects=rows)


@bp.get("/<int:project_id>")
def project_detail(project_id: int):
    projects = db.run_query(
        """
        SELECT p.projectID, p.name, p.description, u.username AS owner
        FROM Projects p JOIN Users u ON u.userID = p.ownerUserID
        WHERE p.projectID = %(id)s
        """,
        {"id": project_id},
    )
    if not projects:
        return ("Not found", 404)
    clips = db.run_query(
        """
        SELECT c.clipID, c.title, u.username AS owner,
               ma.musicalKey, ma.mode, ma.tempo
        FROM ProjectClips pc
        JOIN Clips c ON c.clipID = pc.clipID
        JOIN Users u ON u.userID = c.userID
        LEFT JOIN MusicalAttributes ma ON ma.clipID = c.clipID
        WHERE pc.projectID = %(id)s
        """,
        {"id": project_id},
    )
    collaborators = db.run_query(
        """
        SELECT u.username, pc.role, pc.addedAt
        FROM ProjectCollaborators pc JOIN Users u ON u.userID = pc.userID
        WHERE pc.projectID = %(id)s
        """,
        {"id": project_id},
    )
    return render_template(
        "project_detail.html",
        project=projects[0],
        clips=clips,
        collaborators=collaborators,
    )
