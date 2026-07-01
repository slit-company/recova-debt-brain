from __future__ import annotations

import argparse
import importlib
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Any, AsyncIterator, Protocol

from .auth import GatewayTokenVerifier, IamScopeAuthorizer, require_token
from .legal_tools import JsonObject, register_debt_collection_brain_tools


class McpRegistry(Protocol):
    def tool(self, name: str | None = None) -> Any:
        ...

    def run(self, transport: str) -> None:
        ...


class ClosableBackend(Protocol):
    def close(self) -> None:
        ...


@dataclass(frozen=True, slots=True)
class DebtCollectionServerConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    websocket_url: str = "ws://api-gateway:8088/api/v1/socket"
    auth_issuer: str = ""
    auth_resource_url: str = ""
    repo_root: Path | None = None
    pubsub_config: dict[str, Any] | None = None


@asynccontextmanager
async def debt_collection_lifespan(
    server: McpRegistry,
    pubsub_backend: ClosableBackend | None = None,
) -> AsyncIterator[None]:
    try:
        yield None
    finally:
        if pubsub_backend is not None:
            pubsub_backend.close()


class DebtCollectionMcpServer:
    def __init__(
        self,
        config: DebtCollectionServerConfig | None = None,
        pubsub_backend: ClosableBackend | None = None,
        scope_authorizer: Any = None,
    ) -> None:
        resolved_config = config or DebtCollectionServerConfig()
        self.host = resolved_config.host
        self.port = resolved_config.port
        self.websocket_url = resolved_config.websocket_url
        self.repo_root = resolved_config.repo_root
        self.pubsub_backend = pubsub_backend
        lazy_authorizer = None
        if pubsub_backend is None and scope_authorizer is None:
            lazy_authorizer = _LazyIamScopeAuthorizer(
                resolved_config.pubsub_config or {}
            )
        authorizer = (
            scope_authorizer
            if scope_authorizer is not None
            else (
                IamScopeAuthorizer(self.pubsub_backend)
                if self.pubsub_backend is not None
                else lazy_authorizer
            )
        )
        auth_settings = _auth_settings(
            issuer_url=resolved_config.auth_issuer or f"http://{self.host}:{self.port}",
            resource_server_url=(
                resolved_config.auth_resource_url
                or f"http://{self.host}:{self.port}"
            ),
        )
        lifespan = partial(
            debt_collection_lifespan,
            pubsub_backend=lazy_authorizer or self.pubsub_backend,
        )
        fast_mcp = _fast_mcp_class()
        self.mcp = fast_mcp(
            "Recova Debt Collection Brain",
            dependencies=["trustgraph-base"],
            host=self.host,
            port=self.port,
            lifespan=lifespan,
            token_verifier=GatewayTokenVerifier(self.websocket_url, authorizer),
            auth=auth_settings,
        )
        self.registered_tools: list[JsonObject] = register_debt_collection_brain_tools(
            self.mcp,
            repo_root=self.repo_root,
            token_resolver=require_token,
        )

    def run(self) -> None:
        self.mcp.run(transport="streamable-http")


class _LazyIamScopeAuthorizer:
    def __init__(self, pubsub_config: dict[str, Any]):
        self.pubsub_config = pubsub_config
        self.pubsub_backend: ClosableBackend | None = None
        self.authorizer: Any = None

    async def __call__(self, identity: Any) -> list[str]:
        if self.authorizer is None:
            self.pubsub_backend = _get_pubsub(self.pubsub_config)
            self.authorizer = IamScopeAuthorizer(self.pubsub_backend)
        return list(await self.authorizer(identity))

    def close(self) -> None:
        if self.pubsub_backend is not None:
            self.pubsub_backend.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Recova debt-collection-only MCP server",
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--websocket-url",
        default="ws://api-gateway:8088/api/v1/socket",
    )
    parser.add_argument(
        "--auth-issuer",
        default=os.environ.get("AUTH_ISSUER", ""),
    )
    parser.add_argument(
        "--auth-resource-url",
        default=os.environ.get("AUTH_RESOURCE_URL", ""),
    )
    parser.add_argument("--repo-root", default="")
    _add_pubsub_args(parser)
    _add_logging_args(parser)
    args = parser.parse_args()
    _setup_logging(vars(args))
    repo_root = Path(args.repo_root) if args.repo_root else None
    config = DebtCollectionServerConfig(
        host=args.host,
        port=args.port,
        websocket_url=args.websocket_url,
        auth_issuer=args.auth_issuer,
        auth_resource_url=args.auth_resource_url,
        repo_root=repo_root,
        pubsub_config=vars(args),
    )
    server = DebtCollectionMcpServer(config=config)
    server.run()


def run() -> None:
    main()


def _fast_mcp_class() -> Any:
    return importlib.import_module("mcp.server.fastmcp").FastMCP


def _auth_settings(**kwargs: str) -> Any:
    return importlib.import_module("mcp.server.auth.settings").AuthSettings(**kwargs)


def _get_pubsub(config: dict[str, Any]) -> ClosableBackend:
    return importlib.import_module("trustgraph.base.pubsub").get_pubsub(**config)


def _add_pubsub_args(parser: argparse.ArgumentParser) -> None:
    importlib.import_module("trustgraph.base.pubsub").add_pubsub_args(parser)


def _add_logging_args(parser: argparse.ArgumentParser) -> None:
    importlib.import_module("trustgraph.base.logging").add_logging_args(parser)


def _setup_logging(config: dict[str, Any]) -> None:
    importlib.import_module("trustgraph.base.logging").setup_logging(config)


if __name__ == "__main__":
    main()
