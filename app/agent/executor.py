import re

from app.tools.device_tool import get_device_status
from app.tools.inventory_tool import get_inventory
from app.tools.registry import ToolRegistry
from app.tools.work_order_tool import get_work_orders


class ManufacturingOpsAgent:
    """
    工厂自动化代理
    """

    def __init__(self):
        self.tool_registry = ToolRegistry()
        self._register_tools()

    def _register_tools(self):
        self.tool_registry.registry(
            name="get_work_order",
            description="获取工单信息",
            func=get_work_orders
        )
        self.tool_registry.registry(
            name="get_inventory",
            description="获取库存信息",
            func=get_inventory
        )
        self.tool_registry.registry(
            name="get_device_status",
            description="获取设备库存信息",
            func=get_device_status
        )

    def run(self, text: str):
        order_id = self._extract_order_id(text)
        if order_id:
            return self._analyze_work_order(order_id)

        return {
            "intent": "unknown",
            "tools_used": [],
            "answer": "当前只支持工单查询与基础异常分析。请使用类似：查询工单WO-001的状态"
        }

    def _extract_order_id(self, text: str):
        match = re.search(r"WO-\d+", text)
        if match:
            return match.group(0)
        return None

    def _analyze_work_order(self, order_id: str):
        tools_used = []

        work_order_result = self.tool_registry.execute(
            "get_work_order",
            order_id=order_id
        )
        tools_used.append("get_work_order")

        if not work_order_result["found"]:
            return {
                "intent": "work_order_query",
                "tools_used": tools_used,
                "answer": work_order_result["messages"]
            }
        work_order = work_order_result["data"]
        inventory_result = self.tool_registry.execute(
            "get_inventory",
            material_code=work_order["material_code"]
        )
        tools_used.append("get_inventory")

        device_result = self.tool_registry.execute(
            "get_device_status",
            device_id=work_order["device_id"]
        )
        tools_used.append("get_device_status")

        return {
            "intent": "work_order_exception_analysis",
            "tools_used": tools_used,
            "work_order": work_order,
            "inventory": inventory_result.get("data"),
            "device": device_result.get("data"),
            "answer": self._build_answer(
                work_order=work_order,
                inventory=inventory_result.get("data"),
                device=device_result.get("data")
            )
        }

    def _build_answer(self, work_order: dict, inventory: dict | None, device: dict | None):
        lines = ["## 工单异常分析结果", ""]
        lines.append(f"工单号:{work_order['order_id']}"),
        lines.append(f'工单状态:{work_order["status"]}')
        lines.append(f'当前异常: {work_order['current_issue']}')
        lines.append(f'优先级: {work_order['priority']}')
        lines.append("")

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

        lines.append("## 初步建议")
        if inventory and inventory["last_sync_status"] == "FAILED":
            lines.append("- 库存最近同步失败，可能存在系统库存与现场库存不一致")

        if device and device["status"] != "NORMAL":
            lines.append("- 设备当前不允许继续生产，请及时处理")

        if inventory['total_qty'] > 0:
            available_rate = inventory['available_qty'] / inventory['total_qty']

            if available_rate < 0.1:
                lines.append("- 库存剩余量低于 10%，请及时补充库存。")
            elif available_rate < 0.3:
                lines.append("- 库存剩余量偏低，建议关注后续生产消耗。")
            else:
                lines.append("- 当前可用库存比例正常，库存数量本身不是主要风险点。")

        lines.append("")
        lines.append("## 建议处置")
        lines.append("1.暂停该工单继续投料")
        lines.append("2.核对SAP与XMOM库存差异")
        lines.append("3.检查设备状态")
        lines.append("4.检查库存同步状态")
        lines.append("5.检查设备是否允许继续生产")
        lines.append("6.人工确认后再执行补偿或重新扣减")
        return "\n".join(lines)
