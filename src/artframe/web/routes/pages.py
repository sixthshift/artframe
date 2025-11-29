"""
HTML page routes for Artframe dashboard.
"""

from flask import render_template

from . import bp


@bp.route("/")
def index():
    """Render main dashboard."""
    return render_template("dashboard.html")


@bp.route("/display")
def display_page():
    """Render display page."""
    return render_template("display.html")


@bp.route("/system")
def system_page():
    """Render system page."""
    return render_template("system.html")


@bp.route("/config")
def config_page():
    """Render configuration page."""
    return render_template("config.html")


@bp.route("/plugins")
def plugins_page():
    """Render plugins management page."""
    return render_template("plugins.html")


@bp.route("/playlists")
def playlists_page():
    """Render playlists management page."""
    return render_template("playlists.html")


@bp.route("/schedule")
def schedule_page():
    """Render schedule management page."""
    return render_template("schedule.html")
