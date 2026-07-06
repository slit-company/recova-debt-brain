from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Final

import pytest

from tests.utils.legal_mcp_support import (
    EXPECTED_TOOLS,
    FakeMcp,
    REPO_ROOT,
    assert_no_sensitive_shapes as _assert_no_sensitive_shapes,
    assert_source_refs_are_redacted as _assert_source_refs_are_redacted,
    assert_stable_envelope as _assert_stable_envelope,
    legal_tools_module,
    mapping as _mapping,
    mcp_domain_module as _mcp_domain,
    response_by_tool as _response_by_tool,
    result_object as _result_object,
    tool_name as _tool_name,
)
from trustgraph_legal.case_graph import build_case_graph

FIXTURE_MANIFEST: Final = REPO_ROOT / "tests" / "fixtures" / "legal-ocr" / "manifest.json"
ONTOLOGY_PATH: Final = REPO_ROOT / "resources" / "ontologies" / "recova-debt-collection.json"


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
    assert len(listed_tools) == 25
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
    national_id = "900101" + "-1234567"
    phone = "010" + "-1234" + "-5678"
    account = "123" + "-456" + "-7890"
    sensitive_text = "\n".join(
        [
            "Document marker: 지급명령 / 판결 정본",
            "Case number: 2026차전1001",
            "Respondent id: {}".format(national_id),
            "Respondent phone: {}".format(phone),
            "bank account {}".format(account),
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
    _ = outside_graph.write_text(
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
    legal_tools = legal_tools_module("trustgraph_mcp_server_legal_tools_under_test")
    fake_mcp = FakeMcp()
    seen_scopes: list[str] = []
    _ = legal_tools.register_debt_collection_brain_tools(
        fake_mcp,
        repo_root=REPO_ROOT,
        token_resolver=lambda scope: seen_scopes.append(scope) or legal_tools.AuthContext(
            token="todo9-test-token",
            verified_by_gateway=True,
            scopes=(legal_tools.LEGAL_MCP_GATEWAY_SCOPE,),
        ),
    )

    # When: registered tools are inspected and called through MCP context auth.
    registered_names = set(fake_mcp.registered)
    authorized = fake_mcp.call("list_debt_collection_tools", {})

    # Then: all tools are registered, auth is context-only, and the token is not echoed.
    assert registered_names == set(EXPECTED_TOOLS)
    assert authorized["tool_name"] == "list_debt_collection_tools"
    assert seen_scopes == ["read:tools"]
    assert "todo9-test-token" not in json.dumps(authorized, ensure_ascii=False)
    assert "authorization" not in inspect.signature(
        fake_mcp.registered["list_debt_collection_tools"]
    ).parameters
    with pytest.raises(TypeError):
        fake_mcp.registered["list_debt_collection_tools"](
            authorization="Bearer should-not-be-a-tool-argument",
            arguments={},
        )

    raw_token_mcp = FakeMcp()
    _ = legal_tools.register_debt_collection_brain_tools(
        raw_token_mcp,
        repo_root=REPO_ROOT,
        token_resolver=lambda scope: "raw-token-string",
    )
    with pytest.raises(PermissionError, match="gateway auth context"):
        raw_token_mcp.call("list_debt_collection_tools", {})

    read_only_mcp = FakeMcp()
    _ = legal_tools.register_debt_collection_brain_tools(
        read_only_mcp,
        repo_root=REPO_ROOT,
        token_resolver=lambda scope: legal_tools.AuthContext(
            token="read-only-token",
            verified_by_gateway=True,
            scopes=("read:tools",),
        ),
    )
    with pytest.raises(PermissionError, match="required scope"):
        read_only_mcp.call("promote_ontology_candidate", {})

    unauthenticated_mcp = FakeMcp()
    _ = legal_tools.register_debt_collection_brain_tools(
        unauthenticated_mcp,
        repo_root=REPO_ROOT,
    )
    with pytest.raises(PermissionError, match="MCP auth context"):
        unauthenticated_mcp.call("list_debt_collection_tools", {})
