import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "work_orders.json"


def get_work_orders(order_id: str):
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    order = data.get(order_id)
    if order is None:
        return {
            "found": False,
            "messages": f"工单不存在: {order_id}"
        }
    return {
        "found": True,
        "data": order
    }
