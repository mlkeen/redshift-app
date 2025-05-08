import os
from app import create_app, db
from app.models import User, Character, Display
from dotenv import load_dotenv
load_dotenv()


app = create_app()

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Railway provides PORT
    app.run(host="0.0.0.0", port=port)

""" 
import os
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Welcome to Redshift!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Railway provides PORT
    app.run(host="0.0.0.0", port=port) """