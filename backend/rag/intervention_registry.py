from pathlib import Path
import json

M1_PATH = Path("kb/interventions/M1_micro_interventions.json")


def load_micro_interventions() -> list[dict]:
    if not M1_PATH.exists():
        return []

    try:
        data = json.loads(M1_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def registry_summary() -> dict:
    items = load_micro_interventions()
    return {
        "count": len(items),
        "ids": [x.get("id") for x in items if x.get("id")],
    }
