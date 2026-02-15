from datetime import datetime
from flask_login import UserMixin
from .extensions import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(80), nullable=False, default="Player")

class Game(db.Model):
    __tablename__ = "game"
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="lobby")  # lobby|running|ended
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    name = db.Column(db.String(80), nullable=False, default="Untitled Game")
    tick_length_seconds = db.Column(db.Integer, nullable=False, default=120)  # e.g. 120s
    start_at = db.Column(db.DateTime, nullable=True)  # scheduled start time (local-naive for now)
    started_at = db.Column(db.DateTime, nullable=True)
    last_tick_processed = db.Column(db.Integer, nullable=False, default=0)
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    join_code = db.Column(db.String(32), unique=True, index=True, nullable=False)

    host = db.relationship("User", foreign_keys=[host_id])

class Player(db.Model):
    __tablename__ = "player"
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    role_key = db.Column(db.String(64), nullable=False, default="crew")

    user = db.relationship("User", foreign_keys=[user_id])

class Entity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"), nullable=False, index=True)
    type_key = db.Column(db.String(64), nullable=False)
    data_json = db.Column(db.JSON, nullable=False, default=dict)
    location_json = db.Column(db.JSON, nullable=False, default=dict)  # {panel, zone, pos}
    owner_player_id = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=True)
    version = db.Column(db.Integer, nullable=False, default=0)

class PanelState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"), nullable=False, index=True)
    panel_key = db.Column(db.String(64), nullable=False)
    state_json = db.Column(db.JSON, nullable=False, default=dict)

    __table_args__ = (db.UniqueConstraint("game_id", "panel_key", name="uq_panel_state"),)

class EventLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"), nullable=False, index=True)
    visibility = db.Column(db.String(20), nullable=False, default="public")
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
