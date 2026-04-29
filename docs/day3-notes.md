## Day 3：RAG 知识检索

Day 3 在 Day 2 的 Agent 工程结构基础上，引入了最小 RAG 能力。

### 今日学习章节

- 第 8 章：记忆与检索
- 第 4 章：ReAct 范式复习

### 今日目标

- 新增工业异常处理知识文档
- 实现 Markdown 文档加载
- 实现文档切分
- 实现关键词检索
- 将检索结果接入工单异常分析流程
- 在最终回答中输出知识库依据

### 新增知识文档

| 文档 | 说明 |
|---|---|
| inventory_exception.md | 库存扣减异常处理规范 |
| sap_sync.md | SAP 同步失败处理规范 |
| equipment_alarm.md | 设备报警处理规范 |

### Day 3 RAG 流程

```text
用户输入
  ↓
IntentRouter 判断异常分析意图
  ↓
Executor 调用业务工具
  ↓
KeywordRetriever 检索知识文档
  ↓
业务数据 + 文档依据
  ↓
生成最终回答