from typing import Any

from mypy_extensions import TypedDict


class ManufacturingAgentState(TypedDict, total=False):
    """
        Agent Graph 运行时共享状态。
        它不是业务实体，而是一次 Agent 执行过程中的上下文载体。
        """

    # 会话标识，用于隔离不同用户/不同会话的 Memory
    session_id: str

    # 用户原始输入
    user_input: str

    # 经过 Memory 补全后的输入
    # 例如：用户输入“继续分析刚才那个工单”
    # Memory 可以补全为“继续分析刚才那个工单 WO-001”
    effective_user_input: str

    # Memory 上下文
    memory_context: list[dict[str, Any]]

    # 意图识别结果
    intent: str
    order_id: str | None
    confidence: float
    reason: str

    # 执行结果
    result: dict[str, Any] | None
    tools_used: list[str]
    answer: str

    # 错误信息
    errors: list[str]
