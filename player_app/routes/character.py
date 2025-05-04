from flask import Blueprint, render_template, abort
from shared.models import Character
from flask_login import login_required, current_user

character_bp = Blueprint("character", __name__)

@character_bp.route("/character/<int:char_id>")
@login_required
def character_view(char_id):
    if current_user.id != char_id:
        abort(403)
    return render_template("character.html", character=current_user)
