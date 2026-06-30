from __future__ import annotations

import importlib
import importlib.util
import inspect
import json
import re
import sys
from dataclasses import asdict, dataclass, field, is_dataclass
from pathlib import Path
from types import ModuleType
from typing import Callable, Final, Mapping, Union

import pytest

REPO_ROOT: Final = Path(__file__).resolve().parents[3]
MCP_PACKAGE_ROOT: Final = REPO_ROOT / "trustgraph-mcp"
if str(MCP_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(MCP_PACKAGE_ROOT))

from trustgraph_legal.case_graph import build_case_graph

JsonScalar = Union[str, int, float, bool, None]
JsonValue = Union[JsonScalar, list["JsonValue"], dict[str, "JsonValue"]]
JsonObject = dict[str, JsonValue]
ToolCallable = Callable[..., JsonObject]

FIXTURE_MANIFEST: Final = REPO_ROOT / "tests" / "fixtures" / "legal-ocr" / "manifest.json"
ONTOLOGY_PATH: Final = REPO_ROOT / "resources" / "ontologies" / "recova-debt-collection.json"
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
}
SENSITIVE_SHAPES: Final = (
    re.compile(r"\b\d{6}-\d{7}\b"),
    re.compile(r"\b(?:\+82[-.\s]?)?0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}\b"),
    re.compile(
        r"(?i)\b(?:account|bank|계좌|은행|입금|송금)[^\n\r]{0,24}?"
        r"\d{2,6}[-.\s]\d{2,6}[-.\s]\d{2,8}\b"
    ),
)


@dataclass(slots=True)
class FakeMcp:
    registered: dict[str, ToolCallable] = field(default_factory=dict)

    def tool(self, name: str | None = None) -> Callable[[ToolCallable], ToolCallable]:
        def decorator(func: ToolCallable) -> ToolCallable:
            tool_name = name if name is not None else func.__name__
            self.registered[tool_name] = func
            return func

        return decorator

    def call(
        self,
        tool_name: str,
        arguments: JsonObject,
    ) -> JsonObject:
        return self.registered[tool_name](arguments=arguments)


def test_todo_9_tools_publish_stable_contracts() -> None:
    # Given: the Todo 9 MCP domain-brain public registry.
    mcp_domain = _mcp_domain()
    definitions = {_tool_name(item): _mapping(item) for item in mcp_domain.TOOL_DEFINITIONS}
    listed_tools = {str(item["tool_name"]): item for item in mcp_domain.list_tools()}

    # When: required debt-collection tool contracts are inspected.
    definition_names = set(definitions)
    listed_names = set(listed_tools)

    # Then: every required tool has stable schema, group, scope, and JSON shapes.
    assert definition_names == set(EXPECTED_TOOLS)
    assert listed_names == set(EXPECTED_TOOLS)
    assert len(listed_tools) == 16
    for tool_name, group in EXPECTED_TOOLS.items():
        contract = listed_tools[tool_name]
        assert contract["schema_version"] == "trustgraph-legal-mcp-tool-contract/v1"
        assert contract["tool_name"] == tool_name
        assert contract["group"] == group
        assert isinstance(contract["scope"], str)
        assert contract["scope"].startswith(group)
        assert contract["input_schema"]
        assert contract["output_schema"]
        assert contract["redaction"]["default"] == "redacted"
        assert contract["redaction"]["raw_text_included"] is False
        assert "callable" not in contract


def test_todo_9_tool_calls_return_redacted_source_grounded_json(tmp_path: Path) -> None:
    # Given: synthetic legal OCR fixtures and a sensitive ad-hoc document.
    mcp_domain = _mcp_domain()
    sensitive_text = "\n".join(
        [
            "Document marker: 지급명령 / 판결 정본",
            "Case number: 2026차전1001",
            "Respondent id: 900101-1234567",
            "Respondent phone: 010-1234-5678",
            "bank account 123-456-7890",
        ]
    )
    case_graph = build_case_graph(FIXTURE_MANIFEST, REPO_ROOT).to_json()

    # When: representative Todo 9 tools are called through the public dispatcher.
    responses = [
        mcp_domain.invoke_tool(
            "list_debt_collection_tools",
            repo_root=REPO_ROOT,
        ),
        mcp_domain.invoke_tool(
            "classify_legal_document",
            {
                "document_id": "doc:sensitive",
                "source_ref": "fixture:sensitive.md",
                "text": sensitive_text,
            },
            repo_root=REPO_ROOT,
        ),
        mcp_domain.invoke_tool(
            "extract_case_packet",
            {
                "manifest_path": str(FIXTURE_MANIFEST),
            },
            repo_root=REPO_ROOT,
        ),
        mcp_domain.invoke_tool(
            "check_case_stop_gates",
            {
                "case_graph": case_graph,
            },
            repo_root=REPO_ROOT,
        ),
        mcp_domain.invoke_tool(
            "list_unknown_document_types",
            {
                "manifest_path": str(FIXTURE_MANIFEST),
                "ontology_path": str(ONTOLOGY_PATH),
            },
            repo_root=REPO_ROOT,
        ),
    ]

    # Then: outputs keep the stable MCP envelope and never leak raw PII.
    for response in responses:
        _assert_stable_envelope(response)
        _assert_source_refs_are_redacted(response)
        _assert_no_sensitive_shapes(response)

    stopgate = _response_by_tool(responses, "check_case_stop_gates")
    result = _result_object(stopgate)
    assert isinstance(result["case_id"], str)
    assert result["decision"] in {"가능", "불가능", "보류"}
    assert result["risk_flags"]
    assert result["source_refs"]

    secret = "c-review-secret-value"
    outside_graph = tmp_path / "c-review-secret.json"
    outside_graph.write_text(
        json.dumps({"case_packets": [], "secret": secret}),
        encoding="utf-8",
    )
    rejected = mcp_domain.invoke_tool(
        "get_case_graph",
        {"case_graph_path": str(outside_graph)},
        repo_root=REPO_ROOT,
    )
    rejected_encoded = json.dumps(rejected, ensure_ascii=False, sort_keys=True)
    _assert_stable_envelope(rejected)
    assert rejected["result"] == {"status": "rejected", "reason": "path_outside_repo_root"}
    assert rejected["warnings"] == ["path_outside_repo_root"]
    assert secret not in rejected_encoded
    assert str(outside_graph) not in rejected_encoded


def test_mcp_registration_requires_bearer_token_without_mcp_sdk() -> None:
    # Given: a fake MCP object registered through the thin adapter.
    legal_tools = _legal_tools_adapter()
    fake_mcp = FakeMcp()
    legal_tools.register_debt_collection_brain_tools(
        fake_mcp,
        repo_root=REPO_ROOT,
        token_resolver=lambda: "todo9-test-token",
    )

    # When: registered tools are inspected and called through MCP context auth.
    registered_names = set(fake_mcp.registered)
    authorized = fake_mcp.call("list_debt_collection_tools", {})

    # Then: all tools are registered, auth is context-only, and the token is not echoed.
    assert registered_names == set(EXPECTED_TOOLS)
    assert authorized["tool_name"] == "list_debt_collection_tools"
    assert "todo9-test-token" not in json.dumps(authorized, ensure_ascii=False)
    assert "authorization" not in inspect.signature(
        fake_mcp.registered["list_debt_collection_tools"]
    ).parameters
    with pytest.raises(TypeError):
        fake_mcp.registered["list_debt_collection_tools"](
            authorization="Bearer should-not-be-a-tool-argument",
            arguments={},
        )

    unauthenticated_mcp = FakeMcp()
    legal_tools.register_debt_collection_brain_tools(
        unauthenticated_mcp,
        repo_root=REPO_ROOT,
    )
    with pytest.raises(PermissionError, match="MCP auth context"):
        unauthenticated_mcp.call("list_debt_collection_tools", {})


def _mcp_domain() -> ModuleType:
    try:
        return importlib.import_module("trustgraph_legal.mcp_domain")
    except ModuleNotFoundError as exc:
        raise AssertionError(
            "Todo 9 contract gap: missing trustgraph_legal.mcp_domain"
        ) from exc


def _legal_tools_adapter() -> ModuleType:
    adapter_path = MCP_PACKAGE_ROOT / "trustgraph" / "mcp_server" / "legal_tools.py"
    if not adapter_path.exists():
        raise AssertionError(
            "Todo 9 contract gap: missing trustgraph-mcp/trustgraph/mcp_server/legal_tools.py"
        )
    spec = importlib.util.spec_from_file_location(
        "trustgraph_mcp_server_legal_tools_under_test",
        adapter_path,
    )
    if spec is None or spec.loader is None:
        raise AssertionError("Todo 9 contract gap: cannot load legal_tools adapter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _mapping(item: object) -> Mapping[str, object]:
    if isinstance(item, Mapping):
        return item
    if is_dataclass(item):
        return asdict(item)
    raise AssertionError(f"tool definition is not mapping-like: {item!r}")


def _tool_name(item: object) -> str:
    mapped = _mapping(item)
    return str(mapped["tool_name"])


def _assert_stable_envelope(response: JsonObject) -> None:
    assert response["schema_version"] == "trustgraph-legal-mcp-tool-response/v1"
    assert response["tool_name"] in EXPECTED_TOOLS
    assert response["group"] == EXPECTED_TOOLS[str(response["tool_name"])]
    assert isinstance(response["scope"], str)
    assert response["scope"].startswith(str(response["group"]))
    assert response["pii_profile"]["raw_text_included"] is False
    assert response["pii_profile"]["source_text_included"] is False
    assert response["redaction"]["status"] == "redacted"
    assert isinstance(response["source_refs"], list)
    assert isinstance(response["warnings"], list)
    assert "result" in response


def _assert_source_refs_are_redacted(response: JsonObject) -> None:
    serialized = json.dumps(response["source_refs"], ensure_ascii=False)
    assert "excerpt" not in serialized
    assert "text" not in serialized
    assert "raw" not in serialized.lower()


def _assert_no_sensitive_shapes(response: JsonObject) -> None:
    serialized = json.dumps(response, ensure_ascii=False)
    for pattern in SENSITIVE_SHAPES:
        assert pattern.search(serialized) is None


def _response_by_tool(responses: list[JsonObject], tool_name: str) -> JsonObject:
    for response in responses:
        if response["tool_name"] == tool_name:
            return response
    raise AssertionError(f"missing response for {tool_name}")


def _result_object(response: JsonObject) -> JsonObject:
    result = response["result"]
    assert isinstance(result, dict)
    return result
