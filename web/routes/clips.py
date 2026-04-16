from __future__ import annotations

from flask import Blueprint, render_template, request

from cli import db

bp = Blueprint("clips", __name__, url_prefix="/clips")


@bp.get("/")
def list_clips():
    limit = request.args.get("limit", 50, type=int)
    rows = db.run_query(
        """
        SELECT c.clipID, c.title, u.username AS owner,
               ma.musicalKey, ma.mode, ma.tempo
        FROM Clips c
        JOIN Users u ON u.userID = c.userID
        LEFT JOIN MusicalAttributes ma ON ma.clipID = c.clipID
        ORDER BY c.dateCreated DESC
        LIMIT %(limit)s
        """,
        {"limit": limit},
    )
    return render_template("clips_list.html", clips=rows)


@bp.get("/<int:clip_id>")
def clip_detail(clip_id: int):
    rows = db.run_query(
        """
        SELECT c.*, u.username AS owner,
               ma.musicalKey, ma.mode, ma.tempo, ma.timeSignature
        FROM Clips c
        JOIN Users u ON u.userID = c.userID
        LEFT JOIN MusicalAttributes ma ON ma.clipID = c.clipID
        WHERE c.clipID = %(id)s
        """,
        {"id": clip_id},
    )
    if not rows:
        return ("Not found", 404)
    versions = db.run_query(
        "SELECT versionNumber, notes, filepath, dateCreated "
        "FROM ClipVersions WHERE clipID = %(id)s "
        "ORDER BY versionNumber DESC",
        {"id": clip_id},
    )
    tags = db.run_query(
        "SELECT t.tagName FROM Tags t JOIN ClipTags ct ON ct.tagID = t.tagID "
        "WHERE ct.clipID = %(id)s ORDER BY t.tagName",
        {"id": clip_id},
    )
    return render_template(
        "clip_detail.html", clip=rows[0], versions=versions, tags=tags
    )
