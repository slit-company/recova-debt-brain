from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Protocol, Tuple

from trustgraph_legal.mcp_domain import invoke_tool, list_tools

JsonObject = Dict[str, Any]
LEGAL_MCP_GATEWAY_SCOPE = "trustgraph-legal:mcp-domain"


class AuthContext(NamedTuple):
    token: str
    verified_by_gateway: bool
    scopes: Tuple[str, ...]


TokenResolver = Callable[[str], AuthContext]


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
        required_scope = str(definition["scope"])
        mcp.tool(tool_name)(
            _tool_function(
                tool_name,
                repo_root,
                token_resolver,
                require_auth,
                required_scope,
            )
        )
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
    required_scope: str,
) -> ToolFunction:
    def run(arguments: Optional[JsonObject] = None) -> JsonObject:
        _require_context_auth(token_resolver, require_auth, required_scope)
        return invoke_tool(tool_name, arguments, repo_root)

    run.__name__ = tool_name
    run.__doc__ = "TrustGraph legal debt-collection domain tool: {}".format(tool_name)
    return run


def _require_context_auth(
    token_resolver: Optional[TokenResolver],
    require_auth: bool,
    required_scope: str,
) -> None:
    if not require_auth:
        return
    if token_resolver is None:
        raise PermissionError("MCP auth context required")
    try:
        context = token_resolver(required_scope)
    except RuntimeError as exc:
        raise PermissionError("MCP auth context required") from exc
    if not isinstance(context, AuthContext):
        raise PermissionError("MCP gateway auth context required")
    if not context.verified_by_gateway or not context.token:
        raise PermissionError("MCP auth context required")
    if not _scope_allowed(context.scopes, required_scope):
        raise PermissionError("MCP auth context lacks required scope")


def _scope_allowed(scopes: Tuple[str, ...], required_scope: str) -> bool:
    return (
        "*" in scopes
        or LEGAL_MCP_GATEWAY_SCOPE in scopes
        or required_scope in scopes
    )


__all__ = [
    "AuthContext",
    "LEGAL_MCP_GATEWAY_SCOPE",
    "register_debt_collection_brain_tools",
    "register_debt_collection_tools",
]
