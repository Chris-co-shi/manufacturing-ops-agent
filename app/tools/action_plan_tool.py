from typing import Any

"""
创建处理计划
"""


def create_action_plan(
        work_order: dict[str, Any],
        inventory: dict[str, Any] | None = None,
        device: dict[str, Any] | None = None,
        quality_result: dict[str, Any] | None = None,
        sap_sync: dict[str, Any] | None = None,
):
    """
    创建处理计划
    :param work_order: 工单
    :param inventory: 库存
    :param device: 设备
    :param quality_result: 质检结果
    :param sap_sync: SAP同步结果
    :return:
    """
    actions = [f"暂停工单 {work_order['order_id']} 的继续投料，避免异常扩大。"]

    if sap_sync and sap_sync.get("sync_status") == "FAILED":
        actions.append("核对 SAP 与 XMOM 库存差异，检查同步失败原因。")

        if sap_sync.get("need_compensation"):
            actions.append("当前 SAP 同步失败且需要补偿，建议执行补偿或重试机制。")

    if inventory:
        total_qty = inventory.get("total_qty", 0)
        available_qty = inventory.get("available_qty", 0)

        if total_qty > 0:
            available_rate = available_qty / total_qty

            if available_rate < 0.1:
                actions.append("可用库存低于 10%，需要立即补充库存或调整生产计划。")
            elif available_rate < 0.3:
                actions.append("可用库存偏低，建议关注后续生产消耗。")
            else:
                actions.append("当前库存数量本身不是主要风险点，重点关注库存一致性。")

    if device:
        if device.get("status") != "NORMAL":
            actions.append("检查设备报警状态，确认设备恢复正常前不建议继续生产。")

        if not device.get("can_continue", True):
            actions.append("设备当前不允许继续生产，需要现场确认后再恢复工单。")

    if quality_result:
        if quality_result.get("inspection_status") == "PENDING":
            actions.append("质检结果尚未完成，恢复生产前需要确认质量风险。")

    actions.append("人工确认库存、设备、SAP 同步和现场物料状态后，再执行重新扣减。")

    return {
        "found": True,
        "data": {
            "action_count": len(actions),
            "actions": actions,
        },
    }
