from dataclasses import dataclass, field
from typing import Callable, Dict, Any, TypedDict


@dataclass
class ToolParameter:
    name: str
    type: str
    required: bool = True
    description: str = ""


@dataclass
class ToolDefinition:
    name: str
    description: str
    func: Callable[..., dict[str, Any]]
    parameters: list[ToolParameter] = field(default_factory=list)


"""
工具注册
注册工具、获取工具、工具列表
管理工具
"""


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition):
        if tool.name in self._tools:
            raise ValueError(f"Tool {tool.name} already exists")
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> ToolDefinition:
        """
        获取工具
        :param name: 工具名称
        :return: 工具函数
        """
        tool = self._tools.get(name)
        if tool is None:
            raise ValueError(f"Tool {name} not found")
        return tool

    def list_tools(self) -> list[dict[str, Any]]:
        """

        :return:
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": [
                    {
                        "name": param.name,
                        "type": param.type,
                        "required": param.required,
                        "description": param.description
                    }
                    for param in tool.parameters
                ]
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
        tool = self.get_tool(name)
        try:
            result = tool.func
            return {
                "tool": name,
                "success": True,
                "result": result(**kwargs)
            }
        except Exception as e:
            return {
                "tool": name,
                "success": False,
                "error": str(e)
            }
