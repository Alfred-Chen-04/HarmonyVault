"""Flask entry point for the optional HarmonyVault web UI.

Owner: Jacob (routes) + Sky (templates). Local-only; run with:
    flask --app web.app run
"""

from __future__ import annotations

from flask import Flask

from web.routes import clips, projects, search


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(clips.bp)
    app.register_blueprint(projects.bp)
    app.register_blueprint(search.bp)

    @app.route("/")
    def index():
        return """
        <!doctype html>
        <title>HarmonyVault</title>
        <h1>HarmonyVault</h1>
        <ul>
          <li><a href="/clips">Browse clips</a></li>
          <li><a href="/projects">Projects</a></li>
          <li><a href="/search">Search</a></li>
        </ul>
        """

    return app


app = create_app()
