# Agent 框架拆分


## 核心目标

Day 2 的目标不是新增很多功能，而是把 Day 1 的硬编码流程拆成更清晰的 Agent 工程结构：

- IntentRouter：负责识别用户意图
- ToolRegistry：负责管理工具定义和工具执行
- Executor：负责编排工具调用流程
- Tools：负责具体业务能力

## 4. IntentRouter 的职责

IntentRouter 负责把用户输入转换成明确的任务类型。

## 5. ToolRegistry 的职责

ToolRegistry 负责统一管理工具。

每个工具应该包含：

- name
- description
- parameters
- func

这样后续接入 LangGraph 或 LLM Tool Calling 时，可以直接复用工具定义。

## 6. Executor 的职责

Executor 负责编排流程：

1. 接收用户输入
2. 调用 IntentRouter 判断意图
3. 根据意图选择工具链
4. 通过 ToolRegistry 执行工具
5. 汇总工具结果
6. 生成最终回答
## 7. 包结构边界

- app/core：放 Agent 运行时基础设施，例如 ToolRegistry
- app/agent：放当前 Agent 的执行逻辑，例如 Executor 和 IntentRouter
- app/tools：放具体业务工具，例如工单查询、库存查询、设备查询
- app/common：放无业务语义的通用函数，例如 JSON 文件读取

ToolRegistry 可以放 core，因为它不依赖制造业业务语义。

IntentRouter 当前放 agent，因为它包含工单号、异常、投料、扣减等制造业业务语义。

## 8. 今天结论

Agent 不是一个大函数，而是由多个职责清晰的组件组成。

Day 2 的重点是把 Day 1 的固定流程升级为：

用户输入 → IntentRouter → Executor → ToolRegistry → Tools → Answer

这个结构可以支撑后续 LangGraph、RAG 和 LLM Tool Calling。
