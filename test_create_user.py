from app import db
from app.models import User
from werkzeug.security import generate_password_hash

user = User(username='admin', password=generate_password_hash('password'))
db.session.add(user)
db.session.commit()
