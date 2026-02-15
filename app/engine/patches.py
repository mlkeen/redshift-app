def entity_moved(entity_id: int, location: dict, new_version: int) -> dict:
    return {"op": "entity_moved", "entity_id": entity_id, "location": location, "new_version": new_version}

def panel_state_set(panel: str, path: str, value) -> dict:
    return {"op": "panel_state_set", "panel": panel, "path": path, "value": value}

def event(msg: str, visibility: str = "public") -> dict:
    return {"visibility": visibility, "msg": msg}


def panel_state_merge(panel: str, value: dict) -> dict:
    return {"op": "panel_state_merge", "panel": panel, "value": value}
