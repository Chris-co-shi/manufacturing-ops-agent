import re
from dataclasses import dataclass


@dataclass
class IntentResult:
    """
    意图路由
    """
    intent: str
    order_id: str | None = None
    confidence: float = 0.0
    reason: str = ""


# 提取工单ID
def _extract_order_id(user_input):
    match = re.search(r"WO-\d+", user_input)
    if match:
        return match.group(0)
    return None


# 判断文本中是否包含关键词
def _contains_any(text: str, keywords: list[str]):
    return any(keyword in text for keyword in keywords)


class IntentRouter:
    """
    意图路由
    判断用户意图

    流程：
    """

    def route(self, user_input: str) -> IntentResult:
        order_id = _extract_order_id(user_input)
        if order_id and _contains_any(
                user_input,
                ["异常", "失败", "投料", "扣减", "分析", "原因", "处理", "处置"]
        ):
            return IntentResult(
                intent="work_order_exception_analysis",
                order_id=order_id,
                confidence=0.95,
                reason="包含工单ID和异常关键词"
            )
        if order_id:
            return IntentResult(
                intent="work_order_query",
                order_id=order_id,
                confidence=0.85,
                reason="包含工单ID"
            )
        return IntentResult(
            intent="unknown",
            confidence=0.1,
            reason="未识别到明确工单号或支持的业务意图"
        )