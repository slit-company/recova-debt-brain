from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union

from trustgraph_legal.stop_gates import RULES_PATH, evaluate_case_graph, load_rule_source


REPO_ROOT = Path(__file__).resolve().parents[3]
TASK_6_CASE = (
    Path("/Users/cosmos/dev/ontology/trustgraph")
    / ".omo"
    / "evidence"
    / "debt-collection-ontology"
    / "task-6-case-graph.json"
)
JsonScalar = Union[str, int, float, bool, type(None)]
JsonValue = Union[JsonScalar, List["JsonValue"], Dict[str, "JsonValue"]]


def test_task_6_case_returns_hold_with_static_rule_refs() -> None:
    # Given: the Todo 6 case graph built from redacted legal OCR fixtures.
    graph = json.loads(TASK_6_CASE.read_text(encoding="utf-8"))

    # When: the deterministic StopGate engine evaluates the packet.
    payload = evaluate_case_graph(graph).to_json()
    reason_codes = {gate["reason_code"] for gate in payload["stop_gates"]}

    # Then: the result is a sourced hold, not an execution result or LLM conclusion.
    assert payload["decision"] == "보류"
    assert payload["rule_source"]["review_status"] == "approved"
    assert payload["pii_profile"]["raw_text_included"] is False
    assert reason_codes >= {
        "discharge_proceeding_detected",
        "limitation_risk",
        "exempt_claim_targeted",
        "amount_mismatch",
    }
    assert payload["source_refs"]
    assert all("excerpt" not in ref and "text" not in ref for ref in payload["source_refs"])
    assert all(ref["rule_id"].startswith("dc-stopgate-v0-") for ref in payload["rule_refs"])


def test_execution_clause_and_assignment_chain_have_red_green_coverage() -> None:
    # Given: a graph with a title and assignment packet but missing execution clause and chain proof.
    graph = _graph(
        _document("doc:title", "payment-order"),
        _document("doc:assignment", "assignment-succession"),
        _field("field:case", "court_case_number"),
    )

    # When: the packet is checked before and after adding the required proof.
    blocked = evaluate_case_graph(graph).to_json()
    graph["case_packets"][0]["entities"].extend(
        [
            _field("field:execution", "execution_clause_status", "granted"),
            _field("field:notice", "notice_status", "notice completed"),
            _field("field:succession", "succession_authority", "succession clause"),
            _field("field:limitation", "limitation_cleared", "reviewed"),
        ]
    )
    cleared = evaluate_case_graph(graph).to_json()

    # Then: both StopGates disappear only when their source-backed proof exists.
    blocked_codes = {gate["reason_code"] for gate in blocked["stop_gates"]}
    cleared_codes = {gate["reason_code"] for gate in cleared["stop_gates"]}
    assert {"missing_execution_clause", "assignment_chain_broken"} <= blocked_codes
    assert "missing_execution_clause" not in cleared_codes
    assert "assignment_chain_broken" not in cleared_codes


def test_discharge_exemption_limitation_amount_and_identity_red_green_coverage() -> None:
    # Given: a graph with insolvency, exemption review, mismatched amounts, stale limitation, and identity uncertainty.
    graph = _graph(
        _document("doc:title", "payment-order"),
        _document("doc:service", "service-finality-proof"),
        _document("doc:insolvency", "insolvency-credit-recovery"),
        _field("field:execution", "execution_clause_status", "granted"),
        _field("field:claim", "claim_amount", "KRW 1000", amount_kind="claim_amount"),
        _field("field:principal", "principal_amount", "KRW 2000", amount_kind="principal_amount"),
        _legal_check("check:procedure", "procedure_status"),
        _legal_check("check:exemption", "exemption_review_status"),
        findings=[_finding("identity_uncertain")],
    )

    # When: risky facts are evaluated, then replaced with clearing evidence.
    blocked = evaluate_case_graph(graph).to_json()
    graph = _graph(
        _document("doc:title", "payment-order"),
        _document("doc:service", "service-finality-proof"),
        _field("field:execution", "execution_clause_status", "granted"),
        _field("field:limitation", "limitation_cleared", "reviewed"),
        _field("field:claim", "claim_amount", "KRW 1000", amount_kind="claim_amount"),
        _field("field:principal", "principal_amount", "KRW 1000", amount_kind="principal_amount"),
    )
    cleared = evaluate_case_graph(graph).to_json()

    # Then: every acceptance-required reason has both a hit and a non-hit case.
    blocked_codes = {gate["reason_code"] for gate in blocked["stop_gates"]}
    cleared_codes = {gate["reason_code"] for gate in cleared["stop_gates"]}
    assert {
        "discharge_proceeding_detected",
        "exempt_claim_targeted",
        "limitation_risk",
        "amount_mismatch",
        "identity_uncertain",
    } <= blocked_codes
    assert {
        "discharge_proceeding_detected",
        "exempt_claim_targeted",
        "limitation_risk",
        "amount_mismatch",
        "identity_uncertain",
    }.isdisjoint(cleared_codes)
    assert cleared["decision"] == "가능"


def test_invalid_blocking_fact_without_provenance_is_flagged() -> None:
    # Given: the Todo 6 graph with a blocking legal-check fact missing its source span.
    graph = json.loads(TASK_6_CASE.read_text(encoding="utf-8"))
    packet = graph["case_packets"][0]
    for entity in packet["entities"]:
        if entity.get("reason") == "procedure_status":
            entity["provenance"].pop("source_ref")
            break

    # When: StopGates are evaluated.
    payload = evaluate_case_graph(graph).to_json()
    reason_codes = {gate["reason_code"] for gate in payload["stop_gates"]}

    # Then: the missing provenance is itself a deterministic StopGate.
    assert "invalid_fact_without_provenance" in reason_codes
    assert "invalid_fact_without_provenance" in payload["risk_flags"]


def test_placeholder_missing_provenance_is_invalid() -> None:
    # Given: case_graph-style placeholder provenance on a legal-risk amount fact.
    graph = _graph(
        _document("doc:title", "payment-order"),
        _field("field:execution", "execution_clause_status", "granted"),
        _field("field:claim", "claim_amount", "KRW 1000", amount_kind="claim_amount"),
    )
    graph["case_packets"][0]["entities"][2]["provenance"]["source_ref"] = "missing"

    # When: the engine evaluates the graph.
    payload = evaluate_case_graph(graph).to_json()

    # Then: placeholder provenance is not accepted as source-backed evidence.
    assert "invalid_fact_without_provenance" in {
        gate["reason_code"] for gate in payload["stop_gates"]
    }


def test_unapproved_rule_source_blocks_production_clearance(tmp_path: Path) -> None:
    # Given: the approved static rule source copied into a draft state.
    draft_rules_path = tmp_path / "draft-rules.json"
    rule_json = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    rule_json["review_status"] = "draft"
    draft_rules_path.write_text(json.dumps(rule_json, ensure_ascii=False), encoding="utf-8")
    rule_source = load_rule_source(draft_rules_path)
    graph = _graph(
        _document("doc:title", "payment-order"),
        _document("doc:service", "service-finality-proof"),
        _field("field:execution", "execution_clause_status", "granted"),
        _field("field:limitation", "limitation_cleared", "reviewed"),
        _field("field:claim", "claim_amount", "KRW 1000", amount_kind="claim_amount"),
        _field("field:principal", "principal_amount", "KRW 1000", amount_kind="principal_amount"),
    )

    # When: the otherwise clear graph is evaluated with the draft rule source.
    payload = evaluate_case_graph(graph, rule_source).to_json()

    # Then: unapproved rules cannot clear production StopGates.
    assert payload["decision"] == "보류"
    assert "rule-source-unapproved" in payload["risk_flags"]


def test_broader_v0_document_types_are_supported_or_explicitly_reviewed() -> None:
    # Given: broader contract document types that current extraction may not emit yet.
    graph = _graph(
        _document("doc:judgment", "judgment-or-decision"),
        _document("doc:priority", "attachment-target-priority"),
        _document("doc:rule", "legal-rule-source"),
        _field("field:execution", "execution_clause_status", "granted"),
        _field("field:limitation", "limitation_cleared", "reviewed"),
        _field("field:principal", "principal_amount", "KRW 1000", amount_kind="principal_amount"),
        _field("field:claim", "claim_amount", "KRW 1000", amount_kind="claim_amount"),
    )

    # When: supported broader types are checked, then an unknown type is introduced.
    supported = evaluate_case_graph(graph).to_json()
    graph["case_packets"][0]["entities"].append(_document("doc:unknown", "unknown"))
    reviewed = evaluate_case_graph(graph).to_json()

    # Then: supported broader types do not create a false unsupported-state pass, but unknowns do.
    supported_codes = {gate["reason_code"] for gate in supported["stop_gates"]}
    reviewed_codes = {gate["reason_code"] for gate in reviewed["stop_gates"]}
    assert "unsupported_document_type_review" not in supported_codes
    assert "exempt_claim_targeted" in supported_codes
    assert "unknown_document_type" in reviewed_codes


def test_check_cli_prints_case_decision_json() -> None:
    # Given: the public Todo 7 module invocation contract.
    command = [
        sys.executable,
        "-m",
        "trustgraph_legal.check",
        "--case",
        str(TASK_6_CASE),
    ]

    # When: the CLI evaluates the case graph.
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    # Then: the observable CLI surface returns the deterministic hold.
    assert result.returncode == 0
    assert payload["decision"] == "보류"
    assert payload["case_packet_ids"] == ["case-packet-id-be706068d3a4571b0720"]


def _graph(*entities: Dict[str, JsonValue], findings: Optional[List[Dict[str, JsonValue]]] = None) -> Dict[str, JsonValue]:
    return {
        "schema_version": "trustgraph-legal-case-graph/v1",
        "case_packets": [
            {
                "id": "case:test",
                "entities": list(entities),
                "edges": [],
                "findings": [] if findings is None else findings,
                "evidence_keys": [],
            }
        ],
    }


def _document(identifier: str, document_type: str) -> Dict[str, JsonValue]:
    return {
        "id": identifier,
        "entity_type": "Document",
        "ontology_class": "legal-document",
        "value": document_type,
        "provenance": _provenance(identifier, "manifest"),
    }


def _field(
    identifier: str,
    field_name: str,
    value: str = "present",
    amount_kind: Optional[str] = None,
) -> Dict[str, JsonValue]:
    payload = {
        "id": identifier,
        "entity_type": "SourceSpan",
        "ontology_class": "source-span",
        "value": value,
        "field_name": field_name,
        "provenance": _provenance(identifier, "line-1", field_name),
    }
    if amount_kind is not None:
        payload["ontology_class"] = "amount"
        payload["amount_kind"] = amount_kind
    return payload


def _legal_check(identifier: str, reason: str) -> Dict[str, JsonValue]:
    return {
        "id": identifier,
        "entity_type": "RuleFinding",
        "ontology_class": "legal-check",
        "value": "review required",
        "reason": reason,
        "provenance": _provenance(identifier, "line-2", reason),
    }


def _finding(reason: str) -> Dict[str, JsonValue]:
    return {
        "reason": reason,
        "severity": "review",
        "provenance": _provenance("finding:{}".format(reason), "line-3", reason),
    }


def _provenance(identifier: str, chunk_id: str, field_name: Optional[str] = None) -> Dict[str, JsonValue]:
    payload = {
        "document_id": "doc-for-{}".format(identifier),
        "source_ref": "fixture:{}".format(identifier),
        "chunk_id": chunk_id,
        "line_start": 1,
        "line_end": 1,
        "confidence": 0.91,
        "extractor_version": "test",
        "source_module": "test_stop_gates",
    }
    if field_name is not None:
        payload["field_name"] = field_name
    return payload
