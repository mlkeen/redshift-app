from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Character
from . import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return "Welcome to Redshift"

@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', character=current_user.character)

@main_bp.route('/character/edit', methods=['GET', 'POST'])
@login_required
def edit_character():
    char = current_user.character
    if not char:
        flash("No character assigned.")
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        char.name = request.form['name']
        char.species = request.form['species']
        char.role = request.form['role']
        char.stats = request.form['stats']  # Assume stringified JSON for now
        db.session.commit()
        flash("Character updated.")
        return redirect(url_for('main.dashboard'))

    return render_template('edit_character.html', character=char)
