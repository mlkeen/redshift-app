from flask import Blueprint, jsonify, request
from flask_login import login_required
from ..models import Entity, PanelState, EventLog
from ..engine.apply import (
    apply_move_entity,
    apply_set_fusion_output,
    apply_allocate_power,
    apply_tick_power,
)

bp = Blueprint("api", __name__)

@bp.get("/games/<int:game_id>/snapshot")
@login_required
def snapshot(game_id: int):
    entities = Entity.query.filter_by(game_id=game_id).all()
    panel_states = PanelState.query.filter_by(game_id=game_id).all()
    events = EventLog.query.filter_by(game_id=game_id).order_by(EventLog.id.desc()).limit(80).all()

    return jsonify({
        "ok": True,
        "entities": [{
            "id": e.id,
            "type_key": e.type_key,
            "data": e.data_json,
            "location": e.location_json,
            "version": e.version
        } for e in entities],
        "panel_states": [{"panel_key": ps.panel_key, "state": ps.state_json} for ps in panel_states],
        "events": [{"id": ev.id, "message": ev.message, "created_at": ev.created_at.isoformat()} for ev in reversed(events)],
    })

@bp.post("/games/<int:game_id>/commands")
@login_required
def commands(game_id: int):
    cmd = request.get_json(force=True) or {}
    ctype = cmd.get("type")

    if ctype == "MOVE_ENTITY":
        ok, err, patches, events = apply_move_entity(
            game_id=game_id,
            entity_id=int(cmd["entity_id"]),
            to_loc=cmd["to"],
            expected_version=int(cmd["expected_version"]),
        )
        if not ok:
            return jsonify({"ok": False, "error": err}), 409
        return jsonify({"ok": True, "patches": patches, "events": events})

    if ctype == "SET_FUSION_OUTPUT":
        ok, err, patches, events = apply_set_fusion_output(
            game_id=game_id,
            value=int(cmd.get("value", 0)),
        )
        if not ok:
            return jsonify({"ok": False, "error": err}), 409
        return jsonify({"ok": True, "patches": patches, "events": events})

    if ctype == "ALLOCATE_POWER":
        ok, err, patches, events = apply_allocate_power(
            game_id=game_id,
            system=str(cmd.get("system")),
            delta=int(cmd.get("delta", 0)),
        )
        if not ok:
            return jsonify({"ok": False, "error": err}), 409
        return jsonify({"ok": True, "patches": patches, "events": events})

    if ctype == "TICK_POWER":
        ok, err, patches, events = apply_tick_power(game_id=game_id)
        if not ok:
            return jsonify({"ok": False, "error": err}), 409
        return jsonify({"ok": True, "patches": patches, "events": events})

    return jsonify({"ok": False, "error": "Unknown command"}), 400
