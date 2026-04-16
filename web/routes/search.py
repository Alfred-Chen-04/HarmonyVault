from __future__ import annotations

from flask import Blueprint, render_template, request

from cli import db

bp = Blueprint("search", __name__, url_prefix="/search")


@bp.get("/")
def search_page():
    key = request.args.get("key") or None
    mode = request.args.get("mode") or None
    tempo_min = request.args.get("tempo_min", 0.0, type=float)
    tempo_max = request.args.get("tempo_max", 300.0, type=float)

    rows = []
    if request.args:
        rows = db.run_query(
            """
            SELECT c.clipID, c.title, u.username AS owner,
                   ma.musicalKey, ma.mode, ma.tempo
            FROM Clips c
            JOIN Users u ON u.userID = c.userID
            JOIN MusicalAttributes ma ON ma.clipID = c.clipID
            WHERE (%(key)s  IS NULL OR ma.musicalKey = %(key)s)
              AND (%(mode)s IS NULL OR ma.mode       = %(mode)s)
              AND ma.tempo BETWEEN %(tempo_min)s AND %(tempo_max)s
            ORDER BY ma.tempo
            LIMIT 200
            """,
            {
                "key": key,
                "mode": mode,
                "tempo_min": tempo_min,
                "tempo_max": tempo_max,
            },
        )
    return render_template(
        "search.html",
        rows=rows,
        key=key, mode=mode,
        tempo_min=tempo_min, tempo_max=tempo_max,
    )
