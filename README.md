# Manufacturing Ops Agent

## 1. 项目简介

Manufacturing Ops Agent 是一个面向制造业现场异常分析的 AI Agent 学习项目。

本项目不是普通聊天机器人，而是围绕制造业场景，逐步构建一个具备意图识别、工具调用、多步骤任务执行、RAG 检索、LangGraph 编排和评估能力的工业 Agent。

当前项目主要用于学习和验证 AI Agent 的工程化开发方式。

---

## 2. 项目背景

在 MES / MOM / WMS 等制造业系统中，现场异常通常不是单点问题，而是多个系统状态共同影响，例如：

- 工单状态异常
- 库存扣减失败
- SAP 与本地系统库存不一致
- 设备报警
- AGV / PLC / DCS 回传延迟
- 质检状态未完成
- 人工处置流程不标准

传统系统通常只展示数据，最终仍需要业务人员或工程师人工分析。

本项目尝试将这些分析过程封装为 Agent 执行链路：

```text
用户问题
  ↓
识别业务意图
  ↓
调用业务工具
  ↓
汇总工具结果
  ↓
生成异常判断
  ↓
输出处置建议
```

---

## 3. 项目目标

本项目分阶段完成以下能力：

- Tool Calling
- Intent Router
- Tool Registry
- Agent Executor
- RAG 知识库检索
- LangGraph 状态编排
- Memory / Context 管理
- Agent 评估体系
- 工业场景异常分析
- 面试项目表达与文档沉淀

---

## 4. 当前技术栈


| 模块       | 当前选择                            |
| ---------- | ----------------------------------- |
| 开发语言   | Python                              |
| 数据来源   | JSON Mock 数据                      |
| Agent 执行 | Rule-based Executor                 |
| 意图识别   | IntentRouter                        |
| 工具管理   | ToolRegistry                        |
| 工具调用   | Python Function Tools               |
| 后续计划   | RAG、LangGraph、FastAPI、Evaluation |

---

## 5. 当前项目结构

```text
manufacturing-ops-agent/
├── app/
│   ├── main.py
│   ├── agent/
│   │   ├── executor.py
│   │   └── intent_router.py
│   ├── core/
│   │   └── tool_registry.py
│   ├── tools/
│   │   ├── work_order_tool.py
│   │   ├── inventory_tool.py
│   │   ├── device_tool.py
│   │   ├── quality_tool.py
│   │   ├── sap_tool.py
│   │   └── action_plan_tool.py
│   └── utils/
│       └── json_loader.py
├── data/
├── docs/
├── README.md
└── LICENSE
```

---

## 6. 包结构说明


| 包          | 职责                                                                        |
| ----------- | --------------------------------------------------------------------------- |
| `app/core`  | Agent 运行时基础设施，例如`ToolRegistry`、`ToolDefinition`、`ToolParameter` |
| `app/agent` | 当前 Agent 的执行逻辑，例如`Executor`、`IntentRouter`                       |
| `app/tools` | 具体业务工具，例如工单、库存、设备、质检、SAP 查询                          |
| `app/utils` | 无业务语义的通用函数，例如 JSON 文件读取                                    |
| `data`      | Mock 业务数据                                                               |
| `docs`      | 每日学习记录和设计说明                                                      |

---

## 7. 当前支持的工具


| 工具                  | 说明                                                   |
| --------------------- | ------------------------------------------------------ |
| `get_work_order`      | 根据工单号查询工单状态、物料、设备和当前异常           |
| `get_inventory`       | 根据物料编码查询库存数量、冻结数量、可用数量和同步状态 |
| `get_device_status`   | 根据设备编号查询设备状态、报警信息和是否允许继续生产   |
| `get_quality_result`  | 根据工单号查询质检状态和质量风险                       |
| `get_sap_sync_status` | 根据物料编码查询 SAP 与本地系统同步状态                |
| `create_action_plan`  | 根据工单、库存、设备、质检、SAP 状态生成处置计划       |

---

## 8. 当前支持的 Intent


| Intent                          | 说明         |
| ------------------------------- | ------------ |
| `work_order_query`              | 普通工单查询 |
| `work_order_exception_analysis` | 工单异常分析 |
| `unknown`                       | 未识别任务   |

---

## 9. 运行方式

### 9.1 查看工具清单

```bash
python -m app.main --tools
```

### 9.2 普通工单查询

```bash
python -m app.main "查询工单 WO-001 的状态"
```

### 9.3 工单异常分析

```bash
python -m app.main "工单 WO-001 投料失败，请分析原因"
```

### 9.4 不存在工单测试

```bash
python -m app.main "工单 WO-999 投料失败，请分析原因"
```

### 9.5 unknown 测试

```bash
python -m app.main "你好"
```

---

## 10. 学习进度


| Day   | 主题                   | 学习章节                                         | 输出文档                                     | 状态   |
| ----- | ---------------------- | ------------------------------------------------ | -------------------------------------------- | ------ |
| Day 1 | 最小工具调用闭环       | 第 4 章：智能体经典范式构建                      | [`docs/day1-notes.md`](./docs/day1-notes.md) | 已完成 |
| Day 2 | Agent 工程结构升级     | 第 7 章：构建你的 Agent 框架；第 4 章 ReAct 复习 | [`docs/day2-notes.md`](./docs/day2-notes.md) | 已完成 |
| Day 3 | RAG 知识库接入         | 第 8 章：记忆与检索                              | [`docs/day3-notes.md`](./docs/day3-notes.md) | 待开始 |
| Day 4 | LangGraph 状态编排     | 第 6 章：框架开发实践                            | `docs/day4-notes.md`                         | 待开始 |
| Day 5 | 上下文工程与评估       | 第 9 章；第 12 章                                | `docs/day5-notes.md`                         | 待开始 |
| Day 6 | FastAPI 接口与演示入口 | 项目整合                                         | `docs/day6-notes.md`                         | 待开始 |
| Day 7 | 项目封装与面试表达     | 复盘总结                                         | `docs/day7-notes.md`                         | 待开始 |

---

## 11. 当前阶段成果

### Day 1：最小工具调用闭环

完成内容：

- 工单查询工具
- 库存查询工具
- 设备状态查询工具
- 多工具串联调用
- 工业异常分析输出

详细记录见：

```text
docs/day1-notes.md
```

### Day 2：Agent 工程结构升级

完成内容：

- 新增 `IntentRouter`
- 将 `ToolRegistry` 放入 `core`
- `Executor` 接入意图路由
- 扩展多工具组合能力
- 明确 `core`、`agent`、`tools`、`utils` 包边界

详细记录见：

```text
docs/day2-notes.md
```

---

## 12. 当前限制


| 限制             | 说明                             |
| ---------------- | -------------------------------- |
| 未接入大模型     | 当前主要是规则驱动和函数工具调用 |
| 未接入 RAG       | 还不能检索异常处理文档           |
| 未接入 LangGraph | 当前还不是状态图编排             |
| 未接入真实数据库 | 当前使用 JSON Mock 数据          |
| 未提供 Web API   | 当前主要通过命令行运行           |
| 未建立评估体系   | 暂无自动化评估指标               |

---

## 13. 后续路线

```text
Day 1：最小工具调用闭环
  ↓
Day 2：Agent 工程结构升级
  ↓
Day 3：接入 RAG 知识库
  ↓
Day 4：接入 LangGraph 状态编排
  ↓
Day 5：上下文工程和评估体系
  ↓
Day 6：FastAPI 接口和演示入口
  ↓
Day 7：项目文档、面试稿、README 完善
```

---

## 14. 面试表达

这个项目可以这样介绍：

```text
我做了一个工业运维 Agent 学习项目，场景来自制造业现场异常分析。

Day 1 我先实现了最小闭环：用户输入工单问题后，Agent 可以调用工单、库存、设备三个工具，并输出结构化异常分析和处置建议。

Day 2 我对项目做了工程化拆分，引入 IntentRouter、ToolRegistry 和 Executor。IntentRouter 负责识别用户意图，ToolRegistry 负责统一管理工具定义和执行，Executor 负责编排工具调用链路。

这个阶段虽然还没有接入大模型和 LangGraph，但已经具备 Agent 工程结构的雏形。后续会继续接入 RAG、LangGraph、上下文工程和评估体系。
```
