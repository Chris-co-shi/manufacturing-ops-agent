import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "devices.json"


def get_device_status(device_id: str):
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    device = data.get(device_id)

    if device is None:
        return {
            "found": False,
            "messages": f"设备不存在: {device_id}"
        }

    return {
        "found": True,
        "data": device
    }
