import json
from pathlib import Path

SEED_DIR = Path(__file__).resolve().parents[1] / "seed"

def load_scenario(scenario_id: str) -> dict:
    path = SEED_DIR / f"{scenario_id}.json"
    return json.loads(path.read_text(encoding="utf-8"))

def get_panel_schema(scenario: dict, panel_key: str) -> dict:
    return scenario["panels"][panel_key]
