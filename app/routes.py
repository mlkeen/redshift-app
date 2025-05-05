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

@main_bp.route('/character/create', methods=['GET', 'POST'])
@login_required
def create_character():
    if current_user.character:
        flash("You already have a character.")
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        name = request.form['name']
        species = request.form['species']
        role = request.form['role']
        stats = request.form['stats']

        from .models import Character
        new_char = Character(
            name=name,
            species=species,
            role=role,
            stats=stats,
            user_id=current_user.id
        )
        db.session.add(new_char)
        db.session.commit()
        flash("Character created.")
        return redirect(url_for('main.dashboard'))

    return render_template('create_character.html')
