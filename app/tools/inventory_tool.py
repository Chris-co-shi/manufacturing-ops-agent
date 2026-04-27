import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "inventory.json"


def get_inventory(material_code: str):
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    inventory = data.get(material_code)

    if inventory is None:
        return {
            "found": False,
            "messages": f"库存不存在: {material_code}"
        }

    return {
        "found": True,
        "data": inventory
    }
