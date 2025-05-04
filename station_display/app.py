from flask import Flask
from dotenv import load_dotenv
load_dotenv()
from shared.config import Config
from shared import models
from station_display.routes.status import status_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    models.init_app(app)
    app.register_blueprint(status_bp)

    return app
