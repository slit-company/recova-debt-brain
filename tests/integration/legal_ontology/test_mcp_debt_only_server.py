from __future__ import annotations

import importlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Callable, Final

import pytest

REPO_ROOT: Final = Path(__file__).resolve().parents[3]
TRUSTGRAPH_MCP_PATH: Final = REPO_ROOT / "trustgraph-mcp"
TRUSTGRAPH_BASE_PATH: Final = REPO_ROOT / "trustgraph-base"
EXPECTED_TOOL_NAMES: Final = [
    "list_debt_collection_tools",
    "ingest_legal_document",
    "ingest_ocr_markdown",
    "get_ingest_status",
    "classify_legal_document",
    "extract_case_packet",
    "get_case_graph",
    "check_case_stop_gates",
    "check_limitation_status",
    "check_attachment_target_rules",
    "summarize_case_ledger",
    "recommend_next_action",
    "list_unknown_document_types",
    "review_extracted_fact",
    "promote_ontology_candidate",
    "reprocess_case",
    "assemble_debtor_documents",
    "build_debtor_context_graph",
    "get_debtor_graph_snapshot",
    "list_debtor_route_candidates",
    "explain_debtor_route_candidate",
    "list_claim_domain_routes",
    "explain_collection_workflow_state",
    "evaluate_claim_domain_decision",
    "explain_claim_action_packet",
]
GENERIC_TOOL_NAMES: Final = {
    "embeddings",
    "put_config",
    "load_document",
    "delete_kg_core",
}

JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject = dict[str, JsonValue]
ToolCallable = Callable[..., JsonObject]


@dataclass(slots=True)
class FakeFastMCP:
    name: str
    dependencies: list[str]
    host: str
    port: int
    lifespan: Callable[..., object] | None
    token_verifier: object | None
    auth: object | None
    transport_security: object | None
    registered: dict[str, ToolCallable] = field(default_factory=dict)
    transport: str = ""

    def tool(self, name: str | None = None) -> Callable[[ToolCallable], ToolCallable]:
        def decorator(function: ToolCallable) -> ToolCallable:
            tool_name = name if name is not None else function.__name__
            self.registered[tool_name] = function
            return function

        return decorator

    def run(self, transport: str) -> None:
        self.transport = transport


@dataclass(frozen=True, slots=True)
class FakeAuthSettings:
    issuer_url: str
    resource_server_url: str


@dataclass(frozen=True, slots=True)
class FakeTransportSecuritySettings:
    allowed_hosts: list[str]


class FakeTokenVerifier:
    pass


@dataclass(frozen=True, slots=True)
class FakeAccessToken:
    token: str
    client_id: str
    scopes: list[str]


def test_debt_only_server_registers_only_recova_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    # Given: the MCP SDK is represented by a minimal fake FastMCP registry.
    _install_fake_mcp_sdk(monkeypatch)
    _install_local_packages()
    legal_only = importlib.import_module("trustgraph.mcp_server.legal_only")

    # When: the debt-only server is constructed for the public lab endpoint.
    config = legal_only.DebtCollectionServerConfig(
        host="127.0.0.1",
        port=8800,
        websocket_url="ws://gateway.example/socket",
        auth_issuer="https://recova-mcp-lab.slit.company",
        auth_resource_url="https://recova-mcp-lab.slit.company/mcp",
        repo_root=REPO_ROOT,
    )
    server = legal_only.DebtCollectionMcpServer(
        config=config,
        pubsub_backend=_ClosableBackend(),
        scope_authorizer=lambda identity: ["read:tools"],
    )

    # Then: only the 25 Recova debt-brain tools are externally registered.
    assert list(server.mcp.registered) == EXPECTED_TOOL_NAMES
    assert GENERIC_TOOL_NAMES.isdisjoint(server.mcp.registered)
    assert server.mcp.name == "Recova Debt Collection Brain"
    assert server.registered_tools[0]["tool_name"] == "list_debt_collection_tools"
    assert server.mcp.transport_security is not None
    assert "127.0.0.1:8800" in server.mcp.transport_security.allowed_hosts
    assert "recova-mcp-lab.slit.company" in server.mcp.transport_security.allowed_hosts

    server.run()
    assert server.mcp.transport == "streamable-http"


def test_debt_only_registered_tool_uses_context_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    # Given: a debt-only server with a gateway-wide legal MCP scope.
    _install_fake_mcp_sdk(monkeypatch)
    _install_local_packages()
    legal_only = importlib.import_module("trustgraph.mcp_server.legal_only")
    require_token = importlib.import_module("trustgraph.mcp_server.legal_tools").AuthContext
    auth = require_token(
        token="context-token",
        verified_by_gateway=True,
        scopes=("trustgraph-legal:mcp-domain",),
    )
    monkeypatch.setattr(legal_only, "require_token", lambda scope: auth)
    config = legal_only.DebtCollectionServerConfig(repo_root=REPO_ROOT)
    server = legal_only.DebtCollectionMcpServer(
        config=config,
        pubsub_backend=_ClosableBackend(),
        scope_authorizer=lambda identity: ["read:tools"],
    )

    # When: a registered tool is called through the server's public registry.
    envelope = server.mcp.registered["list_debt_collection_tools"](arguments={})

    # Then: the response is a redacted legal envelope and no token appears.
    encoded = json.dumps(envelope, ensure_ascii=False, sort_keys=True)
    assert envelope["tool_name"] == "list_debt_collection_tools"
    assert "context-token" not in encoded


def test_debt_only_server_defers_pubsub_until_token_authorization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given: a standalone lab server with no injected pubsub backend.
    _install_fake_mcp_sdk(monkeypatch)
    _install_local_packages()
    legal_only = importlib.import_module("trustgraph.mcp_server.legal_only")
    monkeypatch.setattr(
        legal_only,
        "_get_pubsub",
        lambda config: (_ for _ in ()).throw(AssertionError("eager pubsub")),
    )

    # When: the server is constructed so the HTTP MCP endpoint can start.
    server = legal_only.DebtCollectionMcpServer(
        config=legal_only.DebtCollectionServerConfig(repo_root=REPO_ROOT),
    )

    # Then: registering tools does not require the gateway pubsub stack yet.
    assert list(server.mcp.registered) == EXPECTED_TOOL_NAMES


def test_debt_only_server_supports_lab_bearer_without_pubsub(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_mcp_sdk(monkeypatch)
    _install_local_packages()
    legal_only = importlib.import_module("trustgraph.mcp_server.legal_only")
    monkeypatch.setattr(
        legal_only,
        "_get_pubsub",
        lambda config: (_ for _ in ()).throw(AssertionError("eager pubsub")),
    )

    server = legal_only.DebtCollectionMcpServer(
        config=legal_only.DebtCollectionServerConfig(
            repo_root=REPO_ROOT,
            lab_bearer_token="lab-token",
        ),
    )

    assert list(server.mcp.registered) == EXPECTED_TOOL_NAMES
    assert type(server.mcp.token_verifier).__name__ == "LabBearerTokenVerifier"


class _ClosableBackend:
    def close(self) -> None:
        return None


def _install_local_packages() -> None:
    for package_path in (TRUSTGRAPH_MCP_PATH, TRUSTGRAPH_BASE_PATH):
        path = str(package_path)
        if path not in sys.path:
            sys.path.insert(0, path)


def _install_fake_mcp_sdk(monkeypatch: pytest.MonkeyPatch) -> None:
    mcp_module = ModuleType("mcp")
    server_module = ModuleType("mcp.server")
    fastmcp_module = ModuleType("mcp.server.fastmcp")
    auth_module = ModuleType("mcp.server.auth")
    settings_module = ModuleType("mcp.server.auth.settings")
    transport_security_module = ModuleType("mcp.server.transport_security")
    middleware_module = ModuleType("mcp.server.auth.middleware")
    auth_context_module = ModuleType("mcp.server.auth.middleware.auth_context")
    provider_module = ModuleType("mcp.server.auth.provider")

    setattr(fastmcp_module, "FastMCP", FakeFastMCP)
    setattr(settings_module, "AuthSettings", FakeAuthSettings)
    setattr(
        transport_security_module,
        "TransportSecuritySettings",
        FakeTransportSecuritySettings,
    )
    setattr(auth_context_module, "get_access_token", lambda: None)
    setattr(provider_module, "AccessToken", FakeAccessToken)
    setattr(provider_module, "TokenVerifier", FakeTokenVerifier)

    monkeypatch.setitem(sys.modules, "mcp", mcp_module)
    monkeypatch.setitem(sys.modules, "mcp.server", server_module)
    monkeypatch.setitem(sys.modules, "mcp.server.fastmcp", fastmcp_module)
    monkeypatch.setitem(sys.modules, "mcp.server.auth", auth_module)
    monkeypatch.setitem(sys.modules, "mcp.server.auth.settings", settings_module)
    monkeypatch.setitem(
        sys.modules,
        "mcp.server.transport_security",
        transport_security_module,
    )
    monkeypatch.setitem(sys.modules, "mcp.server.auth.middleware", middleware_module)
    monkeypatch.setitem(
        sys.modules,
        "mcp.server.auth.middleware.auth_context",
        auth_context_module,
    )
    monkeypatch.setitem(sys.modules, "mcp.server.auth.provider", provider_module)
