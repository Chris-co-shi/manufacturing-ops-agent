from app.memory.models import MemoryEntry
from app.memory.store import MemoryStore


class MemoryManager:
    def __init__(self, memory_store: MemoryStore):
        self.store = memory_store

    def remember_context(
            self,
            session_id: str,
            content: str,
            metadata: dict | None = None,
    ) -> None:
        self.store.save(
            MemoryEntry(
                session_id=session_id,
                memory_type="short_term_context",
                content=content,
                metadata=metadata or {},
            )
        )

    def remember_execution_trace(
            self,
            session_id: str,
            content: str,
            metadata: dict | None = None,
    ) -> None:
        self.store.save(
            MemoryEntry(
                session_id=session_id,
                memory_type="execution_trace",
                content=content,
                metadata=metadata or {},
            )
        )

    def get_recent_memory(self, session_id: str, limit: int = 5) -> list[MemoryEntry]:
        return self.store.list_by_session(session_id=session_id, limit=limit)
