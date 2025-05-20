from . import db, login_manager
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default='Player')  # 'Player' or 'Control'
    theme = db.Column(db.String(32), default='theme-green')
    character = db.relationship("Character", backref="user", uselist=False)

class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64))
    surname = db.Column(db.String(64))
    position = db.Column(db.String(100))
    affiliation = db.Column(db.String(100))
    status = db.Column(db.String(50), default="Nominal")
    image_filename = db.Column(db.String(128))  # optional
    abilities = db.Column(db.PickleType, default=list)   # List of strings
    conditions = db.Column(db.PickleType, default=list)  # List of strings (empty at start)
    items = db.Column(db.PickleType, default=list)        # List of strings
    claim_code = db.Column(db.String(16), unique=True, nullable=True)
    claimed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Ability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)

class Condition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    effect = db.Column(db.Text)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    code = db.Column(db.String(10), unique=True, nullable=False)


class Display(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)  # e.g. "Med Bay"
    location = db.Column(db.String(64))  # Optional extra label
    message = db.Column(db.Text)  # Displayed text block or status
    alert_level = db.Column(db.String(32), default="Nominal")  # e.g. Nominal, Warning, Critical
    animation_mode = db.Column(db.String(32), default="pulse")  # e.g. pulse, flicker, scan
    code = db.Column(db.String(16), unique=True)
    image_filename = db.Column(db.String(128))  # optional
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

class GameState(db.Model):
    id = db.Column(db.Integer, primary_key=True, default=1)
    current_phase = db.Column(db.String(50), default="Not Started")
    phase_started_at = db.Column(db.DateTime, nullable=True)
    phase_duration_minutes = db.Column(db.Integer, default=40)
    alert_level = db.Column(db.String(20), default="Nominal")