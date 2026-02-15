from flask import Flask
from .config import Config
from .extensions import db, migrate, login_manager
from .models import User

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from .web.routes import bp as web_bp
    from .api.routes import bp as api_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    return app

@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))
