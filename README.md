# Redshift (Flask-only HUD starter)

This is a Flask-only starter that uses a neon HUD style inspired by the provided reference image.
It includes:
- Signup/login
- Dashboard + create game
- Lobby
- Engineering panel with drag/drop (MOVE_ENTITY command)
- Server-side trigger on dropping Coolant Regulator into Cooling Slot 2

## Run locally

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# Migrations
set FLASK_APP=wsgi:app   # PowerShell: $env:FLASK_APP="wsgi:app"
flask db init
flask db migrate -m "init"
flask db upgrade

flask run
```

Open http://localhost:5000
