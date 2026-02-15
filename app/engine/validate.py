from .schemas import load_scenario, get_panel_schema

def validate_move(*, scenario_id: str, panel: str, zone: str, entity_type: str) -> tuple[bool, str]:
    scenario = load_scenario(scenario_id)
    panel_schema = get_panel_schema(scenario, panel)
    zones = panel_schema.get("zones", {})
    z = zones.get(zone)
    if not z:
        return False, "Unknown zone"
    accepts = z.get("accepts", [])
    if accepts and entity_type not in accepts:
        return False, "Not accepted in this zone"
    return True, ""
