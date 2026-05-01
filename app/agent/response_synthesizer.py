from typing import Any

from app.prompts.builder import PromptBuilder


class ResponseSynthesizer:
    """
    响应合成器。

    职责：
    - 读取 state 中的 intent / rag_context / tool_results / memory_context
    - 生成统一结构的业务分析结果
    - 为未来接入 LLM 生成报告保留边界

    不负责：
    - 不做 IntentRouter
    - 不调用 tools
    - 不检索 RAG
    - 不写入 Memory
    """

    def __init__(self, prompt_builder: PromptBuilder | None = None) -> None:
        self.prompt_builder = prompt_builder or PromptBuilder()

    def synthesize(self, state: dict[str, Any]) -> str:
        intent = state.get("intent")

        if intent == "work_order_exception_analysis":
            return self._synthesize_work_order_exception(state)

        if intent == "work_order_query":
            return self._synthesize_work_order_query(state)

        return self._synthesize_default(state)

    def build_prompt(self, state: dict[str, Any]) -> str:
        """
        当前阶段只构建 prompt，不真实调用 LLM。
        后续可以在这里接入 LLMClient。
        """
        return self.prompt_builder.build(state)

    def _synthesize_work_order_exception(self, state: dict[str, Any]) -> str:
        tool_results = state.get("tool_results", {})
        rag_context = state.get("rag_context", [])
        execution_trace = state.get("execution_trace", [])

        work_order = tool_results.get("work_order") or {}
        inventory = tool_results.get("inventory") or {}
        device = tool_results.get("device") or {}
        quality_result = tool_results.get("quality_result") or {}
        sap_sync = tool_results.get("sap_sync") or {}
        action_plan = tool_results.get("action_plan") or {}

        return f"""
# 工单异常分析报告

## 1. 异常摘要
用户请求分析工单异常：{state.get("effective_user_input") or state.get("user_input", "")}

- 工单号：{work_order.get("order_id", state.get("order_id", "未知"))}
- 工单状态：{work_order.get("status", "未知")}
- 当前异常：{work_order.get("current_issue", "未知")}
- 优先级：{work_order.get("priority", "未知")}

## 2. 意图识别
- Intent: {state.get("intent")}
- Confidence: {state.get("confidence")}
- Reason: {state.get("reason")}

## 3. 可能原因
{self._build_possible_causes(inventory, device, quality_result, sap_sync)}

## 4. 证据链

### 4.1 工单信息
{self._format_work_order(work_order)}

### 4.2 库存信息
{self._format_inventory(inventory)}

### 4.3 设备信息
{self._format_device(device)}

### 4.4 SAP 同步信息
{self._format_sap_sync(sap_sync)}

### 4.5 质检信息
{self._format_quality_result(quality_result)}

### 4.6 RAG 知识上下文
{self._format_rag_context(rag_context)}

### 4.7 执行轨迹
{self._format_execution_trace(execution_trace)}

## 5. 建议动作
{self._format_action_plan(action_plan)}

## 6. 风险等级
{self._resolve_risk_level(work_order, quality_result, sap_sync, device)}

## 7. 需要人工确认的信息
- 实际投料批次
- SAP 接口返回码和补偿状态
- 设备报警明细
- 库存扣减流水
- 现场物料状态
- 是否已经人工干预

## 8. 后续追踪项
- 记录本次异常处理结果
- 补充异常案例库
- 优化相似异常检索规则
- 将 SAP 同步失败、设备报警、库存扣减异常纳入统一追踪
""".strip()

    def _synthesize_work_order_query(self, state: dict[str, Any]) -> str:
        tool_results = state.get("tool_results", {})
        work_order = tool_results.get("work_order") or {}

        if not work_order:
            return state.get("answer", "未查询到工单信息。")

        return f"""
# 工单查询结果

## 工单信息
{self._format_work_order(work_order)}

## 执行轨迹
{self._format_execution_trace(state.get("execution_trace", []))}
""".strip()

    def _synthesize_default(self, state: dict[str, Any]) -> str:
        return f"""
# Agent 执行结果

## 用户输入
{state.get("effective_user_input") or state.get("user_input", "")}

## 执行状态
- Intent: {state.get("intent")}
- Confidence: {state.get("confidence")}
- Reason: {state.get("reason")}

## 回答
{state.get("answer", "")}
""".strip()

    def _build_possible_causes(
            self,
            inventory: dict[str, Any],
            device: dict[str, Any],
            quality_result: dict[str, Any],
            sap_sync: dict[str, Any],
    ) -> str:
        causes: list[str] = []

        if inventory and inventory.get("last_sync_status") == "FAILED":
            causes.append("- 库存最近同步失败，可能存在系统库存与现场库存不一致。")

        if sap_sync and sap_sync.get("sync_status") == "FAILED":
            causes.append("- SAP 同步失败，库存扣减链路存在一致性风险。")

        if sap_sync and sap_sync.get("need_compensation"):
            causes.append("- SAP 同步失败后需要补偿，可能存在本地与外部系统状态不一致。")

        if device and device.get("status") != "NORMAL":
            causes.append("- 设备状态异常，可能影响工单继续执行。")

        if device and not device.get("can_continue", True):
            causes.append("- 设备当前不允许继续生产，需要现场确认后才能恢复。")

        if quality_result and quality_result.get("inspection_status") == "PENDING":
            causes.append("- 质检结果尚未完成，恢复生产前存在质量确认风险。")

        if not causes:
            causes.append("- 当前工具结果未发现明确异常，需要人工进一步确认现场状态。")

        return "\n".join(causes)

    def _format_work_order(self, work_order: dict[str, Any]) -> str:
        if not work_order:
            return "- 无工单信息。"

        return "\n".join(
            [
                f"- 工单号：{work_order.get('order_id', '未知')}",
                f"- 状态：{work_order.get('status', '未知')}",
                f"- 物料编码：{work_order.get('material_code', '未知')}",
                f"- 设备编号：{work_order.get('device_id', '未知')}",
                f"- 当前异常：{work_order.get('current_issue', '未知')}",
                f"- 优先级：{work_order.get('priority', '未知')}",
            ]
        )

    def _format_inventory(self, inventory: dict[str, Any]) -> str:
        if not inventory:
            return "- 无库存信息。"

        return "\n".join(
            [
                f"- 物料编码：{inventory.get('material_code', '未知')}",
                f"- 物料名称：{inventory.get('material_name', '未知')}",
                f"- 总库存：{inventory.get('total_qty', '未知')} {inventory.get('unit', '')}",
                f"- 可用库存：{inventory.get('available_qty', '未知')} {inventory.get('unit', '')}",
                f"- 冻结库存：{inventory.get('frozen_qty', '未知')} {inventory.get('unit', '')}",
                f"- 最近同步状态：{inventory.get('last_sync_status', '未知')}",
            ]
        )

    def _format_device(self, device: dict[str, Any]) -> str:
        if not device:
            return "- 无设备信息。"

        return "\n".join(
            [
                f"- 设备编号：{device.get('device_id', '未知')}",
                f"- 设备名称：{device.get('device_name', '未知')}",
                f"- 状态：{device.get('status', '未知')}",
                f"- 最近报警：{device.get('last_alarm', '无')}",
                f"- 是否允许继续生产：{device.get('can_continue', '未知')}",
            ]
        )

    def _format_sap_sync(self, sap_sync: dict[str, Any]) -> str:
        if not sap_sync:
            return "- 无 SAP 同步信息。"

        return "\n".join(
            [
                f"- 同步状态：{sap_sync.get('sync_status', '未知')}",
                f"- 最近同步时间：{sap_sync.get('last_sync_time', '未知')}",
                f"- 错误信息：{sap_sync.get('error_message', '无')}",
                f"- 重试次数：{sap_sync.get('retry_count', '未知')}",
                f"- 是否需要补偿：{sap_sync.get('need_compensation', '未知')}",
            ]
        )

    def _format_quality_result(self, quality_result: dict[str, Any]) -> str:
        if not quality_result:
            return "- 无质检信息。"

        return "\n".join(
            [
                f"- 质检状态：{quality_result.get('inspection_status', '未知')}",
                f"- 最近结果：{quality_result.get('latest_result', '未知')}",
                f"- 质量风险等级：{quality_result.get('risk_level', '未知')}",
                f"- 备注：{quality_result.get('remark', '无')}",
            ]
        )

    def _format_action_plan(self, action_plan: dict[str, Any]) -> str:
        actions = action_plan.get("actions", [])

        if not actions:
            return "1. 暂无自动生成的处置建议，需要人工确认。"

        return "\n".join(
            f"{index}. {action}"
            for index, action in enumerate(actions, start=1)
        )

    def _format_rag_context(self, rag_context: list[dict[str, Any]]) -> str:
        if not rag_context:
            return "- 当前没有结构化 RAG 上下文。"

        lines: list[str] = []

        for index, item in enumerate(rag_context, start=1):
            source = item.get("source", "unknown")
            score = item.get("score", "unknown")
            content = item.get("content", "")

            if len(content) > 120:
                content = content[:120] + "..."

            lines.append(
                f"{index}. 来源：{source}，匹配分数：{score}\n   摘要：{content}"
            )

        return "\n".join(lines)

    def _format_execution_trace(self, execution_trace: list[dict[str, Any]]) -> str:
        if not execution_trace:
            return "- 无执行轨迹。"

        lines: list[str] = []

        for index, item in enumerate(execution_trace, start=1):
            step = item.get("step", "unknown")
            detail = {
                key: value
                for key, value in item.items()
                if key != "step"
            }

            lines.append(f"{index}. {step}：{detail}")

        return "\n".join(lines)

    def _resolve_risk_level(
            self,
            work_order: dict[str, Any],
            quality_result: dict[str, Any],
            sap_sync: dict[str, Any],
            device: dict[str, Any],
    ) -> str:
        if work_order.get("priority") == "HIGH":
            return "HIGH"

        if sap_sync.get("sync_status") == "FAILED":
            return "HIGH"

        if device and not device.get("can_continue", True):
            return "HIGH"

        if quality_result.get("risk_level"):
            return quality_result["risk_level"]

        return "MEDIUM"