from app.utils.json_utils import JsonUtils


def get_work_order(order_id: str):
    data = JsonUtils(base_url="data", file_name="work_orders.json").load_json()
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
