from typing import Any

from langgraph.constants import START, END
from langgraph.graph import StateGraph

from app.agent.executor import ManufacturingOpsAgent
from app.agent.response_synthesizer import ResponseSynthesizer
from app.core.intent_router import IntentRouter
from app.agent.state import ManufacturingAgentState
from app.memory.manager import MemoryManager
from app.memory.store import JsonFileMemoryStore


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
        self.response_synthesizer = ResponseSynthesizer()
        self.memory_manager = MemoryManager(JsonFileMemoryStore())

    def run(
            self,
            user_input: str,
            session_id: str = "default",
    ) -> dict[str, Any] | Any:
        return self.graph.invoke(
            {
                "session_id": session_id,
                "user_input": user_input,
                "effective_user_input": user_input,
                "tools_used": [],
                "errors": [],
                "memory_context": [],
            }
        )

    def _build_graph(self):
        builder = StateGraph(ManufacturingAgentState)
        builder.add_node("load_memory", self.load_memory_node)
        builder.add_node("route_intent", self.route_intent_node)
        builder.add_node("query_work_order", self.query_work_order_node)
        builder.add_node("analyze_exception", self.analyze_exception_node)
        builder.add_node("unknown", self.unknown_node)
        builder.add_node("synthesize_response", self.synthesize_response_node)
        builder.add_node("save_memory", self.save_memory_node)

        builder.add_edge(START, "load_memory")
        builder.add_edge("load_memory", "route_intent")
        builder.add_conditional_edges(
            "route_intent",
            self.route_after_intent,
            {
                "work_order_query": "query_work_order",
                "work_order_exception_analysis": "analyze_exception",
                "unknown": "unknown",
            },
        )

        builder.add_edge("query_work_order", "synthesize_response")
        builder.add_edge("analyze_exception", "synthesize_response")
        builder.add_edge("unknown", "synthesize_response")
        builder.add_edge("synthesize_response", "save_memory")
        builder.add_edge("save_memory", END)
        return builder.compile()

    def route_intent_node(self, state: ManufacturingAgentState) -> dict:
        user_input = state.get("effective_user_input", state["user_input"])
        intent_result = self.intent_router.route(user_input)
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

    def query_work_order_node(self, state: ManufacturingAgentState) -> dict:
        user_input = state.get("effective_user_input", state["user_input"])
        result = self.executor.run(user_input)

        return {
            "result": result,
            "tools_used": result.get("tools_used", []),
            "answer": result.get("answer", ""),
        }

    def analyze_exception_node(self, state: ManufacturingAgentState) -> dict:
        user_input = state.get("effective_user_input", state["user_input"])

        result = self.executor.run(user_input)

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

    def load_memory_node(self, state: ManufacturingAgentState) -> dict:
        """
                执行前加载 Memory。

                职责：
                1. 根据 session_id 读取最近 Memory
                2. 写入 state["memory_context"]
                3. 对“继续分析刚才那个工单”这类输入做轻量上下文补全
        """
        session_id = state.get("session_id", "default")
        user_input = state.get("user_input")
        memories = self.memory_manager.get_recent_memory(session_id=session_id, limit=5)
        memory_context = [
            {
                "memory_type": m.memory_type,
                "content": m.content,
                "metadata": m.metadata,
                "created_at": m.created_at,
            }
            for m in memories
        ]
        effective_user_input = user_input
        last_order_id = self._find_last_order_id(memory_context)
        if last_order_id and self._need_context_completion(user_input):
            effective_user_input = f"{user_input} {last_order_id}"

        return {
            "memory_context": memory_context,
            "effective_user_input": effective_user_input,
        }

    def save_memory_node(self, state: ManufacturingAgentState) -> dict:
        """
                执行后保存 Memory。

                职责：
                1. 保存本次执行轨迹
                2. 保存最近一次工单上下文
                3. 不改变业务结果
        """
        print("[MEMORY DEBUG] enter save_memory_node")
        print("[MEMORY DEBUG] session_id:", state.get("session_id"))
        print("[MEMORY DEBUG] order_id:", state.get("order_id"))
        print("[MEMORY DEBUG] result keys:", list((state.get("result") or {}).keys()))

        session_id = state.get("session_id", "default")
        result = state.get("result") or {}
        order_id = (
                state.get("order_id")
                or result.get("order_id")
                or self._extract_order_id_from_result(result)
        )
        self.memory_manager.remember_execution_trace(
            session_id=session_id,
            content="Agent execution completed",
            metadata={
                "user_input": state.get("user_input"),
                "effective_user_input": state.get("effective_user_input"),
                "intent": state.get("intent"),
                "order_id": order_id,
                "confidence": state.get("confidence"),
                "reason": state.get("reason"),
                "tools_used": state.get("tools_used", []),
                "answer": state.get("answer", ""),
            }
        )
        if order_id:
            self.memory_manager.remember_context(
                session_id=session_id,
                content=f"最近处理的工单是 {order_id}",
                metadata={
                    "last_order_id": order_id,
                    "intent": state.get("intent"),
                },
            )
        return {}

    def _need_context_completion(self, user_input) -> bool:
        return any(
            keyword in user_input
            for keyword in ["继续", "刚才", "上一个", "上一条", "这个工单", "那个工单"]
        )

    def _find_last_order_id(self, memory_context: list[dict[str, Any]]) -> str | None:
        for memory in reversed(memory_context):
            metadata = memory.get("metadata", {})
            last_order_id = metadata.get("last_order_id")
            if last_order_id:
                return last_order_id

            order_id = metadata.get("order_id")
            if order_id:
                return order_id

        return None

    def _extract_order_id_from_result(self, result):
        work_order = result.get("work_order")

        if isinstance(work_order, dict):
            return work_order.get("order_id")

        return None

    def synthesize_response_node(self, state: ManufacturingAgentState) -> ManufacturingAgentState:
        prompt = self.response_synthesizer.build_prompt(state)
        final_answer = self.response_synthesizer.synthesize(state)

        trace = state.get("execution_trace", [])
        trace.append(
            {
                "step": "synthesize_response",
                "description": "Generated structured business analysis response",
            }
        )

        return {
            **state,
            "prompt": prompt,
            "final_answer": final_answer,
            "execution_trace": trace,
        }
