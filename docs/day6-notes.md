# Day 6：Prompt Layer + Response Synthesizer

## 1. 今日目标

Day 6 的目标不是继续增加工具，也不是接入真实数据库，而是引入 Agent 的结果表达层。

在 Day 1 到 Day 5 中，Manufacturing Ops Agent 已经具备了以下能力：

- Day 1：最小工具调用闭环
- Day 2：IntentRouter + ToolRegistry
- Day 3：RAG 知识检索闭环
- Day 4：LangGraph 状态编排
- Day 5：Memory Layer

但是这些能力主要解决的是“能不能执行”的问题。

Day 6 要解决的是：

> Agent 执行完以后，如何把工具结果、Memory 上下文、RAG 上下文、执行轨迹组织成可解释、可复盘、可测试的业务报告。

因此 Day 6 引入：

- Prompt Layer
- PromptBuilder
- ResponseSynthesizer
- `final_answer`
- 全链路 `execution_trace`
- 更清晰的 State 字段协议

最终目标是让 Agent 从：

```text
意图识别
  ↓
工具调用
  ↓
结果打印
```

升级为：

```text
用户输入
  ↓
load_memory
  ↓
route_intent
  ↓
query_work_order / analyze_exception / unknown
  ↓
synthesize_response
  ↓
save_memory
  ↓
final_answer
```

---

## 2. Day 6 在整体架构中的位置

Day 6 新增的核心目录为：

```text
app/
  prompts/
    __init__.py
    templates.py
    builder.py

  agent/
    response_synthesizer.py
```

项目当前整体分层为：

```text
app/
  core/
    intent_router.py
    tool_registry.py

  tools/
    manufacturing_tools.py

  rag/
    retriever.py
    documents/

  memory/
    models.py
    store.py
    manager.py

  prompts/
    templates.py
    builder.py

  agent/
    executor.py
    graph.py
    response_synthesizer.py
    state.py
```

各层职责如下：

| 层 | 职责 |
|---|---|
| `core` | Agent 核心基础设施，例如 IntentRouter、ToolRegistry |
| `tools` | 制造业业务工具，例如工单、库存、设备、SAP、质检查询 |
| `rag` | 知识检索能力 |
| `memory` | 上下文、执行轨迹、历史记忆管理 |
| `prompts` | Prompt 模板与 Prompt 构造 |
| `agent` | Agent 执行器、Graph 编排、响应合成、状态定义 |

---

## 3. 为什么需要 Prompt Layer

在没有 Prompt Layer 之前，Agent 很容易把 prompt 写散：

- 写在 executor 中
- 写在 graph 中
- 写在具体工具中
- 写在 main.py 中

这样会带来几个问题：

1. Prompt 和业务执行逻辑耦合。
2. 不同 intent 的 prompt 不好管理。
3. 后续接入 LLM 时上下文组织不可控。
4. Prompt 版本无法治理。
5. 输出格式难以稳定。
6. 很难测试“Prompt 输入是否正确”。

因此 Day 6 把 Prompt 独立成一层。

Prompt Layer 的职责是：

- 管理 Prompt 模板。
- 根据 AgentState 构造 Prompt 输入。
- 屏蔽模板细节。
- 为未来多意图、多语言、多报告模板、多 LLM 接入保留扩展点。

Prompt Layer 不负责：

- 不做意图识别。
- 不调用工具。
- 不执行 RAG。
- 不写 Memory。
- 不直接生成最终业务报告。

---

## 4. 为什么需要 ResponseSynthesizer

Executor 的职责是业务执行，例如：

- 查询工单。
- 查询库存。
- 查询设备状态。
- 查询 SAP 同步状态。
- 查询质检结果。
- 生成动作建议。

但是 Executor 不应该负责最终报告表达。

如果把最终报告生成逻辑放进 Executor，会导致：

- Executor 同时承担“业务执行”和“结果表达”两类职责。
- 输出格式和业务执行强耦合。
- 后续切换规则输出 / LLM 输出 / JSON 输出会很困难。
- Graph 无法清楚区分“执行阶段”和“表达阶段”。
- 后续多 intent、多报告模板扩展会变复杂。

因此新增 ResponseSynthesizer。

ResponseSynthesizer 的职责是：

- 读取 AgentState 中的结构化上下文。
- 汇总工具结果、Memory、RAG、执行轨迹。
- 生成最终 `final_answer`。
- 统一输出结构。
- 为未来接入 LLM / JSON Schema / 报告模板保留边界。

ResponseSynthesizer 不负责：

- 不做 IntentRouter。
- 不调用 Tools。
- 不执行 RAG 检索。
- 不写入 Memory。
- 不控制 Graph 流程。

---

## 5. Graph 编排调整

Day 6 后，Graph 主流程调整为：

```text
START
  ↓
load_memory
  ↓
route_intent
  ↓
query_work_order / analyze_exception / unknown
  ↓
synthesize_response
  ↓
save_memory
  ↓
END
```

新增节点：

```text
synthesize_response
```

`synthesize_response` 节点负责：

- 基于当前 state 构造 prompt。
- 调用 ResponseSynthesizer 生成 `final_answer`。
- 记录 `synthesize_response` 执行轨迹。
- 不调用任何业务工具。
- 不改变工具原始执行结果。
- 不直接写 Memory。

这保证了：

```text
Graph 只负责编排
Executor 只负责执行
PromptBuilder 只负责 prompt 构造
ResponseSynthesizer 只负责最终表达
MemoryManager 只负责记忆读写
```

---

## 6. State 字段协议

Day 6 对 `ManufacturingAgentState` 做了字段协议收敛。

核心字段如下：

```python
from typing import Any, TypedDict


class ManufacturingAgentState(TypedDict, total=False):
    session_id: str

    user_input: str
    effective_user_input: str

    memory_context: list[dict[str, Any]]

    intent: str
    order_id: str | None
    confidence: float
    reason: str

    result: dict[str, Any] | None
    tool_results: dict[str, Any]
    rag_context: list[dict[str, Any]]

    tools_used: list[str]
    execution_trace: list[dict[str, Any]]

    answer: str
    prompt: str
    final_answer: str

    errors: list[str]
```

字段职责：

| 字段 | 含义 |
|---|---|
| `session_id` | 当前会话标识，用于 Memory 隔离 |
| `user_input` | 用户原始输入 |
| `effective_user_input` | 经过 Memory 补全后的实际输入 |
| `memory_context` | Memory 加载的上下文 |
| `intent` | IntentRouter 识别出的意图 |
| `order_id` | 从输入或上下文中识别出的工单号 |
| `confidence` | 意图识别置信度 |
| `reason` | 意图识别原因 |
| `result` | Executor 原始返回结果 |
| `tool_results` | 给 PromptBuilder / ResponseSynthesizer 使用的结构化工具上下文 |
| `rag_context` | RAG 结构化上下文 |
| `tools_used` | 本次执行调用过的工具列表 |
| `execution_trace` | Graph 全链路执行轨迹 |
| `answer` | Executor 原始回答 |
| `prompt` | PromptBuilder 生成的 prompt |
| `final_answer` | ResponseSynthesizer 生成的最终回答 |
| `errors` | 执行过程中的错误信息 |

其中最重要的职责区分是：

| 字段 | 定位 |
|---|---|
| `result` | 原始执行结果 |
| `tool_results` | 结构化工具上下文 |
| `answer` | Executor 原始文本回答 |
| `final_answer` | 最终对用户展示的结构化报告 |

---

## 7. 当前实现

### 7.1 PromptBuilder

PromptBuilder 负责根据 state 构造 prompt。

当前支持：

- `work_order_exception_analysis`
- default prompt

当前阶段只构造 prompt，不真实调用 LLM。

保留 `build_prompt()` 的意义是：

- 未来可以接入 LLMClient。
- 未来可以做 prompt 版本管理。
- 未来可以根据不同 intent 选择不同模板。
- 未来可以支持 JSON Schema 输出。
- 未来可以支持中英文或多语言报告模板。

PromptBuilder 不直接参与工具调用，也不生成最终业务结论。

---

### 7.2 ResponseSynthesizer

ResponseSynthesizer 当前采用规则式生成，不直接调用 LLM。

它读取：

- `intent`
- `tool_results`
- `rag_context`
- `memory_context`
- `execution_trace`

并输出结构化报告：

```text
1. 异常摘要
2. 意图识别
3. 可能原因
4. 证据链
5. 建议动作
6. 风险等级
7. 需要人工确认的信息
8. 后续追踪项
```

当前采用规则式生成是有意设计：

- 先保证结构化输出可控。
- 先稳定 Agent 架构边界。
- 先让测试结果可预测。
- 后续再替换为 LLM 生成。
- 避免早期把 Prompt、LLM、业务规则混在一起。

---

## 8. Day 6 输出报告结构

当前异常分析报告结构如下：

```text
# 工单异常分析报告

## 1. 异常摘要

## 2. 意图识别

## 3. 可能原因

## 4. 证据链
### 4.1 工单信息
### 4.2 库存信息
### 4.3 设备信息
### 4.4 SAP 同步信息
### 4.5 质检信息
### 4.6 RAG 知识上下文
### 4.7 执行轨迹

## 5. 建议动作

## 6. 风险等级

## 7. 需要人工确认的信息

## 8. 后续追踪项
```

相比 Day 5 之前的输出，Day 6 的提升是：

- 不再简单打印原始 dict。
- 不再只展示工具原始 answer。
- 增加了证据链。
- 增加了执行轨迹。
- 增加了风险等级。
- 增加了人工确认项。
- 增加了后续追踪项。
- 最终输出由 `final_answer` 承载。

---

## 9. Memory 与 Day 6 的联动

Day 6 验证了 Memory 与 Graph 的联动能力。

测试场景：

第一次输入：

```bash
python -m app.main --graph --session demo-001 "工单 WO-001 投料失败，请分析原因"
```

第二次输入：

```bash
python -m app.main --graph --session demo-001 "继续分析这个工单"
```

第二次执行时，Memory 成功补全上下文：

```text
继续分析这个工单 WO-001
```

执行轨迹中可以看到：

```text
load_memory:
  memory_count: 2
  context_completed: True
  last_order_id: WO-001
```

这说明：

- Memory 成功读取同一 session 下的历史上下文。
- Graph 在 `load_memory` 阶段完成了上下文补全。
- IntentRouter 基于补全后的 `effective_user_input` 正确识别意图。
- ResponseSynthesizer 使用补全后的输入生成报告。

因此 Day 5 的 Memory Layer 已经可以服务 Day 6 的 Graph 和 ResponseSynthesizer。

---

## 10. 测试命令

### 10.1 Graph 异常分析测试

```bash
python -m app.main --graph --session demo-001 "工单 WO-001 投料失败，请分析原因"
```

预期结果：

- intent 为 `work_order_exception_analysis`
- tools_used 包含多个制造业工具
- 输出 `# 工单异常分析报告`
- 输出结构化证据链
- 输出风险等级
- 输出建议动作
- 输出执行轨迹

实际验证通过。

---

### 10.2 Memory 上下文补全测试

```bash
python -m app.main --graph --session demo-001 "继续分析这个工单"
```

预期结果：

- Memory 找到最近处理的工单 `WO-001`
- `effective_user_input` 被补全为包含 `WO-001`
- intent 仍能识别为 `work_order_exception_analysis`
- final_answer 正常输出

实际验证通过。

关键输出：

```text
用户请求分析工单异常：继续分析这个工单 WO-001
```

执行轨迹：

```text
1. load_memory：{'memory_count': 2, 'context_completed': True, 'last_order_id': 'WO-001'}
2. route_intent：{'intent': 'work_order_exception_analysis', 'order_id': 'WO-001', 'confidence': 0.95, 'reason': '包含工单ID和异常关键词'}
3. analyze_exception：{'tools_used': ['get_work_order', 'get_inventory', 'get_device_status', 'get_quality_result', 'get_sap_sync_status', 'create_action_plan']}
4. synthesize_response：{'description': 'Generated structured business analysis response'}
```

---

### 10.3 State 字段检查测试

```bash
python - <<'PY'
from app.agent.graph import ManufacturingOpsGraph

graph = ManufacturingOpsGraph()
result = graph.run(
    user_input="工单 WO-001 投料失败，请分析原因",
    session_id="test-day6"
)

print("keys:", sorted(result.keys()))
print("intent:", result.get("intent"))
print("has prompt:", bool(result.get("prompt")))
print("has final_answer:", bool(result.get("final_answer")))
print("has tool_results:", bool(result.get("tool_results")))
print("has rag_context:", "rag_context" in result)
print("has execution_trace:", bool(result.get("execution_trace")))
print("execution_trace:", result.get("execution_trace"))
PY
```

实际验证结果：

```text
has prompt: True
has final_answer: True
has tool_results: True
has rag_context: True
has execution_trace: True
```

返回 keys 包含：

```text
answer
confidence
effective_user_input
errors
execution_trace
final_answer
intent
memory_context
order_id
prompt
rag_context
reason
result
session_id
tool_results
tools_used
user_input
```

最终 `execution_trace` 包含：

```text
load_memory
route_intent
analyze_exception
synthesize_response
save_memory
```

---

## 11. 测试结论

Day 6 验收通过。

已完成：

- Prompt Layer 独立存在。
- ResponseSynthesizer 独立存在。
- Graph 接入 `synthesize_response`。
- CLI 支持 Graph 模式输出 `final_answer`。
- `tool_results` 进入 state。
- `prompt` 进入 state。
- `final_answer` 进入 state。
- `execution_trace` 全链路记录。
- Memory 可以补全“继续分析这个工单”。
- 风险等级可以基于工具结果推导为 `HIGH`。
- Executor 原始链路仍然可以独立运行，没有被 Graph 改造破坏。

---

## 12. 当前限制

### 12.1 RAG 字段已存在，但内容还未结构化返回

当前报告中可以看到：

```text
RAG 知识上下文：
当前没有结构化 RAG 上下文。
```

这说明：

- Graph 已经支持 `rag_context`。
- State 已经声明 `rag_context`。
- ResponseSynthesizer 已经可以读取 `rag_context`。

但是 Executor 还没有把 RAG 检索结果结构化返回。

当前 RAG 结果主要仍然拼接在 Executor 的原始 `answer` 文本中。

后续需要将 RAG 检索结果改为结构化返回：

```python
"rag_context": [
    {
        "source": chunk.source,
        "score": chunk.score,
        "content": chunk.content,
    }
    for chunk in retrieved_chunks
]
```

这个点不阻塞 Day 6 完成，但应该作为 Day 7 的前置优化之一。

---

## 13. 后续扩展方向

Day 6 之后，下一步可以进入 Day 7。

建议 Day 7 方向：

```text
Context Layer / 多轮上下文治理 / 结构化 RAG 回填
```

重点包括：

- 将 RAG 检索结果结构化写入 `rag_context`。
- 区分 short-term context、memory context、rag context。
- 设计 ContextAssembler。
- 支持多轮任务上下文压缩。
- 避免上下文无限膨胀。
- 为未来接入真实 LLM 做上下文治理。
- 明确 Context Layer 与 Memory Layer、RAG Layer、Prompt Layer 的边界。

---

## 14. Day 6 完成标准

Day 6 完成标准如下：

- 可运行。
- 可解释。
- 可测试。
- 可替换。
- 不破坏原有 Executor 链路。
- Prompt Layer 与业务执行解耦。
- ResponseSynthesizer 与工具调用解耦。
- Graph 只负责编排。
- Memory 与 ResponseSynthesizer 已完成联动。
- State 字段协议清晰。
- `final_answer` 成为最终输出入口。
- `execution_trace` 可以复盘一次 Agent 执行过程。

当前状态：

```text
Day 6：Prompt Layer + Response Synthesizer —— 已完成
```