import os
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Load environment variables if needed
load_dotenv()

from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    username = "admin"
    email = "admin@redshift.local"
    password = "adminpass"

    # Check if user already exists
    existing = User.query.filter_by(username=username).first()
    if existing:
        print(f"User '{username}' already exists.")
    else:
        admin_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            is_verified=True,
            role="Control"
        )
        db.session.add(admin_user)
        db.session.commit()
        print(f"Admin user '{username}' with Control role created successfully.")
