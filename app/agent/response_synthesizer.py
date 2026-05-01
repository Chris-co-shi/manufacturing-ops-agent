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

        return f"""
# 工单异常分析报告

## 1. 异常摘要
用户请求分析工单异常：{state.get("user_input", "")}

## 2. 意图识别
- Intent: {state.get("intent")}
- Confidence: {state.get("confidence")}
- Reason: {state.get("reason")}

## 3. 可能原因
- 物料库存或投料状态异常
- SAP 同步可能存在失败或延迟
- 设备状态可能影响当前工单执行
- 质量检测结果可能影响后续流转

## 4. 证据链
### 工具结果
{tool_results}

### RAG 知识上下文
{rag_context}

### 执行轨迹
{execution_trace}

## 5. 建议动作
1. 先确认工单当前状态和物料批次状态。
2. 检查 SAP 同步记录是否存在失败、超时或重复提交。
3. 查看设备状态是否存在报警、停机或参数异常。
4. 如果涉及库存扣减，需要确认是否存在并发扣减或回滚失败。
5. 将本次异常沉淀为案例，后续用于相似问题匹配。

## 6. 风险等级
MEDIUM

## 7. 需要人工确认的信息
- 实际投料批次
- SAP 接口返回码
- 设备报警明细
- 库存扣减流水
- 是否已经人工干预

## 8. 后续追踪项
- 记录本次异常处理结果
- 补充异常案例库
- 优化相似异常检索规则
"""

    def _synthesize_default(self, state: dict[str, Any]) -> str:
        return f"""
# Agent 执行结果

## 用户输入
{state.get("user_input", "")}

## 执行状态
{state}
"""
