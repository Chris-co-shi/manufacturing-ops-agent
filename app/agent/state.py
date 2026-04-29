from typing import Any

from mypy_extensions import TypedDict


class ManufacturingAgentState(TypedDict, total=False):
    """
    定义整张图流转时共享的数据结构。 可以理解成AgentExecutionContext 执行器的上下文
    """
    # 用户输入
    user_input: str

    # 意图
    intent: str

    # 工单ID
    order_id: str | None

    # 置信度
    confidence: float

    # 原因
    reason: str = ""

    # 工具使用
    tools_used: list[str]

    # 错误
    errors: list[str]

    # 工单信息
    # work_order: dict[str, Any] | None
    #
    # # 库存信息
    # inventory: dict[str, Any] | None
    #
    # # 设备信息
    # device: dict[str, Any] | None
    #
    # quality_result: dict[str, Any] | None
    #
    # sap_sync: dict[str, Any] | None
    #
    # action_plan: dict[str, Any] | None
    #
    # retriever: list[dict[str, Any]]

    result: dict[str, Any] | None

    answer: str
