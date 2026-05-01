from app.agent.state import ManufacturingAgentState
from app.prompts.templates import WORK_ORDER_EXCEPTION_ANALYSIS_TEMPLATE


class PromptBuilder:
    """
    Prompt 构建器。

    职责：
    - 将 AgentState 中的结构化上下文转成 Prompt 输入
    - 屏蔽 prompt 模板细节
    - 为未来多意图、多模板、多语言输出保留扩展点

    不负责：
    - 不做意图识别
    - 不调用工具
    - 不调用 LLM
    - 不生成最终业务报告
    """

    def build(self, state: ManufacturingAgentState):
        intent = state.get("intent", "")

        if intent == "work_order_exception_analysis":
            return self._build_work_order_exception_prompt(state)
        return self._build_default_prompt(state)

    def _build_work_order_exception_prompt(self, state: ManufacturingAgentState):
        return WORK_ORDER_EXCEPTION_ANALYSIS_TEMPLATE.format(
            user_input=state.get("user_input", ""),
            intent=state.get("intent", ""),
            confidence=state.get("confidence", ""),
            reason=state.get("reason", ""),
            rag_context=state.get("rag_context", []),
            tool_results=state.get("tool_results", {}),
            memory_context=state.get("memory_context", {}),
        )

    def _build_default_prompt(self, state: ManufacturingAgentState) -> str:
        return f"""
            你是一个制造业运营 Agent。

    请基于以下上下文生成简要分析：

    用户输入：
    {state.get("user_input", "")}

    上下文：
    {state}
    """
