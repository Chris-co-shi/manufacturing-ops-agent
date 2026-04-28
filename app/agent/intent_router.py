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


class IntentRouter:
    """
    意图路由
    判断用户意图
    """
    def router(self, user_input: str) -> IntentResult:
        order_id = self._extract_order_id(user_input)
        if order_id and self._con

    def _extract_order_id(self, user_input):
        pass