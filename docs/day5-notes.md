# Day 5 Notes：Agent Memory Layer 上下文记忆闭环

> 本文记录 Manufacturing Ops Agent 第 5 天的架构演进：从一次性执行流程，升级为具备短期上下文记忆、执行轨迹记录和 session 隔离能力的 Agent Workflow。

---

## 0. 今日摘要

| 项目 | 内容 |
|---|---|
| Day | Day 5 |
| 主题 | Agent Memory Layer |
| 核心目标 | 引入独立 Memory 层，让 Agent 支持上下文读取、执行轨迹保存、会话隔离 |
| 架构位置 | Graph 编排层中的运行时上下文能力 |
| 当前实现 | `JsonFileMemoryStore` + JSONL 文件持久化 |
| 关键字段 | `session_id`、`memory_context`、`effective_user_input`、`last_order_id` |
| 完成状态 | 已完成 |
| 验证方式 | CLI 三轮测试：首次执行、同 session 续接、不同 session 隔离 |

---

## 1. 今日目标

Day 5 的目标不是简单保存聊天记录，而是为 Agent 引入一个独立的 **Memory Layer**。

它要解决的问题是：

```text
Agent 不能只知道当前这一次输入。
Agent 需要知道：
- 当前 session 最近处理过什么
- 上一次分析的是哪个工单
- 本次执行过程中调用了哪些工具
- 本次执行产生了什么结果
- 不同 session 之间不能串上下文
```

Day 5 的重点包括：

- 新增 `app/memory` 独立模块
- 定义 `MemoryEntry` 数据模型
- 定义 `MemoryStore` 抽象接口
- 实现 `JsonFileMemoryStore` 文件存储
- 实现 `MemoryManager` 作为 Memory 操作入口
- 在 Graph 中增加 `load_memory_node`
- 在 Graph 中增加 `save_memory_node`
- 支持 `session_id`
- 支持 `effective_user_input`
- 支持基于 `last_order_id` 的轻量上下文续接
- 验证不同 session 的上下文隔离

---

## 2. 今日主要学习内容

### 2.1 Memory 在 Agent 架构中的定位

Memory 不是工具，也不是 RAG，也不是普通日志。

它在当前项目中的定位是：

```text
Memory = Agent 运行时上下文与历史执行经验管理层
```

它负责记录：

| Memory 类型 | 作用 | Day 5 状态 |
|---|---|---|
| `short_term_context` | 当前 session 的短期上下文，例如最近处理的工单 | 已实现 |
| `execution_trace` | Agent 本次执行轨迹，例如 intent、tools_used、answer | 已实现 |
| `historical_case` | 后续可扩展为历史异常案例 | 预留 |
| `user_preference` | 后续可扩展为用户偏好 | 预留 |

当前 Day 5 先实现最小闭环：

```text
short_term_context + execution_trace
```

---

## 3. 今日最终采用的方案

### 3.1 引入独立 Memory 模块

最终新增结构：

```text
app/
├── agent/
│   ├── graph.py
│   ├── executor.py
│   └── state.py
├── memory/
│   ├── __init__.py
│   ├── models.py
│   ├── store.py
│   └── manager.py
└── main.py

data/
└── memory/
    └── session_memory.jsonl
```

其中：

| 文件 | 职责 |
|---|---|
| `models.py` | 定义 Memory 数据结构，例如 `MemoryEntry` |
| `store.py` | 定义 `MemoryStore` 抽象接口和 JSONL 实现 |
| `manager.py` | 提供面向 Graph 的 Memory 操作入口 |
| `graph.py` | 在执行前加载 Memory，在执行后保存 Memory |
| `session_memory.jsonl` | 当前阶段的轻量持久化文件 |

---

## 4. 为什么 Memory 不放在 utils

### 4.1 utils 的边界

`utils` 只适合放无业务语义、无架构语义的通用函数。

例如：

- 字符串处理
- 时间格式转换
- 文件路径工具
- 通用 JSON 工具

而 Memory 不是普通工具函数。

---

### 4.2 Memory 是 Agent Runtime 的核心能力

Memory 具备明确的 Agent 架构语义：

```text
它记录 Agent 执行过什么。
它影响下一轮 Agent 如何理解用户输入。
它参与 Graph 的执行状态流转。
它需要支持 session 隔离。
它未来可以替换为 Redis / Database / VectorDB。
```

所以 Memory 应该作为独立模块存在：

```text
app/memory
```

而不是：

```text
app/utils
```

---

## 5. Memory 与 RAG 的边界

这是 Day 5 最重要的设计边界之一。

### 5.1 RAG 解决什么

RAG 解决的是外部知识检索问题。

例如：

```text
- 投料失败处理 SOP
- SAP 同步失败处理规范
- 库存异常处理规则
- 设备报警处理手册
```

RAG 的核心问题是：

```text
当前问题需要参考哪些知识？
```

---

### 5.2 Memory 解决什么

Memory 解决的是 Agent 自己的历史上下文问题。

例如：

```text
- 上一次分析的是哪个工单
- 上一次调用了哪些工具
- 上一次分析结果是什么
- 当前 session 最近处理过什么
```

Memory 的核心问题是：

```text
当前问题和之前的交互有什么关系？
```

---

### 5.3 当前边界结论

```text
RAG = 外部知识
Memory = Agent 运行历史
```

当前项目中：

```text
app/rag      负责知识检索
app/memory   负责上下文记忆
```

两者不能混在一起。

---

## 6. 当前 Day 5 架构理解

### 6.1 Day 4 的 Graph 模式

Day 4 的执行链路是：

```text
用户输入
  ↓
ManufacturingOpsGraph
  ↓
route_intent
  ↓
query_work_order / analyze_exception / unknown
  ↓
END
```

---

### 6.2 Day 5 加入 Memory 后的 Graph 模式

Day 5 后，执行链路变成：

```text
用户输入
  ↓
ManufacturingOpsGraph
  ↓
load_memory_node
  ↓
route_intent_node
  ↓
query_work_order / analyze_exception / unknown
  ↓
save_memory_node
  ↓
END
```

Memory 层接入后，Graph 不再只是一次性执行流程，而是具备了基础上下文能力。

---

## 7. State 结构演进

Day 5 对 Graph State 做了扩展。

核心新增字段：

| 字段 | 作用 |
|---|---|
| `session_id` | 用于隔离不同会话的 Memory |
| `memory_context` | 从 Memory 中加载出的上下文列表 |
| `effective_user_input` | 结合 Memory 补全后的有效输入 |

推荐结构：

```python
from typing import Any
from typing_extensions import TypedDict


class ManufacturingAgentState(TypedDict, total=False):
    """
    Agent Graph 运行时共享状态。
    它不是业务实体，而是一次 Agent 执行过程中的上下文载体。
    """

    session_id: str

    user_input: str
    effective_user_input: str

    memory_context: list[dict[str, Any]]

    intent: str
    order_id: str | None
    confidence: float
    reason: str

    result: dict[str, Any] | None
    tools_used: list[str]
    answer: str

    errors: list[str]
```

---

## 8. load_memory_node 的职责

### 8.1 节点定位

`load_memory_node` 是执行前节点。

它的职责是：

- 根据 `session_id` 读取最近 Memory
- 构造 `memory_context`
- 查找最近处理的工单号
- 对“继续分析刚才那个工单”这类输入进行轻量补全
- 生成 `effective_user_input`

---

### 8.2 当前处理逻辑

示例：

```text
用户输入：
继续分析刚才那个工单

Memory 中存在：
last_order_id = WO-001

补全后：
继续分析刚才那个工单 WO-001
```

这个补全结果会写入：

```text
state["effective_user_input"]
```

后续这些节点都应该优先使用 `effective_user_input`：

- `route_intent_node`
- `query_work_order_node`
- `analyze_exception_node`

---

## 9. save_memory_node 的职责

### 9.1 节点定位

`save_memory_node` 是执行后节点。

它的职责是：

- 保存本次执行轨迹
- 保存当前 session 最近处理的工单
- 不改变业务结果
- 不承担业务分析逻辑

---

### 9.2 当前保存内容

当前写入两类 Memory。

#### 1. `execution_trace`

用于记录完整执行轨迹：

```json
{
  "memory_type": "execution_trace",
  "metadata": {
    "user_input": "工单 WO-001 投料失败，请分析原因",
    "effective_user_input": "工单 WO-001 投料失败，请分析原因",
    "intent": "work_order_exception_analysis",
    "order_id": "WO-001",
    "confidence": 0.95,
    "reason": "包含工单ID和异常关键词",
    "tools_used": [
      "get_work_order",
      "get_inventory",
      "get_device_status",
      "get_quality_result",
      "get_sap_sync_status",
      "create_action_plan"
    ],
    "answer": "..."
  }
}
```

#### 2. `short_term_context`

用于记录当前 session 的短期上下文：

```json
{
  "memory_type": "short_term_context",
  "content": "最近处理的工单是 WO-001",
  "metadata": {
    "last_order_id": "WO-001",
    "intent": "work_order_exception_analysis"
  }
}
```

---

## 10. 当前关键设计原则

### 10.1 graph.py 只负责编排

`graph.py` 负责：

- 加载 Memory
- 路由意图
- 调用 Executor
- 保存 Memory
- 控制节点流转

它不负责：

- 具体工单怎么查
- 库存怎么分析
- SAP 同步怎么判断
- 质检风险怎么生成
- RAG 内容怎么组织

---

### 10.2 executor.py 仍然是业务执行核心

`executor.py` 继续负责：

- 执行业务工具
- 调用 RAG 检索
- 组织业务答案
- 返回执行结果

Day 5 没有把 Memory 写进 `executor.py`。

这样可以避免：

```text
executor.py 同时负责：
- 业务执行
- 流程编排
- Memory 读写
- 状态补全
```

否则 Executor 会越来越臃肿。

---

### 10.3 MemoryStore 必须隔离底层存储细节

`JsonFileMemoryStore` 负责：

```text
MemoryEntry <-> JSONL
```

上层不应该直接处理 JSON dict。

正确边界是：

```text
store.py
  负责存储格式转换

manager.py
  提供 Memory 操作语义

graph.py
  消费 MemoryEntry 并写入 State
```

---

## 11. 当前代码形态总结

### 11.1 `MemoryEntry`

`MemoryEntry` 是 Memory 的结构化数据模型。

它至少包含：

- `id`
- `session_id`
- `memory_type`
- `content`
- `metadata`
- `created_at`

---

### 11.2 `MemoryStore`

`MemoryStore` 是抽象存储接口。

当前定义两个核心方法：

```python
def save(self, entry: MemoryEntry) -> None:
    pass


def list_by_session(self, session_id: str, limit: int = 20) -> list[MemoryEntry]:
    pass
```

它的设计价值是：

```text
当前可以用 JSONL。
未来可以替换 Redis / SQLite / PostgreSQL / VectorDB。
Graph 不应该因为底层存储变化而修改。
```

---

### 11.3 `MemoryManager`

`MemoryManager` 是 Memory 的操作入口。

它对 Graph 暴露语义化方法：

- `remember_context()`
- `remember_execution_trace()`
- `get_recent_context()`

Graph 不直接操作文件，也不直接处理 JSONL。

---

## 12. 今日遇到的问题

### 12.1 `graph.invoke` 报 tuple 错误

曾经出现：

```text
AttributeError: 'tuple' object has no attribute 'invoke'
```

原因是某处多写了逗号，例如：

```python
self.graph = self._build_graph(),
```

或者：

```python
return builder.compile(),
```

这会导致对象变成 tuple。

修正为：

```python
self.graph = self._build_graph()
```

以及：

```python
return builder.compile()
```

---

### 12.2 `save_memory_node` 没有执行

一开始 Graph 中只定义了：

```text
save_memory -> END
```

但是没有任何业务节点连接到 `save_memory`。

错误结构：

```text
query_work_order
analyze_exception
unknown

save_memory -> END
```

正确结构：

```text
query_work_order -> save_memory -> END
analyze_exception -> save_memory -> END
unknown -> save_memory -> END
```

最终修正为：

```python
builder.add_edge("query_work_order", "save_memory")
builder.add_edge("analyze_exception", "save_memory")
builder.add_edge("unknown", "save_memory")
builder.add_edge("save_memory", END)
```

---

### 12.3 MemoryStore 返回 dict 导致读取失败

曾经出现：

```text
AttributeError: 'dict' object has no attribute 'memory_type'
```

原因是 `list_by_session()` 中写成了：

```python
entries.append(data)
```

这会返回 dict。

修正为：

```python
entries.append(MemoryEntry(**data))
```

这样 `graph.py` 中才能正常使用：

```python
memory.memory_type
memory.content
memory.metadata
memory.created_at
```

---

### 12.4 第二轮测试识别成 unknown

曾经出现：

```text
继续分析刚才那个工单
  -> Intent: unknown
```

原因是虽然 Memory 已经保存了 `last_order_id=WO-001`，但后续节点没有正确使用 `effective_user_input`。

需要确保以下节点都使用：

```python
user_input = state.get("effective_user_input", state["user_input"])
```

涉及节点：

- `route_intent_node`
- `query_work_order_node`
- `analyze_exception_node`

---

## 13. 测试结果

### 13.1 测试一：首次工单异常分析

#### 测试命令

```bash
python -m app.main --graph --session demo-001 "工单 WO-001 投料失败，请分析原因"
```

#### 测试目标

验证：

- Graph 可以正常执行
- IntentRouter 可以识别 `work_order_exception_analysis`
- Executor 可以完成工具调用
- RAG 可以返回知识库依据
- `save_memory_node` 可以写入 Memory

#### 测试结果

通过。

输出中识别为：

```text
Intent: work_order_exception_analysis
Confidence: 0.95
Reason: 包含工单ID和异常关键词
```

并成功写入：

```text
execution_trace
short_term_context
```

其中 `short_term_context` 包含：

```json
{
  "last_order_id": "WO-001",
  "intent": "work_order_exception_analysis"
}
```

---

### 13.2 测试二：同 session 上下文续接

#### 测试命令

```bash
python -m app.main --graph --session demo-001 "继续分析刚才那个工单"
```

#### 测试目标

验证：

- `load_memory_node` 能读取 `demo-001` 的历史 Memory
- 能找到 `last_order_id=WO-001`
- 能生成 `effective_user_input`
- IntentRouter 能继续识别工单分析意图

#### 测试结果

通过。

实际行为：

```text
原始输入：
继续分析刚才那个工单

Memory 补全：
继续分析刚才那个工单 WO-001

最终识别：
work_order_exception_analysis
```

---

### 13.3 测试三：不同 session 隔离

#### 测试命令

```bash
python -m app.main --graph --session demo-002 "继续分析刚才那个工单"
```

#### 测试目标

验证：

- `demo-002` 不能读取 `demo-001` 的 Memory
- 不同 session 之间不会串上下文
- 没有历史上下文时应返回 unknown

#### 测试结果

通过。

输出结果：

```text
Intent: unknown
Confidence: 0.1
Reason: 未识别到明确工单号或支持的业务意图
```

这说明 session 隔离符合预期。

---

## 14. Day 5 完成标准

Day 5 当前完成情况：

- [x] 新增 `app/memory` 独立模块
- [x] 定义 `MemoryEntry`
- [x] 定义 `MemoryStore` 抽象接口
- [x] 实现 `JsonFileMemoryStore`
- [x] 实现 `MemoryManager`
- [x] Graph 中新增 `load_memory_node`
- [x] Graph 中新增 `save_memory_node`
- [x] 支持 `session_id`
- [x] 支持 `effective_user_input`
- [x] 支持 `last_order_id` 上下文续接
- [x] 完成首次执行写入测试
- [x] 完成同 session 上下文续接测试
- [x] 完成不同 session 隔离测试
- [x] 保持 `executor.py` 不被 Memory 污染
- [x] 保持 `graph.py` 仍然承担编排职责

---

## 15. 当前项目分层认知

Day 5 后，当前项目分层可以理解为：

```text
app/
├── main.py                    # CLI 入口
├── agent/
│   ├── graph.py               # Agent Workflow 编排层
│   ├── executor.py            # Agent 业务执行层
│   └── state.py               # Graph State 定义
├── core/
│   ├── intent_router.py       # 意图识别
│   └── tool_registry.py       # 工具注册与执行
├── tools/
│   ├── work_order_tool.py     # 工单工具
│   ├── inventory_tool.py      # 库存工具
│   ├── device_tool.py         # 设备工具
│   ├── quality_tool.py        # 质检工具
│   ├── sap_tool.py            # SAP 同步工具
│   └── action_plan_tool.py    # 处置建议工具
├── rag/
│   ├── document.py            # 文档结构
│   ├── loader.py              # 知识加载
│   ├── splitter.py            # 文档切分
│   └── retriever.py           # 检索器
└── memory/
    ├── models.py              # Memory 数据模型
    ├── store.py               # Memory 存储接口与实现
    └── manager.py             # Memory 操作入口
```

### 15.1 当前调用链路

```text
main.py
  ↓
ManufacturingOpsGraph.run()
  ↓
load_memory_node
  ↓
route_intent_node
  ↓
query_work_order_node / analyze_exception_node / unknown_node
  ↓
ManufacturingOpsAgent.run()
  ↓
IntentRouter + ToolRegistry + RAG
  ↓
save_memory_node
  ↓
返回结果
```

---

## 16. 当前简化点

当前 Day 5 仍然是教学级实现。

简化点包括：

- Memory 使用 JSONL 文件存储
- 只支持基于 `last_order_id` 的上下文补全
- 没有 Memory 检索评分
- 没有长期记忆
- 没有向量化记忆
- 没有 Memory TTL
- 没有 Memory 压缩
- 没有用户偏好管理
- 没有真实多用户认证体系
- 没有并发写入保护

这些简化是合理的。

当前阶段重点不是做复杂 Memory 系统，而是完成架构闭环。

---

## 17. 未来扩展方向

### 17.1 替换存储层

当前：

```text
JsonFileMemoryStore
```

未来可以替换为：

```text
RedisMemoryStore
SQLiteMemoryStore
PostgresMemoryStore
VectorMemoryStore
```

由于已经定义了 `MemoryStore` 抽象接口，所以未来替换不应该影响 Graph。

---

### 17.2 增加 Memory 类型

当前支持：

```text
short_term_context
execution_trace
```

未来可以扩展：

```text
historical_case
tool_failure_pattern
operator_feedback
user_preference
```

---

### 17.3 引入 Memory 检索能力

当前是简单读取最近几条 Memory。

未来可以支持：

```text
- 按 session 检索
- 按 memory_type 检索
- 按 order_id 检索
- 按相似问题检索
- 按异常类型检索
- 按时间窗口检索
```

---

### 17.4 让 Memory 参与更高级决策

未来 Memory 可以用于：

```text
- 识别重复异常
- 复用历史处置方案
- 对比本次异常和历史异常
- 记录用户偏好的输出格式
- 识别高频失败工具
- 为 Planner 提供历史依据
```

---

## 18. 今日核心收获

### 18.1 Memory 不是聊天记录

今天最重要的认知是：

```text
Memory 不是简单保存对话文本。
Memory 是 Agent 运行时上下文和执行经验。
```

如果只保存聊天记录，Agent 仍然不知道：

- 哪些信息有业务意义
- 哪些字段可以用于下一轮推理
- 哪些执行轨迹值得复用
- 当前 session 最近的业务对象是什么

所以 Day 5 保存的是结构化 Memory，而不是纯文本聊天历史。

---

### 18.2 session_id 是 Memory 的基础边界

没有 `session_id`，Memory 很容易发生上下文污染。

例如：

```text
用户 A 刚分析 WO-001
用户 B 说“继续分析刚才那个工单”
如果没有 session 隔离，用户 B 可能错误拿到 WO-001
```

所以 `session_id` 是 Memory 层必须具备的基础字段。

---

### 18.3 effective_user_input 是当前阶段的关键桥梁

当前 IntentRouter 仍然是规则路由。

它依赖输入中存在：

```text
WO-xxx
```

所以对于：

```text
继续分析刚才那个工单
```

必须通过 Memory 补全为：

```text
继续分析刚才那个工单 WO-001
```

这就是 `effective_user_input` 的意义。

它不是用户原始输入，而是结合上下文后的有效输入。

---

## 19. Day 5 最终结论

Day 5 完成的是 Agent 架构中的一次关键升级：

```text
从一次性 Agent 执行
升级为
具备上下文记忆能力的 Agent Workflow
```

当前 Memory 能力虽然简单，但已经满足工程化 Agent 的基础要求：

```text
可写入
可读取
可续接
可隔离
可替换
不污染业务执行层
```

Day 5 的核心价值不在于 JSONL 文件本身，而在于建立了 Memory 层的职责边界和接入方式。

当前项目继续保持了正确方向：

- 小步演进
- 每天可运行
- 有明确架构边界
- 不过度设计
- 不把所有逻辑堆进 executor
- 不把核心运行时组件放进 utils

---

## 20. README 追加内容

README 只做整体架构和索引，不堆 Day 5 的实现细节。

建议追加：

```markdown
### Day 5 - Agent Memory Layer

- 引入独立 Memory 层，用于管理 Agent 运行时上下文与执行轨迹
- 在 Graph 编排层接入 `load_memory_node` 与 `save_memory_node`
- 支持基于 `session_id` 的上下文隔离
- 支持基于 `last_order_id` 的轻量上下文续接
- 当前使用 JSONL 作为最小存储实现，未来可替换为 Redis / SQLite / PostgreSQL / VectorDB
- 详细记录见：`docs/day5_memory.md`
```

---

## 21. 后续文档样式约定

后续每日 notes 建议统一采用当前文档风格：

```text
1. 顶部用摘要表说明 Day、主题、目标、状态
2. 每一节只讲一个问题，标题明确
3. 架构内容尽量用 text diagram 展示调用链
4. 职责边界用表格或“负责 / 不负责”表达
5. 问题复盘单独成节，记录错误、原因、修正方式
6. 测试结果按“命令 / 目标 / 结果”三段写
7. README 只放索引和总览，Day 文档承载细节
8. 结论部分必须总结“今天完成了哪一层架构演进”
```

---

## 22. 下一步方向

### 22.1 推荐方向一：Prompt 层

下一步可以引入：

```text
app/prompts
```

用于管理不同业务场景下的提示词模板。

目标是把以下内容从代码里逐步抽离出来：

```text
答案组织逻辑
输出格式约束
角色定义
业务分析结构
```

---

### 22.2 推荐方向二：Planner 层

后续可以引入：

```text
app/planner
```

用于根据意图、Memory、RAG、工具能力生成执行计划。

当前是固定流程：

```text
识别意图 -> 调用固定工具链
```

未来可以演进为：

```text
识别目标 -> 生成计划 -> 按计划调用工具 -> 汇总结果
```

---

### 22.3 推荐方向三：更真实的数据源

当前工具仍然是本地假数据。

后续可以逐步替换为：

```text
数据库查询
REST API
SAP mock service
设备状态 mock service
真实工单表结构
```

但替换时仍然要保持：

```text
Tools 作为外部能力边界
Executor 不直接依赖具体数据源实现
```

---

## 23. 今日复盘

Day 5 的过程说明了一件事：

```text
Agent 工程化不是一次把功能做复杂，
而是不断把边界拆清楚。
```

今天新增的 Memory 层，让项目从：

```text
能执行一次任务
```

演进为：

```text
能理解当前任务和上一轮任务之间的关系
```

这一步很关键。

当前项目仍然是学习项目，数据仍然简单，但架构已经开始体现真实 Agent 系统应有的分层：

```text
入口层
编排层
执行层
工具层
知识层
记忆层
```

Day 5 完成。
