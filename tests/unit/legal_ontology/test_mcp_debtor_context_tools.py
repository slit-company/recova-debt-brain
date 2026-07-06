from __future__ import annotations

import inspect
import importlib.util
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Callable, Final, Protocol, TypeGuard

from trustgraph_legal.mcp_domain import invoke_tool, list_tools

REPO_ROOT: Final = Path(__file__).resolve().parents[3]
TRUSTGRAPH_MCP_PATH: Final = REPO_ROOT / "trustgraph-mcp"
PAGES_FIXTURE: Final = "tests/fixtures/legal-ocr-pages"
BASE_TOOL_NAMES: Final = [
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
]
DEBTOR_TOOL_SCOPES: Final = {
    "assemble_debtor_documents": "debtor_graph:assembly",
    "build_debtor_context_graph": "debtor_graph:build",
    "get_debtor_graph_snapshot": "debtor_graph:read",
    "list_debtor_route_candidates": "debtor_graph:routes",
    "explain_debtor_route_candidate": "debtor_graph:routes",
}
ROUTE_EXPLANATION_KEYS: Final = {
    "route_id",
    "route_label",
    "status",
    "review_status",
    "required_facts",
    "missing_facts",
    "blocking_facts",
    "legal_source_refs",
    "source_fact_ids",
    "no_direct_execution",
}
GOVERNANCE_RECORD_KEYS: Final = {"record_id", "suggested_action", "audit"}
JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject = dict[str, JsonValue]
ToolCallable = Callable[..., JsonObject]


class AuthContextValue(Protocol):
    token: str
    verified_by_gateway: bool
    scopes: tuple[str, ...]


class AuthContextFactory(Protocol):
    def __call__(
        self,
        token: str,
        verified_by_gateway: bool,
        scopes: tuple[str, ...],
    ) -> AuthContextValue:
        ...


class LegalToolsModule(Protocol):
    LEGAL_MCP_GATEWAY_SCOPE: str
    AuthContext: AuthContextFactory

    def register_debt_collection_brain_tools(
        self,
        mcp: "FakeMcp",
        repo_root: Path,
        token_resolver: Callable[[str], AuthContextValue],
        require_auth: bool = True,
    ) -> list[JsonObject]:
        ...


@dataclass(slots=True)
class FakeMcp:
    registered: dict[str, ToolCallable] = field(default_factory=dict)

    def tool(self, name: str | None = None) -> Callable[[ToolCallable], ToolCallable]:
        def decorator(function: ToolCallable) -> ToolCallable:
            self.registered[name if name is not None else function.__name__] = function
            return function

        return decorator


def test_debtor_graph_tools_are_additive_after_existing_mcp_tools() -> None:
    # Given: the public MCP tool registry.
    tools = list_tools()

    # When: tool contracts are listed for MCP clients.
    names = [str(tool["tool_name"]) for tool in tools]
    debtor_tools = {str(tool["tool_name"]): tool for tool in tools[16:]}

    # Then: the existing Todo 9 surface stays ordered and debtor tools append after it.
    assert names[:16] == BASE_TOOL_NAMES
    assert names[16:] == list(DEBTOR_TOOL_SCOPES)
    assert len(tools) == 21
    for tool_name, scope in DEBTOR_TOOL_SCOPES.items():
        tool = debtor_tools[tool_name]
        parameters = tool["parameters"]
        assert isinstance(parameters, list)
        parameter_names = {item for item in parameters if isinstance(item, str)}
        assert tool["group"] == "debtor_graph"
        assert tool["scope"] == scope
        assert "authorization" not in parameter_names
        assert "token" not in parameter_names
        assert "bearer" not in parameter_names


def test_debtor_graph_tools_build_redacted_route_explanation() -> None:
    # Given: the synthetic OCR page fixture and additive debtor graph tools.
    graph_envelope = invoke_tool(
        "build_debtor_context_graph",
        {"ocr_root": PAGES_FIXTURE},
        REPO_ROOT,
    )
    graph = graph_envelope["result"]
    assert isinstance(graph, dict)

    # When: route candidates and one route explanation are requested from the graph.
    candidates = invoke_tool(
        "list_debtor_route_candidates",
        {"graph": graph},
        REPO_ROOT,
    )
    explanation = invoke_tool(
        "explain_debtor_route_candidate",
        {"graph": graph, "route_id": "bank_account_attachment"},
        REPO_ROOT,
    )

    # Then: the MCP envelopes expose advisory routes without raw OCR text or local paths.
    for envelope in (graph_envelope, candidates, explanation):
        encoded = json.dumps(envelope, ensure_ascii=False, sort_keys=True)
        pii_profile = envelope["pii_profile"]
        assert isinstance(pii_profile, dict)
        assert envelope["group"] == "debtor_graph"
        assert pii_profile["raw_text_included"] is False
        assert "Synthetic OCR Page" not in encoded
        assert str(REPO_ROOT) not in encoded

    candidate_result = candidates["result"]
    assert isinstance(candidate_result, dict)
    assert candidate_result["route_count"] == 18
    explained = explanation["result"]
    assert isinstance(explained, dict)
    assert set(explained) == ROUTE_EXPLANATION_KEYS
    assert GOVERNANCE_RECORD_KEYS.isdisjoint(explained)
    assert explained["route_id"] == "bank_account_attachment"
    assert explained["status"] == "possible"
    assert explained["no_direct_execution"] is True
    required_facts = explained["required_facts"]
    assert isinstance(required_facts, list)
    assert "third_party_debtor_bank_hint" in required_facts


def test_debtor_graph_snapshot_rejects_outside_root_path(tmp_path: Path) -> None:
    # Given: a graph path outside the registered repository root.
    secret = "task-11-secret-graph-content"
    outside_graph = tmp_path / "secret-graph.json"
    _ = outside_graph.write_text(json.dumps({"graph_snapshot": {}, "secret": secret}), encoding="utf-8")

    # When: the MCP tool is invoked with that out-of-bounds path.
    envelope = invoke_tool(
        "get_debtor_graph_snapshot",
        {"graph_path": str(outside_graph)},
        REPO_ROOT,
    )

    # Then: the failure is redacted and does not leak the path or file content.
    encoded = json.dumps(envelope, ensure_ascii=False, sort_keys=True)
    assert envelope["result"] == {"status": "rejected", "reason": "path_outside_repo_root"}
    assert envelope["warnings"] == ["path_outside_repo_root"]
    assert str(outside_graph) not in encoded
    assert secret not in encoded


def test_fake_mcp_debtor_graph_tools_use_context_auth_only() -> None:
    # Given: the thin MCP adapter registered into an SDK-free fake MCP object.
    adapter_path = TRUSTGRAPH_MCP_PATH / "trustgraph" / "mcp_server" / "legal_tools.py"
    adapter_source = adapter_path.read_text(encoding="utf-8")
    assert "from mcp" not in adapter_source
    assert "import mcp" not in adapter_source
    legal_tools = _legal_tools_module()
    fake = FakeMcp()
    seen_scopes: list[str] = []
    _ = legal_tools.register_debt_collection_brain_tools(
        fake,
        REPO_ROOT,
        token_resolver=lambda scope: seen_scopes.append(scope) or legal_tools.AuthContext(
            token="task-11-context-token",
            verified_by_gateway=True,
            scopes=("debtor_graph:routes",),
        ),
    )

    # When: an additive debtor route tool is called through the fake MCP surface.
    envelope = fake.registered["list_debtor_route_candidates"](
        arguments={"ocr_root": PAGES_FIXTURE},
    )

    # Then: auth stayed in context and the public callable accepts only arguments.
    encoded = json.dumps(envelope, ensure_ascii=False, sort_keys=True)
    assert envelope["tool_name"] == "list_debtor_route_candidates"
    assert seen_scopes == ["debtor_graph:routes"]
    assert "task-11-context-token" not in encoded
    assert "authorization" not in inspect.signature(
        fake.registered["list_debtor_route_candidates"]
    ).parameters


def test_fake_mcp_authorization_argument_is_rejected_without_token_echo() -> None:
    # Given: the fake MCP adapter and a token-shaped authorization tool argument.
    token = "Bearer task-13-tool-arg-token"
    legal_tools = _legal_tools_module()
    fake = FakeMcp()
    _ = legal_tools.register_debt_collection_brain_tools(
        fake,
        REPO_ROOT,
        token_resolver=lambda scope: legal_tools.AuthContext(
            token="task-13-context-token:{}".format(scope),
            verified_by_gateway=True,
            scopes=("debtor_graph:routes",),
        ),
    )

    # When: authorization is passed as a public callable argument instead of context.
    try:
        _ = fake.registered["list_debtor_route_candidates"](
            authorization=token,
            arguments={"ocr_root": PAGES_FIXTURE},
        )
    except TypeError as exc:
        assert "authorization" in str(exc)
    else:
        raise AssertionError("fake MCP callable accepted authorization tool arg")

    # Then: the SDK-independent domain layer ignores extra args without token echo.
    envelope = invoke_tool(
        "list_debtor_route_candidates",
        {"ocr_root": PAGES_FIXTURE, "authorization": token},
        REPO_ROOT,
    )
    encoded = json.dumps(envelope, ensure_ascii=False, sort_keys=True)
    assert envelope["tool_name"] == "list_debtor_route_candidates"
    assert token not in encoded


def _legal_tools_module() -> LegalToolsModule:
    adapter_path = TRUSTGRAPH_MCP_PATH / "trustgraph" / "mcp_server" / "legal_tools.py"
    spec = importlib.util.spec_from_file_location(
        "trustgraph_mcp_server_legal_tools_task_11",
        adapter_path,
    )
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load legal_tools adapter")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if _is_legal_tools_module(module):
        return module
    raise AssertionError("legal_tools adapter is missing MCP registration attributes")


def _is_legal_tools_module(module: ModuleType) -> TypeGuard[LegalToolsModule]:
    return (
        hasattr(module, "register_debt_collection_brain_tools")
        and hasattr(module, "AuthContext")
        and hasattr(module, "LEGAL_MCP_GATEWAY_SCOPE")
    )
