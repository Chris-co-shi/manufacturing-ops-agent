import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.memory.models import MemoryEntry


class MemoryStore(ABC):
    """
    定义 MemoryStore 接口。
    提供 JsonFileMemoryStore 实现。
    未来可以替换成 Redis / SQLite / PostgreSQL / VectorDB。
    """

    @abstractmethod
    def save(self, entry: MemoryEntry) -> None:
        pass

    """
    根据session_id 查询列表
    """

    @abstractmethod
    def list_by_session(self, session_id: str, limit: int = 20) -> list[MemoryEntry]:
        pass


class JsonFileMemoryStore(MemoryStore):
    """
    基于 JSON 文件的存储实现
    """

    def __init__(self, file_path: str = "data/memory/session_memory.jsonl"):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, entry: MemoryEntry) -> None:
        with self.file_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry.__dict__, ensure_ascii=False) + "\n")

    def list_by_session(self, session_id: str, limit: int = 20) -> list[MemoryEntry]:
        if not self.file_path.exists():
            return []
        entries = []
        with self.file_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                data = json.loads(line)
                if data.get("session_id") == session_id:
                    entries.append(MemoryEntry(**data))
        return entries[-limit:]
