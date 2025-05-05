from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Character
from . import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'Control':
        from .models import User, Character
        all_users = User.query.all()
        all_characters = Character.query.all()
        return render_template('control_dashboard.html', users=all_users, characters=all_characters)
    else:
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
        position = request.form['position']
        affiliation = request.form['affiliation']
        status = request.form['status']

        abilities_raw = request.form.get('abilities', '')
        items_raw = request.form.get('items', '')

        abilities = [a.strip() for a in abilities_raw.split(',') if a.strip()]
        items = [i.strip() for i in items_raw.split(',') if i.strip()]

        new_char = Character(
            name=name,
            position=position,
            affiliation=affiliation,
            status=status,
            abilities=abilities,
            items=items,
            conditions=[],  # Always empty on creation
            user_id=current_user.id
        )
        db.session.add(new_char)
        db.session.commit()
        flash("Character created.")
        return redirect(url_for('main.dashboard'))


    return render_template('create_character.html')


@main_bp.route('/control/data')
@login_required
def control_data():
    if current_user.role != 'Control':
        abort(403)
    abilities = Ability.query.all()
    conditions = Condition.query.all()
    items = Item.query.all()
    return render_template('control_data.html', abilities=abilities, conditions=conditions, items=items)

