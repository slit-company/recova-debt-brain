from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional

import pytest

from trustgraph_legal.mcp_domain import TOOL_DEFINITIONS, invoke_tool, list_tools


REPO_ROOT = Path(__file__).resolve().parents[3]
TRUSTGRAPH_MCP_PATH = REPO_ROOT / "trustgraph-mcp"
EXPECTED_TOOL_NAMES = [
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
EXPECTED_GROUPS = {"read", "ingest", "graph", "stopgate", "governance", "admin"}
JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | List["JsonValue"] | Dict[str, "JsonValue"]
JsonObject = Dict[str, JsonValue]


class FakeMcp:
    def __init__(self) -> None:
        self.registered: Dict[str, Callable[..., JsonObject]] = {}

    def tool(self, name: Optional[str] = None) -> Callable[[Callable[..., JsonObject]], Callable[..., JsonObject]]:
        def decorate(function: Callable[..., JsonObject]) -> Callable[..., JsonObject]:
            self.registered[name or function.__name__] = function
            return function

        return decorate


def test_tool_contracts_expose_final_todo_9_surface() -> None:
    tools = list_tools()

    assert len(TOOL_DEFINITIONS) == 16
    assert [tool["tool_name"] for tool in tools] == EXPECTED_TOOL_NAMES
    assert [tool["name"] for tool in tools] == EXPECTED_TOOL_NAMES
    assert {tool["group"] for tool in tools} == EXPECTED_GROUPS
    for tool in tools:
        group = tool["group"]
        redaction = tool["redaction"]
        assert tool["schema_version"] == "trustgraph-legal-mcp-tool-contract/v1"
        assert isinstance(group, str)
        assert isinstance(tool["scope"], str)
        assert tool["scope"].startswith("{}:".format(group))
        assert isinstance(tool["input_schema"], dict)
        assert isinstance(tool["output_schema"], dict)
        assert redaction == {
            "default": "redacted",
            "raw_text_included": False,
            "source_text_included": False,
        }


def test_invoke_tool_returns_redacted_stable_response_envelope() -> None:
    sensitive_number = "900101" + "-1234567"
    sensitive_phone = "010" + "-1234" + "-5678"
    text = "\n".join(
        [
            "Document marker: 채권압류 및 추심명령 결정",
            "Third-party debtor: [THIRD_PARTY_ORG]",
            "The court orders attachment",
            "identity: {}".format(sensitive_number),
            "phone: {}".format(sensitive_phone),
        ]
    )

    envelope = invoke_tool(
        "classify_legal_document",
        {"document_id": "doc-sensitive", "source_ref": "fixture:sensitive.md", "text": text},
        REPO_ROOT,
    )
    encoded = json.dumps(envelope, ensure_ascii=False, sort_keys=True)

    assert envelope["schema_version"] == "trustgraph-legal-mcp-tool-response/v1"
    assert envelope["tool_name"] == "classify_legal_document"
    assert envelope["group"] == "read"
    assert envelope["scope"] == "read:documents"
    assert envelope["pii_profile"]["raw_text_included"] is False
    assert envelope["redaction"]["raw_text_included"] is False
    assert "fixture:sensitive.md" in envelope["source_refs"]
    assert sensitive_number not in encoded
    assert sensitive_phone not in encoded
    assert "[NATIONAL_ID_REDACTED]" in encoded
    assert "[PHONE_REDACTED]" in encoded


def test_write_like_tools_are_review_safe_and_non_executing() -> None:
    review = invoke_tool(
        "review_extracted_fact",
        {"fact_id": "fact:test", "decision": "accept", "reviewer": "reviewer:ops"},
        REPO_ROOT,
    )
    recommendation = invoke_tool("recommend_next_action", {}, REPO_ROOT)

    assert review["result"]["status"] == "queued_for_review"
    assert review["result"]["production_graph_modified"] is False
    assert recommendation["result"]["no_direct_filing_contact_or_collection"] is True


def test_register_debt_collection_brain_tools_is_fake_mcp_and_auth_safe() -> None:
    sys.path.insert(0, str(TRUSTGRAPH_MCP_PATH))
    try:
        from trustgraph.mcp_server.legal_tools import register_debt_collection_brain_tools
    finally:
        sys.path.remove(str(TRUSTGRAPH_MCP_PATH))
    fake = FakeMcp()

    registered = register_debt_collection_brain_tools(fake, REPO_ROOT)

    assert [item["tool_name"] for item in registered] == EXPECTED_TOOL_NAMES
    assert list(fake.registered) == EXPECTED_TOOL_NAMES
    with pytest.raises(PermissionError):
        fake.registered["list_debt_collection_tools"](arguments={})
    with pytest.raises(PermissionError):
        fake.registered["list_debt_collection_tools"](
            authorization="Token should-not-work",
            arguments={},
        )
    envelope = fake.registered["list_debt_collection_tools"](
        authorization="Bearer secret-token",
        arguments={},
    )
    encoded = json.dumps(envelope, sort_keys=True)
    assert envelope["tool_name"] == "list_debt_collection_tools"
    assert "secret-token" not in encoded
