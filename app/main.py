import sys

from app.agent.executor import ManufacturingOpsAgent


def main(text: str = ""):
    agent = ManufacturingOpsAgent()

    if len(sys.argv) >= 2 and sys.argv[1] == "--tools":
        tools = agent.list_tools()

        print("## Registered Tools")
        for tool in tools:
            print(f"- {tool['name']}: {tool['description']}")

        return

    # if len(sys.argv) < 2:
    #     print("用法：")
    #     print("  python -m app.main \"查询工单 WO-001 的状态\"")
    #     print("  python -m app.main \"工单 WO-001 投料失败，请分析原因\"")
    #     print("  python -m app.main --tools")
    #     return

    user_input = text or sys.argv[1]

    result = agent.run(user_input)

    print("Intent:", result["intent"])
    print("Confidence:", result.get("confidence"))
    print("Reason:", result.get("reason"))
    print("Tools Used:", result["tools_used"])
    print()
    print(result["answer"])


if __name__ == '__main__':
    main("")
