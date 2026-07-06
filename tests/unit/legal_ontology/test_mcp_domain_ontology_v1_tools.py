from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from tests.utils.legal_mcp_support import (
    CLAIM_DOMAIN_TOOL_SCOPES,
    EXPECTED_21_TOOL_NAMES,
    FakeMcp,
    REPO_ROOT,
    claim_domain_adapter_payload,
    legal_tools_module,
    object_list,
    only_object,
    result_object,
)
from trustgraph_legal.mcp_domain import invoke_tool, list_tools


def test_claim_domain_tools_append_after_existing_mcp_tools() -> None:
    # Given: the public MCP tool registry.
    tools = list_tools()

    # When: claim-domain v1 tools are inspected by MCP clients.
    names = [str(tool["tool_name"]) for tool in tools]
    claim_domain_tools = {str(tool["tool_name"]): tool for tool in tools[21:]}

    # Then: the existing 21 tools remain first and four claim-domain tools append.
    assert names[:21] == EXPECTED_21_TOOL_NAMES
    assert names[21:] == list(CLAIM_DOMAIN_TOOL_SCOPES)
    assert len(tools) == 25
    for tool_name, scope in CLAIM_DOMAIN_TOOL_SCOPES.items():
        tool = claim_domain_tools[tool_name]
        parameters = tool["parameters"]
        assert isinstance(parameters, list)
        parameter_names = {item for item in parameters if isinstance(item, str)}
        assert tool["group"] == "claim_domain"
        assert tool["scope"] == scope
        assert "authorization" not in parameter_names
        assert "token" not in parameter_names
        assert "bearer" not in parameter_names


def test_fake_mcp_claim_domain_tools_use_context_auth_only() -> None:
    # Given: the thin MCP adapter registered into an SDK-free fake MCP object.
    legal_tools = legal_tools_module("trustgraph_mcp_server_legal_tools_task_12")
    fake = FakeMcp()
    seen_scopes: list[str] = []
    _ = legal_tools.register_debt_collection_brain_tools(
        fake,
        REPO_ROOT,
        token_resolver=lambda scope: seen_scopes.append(scope) or legal_tools.AuthContext(
            token="task-12-context-token",
            verified_by_gateway=True,
            scopes=(legal_tools.LEGAL_MCP_GATEWAY_SCOPE,),
        ),
    )

    # When: a claim-domain route tool is called through MCP context auth.
    envelope = fake.registered["list_claim_domain_routes"](arguments={})

    # Then: auth stayed outside public tool arguments and the token is not echoed.
    encoded = json.dumps(envelope, ensure_ascii=False, sort_keys=True)
    assert envelope["tool_name"] == "list_claim_domain_routes"
    assert seen_scopes == ["claim_domain:routes"]
    assert "task-12-context-token" not in encoded
    assert "authorization" not in inspect.signature(
        fake.registered["list_claim_domain_routes"]
    ).parameters
    with pytest.raises(TypeError):
        _ = fake.registered["list_claim_domain_routes"](
            authorization="Bearer task-12-public-token",
            arguments={},
        )

    unauthenticated = FakeMcp()
    _ = legal_tools.register_debt_collection_brain_tools(unauthenticated, REPO_ROOT)
    with pytest.raises(PermissionError, match="MCP auth context"):
        _ = unauthenticated.registered["list_claim_domain_routes"](arguments={})


def test_claim_domain_tools_return_advisory_redacted_envelopes() -> None:
    # Given: a PII-safe claim-domain adapter payload and the four read/explain tools.
    payload = claim_domain_adapter_payload(
        ("bank_account_attachment",),
        ("enforceable_title", "financial_account_hint"),
    )

    # When: the new claim-domain tools are called through the SDK-independent dispatcher.
    envelopes = [
        invoke_tool("list_claim_domain_routes", repo_root=REPO_ROOT),
        invoke_tool(
            "explain_collection_workflow_state",
            {"state_id": "execution_route_selection"},
            REPO_ROOT,
        ),
        invoke_tool(
            "evaluate_claim_domain_decision",
            {"claim_domain_payload": payload, "workflow_state": "execution_route_selection"},
            REPO_ROOT,
        ),
        invoke_tool(
            "explain_claim_action_packet",
            {"packet_type": "legal_action_review"},
            REPO_ROOT,
        ),
    ]

    # Then: every result is a redacted, source-grounded, non-executing MCP envelope.
    for envelope in envelopes:
        encoded = json.dumps(envelope, ensure_ascii=False, sort_keys=True)
        assert envelope["schema_version"] == "trustgraph-legal-mcp-tool-response/v1"
        assert envelope["group"] == "claim_domain"
        assert '"raw_text":' not in encoded
        assert str(REPO_ROOT) not in encoded
        assert '"filing_destination":' not in encoded
        assert '"debtor_contact_payload":' not in encoded
        result = envelope["result"]
        assert isinstance(result, dict)
        assert result["non_execution_semantics"] == "advisory_only_human_review_required"

    routes = result_object(envelopes[0])
    assert routes["route_count"] == 32
    assert object_list(routes["routes"])

    workflow = result_object(envelopes[1])
    assert workflow["state_id"] == "execution_route_selection"
    assert workflow["route_link_semantics"] == "workflow_precondition_only_no_route_decision_logic"

    decision = result_object(envelopes[2])
    assert decision["schema_version"] == "trustgraph-claim-domain-decision/v1"
    route_decision = only_object(decision["route_decisions"])
    assert route_decision["route_id"] == "bank_account_attachment"
    assert route_decision["status"] == "possible"

    packet = result_object(envelopes[3])
    assert packet["packet_type"] == "legal_action_review"
    assert packet["direct_execution_allowed"] is False


def test_claim_domain_path_failures_are_redacted(tmp_path: Path) -> None:
    # Given: a path outside the registered repository root containing sensitive text.
    secret = "task-12-outside-root-secret"
    outside_routes = tmp_path / "secret-routes.json"
    _ = outside_routes.write_text(json.dumps({"secret": secret}), encoding="utf-8")

    # When: a claim-domain MCP tool receives the out-of-bounds path.
    envelope = invoke_tool(
        "list_claim_domain_routes",
        {"routes_path": str(outside_routes)},
        REPO_ROOT,
    )

    # Then: the failure envelope does not leak file content or local path details.
    encoded = json.dumps(envelope, ensure_ascii=False, sort_keys=True)
    assert envelope["result"] == {"status": "rejected", "reason": "path_outside_repo_root"}
    assert envelope["warnings"] == ["path_outside_repo_root"]
    assert secret not in encoded
    assert str(outside_routes) not in encoded
