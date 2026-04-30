import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Any

MemoryType = Literal[
    "short_term_context",# 当前会话上下文，例如刚才分析的是哪个工单。
    "execution_trace", # 本次执行轨迹，例如 intent、tools_used、rag_sources、final_result。
    "historical_case", # 历史案例，例如 WO-001 曾经因为库存不足 + SAP 同步失败导致投料失败。
    "user_preference" # 用户偏好，例如希望输出结构为“原因分析 + 建议动作 + 风险提醒”。
]


@dataclass
class MemoryEntry:
    """
    定义 Memory 的数据结构。
    不负责读写。
    不负责业务判断。
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    session_id: str = "default"

    memory_type: MemoryType = "short_term_context"

    content: str = ""

    metadata: dict[str, Any] = field(default_factory=dict)

    created_at: str = field(default_factory=lambda : datetime.now().isoformat())
