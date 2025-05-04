from flask import Flask
from shared.models import db, Character
from shared.config import Config
from sqlalchemy import inspect

app = Flask(__name__)
app.config.from_object(Config)

print("🔧 Config loaded:")
print("DATABASE_URL =", app.config['SQLALCHEMY_DATABASE_URI'])

db.init_app(app)


with app.app_context():
    print("📡 Entering app context...")
    
    print("📋 SQLAlchemy metadata BEFORE create_all:")
    print(db.metadata.tables.keys())  # Should include 'character'
    
    db.create_all()
    
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print("📊 Tables in database:", tables)
    
    if "character" not in tables:
        print("❌ ERROR: Character table still missing.")
    else:
        print("🎉 SUCCESS: Character table created.")
