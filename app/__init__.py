from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv
load_dotenv()


db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    mail.init_app(app)

    global serializer 
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    from .auth import auth_bp
    from .routes import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    return app

#__all__ = ['db', 'login_manager', 'mail', 'ts']

