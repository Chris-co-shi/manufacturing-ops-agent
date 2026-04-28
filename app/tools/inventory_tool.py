import json
from pathlib import Path

from app.utils.json_utils import JsonUtils


def get_inventory(material_code: str):
    data = JsonUtils(base_url="data", file_name="inventory.json").load_json()
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
