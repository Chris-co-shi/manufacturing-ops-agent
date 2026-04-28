from app.utils.json_utils import JsonUtils


def get_quality_result(order_id: str):
    data = JsonUtils(base_url="data", file_name="quality_results.json").load_json()

    result = data.get(order_id)

    if result is None:
        return {
            "found": False,
            "message": f"未找到工单质检结果: {order_id}",
        }

    return {
        "found": True,
        "data": result,
    }
