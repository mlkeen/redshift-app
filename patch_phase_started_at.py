from app import create_app, db
from app.models import GameState
from datetime import timezone

app = create_app()

with app.app_context():
    state = GameState.query.get(1)

    if state and state.phase_started_at and state.phase_started_at.tzinfo is None:
        state.phase_started_at = state.phase_started_at.replace(tzinfo=timezone.utc)
        db.session.add(state)  # <- include this to ensure SQLAlchemy tracks the change
        db.session.commit()
        print("GameState timestamp updated to UTC-aware.")
    else:
        print("No patch needed.")
