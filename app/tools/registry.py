from typing import Callable, Dict, Any, TypedDict

"""
工具信息
"""


class ToolInfo(TypedDict):
    name: str
    description: str
    func: Callable[[Any], Any]


"""
工具注册
注册工具、获取工具、工具列表
"""


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolInfo] = {}

    def registry(self, name: str, description: str, func: Callable):
        """
        工具注册
        :param name: 工具名称
        :param description:  工具描述
        :param func: 工具回调函数
        :return:
        """
        self._tools[name] = {
            "name": name,
            "description": description,
            "func": func,
        }

    def get_tool(self, name: str) -> Callable:
        """
        获取工具
        :param name: 工具名称
        :return: 工具函数
        """
        tool = self._tools.get(name)
        if tool is None:
            raise ValueError(f"Tool {name} not found")
        return tool["func"]

    def list_tools(self):
        """
        获取工具列表清单
        :return:
        """
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
            }
            for tool in self._tools.values()
        ]

    def execute(self, name: str, **kwargs):
        """
        执行工具
        :param name: 工具名称
        :param kwargs: 工具参数
        :return: 工具返回结果
        """
        func = self.get_tool(name)
        return func(**kwargs)
