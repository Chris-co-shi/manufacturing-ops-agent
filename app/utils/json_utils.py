import json
from pathlib import Path
from typing import Any

# 数据文件路径，现在是写死的 后面应该动态传入
DATA_PATH = Path(__file__).resolve().parents[2]


class JsonUtils:
    """
    JSON 工具类
    """

    def __init__(self, base_url: str, file_name: str, json_str: str = None, encoding: str = "utf-8"):
        self.json_str = json_str
        self.encoding = encoding
        self.file_path = DATA_PATH / base_url / file_name

    def load_json(self) -> Any:
        if not self.file_path.exists():
            raise FileNotFoundError(f"文件不存在: {self.file_path}")

        if not self.file_path.is_file():
            raise ValueError(f"路径不是有效文件: {self.file_path}")

        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
