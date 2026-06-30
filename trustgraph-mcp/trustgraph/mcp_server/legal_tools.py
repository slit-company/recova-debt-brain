from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Protocol

from trustgraph_legal.mcp_domain import JsonValue, invoke_tool, list_tools

JsonObject = Dict[str, JsonValue]


class ToolFunction(Protocol):
    def __call__(
        self,
        arguments: Optional[JsonObject] = None,
        authorization: Optional[str] = None,
    ) -> JsonObject:
        ...


class ToolDecorator(Protocol):
    def __call__(self, function: ToolFunction) -> ToolFunction:
        ...


class ToolRegistry(Protocol):
    def tool(self, name: Optional[str] = None) -> ToolDecorator:
        ...


def register_debt_collection_brain_tools(
    mcp: ToolRegistry,
    repo_root: Optional[Path] = None,
) -> List[JsonObject]:
    registered: List[JsonObject] = []
    for definition in list_tools():
        tool_name = str(definition["tool_name"])
        mcp.tool(tool_name)(_tool_function(tool_name, repo_root))
        registered.append(definition)
    return registered


def register_debt_collection_tools(
    mcp: ToolRegistry,
    repo_root: Optional[Path] = None,
) -> List[JsonObject]:
    return register_debt_collection_brain_tools(mcp, repo_root)


def _tool_function(tool_name: str, repo_root: Optional[Path]) -> ToolFunction:
    def run(
        arguments: Optional[JsonObject] = None,
        authorization: Optional[str] = None,
    ) -> JsonObject:
        if authorization is None or not authorization.startswith("Bearer "):
            raise PermissionError("Bearer authorization required")
        return invoke_tool(tool_name, arguments, repo_root)

    run.__name__ = tool_name
    run.__doc__ = "TrustGraph legal debt-collection domain tool: {}".format(tool_name)
    return run


__all__ = ["register_debt_collection_brain_tools", "register_debt_collection_tools"]
