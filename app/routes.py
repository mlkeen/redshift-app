from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from .models import Character, Item, User, Ability, Condition, Display
from . import db
import qrcode
import io
import os
from PIL import Image
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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

@main_bp.route('/control/character/<int:char_id>', methods=['GET', 'POST'])
@login_required
def edit_character_control(char_id):
    if current_user.role != 'Control':
        abort(403)

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
        all_conditions=all_conditions
    )





@main_bp.route('/claim_item', methods=['GET', 'POST'])
@login_required
def claim_item():
    if current_user.role != 'Player':
        abort(403)

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
        
    return render_template('claim_item.html', message=message)

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
    displays = Display.query.all()
    return render_template('displays.html', displays=displays)

@main_bp.route('/control/displays/edit/<int:display_id>', methods=['GET', 'POST'])
@login_required
def edit_display(display_id):
    if current_user.role != 'Control':
        abort(403)
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
    return render_template('edit_display.html', display=display)
    

@main_bp.route('/display/<int:display_id>')
def show_display(display_id):
    display = Display.query.get_or_404(display_id)
    state = GameState.query.get(1)
    return render_template('show_display.html', display=display)

@main_bp.route('/control/displays/new', methods=['GET', 'POST'])
@login_required
def create_display():
    if current_user.role != 'Control':
        abort(403)
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
    return render_template('create_display.html')

@main_bp.route('/display/<int:display_id>/qr')
def display_qr(display_id):
    display = Display.query.get_or_404(display_id)
    url = url_for('main.show_display', display_id=display.id, _external=True)
    img = qrcode.make(url)

    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@main_bp.route('/control/game', methods=['GET', 'POST'])
@login_required
def control_game_state():
    if current_user.role != 'Control':
        abort(403)

    state = GameState.query.get(1)
    if not state:
        state = GameState(id=1)
        db.session.add(state)
        db.session.commit()

    if request.method == 'POST':
        state.current_cycle = int(request.form['current_cycle'])
        state.current_phase = request.form['current_phase']
        state.global_alert = request.form['global_alert']
        state.global_message = request.form['global_message']
        state.lockdown_enabled = 'lockdown_enabled' in request.form
        db.session.commit()

    return render_template('control_game_state.html', state=state)
