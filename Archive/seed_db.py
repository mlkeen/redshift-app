from shared.models import db, Character
from shared.config import Config
from flask import Flask

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    # Create characters with passwords
    varos = Character(name="Dr. Elen Varos", role="Engineer", email="varos@hotmail.com", health=92)
    varos.set_password("pass123")

    kael = Character(name="Mira Kael", role="Security", email="kael@gmail.com", health=100)
    kael.set_password("pass123")

    solin = Character(name="Solin-9", role="Synthetic", email="tippitytop@gmail.com", health=83, station_status="Offline")
    solin.set_password("pass123")

    db.session.add_all([varos, kael, solin])
    db.session.commit()
    print("✅ Database seeded with hashed passwords.")
