from ..extensions import db
from ..models import PanelState, EventLog
from .patches import panel_state_set, event

def trigger_install_regulator_slot2(*, game_id: int) -> tuple[list[dict], list[dict]]:
    patches, events = [], []
    ps = PanelState.query.filter_by(game_id=game_id, panel_key="engineering").with_for_update().first()
    if not ps:
        ps = PanelState(game_id=game_id, panel_key="engineering", state_json={})
        db.session.add(ps)
        db.session.flush()

    ps.state_json["coolant_efficiency"] = 0.72
    patches.append(panel_state_set("engineering", "/coolant_efficiency", 0.72))

    msg = "Cooling Array updated: Regulator installed in Slot 2 (+efficiency)."
    db.session.add(EventLog(game_id=game_id, visibility="public", message=msg))
    events.append(event(msg, "public"))
    return patches, events
