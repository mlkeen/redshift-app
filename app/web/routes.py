import secrets
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm import joinedload
from sqlalchemy import or_

from ..extensions import db
from ..models import User, Game, Player, Entity, PanelState
from ..engine.ticks import process_ticks


bp = Blueprint("web", __name__)

def ensure_player(game_id: int) -> Player:
    p = Player.query.filter_by(game_id=game_id, user_id=current_user.id).first()
    if p:
        return p
    p = Player(game_id=game_id, user_id=current_user.id, role_key="crew")
    db.session.add(p)
    db.session.commit()
    return p

@bp.get("/")
def home():
    return render_template("home.html")

@bp.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        pw = request.form.get("password") or ""
        name = request.form.get("display_name") or "Player"
        if not email or not pw:
            flash("Missing email or password", "error")
            return redirect(url_for("web.signup"))
        if User.query.filter_by(email=email).first():
            flash("Email already exists", "error")
            return redirect(url_for("web.signup"))
        u = User(email=email, password_hash=generate_password_hash(pw), display_name=name)
        db.session.add(u); db.session.commit()
        login_user(u)
        return redirect(url_for("web.dashboard"))
    return render_template("signup.html")

@bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        pw = request.form.get("password") or ""
        u = User.query.filter_by(email=email).first()
        if not u or not check_password_hash(u.password_hash, pw):
            flash("Invalid credentials", "error")
            return redirect(url_for("web.login"))
        login_user(u)
        return redirect(url_for("web.dashboard"))
    return render_template("login.html")

@bp.get("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("web.home"))

@bp.get("/dashboard")
@login_required
def dashboard():
    # games you are already in
    my_game_ids = (
        db.session.query(Player.game_id)
        .filter(Player.user_id == current_user.id)
        .subquery()
    )

    games = (
        Game.query
        .filter(or_(Game.id.in_(my_game_ids), Game.is_public == True))
        .order_by(Game.id.desc())
        .all()
    )
    return render_template("dashboard.html", games=games)

@bp.route("/games/create", methods=["GET"])
#@login_required
def game_create():
    # Defaults: start time = now + 5 minutes
    dt_default = datetime.now().replace(second=0, microsecond=0)
    return render_template("game_create.html", dt_default=dt_default)

@bp.route("/games/new", methods=["GET", "POST"])
@login_required
def new_game():
    # If someone GETs this (Option B), send them to the create form
    if request.method == "GET":
        return redirect(url_for("web.game_create"))

    name = (request.form.get("name") or "").strip() or "Untitled Game"
    tick_len = int(request.form.get("tick_length_seconds") or 120)
    start_raw = (request.form.get("start_at") or "").strip()
    is_public = (request.form.get("is_public") == "1")
    join_code = secrets.token_urlsafe(16)  # ~22 chars, URL-safe

    # Basic validation
    tick_len = max(10, min(tick_len, 3600))  # 10s..60m guardrails

    start_at = None
    if start_raw:
        # HTML datetime-local comes in like "2026-02-12T16:30"
        start_at = datetime.fromisoformat(start_raw)

    g = Game(
        host_id=current_user.id,
        status="lobby",
        name=name,
        tick_length_seconds=tick_len,
        start_at=start_at,
        is_public=is_public,
        join_code=join_code,
    )
    db.session.add(g)
    db.session.commit()

    p = ensure_player(g.id)

    # Seed panel states (keep your existing seeding; example below)
    eng_ps = PanelState(game_id=g.id, panel_key="engineering",
                        state_json={"coolant_efficiency": 0.50, "alert": "NOMINAL", "heat": 0})
    power_ps = PanelState(game_id=g.id, panel_key="power",
                          state_json={"fusion_output": 3, "max_output": 6,
                                      "alloc": {"engineering": 2, "comms": 1, "biolab": 0, "life_support": 1}})
    db.session.add_all([eng_ps, power_ps])
    db.session.commit()

    # Seed entities, etc... (keep your current code)
    # ...

    return redirect(url_for("web.lobby", game_id=g.id))

@bp.get("/join/<join_code>")
@login_required
def join_game(join_code: str):
    g = Game.query.filter_by(join_code=join_code).first_or_404()

    # If already a player, just go to lobby
    p = Player.query.filter_by(game_id=g.id, user_id=current_user.id).first()
    if not p:
        p = Player(game_id=g.id, user_id=current_user.id, role_key="crew")
        db.session.add(p)
        db.session.commit()

    return redirect(url_for("web.lobby", game_id=g.id))


def require_owner(g: Game):
    if g.host_id != current_user.id:
        flash("Only the game owner can do that.", "error")
        return False
    return True

@bp.post("/games/<int:game_id>/pause")
@login_required
def pause_game(game_id: int):
    g = Game.query.get_or_404(game_id)
    if not require_owner(g):
        return redirect(url_for("web.dashboard"))
    g.status = "paused"
    db.session.commit()
    flash("Game paused.", "ok")
    return redirect(url_for("web.dashboard"))

@bp.post("/games/<int:game_id>/resume")
@login_required
def resume_game(game_id: int):
    g = Game.query.get_or_404(game_id)
    if not require_owner(g):
        return redirect(url_for("web.dashboard"))
    g.status = "running"
    db.session.commit()
    flash("Game resumed.", "ok")
    return redirect(url_for("web.dashboard"))

@bp.post("/games/<int:game_id>/end")
@login_required
def end_game(game_id: int):
    g = Game.query.get_or_404(game_id)
    if not require_owner(g):
        return redirect(url_for("web.dashboard"))
    g.status = "ended"
    db.session.commit()
    flash("Game ended.", "ok")
    return redirect(url_for("web.dashboard"))

@bp.post("/games/<int:game_id>/delete")
@login_required
def delete_game(game_id: int):
    g = Game.query.get_or_404(game_id)
    if not require_owner(g):
        return redirect(url_for("web.dashboard"))

    # IMPORTANT: delete dependent rows first if you don't have cascade set up
    PanelState.query.filter_by(game_id=game_id).delete()
    Player.query.filter_by(game_id=game_id).delete()
    Entity.query.filter_by(game_id=game_id).delete()

    db.session.delete(g)
    db.session.commit()
    flash("Game deleted.", "ok")
    return redirect(url_for("web.dashboard"))



@bp.get("/games/<int:game_id>")
@login_required
def lobby(game_id: int):
    ensure_player(game_id)
    g = Game.query.get_or_404(game_id)

    if g.started_at is None and g.start_at and datetime.now() >= g.start_at:
        g.started_at = datetime.now()
        g.status = "running"
        db.session.commit()

    process_ticks(game_id)

    players = (
        Player.query
        .filter_by(game_id=game_id)
        .options(joinedload(Player.user))
        .order_by(Player.id.asc())
        .all()
    )

    return render_template("lobby.html", 
                           game=g,
                           game_id=g.id,
                           game_name=getattr(g, "name", None),
                           players=players,
                           )

@bp.get("/games/<int:game_id>/panel/<panel_key>")
@login_required
def panel(game_id: int, panel_key: str):
    ensure_player(game_id)
    g = Game.query.get_or_404(game_id)

    if g.started_at is None and g.start_at and datetime.now() >= g.start_at:
        g.started_at = datetime.now()
        g.status = "running"
        db.session.commit()

    ps = PanelState.query.filter_by(game_id=game_id, panel_key=panel_key).first()
    state = ps.state_json if ps else {}

    return render_template("panel.html",
                           game=g,
                           game_id=game_id,
                           game_name=getattr(g, "name", None),
                           panel_key=panel_key,
                           state=state)


@bp.get("/games/<int:game_id>/time")
@login_required
def game_time(game_id: int):
    g = Game.query.get_or_404(game_id)

    # Use UTC timestamps in responses (safe for JS)
    def to_iso(dt):
        if not dt:
            return None
        # treat naive as local; for now just return isoformat (JS can parse)
        return dt.isoformat()

    process_ticks(game_id)

    now = datetime.utcnow().isoformat() + "Z"

    ticks_elapsed = 0
    if getattr(g, "started_at", None) and getattr(g, "tick_length_seconds", None):
        elapsed = (datetime.now() - g.started_at).total_seconds()
        tl = max(1, int(g.tick_length_seconds))
        ticks_elapsed = max(0, int(elapsed // tl))


    return jsonify({
        "ok": True,
        "now_utc": now,
        "status": g.status,
        "tick_length_seconds": g.tick_length_seconds,
        "start_at": to_iso(g.start_at),
        "started_at": to_iso(getattr(g, "started_at", None)),
        "ticks_elapsed": ticks_elapsed,
        "last_tick_processed": getattr(g, "last_tick_processed", 0),
        "game_name": getattr(g, "name", None),
    })

@bp.get("/games/<int:game_id>/snapshot")
@login_required
def game_snapshot(game_id: int):
    # Keep simulation caught up before returning state
    process_ticks(game_id)

    # Pull all panel states for the game
    states = PanelState.query.filter_by(game_id=game_id).all()
    panels = {ps.panel_key: (ps.state_json or {}) for ps in states}

    g = Game.query.get_or_404(game_id)

    return jsonify({
        "ok": True,
        "game": {
            "id": g.id,
            "status": g.status,
            "name": getattr(g, "name", None),
            "tick_length_seconds": getattr(g, "tick_length_seconds", None),
            "start_at": g.start_at.isoformat() if g.start_at else None,
            "started_at": g.started_at.isoformat() if getattr(g, "started_at", None) else None,
            "last_tick_processed": getattr(g, "last_tick_processed", None),
        },
        "panels": panels,
        # convenience: power allocations (so panels don't have to navigate deep)
        "power": {
            "fusion_output": int(panels.get("power", {}).get("fusion_output", 0)),
            "alloc": panels.get("power", {}).get("alloc", {}),
            "produced": int(panels.get("power", {}).get("fusion_output", 0)) * 2,
        },
        # convenience: engineering heat
        "engineering": {
            "heat": int(panels.get("engineering", {}).get("heat", 0)),
        }
    })


@bp.post("/games/<int:game_id>/power/update")
@login_required
def update_power(game_id: int):
    ensure_player(game_id)

    ps = PanelState.query.filter_by(game_id=game_id, panel_key="power").first_or_404()
    state = ps.state_json or {}

    fusion_output = int(request.form.get("fusion_output", state.get("fusion_output", 0)))
    max_output = int(state.get("max_output", 6))

    # Clamp fusion output
    fusion_output = max(0, min(fusion_output, max_output))

    # Parse allocations
    alloc = {}
    total_alloc = 0
    for key in ["engineering", "comms", "biolab", "life_support"]:
        val = int(request.form.get(f"alloc_{key}", 0))
        val = max(0, val)
        alloc[key] = val
        total_alloc += val

    # Enforce power cap
    produced = fusion_output * 2
    if total_alloc > produced:
        flash(f"Allocation exceeds available power ({total_alloc}/{produced}).", "error")
        return redirect(url_for("web.panel", game_id=game_id, panel_key="power"))


    # Heat spike if output increased
    old_output = int(state.get("fusion_output", 0))
    if fusion_output > old_output:
        eng_ps = PanelState.query.filter_by(game_id=game_id, panel_key="engineering").first()
        eng_state = eng_ps.state_json or {}
        eng_state["heat"] = int(eng_state.get("heat", 0)) + (fusion_output - old_output)
        eng_ps.state_json = dict(eng_state)
        flag_modified(eng_ps, "state_json")


    new_state = dict(state)   # create fresh dict
    new_state["fusion_output"] = fusion_output
    new_state["alloc"] = alloc

    ps.state_json = new_state
    flag_modified(ps, "state_json")  # force SQLAlchemy to detect change

    db.session.commit()

    return redirect(url_for("web.panel", game_id=game_id, panel_key="power"))

