from datetime import datetime
from ..extensions import db
from ..models import Game, PanelState, EventLog

def _get_panel_state(game_id: int, panel_key: str) -> PanelState:
    ps = PanelState.query.filter_by(game_id=game_id, panel_key=panel_key).with_for_update().first()
    if not ps:
        ps = PanelState(game_id=game_id, panel_key=panel_key, state_json={})
        db.session.add(ps)
        db.session.flush()
    return ps

def process_ticks(game_id: int) -> int:
    """
    Advance the game simulation up to the current tick based on started_at.
    Returns number of ticks processed in this call.
    """
    g = Game.query.filter_by(id=game_id).with_for_update().first()
    if not g or not g.started_at:
        return 0

    now = datetime.now()
    tick_len = int(g.tick_length_seconds or 120)
    if tick_len <= 0:
        tick_len = 120

    elapsed = (now - g.started_at).total_seconds()
    should_have = int(elapsed // tick_len)
    done = int(g.last_tick_processed or 0)

    if should_have <= done:
        return 0

    # Load power + engineering states under lock
    power_ps = _get_panel_state(game_id, "power")
    eng_ps = _get_panel_state(game_id, "engineering")

    power_state = power_ps.state_json or {}
    eng_state = eng_ps.state_json or {}

    fusion_output = int(power_state.get("fusion_output", 0))
    heat = int(eng_state.get("heat", 0))

    ticks_to_apply = should_have - done

    # Apply heat each tick (no cooling yet)
    heat += ticks_to_apply * max(0, fusion_output)
    eng_state["heat"] = heat
    eng_ps.state_json = eng_state

    # Update processed tick counter
    g.last_tick_processed = should_have

    # Optional: log one summary event (not one per tick to avoid spam)
    db.session.add(EventLog(
        game_id=game_id,
        visibility="public",
        message=f"Auto-tick x{ticks_to_apply}: output {fusion_output} → heat +{ticks_to_apply * max(0, fusion_output)}."
    ))

    db.session.commit()
    return ticks_to_apply
