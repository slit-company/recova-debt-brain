from __future__ import annotations

import importlib
import importlib.util
import json
import re
import sys
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field, is_dataclass
from pathlib import Path
from types import ModuleType
from typing import Callable, Final, Protocol, TypeGuard

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
MCP_PACKAGE_ROOT: Final = REPO_ROOT / "trustgraph-mcp"
TRUSTGRAPH_MCP_PATH: Final = MCP_PACKAGE_ROOT
if str(MCP_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(MCP_PACKAGE_ROOT))

JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject = dict[str, JsonValue]
ToolCallable = Callable[..., JsonObject]
EXPECTED_21_TOOL_NAMES: Final = [
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
]
CLAIM_DOMAIN_TOOL_SCOPES: Final = {
    "list_claim_domain_routes": "claim_domain:routes",
    "explain_collection_workflow_state": "claim_domain:workflow",
    "evaluate_claim_domain_decision": "claim_domain:decision",
    "explain_claim_action_packet": "claim_domain:action_packet",
}
EXPECTED_TOOLS: Final = {
    "ingest_legal_document": "ingest",
    "ingest_ocr_markdown": "ingest",
    "get_ingest_status": "ingest",
    "classify_legal_document": "graph",
    "extract_case_packet": "graph",
    "get_case_graph": "graph",
    "check_case_stop_gates": "stopgate",
    "check_limitation_status": "stopgate",
    "check_attachment_target_rules": "stopgate",
    "summarize_case_ledger": "read",
    "recommend_next_action": "stopgate",
    "list_unknown_document_types": "governance",
    "review_extracted_fact": "governance",
    "promote_ontology_candidate": "governance",
    "reprocess_case": "governance",
    "list_debt_collection_tools": "read",
    "assemble_debtor_documents": "debtor_graph",
    "build_debtor_context_graph": "debtor_graph",
    "get_debtor_graph_snapshot": "debtor_graph",
    "list_debtor_route_candidates": "debtor_graph",
    "explain_debtor_route_candidate": "debtor_graph",
    "list_claim_domain_routes": "claim_domain",
    "explain_collection_workflow_state": "claim_domain",
    "evaluate_claim_domain_decision": "claim_domain",
    "explain_claim_action_packet": "claim_domain",
}
SENSITIVE_SHAPES: Final = (
    re.compile(r"\b\d{6}-\d{7}\b"),
    re.compile(r"\b(?:\+82[-.\s]?)?0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}\b"),
    re.compile(r"(?i)\b(?:account|bank|계좌|은행|입금|송금)[^\n\r]{0,24}?\d{2,6}[-.\s]\d{2,6}[-.\s]\d{2,8}\b"),
)


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
        token_resolver: Callable[[str], AuthContextValue | str] | None = None,
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

    def call(self, tool_name: str, arguments: JsonObject) -> JsonObject:
        return self.registered[tool_name](arguments=arguments)


def mcp_domain_module() -> ModuleType:
    return importlib.import_module("trustgraph_legal.mcp_domain")


def legal_tools_module(module_name: str) -> LegalToolsModule:
    adapter_path = TRUSTGRAPH_MCP_PATH / "trustgraph" / "mcp_server" / "legal_tools.py"
    spec = importlib.util.spec_from_file_location(module_name, adapter_path)
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load legal_tools adapter")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if _is_legal_tools_module(module):
        return module
    raise AssertionError("legal_tools adapter is missing MCP registration attributes")


def claim_domain_adapter_payload(route_ids: tuple[str, ...], fact_handles: tuple[str, ...]) -> JsonObject:
    legal_source_refs = (
        "kr-law-l009290-m268837-a223",
        "kr-law-l009290-m268837-a229",
        "kr-law-l009290-m268837-a246",
        "kr-law-l009930-m267359-a593",
        "kr-law-l010910-m268669-a12",
    )
    return {
        "schema_version": "trustgraph-claim-domain-adapter/v1",
        "domain_ontology_version": "recova-debt-collection-v1@1.0.0",
        "claim_root": {
            "claim_id": "claim:fixture",
            "claim_ref": "claim:fixture",
            "source_refs": ["fixture:source#claim"],
        },
        "fact_handles": [
            {
                "fact_id": "fact:{}".format(fact_handle),
                "claim_id": "claim:fixture",
                "fact_handle": fact_handle,
                "source_refs": ["fixture:source#{}".format(fact_handle)],
            }
            for fact_handle in fact_handles
        ],
        "route_candidates": [
            {
                "route_id": route_id,
                "domain_route_id": route_id,
                "claim_id": "claim:fixture",
                "domain_legal_source_refs": list(legal_source_refs),
                "direct_execution_allowed": False,
                "domain_review_status": "approved_static_v1",
            }
            for route_id in route_ids
        ],
        "source_refs": ["fixture:source#claim", "fixture:source#title"],
        "legal_source_refs": list(legal_source_refs),
        "non_execution_semantics": "adapter_projection_only_human_review_required",
        "pii_profile": {"raw_text_included": False, "source_text_included": False},
    }


def mapping(item: object) -> Mapping[str, object]:
    if isinstance(item, Mapping):
        return item
    if is_dataclass(item) and not isinstance(item, type):
        return asdict(item)
    raise AssertionError(f"tool definition is not mapping-like: {item!r}")


def tool_name(item: object) -> str:
    return str(mapping(item)["tool_name"])


def assert_stable_envelope(response: JsonObject) -> None:
    assert response["schema_version"] == "trustgraph-legal-mcp-tool-response/v1"
    assert response["tool_name"] in EXPECTED_TOOLS
    assert response["group"] == EXPECTED_TOOLS[str(response["tool_name"])]
    assert isinstance(response["scope"], str)
    assert response["scope"].startswith(str(response["group"]))
    pii_profile = json_object(response["pii_profile"])
    redaction = json_object(response["redaction"])
    assert pii_profile["raw_text_included"] is False
    assert pii_profile["source_text_included"] is False
    assert redaction["status"] == "redacted"
    assert isinstance(response["source_refs"], list)
    assert isinstance(response["warnings"], list)
    assert "result" in response


def assert_source_refs_are_redacted(response: JsonObject) -> None:
    serialized = json.dumps(response["source_refs"], ensure_ascii=False)
    assert "excerpt" not in serialized
    assert "text" not in serialized
    assert "raw" not in serialized.lower()


def assert_no_sensitive_shapes(response: JsonObject) -> None:
    serialized = json.dumps(response, ensure_ascii=False)
    for pattern in SENSITIVE_SHAPES:
        assert pattern.search(serialized) is None


def response_by_tool(responses: list[JsonObject], tool_name: str) -> JsonObject:
    for response in responses:
        if response["tool_name"] == tool_name:
            return response
    raise AssertionError(f"missing response for {tool_name}")


def result_object(response: JsonObject) -> JsonObject:
    result = response["result"]
    assert isinstance(result, dict)
    return result


def json_object(value: JsonValue) -> JsonObject:
    assert isinstance(value, dict)
    return value


def object_list(value: JsonValue) -> list[JsonObject]:
    assert isinstance(value, list)
    objects: list[JsonObject] = []
    for item in value:
        assert isinstance(item, dict)
        objects.append(item)
    return objects


def only_object(value: JsonValue) -> JsonObject:
    objects = object_list(value)
    assert len(objects) == 1
    return objects[0]


def _is_legal_tools_module(module: ModuleType) -> TypeGuard[LegalToolsModule]:
    return (
        hasattr(module, "register_debt_collection_brain_tools")
        and hasattr(module, "AuthContext")
        and hasattr(module, "LEGAL_MCP_GATEWAY_SCOPE")
    )
