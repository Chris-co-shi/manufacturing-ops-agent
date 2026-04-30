from typing import  Any

from langgraph.constants import START, END
from langgraph.graph import StateGraph

from app.agent.executor import ManufacturingOpsAgent
from app.core.intent_router import IntentRouter
from app.agent.state import ManufacturingAgentState

class ManufacturingOpsGraph:
    """
    目标：
    - Graph 只负责流程编排
    - 业务执行继续复用 ManufacturingOpsAgent
    - 避免把 graph.py 写成第二个 executor.py
    """

    def __init__(self):
        # 路由初始化
        self.intent_router = IntentRouter()
        # 初始化执行器
        self.executor = ManufacturingOpsAgent()
        # 工具注册
        # 图初始化
        self.graph = self._build_graph()

    def run(self, user_input: str) -> dict[str, Any] | Any:
        return self.graph.invoke(
            {
                "user_input": user_input,
                "tools_used": [],
            }
        )

    def _build_graph(self):
        builder = StateGraph(ManufacturingAgentState)

        builder.add_node("route_intent", self.route_intent_node)
        builder.add_node("query_work_order", self.query_work_order_node)
        builder.add_node("analyze_exception", self.analyze_exception_node)
        builder.add_node("unknown", self.unknown_node)

        builder.add_edge(START, "route_intent")

        builder.add_conditional_edges(
            "route_intent",
            self.route_after_intent,
            {
                "work_order_query": "query_work_order",
                "work_order_exception_analysis": "analyze_exception",
                "unknown": "unknown",
            },
        )

        builder.add_edge("query_work_order", END)
        builder.add_edge("analyze_exception", END)
        builder.add_edge("unknown", END)

        return builder.compile()

    def route_intent_node(self, state: ManufacturingAgentState) -> dict:
        intent_result = self.intent_router.route(state["user_input"])

        return {
            "intent": intent_result.intent,
            "order_id": intent_result.order_id,
            "confidence": intent_result.confidence,
            "reason": intent_result.reason,
        }
    def route_after_intent(self, state):
        intent = state.get("intent")

        if intent == "work_order_query":
            return "work_order_query"

        if intent == "work_order_exception_analysis":
            return "work_order_exception_analysis"

        return "unknown"
    def intent_router_node(self, state: ManufacturingAgentState):
        intent_result = self.intent_router.route(state["user_input"])
        return {
            "intent": intent_result.intent,
            "order_id": intent_result.order_id,
            "confidence": intent_result.confidence,
            "reason": intent_result.reason,
        }

    def query_work_order_node(self, state: ManufacturingAgentState) -> dict:
        result = self.executor.run(state['user_input'])

        return {
            "result": result,
            "tools_used": result.get("tools_used", []),
            "answer": result.get("answer", ""),
        }

    def analyze_exception_node(self, state: ManufacturingAgentState) -> dict:
        result = self.executor.run(state["user_input"])

        return {
            "result": result,
            "tools_used": result.get("tools_used", []),
            "answer": result.get("answer", ""),
        }

    def unknown_node(
            self,
            state: ManufacturingAgentState,
    ) -> dict:
        return {
            "tools_used": [],
            "answer": "当前只支持工单查询和工单异常分析。请使用类似：查询工单 WO-001 的状态。",
        }
