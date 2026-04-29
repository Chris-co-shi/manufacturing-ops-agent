import sys

from app.agent.executor import ManufacturingOpsAgent
from app.agent.graph import ManufacturingOpsGraph


def print_result(result: dict):
    print("Intent:", result.get("intent"))
    print("Confidence:", result.get("confidence"))
    print("Reason:", result.get("reason"))
    print("Tools Used:", result.get("tools_used", []))
    print()
    print(result.get("answer"))


def main():
    if len(sys.argv) < 2:
        print("用法：")
        print("  python -m app.main \"查询工单 WO-001 的状态\"")
        print("  python -m app.main --graph \"查询工单 WO-001 的状态\"")
        print("  python -m app.main --graph \"工单 WO-001 投料失败，请分析原因\"")
        return

    if sys.argv[1] == "--graph":
        if len(sys.argv) < 3:
            print("用法：python -m app.main --graph \"工单 WO-001 投料失败，请分析原因\"")
            return

        agent = ManufacturingOpsGraph()
        result = agent.run(sys.argv[2])
        print_result(result)
        return

    agent = ManufacturingOpsAgent()
    result = agent.run(sys.argv[1])
    print_result(result)


if __name__ == "__main__":
    main()