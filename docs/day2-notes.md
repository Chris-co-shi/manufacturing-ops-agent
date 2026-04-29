# Day 2 学习记录：Agent 工程结构拆分

## 1. 今天主要看哪几章

| 章节 | 重点 |
|---|---|
| 第 7 章：构建你的 Agent 框架 | Agent 组件拆分、Tool、Executor、工具注册 |
| 第 4 章：智能体经典范式构建 | 复习 ReAct、Tool Calling、Action / Observation / Answer |

---

## 2. 今天为什么学这个

Day 1 已经完成了最小工具调用闭环，但整体结构仍然偏硬编码。

Day 1 的 `executor.py` 承担了太多职责：

- 提取工单号
- 判断用户意图
- 调用工具
- 汇总工具结果
- 生成异常判断
- 输出处置建议

这种结构在 MVP 阶段可以接受，但如果继续增加 RAG、Memory、LangGraph、SAP 工具、质检工具、处置计划工具，`executor.py` 会越来越臃肿。

所以 Day 2 的目标不是继续堆功能，而是把 Day 1 的固定流程拆成更清晰的 Agent 工程结构。

---

## 3. 今天的核心目标

Day 2 的核心目标：

```text
把 Day 1 的硬编码流程升级为：

用户输入
  ↓
IntentRouter 判断意图
  ↓
Executor 根据 intent 选择工具链
  ↓
ToolRegistry 执行工具
  ↓
业务工具返回结果
  ↓
Executor 汇总并输出答案
```

---

## 4. 今天理解的核心概念

### 4.1 IntentRouter 是什么

`IntentRouter` 负责识别用户意图。

它把用户输入转换成明确的任务类型。

示例：

```text
查询工单 WO-001 的状态
→ work_order_query

工单 WO-001 投料失败，请分析原因
→ work_order_exception_analysis

你好
→ unknown
```

它解决的问题是：

> 不同用户问题不应该走同一条工具链。

例如：

- 普通工单查询只需要调用 `get_work_order`
- 工单异常分析需要调用多个工具
- 无关输入不应该调用任何工具

---

### 4.2 ToolRegistry 是什么

`ToolRegistry` 负责统一管理工具。

每个工具不只是一个函数，还应该有完整定义：

- `name`
- `description`
- `parameters`
- `func`

这样后续接入 LangGraph 或 LLM Tool Calling 时，可以直接复用工具定义。

`ToolRegistry` 不关心工单、库存、设备这些业务语义，它只关心工具如何注册、如何查找、如何执行。

所以它属于 Agent 运行时基础设施。

---

### 4.3 Executor 是什么

`Executor` 负责编排执行流程。

它不应该负责所有细节，而应该：

1. 接收用户输入
2. 调用 `IntentRouter` 判断意图
3. 根据意图选择工具链
4. 通过 `ToolRegistry` 执行工具
5. 汇总工具结果
6. 生成最终回答

它类似 Java 后端里的应用服务层或用例编排层。

---

### 4.4 ReAct 和当前项目的对应关系

ReAct 链路：

```text
Thought → Action → Observation → Answer
```

对应到当前项目：

| ReAct 概念 | 当前项目 |
|---|---|
| Thought | IntentRouter 判断用户意图 |
| Action | Executor 选择并调用工具 |
| Observation | 工具返回工单、库存、设备、SAP、质检数据 |
| Answer | Executor 汇总并生成分析结果 |

---

## 5. 今天关于包结构的理解

### 5.1 为什么不放 utils

`utils` 只适合放无业务语义、无架构职责的通用函数，例如：

- JSON 文件读取
- 时间格式化
- 字符串处理
- 路径处理

`IntentRouter` 和 `ToolRegistry` 都不适合直接放 `utils`。

---

### 5.2 ToolRegistry 为什么放 core

`ToolRegistry` 不依赖制造业业务语义。

它只负责：

- 注册工具
- 保存工具元数据
- 查找工具
- 执行工具
- 返回统一执行结果

所以它属于 Agent 工具系统基础设施，适合放在：

```text
app/core/tool_registry.py
```

---

### 5.3 IntentRouter 为什么放 agent

当前 `IntentRouter` 包含制造业业务语义，例如：

- 工单号
- 投料
- 扣减
- 异常
- 原因分析
- 处置建议

所以它不适合放在 `core`，而应该放在：

```text
app/agent/intent_router.py
```

未来如果要进一步抽象，可以把：

- `BaseIntentRouter`
- `IntentResult`

放进 `core`，然后把 `ManufacturingIntentRouter` 留在 `agent` 或 `domain` 层。

---

## 6. 今天代码输出

| 类型 | 文件 | 说明 |
|---|---|---|
| 代码 | `app/agent/intent_router.py` | 新增 IntentRouter |
| 代码 | `app/core/tool_registry.py` | 将 ToolRegistry 放入 core |
| 代码 | `app/agent/executor.py` | Executor 接入 IntentRouter 和 core ToolRegistry |
| 代码 | `app/tools/quality_tool.py` | 新增质检工具 |
| 代码 | `app/tools/sap_tool.py` | 新增 SAP 同步工具 |
| 代码 | `app/tools/action_plan_tool.py` | 新增处置计划工具 |
| 数据 | `data/quality_results.json` | 质检 Mock 数据 |
| 数据 | `data/sap_sync.json` | SAP 同步 Mock 数据 |
| 工具 | `app/utils/json_loader.py` | JSON 文件读取工具 |
| 文档 | `docs/day2-notes.md` | Day 2 学习记录 |

---

## 7. 今天完成的功能

### 7.1 新增 IntentRouter

支持三种意图：

| Intent | 说明 |
|---|---|
| `work_order_query` | 普通工单查询 |
| `work_order_exception_analysis` | 工单异常分析 |
| `unknown` | 未识别任务 |

---

### 7.2 ToolRegistry 放入 core

`ToolRegistry` 从普通工具注册器升级为 Agent 运行时基础设施。

支持：

- 工具定义
- 工具参数定义
- 工具注册
- 工具列表
- 工具执行
- 执行结果包装

---

### 7.3 Executor 接入 IntentRouter

Day 2 后，Executor 不再直接自己判断所有逻辑，而是先调用：

```python
intent_result = self.intent_router.route(user_input)
```

然后根据不同 intent 选择不同工具链。

---

### 7.4 扩展业务工具

工具从 Day 1 的 3 个扩展到 6 个：

| 工具 | 说明 |
|---|---|
| `get_work_order` | 工单查询 |
| `get_inventory` | 库存查询 |
| `get_device_status` | 设备查询 |
| `get_quality_result` | 质检查询 |
| `get_sap_sync_status` | SAP 同步查询 |
| `create_action_plan` | 生成处置计划 |

---

## 8. 当前执行流程

### 8.1 普通工单查询

```text
用户输入
  ↓
IntentRouter → work_order_query
  ↓
Executor
  ↓
ToolRegistry.execute("get_work_order")
  ↓
get_work_order
  ↓
返回工单查询结果
```

---

### 8.2 工单异常分析

```text
用户输入
  ↓
IntentRouter → work_order_exception_analysis
  ↓
Executor
  ↓
ToolRegistry.execute("get_work_order")
  ↓
ToolRegistry.execute("get_inventory")
  ↓
ToolRegistry.execute("get_device_status")
  ↓
ToolRegistry.execute("get_quality_result")
  ↓
ToolRegistry.execute("get_sap_sync_status")
  ↓
ToolRegistry.execute("create_action_plan")
  ↓
返回结构化异常分析和处置建议
```

---

### 8.3 未知输入

```text
用户输入
  ↓
IntentRouter → unknown
  ↓
不调用工具
  ↓
返回当前支持范围提示
```

---

## 9. 今天的验收命令

### 9.1 查看工具清单

```bash
python -m app.main --tools
```

预期看到：

```text
get_work_order
get_inventory
get_device_status
get_quality_result
get_sap_sync_status
create_action_plan
```

---

### 9.2 普通工单查询

```bash
python -m app.main "查询工单 WO-001 的状态"
```

预期：

```text
Intent: work_order_query
Tools Used: ['get_work_order']
```

---

### 9.3 工单异常分析

```bash
python -m app.main "工单 WO-001 投料失败，请分析原因"
```

预期：

```text
Intent: work_order_exception_analysis
Tools Used: ['get_work_order', 'get_inventory', 'get_device_status', 'get_quality_result', 'get_sap_sync_status', 'create_action_plan']
```

---

### 9.4 不存在工单测试

```bash
python -m app.main "工单 WO-999 投料失败，请分析原因"
```

预期：

```text
工单不存在: WO-999
```

注意：项目中业务提示字段统一使用 `messages`。

---

### 9.5 unknown 测试

```bash
python -m app.main "你好"
```

预期：

```text
Intent: unknown
Tools Used: []
```

---

## 10. 今天遇到的问题

### 问题 1：IntentRouter 和 ToolRegistry 是否应该放 utils

最开始考虑过是否把它们放到 `utils`。

结论：

- 不建议放 `utils`
- `utils` 只放无业务语义的通用函数
- `ToolRegistry` 属于 Agent 运行时基础设施，应该放 `core`
- `IntentRouter` 当前包含业务语义，应该放 `agent`

---

### 问题 2：是否应该放 core

结论：

- `ToolRegistry` 可以放 `core`
- 当前具体的 `IntentRouter` 不建议放 `core`
- 未来可以把 `BaseIntentRouter`、`IntentResult` 抽到 `core`
- 当前制造业意图识别实现仍然放在 `agent`

---

### 问题 3：`message` 和 `messages` 字段统一

项目中业务提示字段统一使用：

```text
messages
```

例如：

```python
{
    "found": False,
    "messages": "工单不存在: WO-999"
}
```

后续要避免同时存在 `message` 和 `messages` 两种字段。

---

## 11. 今天的结论

Day 2 的核心不是新增几个工具，而是完成 Agent 工程结构升级。

现在项目从 Day 1 的固定流程：

```text
输入 → 固定查工单 → 固定查库存 → 固定查设备 → 输出
```

升级为：

```text
输入 → IntentRouter → Executor → ToolRegistry → Tools → Answer
```

这个结构可以支撑后续接入：

- RAG
- LangGraph
- LLM Tool Calling
- Memory
- Evaluation

---

## 12. 面试表达

Day 2 可以这样对面试官讲：

```text
第二天我对 Day 1 的最小 Agent 做了工程化拆分。

Day 1 还是固定流程，只要输入工单号，就固定查询工单、库存和设备。

Day 2 我引入了 IntentRouter、ToolRegistry 和 Executor。IntentRouter 负责识别用户输入是普通工单查询，还是工单异常分析；ToolRegistry 负责统一管理工具定义、参数和执行函数；Executor 负责根据不同 intent 编排工具调用链路。

同时我把 ToolRegistry 放到了 core，因为它不依赖制造业业务语义，属于 Agent 运行时基础设施；而 IntentRouter 仍然放在 agent，因为当前实现中包含工单、投料、扣减、异常分析等业务语义。

这一步的目的不是堆功能，而是为后续接入 RAG、LangGraph 和 LLM Tool Calling 做准备。
```

---

## 13. Git 提交

```bash
git add .
git commit -m "day2: introduce intent router and tool registry core"
git push
```

或者封板提交：

```bash
git add .
git commit -m "day2: finalize agent structure and documentation"
git push
```