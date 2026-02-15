from __future__ import annotations

from ..extensions import db
from ..models import Game, Entity, PanelState, EventLog
from .validate import validate_move
from .patches import entity_moved, panel_state_set, panel_state_merge, event
from .schemas import load_scenario, get_panel_schema
from . import triggers
from .power import power_produced, heat_per_tick, heat_on_output_increase

POWER_PANEL = "power"
ENGINEERING_PANEL = "engineering"

def _get_panel_state(game_id: int, panel_key: str) -> PanelState:
    ps = PanelState.query.filter_by(game_id=game_id, panel_key=panel_key).with_for_update().first()
    if not ps:
        ps = PanelState(game_id=game_id, panel_key=panel_key, state_json={})
        db.session.add(ps)
        db.session.flush()
    return ps

def _add_event(game_id: int, msg: str) -> None:
    db.session.add(EventLog(game_id=game_id, visibility="public", message=msg))

def apply_move_entity(*, game_id: int, entity_id: int, to_loc: dict, expected_version: int):
    g = Game.query.get(game_id)
    if not g:
        return False, "Game not found", [], []

    ent = Entity.query.filter_by(id=entity_id, game_id=game_id).with_for_update().first()
    if not ent:
        return False, "Entity not found", [], []
    if ent.version != expected_version:
        return False, "Stale version", [], []

    ok, reason = validate_move(
        scenario_id="engineering_demo",
        panel=to_loc["panel"],
        zone=to_loc["zone"],
        entity_type=ent.type_key,
    )
    if not ok:
        return False, reason, [], []

    ent.location_json = to_loc
    ent.version += 1
    patches = [entity_moved(ent.id, ent.location_json, ent.version)]
    events = []

    # Trigger based on schema
    scenario = load_scenario("engineering_demo")
    panel_schema = get_panel_schema(scenario, to_loc["panel"])
    zone_schema = panel_schema.get("zones", {}).get(to_loc["zone"], {})
    trig = zone_schema.get("trigger")
    if trig == "install_regulator_slot2" and ent.type_key == "coolant_regulator":
        p2, e2 = triggers.trigger_install_regulator_slot2(game_id=game_id)
        patches.extend(p2)
        events.extend(e2)

    db.session.commit()
    return True, "", patches, events

def apply_set_fusion_output(*, game_id: int, value: int):
    g = Game.query.get(game_id)
    if not g:
        return False, "Game not found", [], []

    power_ps = _get_panel_state(game_id, POWER_PANEL)
    eng_ps = _get_panel_state(game_id, ENGINEERING_PANEL)

    state = power_ps.state_json or {}
    old_out = int(state.get("fusion_output", 0))
    max_out = int(state.get("max_output", 6))
    new_out = max(0, min(int(value), max_out))

    # compute immediate heat from ramp-up
    immediate_heat = heat_on_output_increase(old_out, new_out)

    state["fusion_output"] = new_out
    state.setdefault("max_output", max_out)
    state.setdefault("alloc", {"engineering": 0, "comms": 0, "biolab": 0, "life_support": 0})

    power_ps.state_json = state

    eng_state = eng_ps.state_json or {}
    eng_state["heat"] = int(eng_state.get("heat", 0)) + int(immediate_heat)
    eng_ps.state_json = eng_state

    patches = [
        panel_state_merge(POWER_PANEL, {"fusion_output": new_out, "max_output": max_out, "power_produced": power_produced(new_out)}),
    ]
    if immediate_heat:
        patches.append(panel_state_set(ENGINEERING_PANEL, "/heat", eng_state["heat"]))

    events = []
    if new_out != old_out:
        if new_out > old_out:
            msg = f"Fusion output increased to {new_out}. Heat spike +{immediate_heat}."
        else:
            msg = f"Fusion output decreased to {new_out}."
        _add_event(game_id, msg)
        events.append(event(msg))

    db.session.commit()
    return True, "", patches, events

def apply_allocate_power(*, game_id: int, system: str, delta: int):
    g = Game.query.get(game_id)
    if not g:
        return False, "Game not found", [], []

    system = str(system)
    if system not in {"engineering", "comms", "biolab", "life_support"}:
        return False, "Unknown system", [], []

    power_ps = _get_panel_state(game_id, POWER_PANEL)
    state = power_ps.state_json or {}
    out = int(state.get("fusion_output", 0))
    produced = power_produced(out)

    alloc = state.get("alloc") or {"engineering": 0, "comms": 0, "biolab": 0, "life_support": 0}
    for k in ["engineering", "comms", "biolab", "life_support"]:
        alloc.setdefault(k, 0)

    cur = int(alloc.get(system, 0))
    new_val = max(0, cur + int(delta))

    # Check capacity against produced
    new_alloc = dict(alloc)
    new_alloc[system] = new_val
    total = sum(int(v) for v in new_alloc.values())
    if total > produced:
        return False, "Insufficient power (over allocation)", [], []

    state["alloc"] = new_alloc
    power_ps.state_json = state

    patches = [panel_state_merge(POWER_PANEL, {"alloc": new_alloc, "power_produced": produced})]
    msg = f"Power allocation updated: {system} = {new_val} PU."
    _add_event(game_id, msg)
    events = [event(msg)]

    db.session.commit()
    return True, "", patches, events

def apply_tick_power(*, game_id: int):
    """Advances one 'tick' of reactor operation: adds heat based on current output."""
    g = Game.query.get(game_id)
    if not g:
        return False, "Game not found", [], []

    power_ps = _get_panel_state(game_id, POWER_PANEL)
    eng_ps = _get_panel_state(game_id, ENGINEERING_PANEL)

    out = int((power_ps.state_json or {}).get("fusion_output", 0))
    heat = heat_per_tick(out)

    eng_state = eng_ps.state_json or {}
    eng_state["heat"] = int(eng_state.get("heat", 0)) + int(heat)
    eng_ps.state_json = eng_state

    patches = [panel_state_set(ENGINEERING_PANEL, "/heat", eng_state["heat"])]
    msg = f"Reactor tick: output {out} → heat +{heat}."
    _add_event(game_id, msg)
    events = [event(msg)]

    db.session.commit()
    return True, "", patches, events
