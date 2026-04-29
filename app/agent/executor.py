from app.agent.intent_router import IntentRouter
from app.core.tool_registry import ToolDefinition, ToolParameter, ToolRegistry
from app.rag.document import DocumentChunk
from app.rag.retriever import KeywordRetriever
from app.tools.work_order_tool import get_work_order
from app.tools.inventory_tool import get_inventory
from app.tools.device_tool import get_device_status
from app.tools.quality_tool import get_quality_result
from app.tools.sap_tool import get_sap_sync_status
from app.tools.action_plan_tool import create_action_plan


def _build_exception_analysis_answer(
        work_order: dict,
        inventory: dict | None,
        device: dict | None,
        quality_result: dict | None,
        sap_sync: dict | None,
        action_plan: dict,
        retrieved_chunks: list[DocumentChunk],

):
    lines = ["## 工单异常分析结果", "", f"工单号: {work_order['order_id']}", f"工单状态: {work_order['status']}",
             f"当前异常: {work_order['current_issue']}", f"优先级: {work_order['priority']}", ""]

    if inventory:
        lines.append("## 库存信息")
        lines.append(f"物料编码: {inventory['material_code']}")
        lines.append(f"物料名称: {inventory['material_name']}")
        lines.append(f"总库存: {inventory['total_qty']} {inventory['unit']}")
        lines.append(f"可用库存: {inventory['available_qty']} {inventory['unit']}")
        lines.append(f"冻结库存: {inventory['frozen_qty']} {inventory['unit']}")
        lines.append(f"最近同步状态: {inventory['last_sync_status']}")
        lines.append("")

    if device:
        lines.append("## 设备信息")
        lines.append(f"设备ID: {device['device_id']}")
        lines.append(f"设备名称: {device['device_name']}")
        lines.append(f"设备状态: {device['status']}")
        lines.append(f"最近报警: {device['last_alarm']}")
        lines.append(f"是否允许继续生产: {device['can_continue']}")
        lines.append("")

    if sap_sync:
        lines.append("## SAP 同步信息")
        lines.append(f"同步状态: {sap_sync['sync_status']}")
        lines.append(f"最近同步时间: {sap_sync['last_sync_time']}")
        lines.append(f"错误信息: {sap_sync['error_message']}")
        lines.append(f"重试次数: {sap_sync['retry_count']}")
        lines.append(f"是否需要补偿: {sap_sync['need_compensation']}")
        lines.append("")

    if quality_result:
        lines.append("## 质检信息")
        lines.append(f"质检状态: {quality_result['inspection_status']}")
        lines.append(f"最近结果: {quality_result['latest_result']}")
        lines.append(f"质量风险等级: {quality_result['risk_level']}")
        lines.append(f"备注: {quality_result['remark']}")
        lines.append("")

    lines.append("## 初步判断")

    if inventory and inventory.get("last_sync_status") == "FAILED":
        lines.append("- 库存最近同步失败，可能存在系统库存与现场库存不一致。")

    if sap_sync and sap_sync.get("sync_status") == "FAILED":
        lines.append("- SAP 同步状态失败，库存扣减链路存在一致性风险。")

    if device and device.get("status") != "NORMAL":
        lines.append("- 设备状态异常，可能影响工单继续执行。")

    if device and not device.get("can_continue", True):
        lines.append("- 设备当前不允许继续生产，需要现场确认。")

    if quality_result and quality_result.get("inspection_status") == "PENDING":
        lines.append("- 质检尚未完成，恢复生产前需要确认质量风险。")



    if inventory:
        total_qty = inventory.get("total_qty", 0)
        available_qty = inventory.get("available_qty", 0)

        if total_qty > 0:
            available_rate = available_qty / total_qty

            if available_rate >= 0.3:
                lines.append("- 当前可用库存比例正常，库存数量本身不是主要风险点。")

    lines.append("")
    lines.append("## 建议处置")

    for index, action in enumerate(action_plan["actions"], start=1):
        lines.append(f"{index}. {action}")

    lines.append("")
    lines.append("## 知识库依据")

    for index, chunk in enumerate(retrieved_chunks, start=1):
        lines.append(f"{index}. 来源: {chunk.source}，匹配分数: {chunk.score}")
        lines.append(f"   摘要: {chunk.content[:120]}...")
    return "\n".join(lines)


def _build_work_order_query_answer(work_order: dict):
    lines = ["## 工单查询结果", "", f"工单号: {work_order['order_id']}", f"工单状态: {work_order['status']}",
             f"物料编码: {work_order['material_code']}", f"设备编号: {work_order['device_id']}",
             f"当前异常: {work_order['current_issue']}", f"优先级: {work_order['priority']}"]

    return "\n".join(lines)


class ManufacturingOpsAgent:
    def __init__(self):
        self.registry = ToolRegistry()
        self.router = IntentRouter()
        self._register_tools()
        self.retriever = KeywordRetriever()

    def _register_tools(self):
        self.registry.register(
            ToolDefinition(
                name="get_work_order",
                description="根据工单号查询工单状态、物料、设备和当前异常",
                func=get_work_order,
                parameters=[
                    ToolParameter(
                        name="order_id",
                        type="string",
                        description="工单号，例如 WO-001",
                    )
                ],
            )
        )

        self.registry.register(
            ToolDefinition(
                name="get_inventory",
                description="根据物料编码查询库存数量、冻结数量、可用数量和同步状态",
                func=get_inventory,
                parameters=[
                    ToolParameter(
                        name="material_code",
                        type="string",
                        description="物料编码，例如 MAT-AL-001",
                    )
                ],
            )
        )

        self.registry.register(
            ToolDefinition(
                name="get_device_status",
                description="根据设备编号查询设备状态、报警信息和是否允许继续生产",
                func=get_device_status,
                parameters=[
                    ToolParameter(
                        name="device_id",
                        type="string",
                        description="设备编号，例如 DEV-MIX-001",
                    )
                ],
            )
        )

        self.registry.register(
            ToolDefinition(
                name="get_quality_result",
                description="根据工单号查询质检状态和质量风险",
                func=get_quality_result,
                parameters=[
                    ToolParameter(
                        name="order_id",
                        type="string",
                        description="工单号，例如 WO-001",
                    )
                ],
            )
        )

        self.registry.register(
            ToolDefinition(
                name="get_sap_sync_status",
                description="根据物料编码查询 SAP 与本地系统的同步状态",
                func=get_sap_sync_status,
                parameters=[
                    ToolParameter(
                        name="material_code",
                        type="string",
                        description="物料编码，例如 MAT-AL-001",
                    )
                ],
            )
        )

        self.registry.register(
            ToolDefinition(
                name="create_action_plan",
                description="根据工单、库存、设备、质检和 SAP 同步状态生成处置计划",
                func=create_action_plan,
                parameters=[
                    ToolParameter(
                        name="work_order",
                        type="object",
                        description="工单数据",
                    ),
                    ToolParameter(
                        name="inventory",
                        type="object",
                        required=False,
                        description="库存数据",
                    ),
                    ToolParameter(
                        name="device",
                        type="object",
                        required=False,
                        description="设备数据",
                    ),
                    ToolParameter(
                        name="quality_result",
                        type="object",
                        required=False,
                        description="质检数据",
                    ),
                    ToolParameter(
                        name="sap_sync",
                        type="object",
                        required=False,
                        description="SAP 同步数据",
                    ),
                ],
            )
        )

    def run(self, user_input: str):
        intent_result = self.router.route(user_input)

        if intent_result.intent == "work_order_exception_analysis":
            return self._analyze_work_order_exception(intent_result)

        if intent_result.intent == "work_order_query":
            return self._query_work_order(intent_result)

        return {
            "intent": intent_result.intent,
            "confidence": intent_result.confidence,
            "reason": intent_result.reason,
            "tools_used": [],
            "answer": "当前只支持工单查询和工单异常分析。请使用类似：查询工单 WO-001 的状态。",
        }

    def list_tools(self):
        return self.registry.list_tools()

    def _query_work_order(self, intent_result):
        tools_used = []

        work_order_result = self.registry.execute(
            "get_work_order",
            order_id=intent_result.order_id,
        )
        tools_used.append("get_work_order")

        result = work_order_result["result"]

        if not result["found"]:
            return {
                "intent": intent_result.intent,
                "confidence": intent_result.confidence,
                "reason": intent_result.reason,
                "tools_used": tools_used,
                "answer": result["message"],
            }

        work_order = result["data"]

        return {
            "intent": intent_result.intent,
            "confidence": intent_result.confidence,
            "reason": intent_result.reason,
            "tools_used": tools_used,
            "work_order": work_order,
            "answer": _build_work_order_query_answer(work_order),
        }

    def _analyze_work_order_exception(self, intent_result):
        tools_used = []

        work_order_exec = self.registry.execute(
            "get_work_order",
            order_id=intent_result.order_id,
        )
        tools_used.append("get_work_order")

        work_order_result = work_order_exec["result"]

        if not work_order_result["found"]:
            return {
                "intent": intent_result.intent,
                "confidence": intent_result.confidence,
                "reason": intent_result.reason,
                "tools_used": tools_used,
                "answer": work_order_result["messages"],
            }

        work_order = work_order_result["data"]

        inventory = self._execute_and_get_data(
            tool_name="get_inventory",
            tools_used=tools_used,
            material_code=work_order["material_code"],
        )

        device = self._execute_and_get_data(
            tool_name="get_device_status",
            tools_used=tools_used,
            device_id=work_order["device_id"],
        )

        quality_result = self._execute_and_get_data(
            tool_name="get_quality_result",
            tools_used=tools_used,
            order_id=work_order["order_id"],
        )

        sap_sync = self._execute_and_get_data(
            tool_name="get_sap_sync_status",
            tools_used=tools_used,
            material_code=work_order["material_code"],
        )

        action_plan_result = self.registry.execute(
            "create_action_plan",
            work_order=work_order,
            inventory=inventory,
            device=device,
            quality_result=quality_result,
            sap_sync=sap_sync,
        )
        tools_used.append("create_action_plan")

        action_plan = action_plan_result["result"]["data"]

        retrieved_chunks = self.retriever.retrieve(
            query=f"{work_order['current_issue']} {work_order['material_code']} {work_order['device_id']}",
            top_k=3,
        )
        return {
            "intent": intent_result.intent,
            "confidence": intent_result.confidence,
            "reason": intent_result.reason,
            "tools_used": tools_used,
            "work_order": work_order,
            "inventory": inventory,
            "device": device,
            "quality_result": quality_result,
            "sap_sync": sap_sync,
            "action_plan": action_plan,
            "answer": _build_exception_analysis_answer(
                work_order=work_order,
                inventory=inventory,
                device=device,
                quality_result=quality_result,
                sap_sync=sap_sync,
                action_plan=action_plan,
                retrieved_chunks=retrieved_chunks,
            ),
        }

    def _execute_and_get_data(self, tool_name: str, tools_used: list[str], **kwargs):
        exec_result = self.registry.execute(tool_name, **kwargs)
        tools_used.append(tool_name)

        if not exec_result["success"]:
            return None

        result = exec_result["result"]

        if not result.get("found"):
            return None

        return result.get("data")
