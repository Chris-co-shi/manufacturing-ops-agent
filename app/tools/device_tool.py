from app.utils.json_utils import JsonUtils


def get_device_status(device_id: str):
    data = JsonUtils(base_url="data", file_name="devices.json").load_json()
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
#
# if __name__ == '__main__':
#     get_device_status("DEV-MIX-0023")
