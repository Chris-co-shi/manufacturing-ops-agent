# Day 4 Notes：LangGraph 状态编排闭环

## 1. 今日目标

Day 4 的核心目标不是重写 Agent，而是把 Day 1 到 Day 3 已经完成的能力接入到一个最小可运行的 Graph 编排层中。

前 3 天已经完成：

- Day 1：最小工具调用闭环
- Day 2：IntentRouter + ToolRegistry 工程结构
- Day 3：RAG 知识检索闭环

Day 4 的重点是：

- 引入 LangGraph 的状态编排思想
- 建立 Agent 执行链路的 Graph 入口
- 保持原有 `executor.py` 作为业务执行核心
- 避免 `graph.py` 变成第二个大型 Executor
- 通过命令行验证 Graph 模式可以正常运行

---

## 2. 今日主要学习内容

### 2.1 LangGraph 的核心概念

今天主要理解了 LangGraph 中几个基础概念：

| 概念 | 作用 |
|---|---|
| State | Graph 执行过程中的状态容器 |
| Node | 一个处理步骤，例如解析意图、执行工具、生成结果 |
| Edge | 节点之间的流转关系 |
| START | Graph 起点 |
| END | Graph 终点 |
| StateGraph | 用于声明状态图 |
| compile | 将声明式 Graph 编译为可执行对象 |

本质上，LangGraph 不是替代业务代码，而是负责把多个处理步骤组织成一个可控流程。

---

## 3. 今日最终采用的方案

### 3.1 采用轻量 Graph 包装模式

最终采用的结构是：

```text
app/
├── agent/
│   └── executor.py
├── graph.py
└── main.py
```

其中：

- `executor.py`：继续负责 Agent 的业务执行逻辑
- `graph.py`：只负责流程编排
- `main.py`：提供普通模式和 Graph 模式入口

也就是说，Day 4 没有把所有逻辑都迁移到 LangGraph 中，而是先做一个轻量接入。

---

## 4. 为什么不把业务逻辑都写进 graph.py

### 4.1 原因一：避免职责混乱

`graph.py` 的职责应该是编排流程，而不是处理业务细节。

不推荐的写法：

```text
graph.py 同时负责：
- 意图识别
- 工具选择
- 工具执行
- RAG 检索
- 异常分析
- 最终响应生成
```

这样会导致 `graph.py` 快速膨胀，最终变成另一个 `Executor`。

推荐的写法：

```text
graph.py 只负责：
- 定义 State
- 定义节点
- 定义节点流转
- 调用已有 Executor
```

---

### 4.2 原因二：复用已有能力

Day 1 到 Day 3 已经完成了：

- ToolRegistry
- IntentRouter
- AgentExecutor
- RAG Retriever
- 业务工具函数

这些能力本身已经可以工作。

Day 4 的目标不是推翻前面的成果，而是把它们纳入一个更清晰的运行流程。

---

### 4.3 原因三：方便后续渐进式演进

当前 Graph 只有一个核心执行节点，这是合理的。

后续可以逐步拆分为：

```text
START
  ↓
parse_intent
  ↓
retrieve_context
  ↓
execute_tools
  ↓
generate_response
  ↓
END
```

但是现在不需要一步到位。

当前阶段更重要的是：

- 先跑通
- 保持结构清晰
- 不过度设计
- 为后续扩展留入口

---

## 5. 当前 Day 4 架构理解

### 5.1 普通 Executor 模式

普通模式下，执行链路大致是：

```text
用户输入
  ↓
AgentExecutor
  ↓
IntentRouter
  ↓
ToolRegistry
  ↓
Tools
  ↓
RAG Retriever
  ↓
返回结果
```

---

### 5.2 Graph 模式

Graph 模式下，执行链路变成：

```text
用户输入
  ↓
ManufacturingOpsGraph
  ↓
LangGraph StateGraph
  ↓
执行节点
  ↓
复用 AgentExecutor
  ↓
返回结果
```

Graph 并没有替代 Executor，而是在 Executor 外层增加了一层流程编排能力。

---

## 6. Day 4 的关键设计原则

### 6.1 graph.py 不承载复杂业务逻辑

`graph.py` 应该保持轻量。

它不应该直接关心：

- 某个工单状态如何查询
- 某个设备异常如何分析
- 某个库存异常如何判断
- 某个 SAP 同步失败如何处理

这些仍然应该由：

- tools
- executor
- router
- retriever

分别承担。

---

### 6.2 executor.py 仍然是业务执行核心

当前阶段，`executor.py` 是 Agent 的主执行器。

它负责把以下能力串起来：

- 意图识别
- 工具调用
- RAG 检索
- 业务结果组织

Graph 只是把这个执行器封装为一个节点。

---

### 6.3 Graph 是流程骨架，不是业务大脑

对当前项目来说，Graph 的定位是：

```text
Graph = 编排层
Executor = 执行层
Tools = 能力层
RAG = 知识层
Router = 意图识别层
```

这个分层比把所有代码堆进一个文件更稳定。

---

## 7. 当前代码形态总结

### 7.1 ManufacturingOpsGraph

当前 `ManufacturingOpsGraph` 的职责是：

- 初始化 `AgentExecutor`
- 构建 LangGraph
- 定义状态结构
- 定义执行节点
- 暴露统一运行入口

它是 Graph 模式的门面对象。

---

### 7.2 main.py 增加 Graph 模式入口

通过命令行参数可以选择是否走 Graph 模式。

示例：

```bash
python -m app.main --graph "查询工单 WO-001 的状态"
```

这条命令说明：

- 用户输入仍然是自然语言
- `--graph` 表示走 LangGraph 编排流程
- 底层仍然复用已有 Agent 执行能力

---

## 8. 测试结果

### 8.1 测试命令

```bash
python -m app.main --graph "查询工单 WO-001 的状态"
```

### 8.2 测试目标

该测试用于验证：

- Graph 对象可以正常初始化
- StateGraph 可以正常编译
- Graph 节点可以正常执行
- Executor 可以被 Graph 正确调用
- 用户输入可以得到最终响应

---

## 9. 今日遇到的问题

### 9.1 初始化报错

在测试 Graph 模式时，曾经出现过初始化失败问题。

问题发生在：

```text
agent = ManufacturingOpsGraph()
```

说明 Graph 初始化阶段存在对象构造或依赖传递问题。

---

### 9.2 问题本质

这类问题通常不是 LangGraph 本身的问题，而是工程集成问题。

常见原因包括：

- 构造函数参数不一致
- State 类型定义不匹配
- 节点函数返回值格式不符合 State 要求
- Graph 编译前节点或边定义不完整
- 复用 Executor 时没有正确初始化依赖

---

### 9.3 解决思路

解决这类问题时，不应该一开始就大改架构。

应该按顺序检查：

```text
1. ManufacturingOpsGraph 是否能单独实例化
2. AgentExecutor 是否能单独实例化
3. Graph State 定义是否正确
4. Node 函数输入输出是否符合 State
5. compile 是否成功
6. invoke 是否能返回预期结果
```

---

## 10. 今日核心收获

### 10.1 LangGraph 不是魔法

今天最大的认识是：

LangGraph 并不会自动让 Agent 变得智能。

它解决的是：

- 流程组织
- 状态传递
- 多节点编排
- 条件分支
- 后续可观测和可扩展

它不直接解决：

- 工具设计
- 意图识别质量
- RAG 检索质量
- 业务规则建模
- 数据真实性

---

### 10.2 当前项目仍然是教学级 Agent

当前 Manufacturing Ops Agent 仍然比较简单。

原因包括：

- 数据源是假的
- 分词是简单规则
- 检索是关键词匹配
- 工具是本地模拟函数
- 没有真实数据库
- 没有真实 LLM 工具调用闭环
- 没有真实工业系统集成

所以当前阶段看起来像“小孩子过家家”是正常的。

但它的价值不在于业务复杂度，而在于建立 Agent 工程骨架。

---

### 10.3 现在学的是骨架，不是最终产品

当前阶段真正要掌握的是：

- Agent 项目如何分层
- 工具如何注册和调用
- 意图如何路由
- RAG 如何接入
- Graph 如何编排
- CLI 如何验证
- 每天如何交付一个可运行增量

这套骨架掌握以后，后面才能替换为真实能力：

```text
假数据 → 数据库
规则路由 → LLM / Embedding / Classifier
关键词检索 → 向量检索 / 混合检索
本地工具 → API / 数据库 / 工业系统接口
单节点 Graph → 多节点 Agent Workflow
```

---

## 11. 当前项目分层认知

当前项目推荐继续保持如下分层：

```text
app/
├── main.py                  # 程序入口
├── graph.py                 # Graph 编排层
├── agent/
│   └── executor.py          # Agent 执行层
├── core/
│   ├── intent_router.py     # 意图识别
│   └── tool_registry.py     # 工具注册
├── tools/
│   └── manufacturing_tools.py
├── rag/
│   ├── retriever.py
│   └── knowledge_base/
└── schemas/
    └── ...
```

### 11.1 core 和 utils 的区别

这里再次确认一个重要原则：

`IntentRouter` 和 `ToolRegistry` 不应该放在 `utils`。

原因是：

- `utils` 只适合放无业务语义的通用工具函数
- `IntentRouter` 是 Agent 的意图路由基础设施
- `ToolRegistry` 是 Agent 的工具管理基础设施
- 它们属于 Agent Runtime / Core，而不是普通工具类

所以放在 `core` 中更合理。

---

## 12. Day 4 完成标准

Day 4 可以认为完成的标准是：

- [x] 项目中引入 LangGraph
- [x] 新增 Graph 编排入口
- [x] Graph 能够复用已有 Executor
- [x] main.py 支持 `--graph` 模式
- [x] 可以通过 CLI 执行 Graph 流程
- [x] graph.py 没有变成第二个大型 Executor
- [x] 保持了当前项目的分层清晰度

---

## 13. Day 4 的最终结论

Day 4 的重点不是做复杂 Agent，而是完成一次工程化升级：

```text
从普通函数式执行
升级为
具备状态编排能力的 Agent Workflow
```

当前采用轻量 Graph 包装模式是正确的。

它既保留了 Day 1 到 Day 3 已经完成的能力，又为后续扩展多节点流程、条件分支、Human-in-the-loop、错误恢复和可观测性打下基础。

---

## 14. 下一步方向

### 14.1 推荐方向一：把 Graph 拆成多节点

将当前单节点 Graph 拆成更清晰的流程：

```text
START
  ↓
route_intent
  ↓
retrieve_context
  ↓
execute_agent
  ↓
format_response
  ↓
END
```

这样可以真正体现 LangGraph 的价值。

---

### 14.2 推荐方向二：引入更真实的 State

当前 State 可以逐步扩展为：

```text
{
  "query": "...",
  "intent": "...",
  "confidence": 0.95,
  "retrieved_chunks": [],
  "tool_results": [],
  "final_answer": "...",
  "errors": []
}
```

这样每个节点都只处理自己负责的状态字段。

---

### 14.3 推荐方向三：增加失败处理节点

后续可以加入：

```text
execute_agent
  ↓
是否失败？
  ├── 是：error_handler
  └── 否：format_response
```

这会让 Agent 更接近真实工程项目。

---

## 15. 今日复盘

今天完成的是 Agent 工程结构中的一个重要转折点。

前 3 天主要是能力建设：

```text
工具能力
意图识别能力
知识检索能力
```

Day 4 开始进入流程编排：

```text
状态
节点
边
执行流
```

当前项目虽然仍然简单，但方向是正确的。

现在最重要的是继续保持：

- 小步提交
- 每天可运行
- 每天有明确交付物
- 不过度抽象
- 不把所有逻辑堆进一个文件

Day 4 完成。