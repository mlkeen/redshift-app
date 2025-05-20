from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from .models import Character, Item, User, Ability, Condition, Display, GameState
from app.models import GameState
from . import db
import qrcode
import io
import os
from PIL import Image
from werkzeug.utils import secure_filename
#import secrets
#import string
from datetime import datetime, timezone

#def generate_claim_code():
#    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


main_bp = Blueprint('main', __name__)

@main_bp.route('/') #Initial landing page
def index():
    state = GameState.query.get(1)
    now = datetime.now()
    return render_template('index.html', state=state, now=now)

@main_bp.route('/dashboard') 
@login_required
def dashboard():
    state = GameState.query.get(1)
    now = datetime.now()
    if current_user.role == 'Control':
        from .models import User, Character
        all_users = User.query.all()
        all_characters = Character.query.all()
        return render_template('control/dashboard.html', users=all_users, characters=all_characters, state=state, now=now)
    else:
        character = current_user.character
        return render_template(
            'player/dashboard.html',
            character=current_user.character,
            state=state,
            now=now
        )
        #return render_template('player/dashboard.html', character=current_user.character)



@main_bp.route('/control/data')
@login_required
def control_data():
    if current_user.role != 'Control':
        abort(403)
    state = GameState.query.get(1)
    now = datetime.now()
    abilities = Ability.query.all()
    conditions = Condition.query.all()
    items = Item.query.all()
    return render_template('control_data.html', abilities=abilities, conditions=conditions, items=items, state=state, now=now)

@main_bp.route('/control/character/<int:char_id>', methods=['GET', 'POST'])
@login_required
def edit_character_control(char_id):
    if current_user.role != 'Control':
        abort(403)
    state = GameState.query.get(1)
    now = datetime.now()
    char = Character.query.get_or_404(char_id)
    all_items = Item.query.all()
    all_abilities = Ability.query.all()
    all_conditions = Condition.query.all()

    if request.method == 'POST':
        # Update status
        char.status = request.form.get('status', 'Nominal')

        # Update lists (clear and repopulate)
        char.items = request.form.getlist('items')
        char.abilities = request.form.getlist('abilities')
        char.conditions = request.form.getlist('conditions')

        db.session.commit()
        flash("Character updated.")
        return redirect(url_for('main.edit_character_control', char_id=char.id))

    return render_template(
        'edit_character_control.html',
        char=char,
        all_items=all_items,
        all_abilities=all_abilities,
        all_conditions=all_conditions, 
        state=state,
        now=now
    )



@main_bp.route('/claim_item', methods=['GET', 'POST'])
@login_required
def claim_item():
    if current_user.role != 'Player':
        abort(403)

    state = GameState.query.get(1)
    now = datetime.now()
    message = None
    if request.method == 'POST':
        code = request.form['code'].strip().upper()
        item = Item.query.filter_by(code=code).first()

        char = current_user.character
        if not char:
            message = "You must create a character before claiming items."
        elif not item:
            message = "Invalid code."
        elif item.name in char.items:
            message = "Item already claimed."
        else:
            char.items.append(item.name)
            db.session.commit()
            message = f"Claimed item: {item.name}"
        
    return render_template('claim_item.html', message=message, state=state, now=now)

@main_bp.route('/set_theme', methods=['POST'])
@login_required
def set_theme():
    theme = request.form.get('theme', 'theme-green')
    if theme not in ['theme-green', 'theme-yellow']:
        abort(400)
    current_user.theme = theme
    db.session.commit()
    return redirect(request.referrer or url_for('main.dashboard'))


@main_bp.route('/control/displays')
@login_required
def manage_displays():
    if current_user.role != 'Control':
        abort(403)
    state = GameState.query.get(1)
    now = datetime.now()
    displays = Display.query.all()
    return render_template('display/displays.html', displays=displays, state=state, now=now)

@main_bp.route('/control/displays/edit/<int:display_id>', methods=['GET', 'POST'])
@login_required
def edit_display(display_id):
    if current_user.role != 'Control':
        abort(403)
    state = GameState.query.get(1)
    now = datetime.now()
    display = Display.query.get_or_404(display_id)
    if 'lineart' in request.files:
        file = request.files['lineart']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"display_{display.id}.png")
            filepath = os.path.join(UPLOAD_FOLDER, filename)

            # Convert to monochrome and apply theme
            img = Image.open(file).convert('L').point(lambda x: 0 if x < 128 else 255, '1')
            print(filepath)
            # Save for future recoloring (use original 1-bit image as mask)
            img.save(filepath)
            print("Saved!")
            display.image_filename = filename
            db.session.commit()
    if request.method == 'POST':
        display.message = request.form['message']
        display.alert_level = request.form['alert_level']
        display.animation_mode = request.form['animation_mode']
        db.session.commit()
        flash("Display updated.")
        return redirect(url_for('main.manage_displays'))
    return render_template('display/edit_display.html', display=display, state=state, now=now)
    

@main_bp.route('/display/<int:display_id>')
def show_display(display_id):
    display = Display.query.get_or_404(display_id)
    state = GameState.query.get(1)
    now = datetime.now()
    return render_template('display/show_display.html', display=display, state=state, now=now)

@main_bp.route('/control/displays/new', methods=['GET', 'POST'])
@login_required
def create_display():
    if current_user.role != 'Control':
        abort(403)
    state = GameState.query.get(1)
    now = datetime.now()
    if request.method == 'POST':
        name = request.form['name']
        location = request.form.get('location', '')
        new_display = Display(
            name=name,
            location=location,
            message='Welcome to ' + name,
            alert_level='Nominal',
            animation_mode='pulse'
        )
        db.session.add(new_display)
        db.session.commit()
        return redirect(url_for('main.manage_displays'))
    return render_template('display/create_display.html', state=state, now=now)

@main_bp.route('/display/<int:display_id>/qr')
def display_qr(display_id):
    display = Display.query.get_or_404(display_id)
    url = url_for('main.show_display', display_id=display.id, _external=True)
    img = qrcode.make(url)

    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


@main_bp.route('/control/game_state', methods=['GET', 'POST'])
@login_required
def control_game_state():
    if current_user.role != 'Control':
        abort(403)

    state = GameState.query.get(1)
    now = datetime.now()

    # Create GameState if it doesn't exist
    if not state:
        state = GameState(id=1)
        db.session.add(state)
        db.session.commit()

    if request.method == 'POST':
        phase = request.form.get('phase', '').strip()
        duration = request.form.get('duration', '40').strip()

        if not phase:
            flash("Phase name is required.", "error")
        else:
            state.current_phase = phase
            state.phase_started_at = now
            state.phase_duration_minutes = int(duration) if duration.isdigit() else 40
            db.session.commit()
            flash(f"Phase updated to '{state.current_phase}'.")

    return render_template('control/game_state.html', state=state, now=now)




@main_bp.route('/claim/', methods=['GET', 'POST'])
@main_bp.route('/claim/<code>', methods=['GET', 'POST'])
@login_required
def claim_character(code=None):
    # Handle form where user types in their claim code
    state = GameState.query.get(1)
    now = datetime.now()
    if not code:
        if request.method == 'POST':
            code = request.form.get('code', '').strip()
            return redirect(url_for('main.claim_character', code=code))
        return render_template('player/claim_character_prompt.html', state=state, now=now)  # claim code entry form

    # Look up the character using the provided claim code
    char = Character.query.filter_by(claim_code=code).first()

    if not char:
        flash("Invalid claim code. Please try again.")
        return redirect(url_for('main.claim_character'))

    if char.claimed:
        flash("This character has already been claimed.")
        return redirect(url_for('main.claim_character'))

    # Show character claim form
    if request.method == 'GET':
        return render_template('player/claim_character.html', character=char, state=state, now=now)

    # POST: process the character claim form
    char.first_name = request.form.get('first_name', '').strip()
    char.surname = request.form.get('surname', '').strip()

    # Handle optional portrait upload
    file = request.files.get('portrait')
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        char.image_filename = filename

    char.claimed = True
    char.user_id = current_user.id
    db.session.commit()

    flash("Character successfully claimed.")
    return redirect(url_for('main.dashboard'))




@main_bp.route('/character/edit', methods=['GET', 'POST'])
@login_required
def edit_character():
    state = GameState.query.get(1)
    now = datetime.now()
    char = current_user.character
    if not char:
        flash("No character assigned.")
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        char.first_name = request.form['first_name']
        char.surname = request.form['surname']
        char.image_filename = request.form['image_filename']
        db.session.commit()
        flash("Character updated.")
        return redirect(url_for('main.dashboard'))

    return render_template('player/edit_character.html', character=char, state=state, now=now)

