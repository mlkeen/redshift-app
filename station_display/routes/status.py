from flask import Blueprint, render_template
from shared.models import Character

status_bp = Blueprint("status", __name__, url_prefix="/display")

@status_bp.route("/overview")
def station_status():
    crew = Character.query.all()
    return render_template("display.html", crew=crew)
