import sys

from app.agent.executor import ManufacturingOpsAgent
from app.agent.graph import ManufacturingOpsGraph


def print_usage() -> None:
    print("Usage:")
    print('  python -m app.main "查询工单 WO-001 的状态"')
    print('  python -m app.main --graph "查询工单 WO-001 的状态"')
    print('  python -m app.main --graph "工单 WO-001 投料失败，请分析原因"')
    print('  python -m app.main --graph --session demo-001 "工单 WO-001 投料失败，请分析原因"')
    print("  python -m app.main --tools")


def main() -> None:
    args = sys.argv[1:]

    if not args:
        print_usage()
        return

    if args[0] == "--tools":
        agent = ManufacturingOpsAgent()
        tools = agent.list_tools()

        print("## Registered Tools")
        for tool in tools:
            print(f"- {tool['name']}: {tool['description']}")
        return

    use_graph = False
    session_id = "default"

    if "--graph" in args:
        use_graph = True
        args.remove("--graph")

    if "--session" in args:
        index = args.index("--session")

        if index + 1 >= len(args):
            raise ValueError("--session 后面必须提供 session_id")

        session_id = args[index + 1]
        del args[index:index + 2]

    user_input = " ".join(args).strip()

    if not user_input:
        print_usage()
        return

    if use_graph:
        graph = ManufacturingOpsGraph()
        result = graph.run(
            user_input=user_input,
            session_id=session_id,
        )
    else:
        agent = ManufacturingOpsAgent()
        result = agent.run(user_input)

    print("Intent:", result.get("intent"))
    print("Confidence:", result.get("confidence"))
    print("Reason:", result.get("reason"))
    print("Tools Used:", result.get("tools_used", []))

    if use_graph:
        print("Session ID:", session_id)

    print()
    print(result.get("final_answer") or result.get("answer"))


if __name__ == "__main__":
    main()