import sys

from app.agent.executor import ManufacturingOpsAgent


def main(text: str):
    # if len(sys.argv) < 2:
    #     print("Usage: python main.py <input>")
    #     return
    # input = sys.argv[1]

    agent = ManufacturingOpsAgent()
    result = agent.run(text)

    print("Intent:", result["intent"])
    print("Tools Used:", result["tools_used"])
    print()
    print(result["answer"])


if __name__ == '__main__':
    main("查询工单 WO-001的状态")
