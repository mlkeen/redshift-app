from flask import Flask
from dotenv import load_dotenv
load_dotenv()
from shared.config import Config
from shared.models import db, Character
from flask_login import LoginManager
from flask_mail import Mail

login_manager = LoginManager()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    with app.app_context():
        db.create_all()

    login_manager.login_view = 'auth.login'  # redirect route

    from player_app.routes.auth import auth_bp
    from player_app.routes.character import character_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(character_bp)

    return app

@login_manager.user_loader
def load_user(user_id):

    return Character.query.get(int(user_id))
