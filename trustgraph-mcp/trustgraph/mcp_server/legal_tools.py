from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Optional, Protocol

from trustgraph_legal.mcp_domain import JsonValue, invoke_tool, list_tools

JsonObject = Dict[str, JsonValue]
TokenResolver = Callable[[], str]


class ToolFunction(Protocol):
    def __call__(
        self,
        arguments: Optional[JsonObject] = None,
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
    token_resolver: Optional[TokenResolver] = None,
    require_auth: bool = True,
) -> List[JsonObject]:
    registered: List[JsonObject] = []
    for definition in list_tools():
        tool_name = str(definition["tool_name"])
        mcp.tool(tool_name)(_tool_function(tool_name, repo_root, token_resolver, require_auth))
        registered.append(definition)
    return registered


def register_debt_collection_tools(
    mcp: ToolRegistry,
    repo_root: Optional[Path] = None,
    token_resolver: Optional[TokenResolver] = None,
    require_auth: bool = True,
) -> List[JsonObject]:
    return register_debt_collection_brain_tools(mcp, repo_root, token_resolver, require_auth)


def _tool_function(
    tool_name: str,
    repo_root: Optional[Path],
    token_resolver: Optional[TokenResolver],
    require_auth: bool,
) -> ToolFunction:
    def run(arguments: Optional[JsonObject] = None) -> JsonObject:
        _require_context_auth(token_resolver, require_auth)
        return invoke_tool(tool_name, arguments, repo_root)

    run.__name__ = tool_name
    run.__doc__ = "TrustGraph legal debt-collection domain tool: {}".format(tool_name)
    return run


def _require_context_auth(
    token_resolver: Optional[TokenResolver],
    require_auth: bool,
) -> None:
    if not require_auth:
        return
    if token_resolver is None:
        raise PermissionError("MCP auth context required")
    try:
        token = token_resolver()
    except RuntimeError as exc:
        raise PermissionError("MCP auth context required") from exc
    if not isinstance(token, str) or not token:
        raise PermissionError("MCP auth context required")


__all__ = ["register_debt_collection_brain_tools", "register_debt_collection_tools"]
