from app.utils.json_utils import JsonUtils


def get_sap_sync_status(material_code: str):
    data = JsonUtils(base_url="data", file_name="sap_sync.json").load_json()
    result = data.get(material_code)

    if result is None:
        return {
            "found": False,
            "messages": f"未找到 SAP 同步状态: {material_code}",
        }

    return {
        "found": True,
        "data": result,
    }
