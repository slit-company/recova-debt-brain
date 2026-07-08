from __future__ import annotations

from trustgraph_legal.legal_workflow_checkpoints import evaluate_legal_workflow_checkpoints
from trustgraph_legal.stop_gates_domain_v1 import evaluate_domain_v1_case_graph
from trustgraph_legal.stopgate_types import JsonObject, JsonValue


def test_missing_title_routes_to_title_acquisition_loop() -> None:
    # Given: a case with limitation cleared but no enforceable title document.
    graph = _graph(
        _document("doc:intake", "identity-evidence"),
        _field("field:limitation", "limitation_cleared", "reviewed"),
        _field("field:claim", "claim_amount", "KRW 1000", amount_kind="claim_amount"),
        _field("field:principal", "principal_amount", "KRW 1000", amount_kind="principal_amount"),
    )
    stopgate_payload = evaluate_domain_v1_case_graph(graph)

    # When: the legal workflow checkpoint adapter consumes the reviewed StopGate result.
    checkpoints = evaluate_legal_workflow_checkpoints(stopgate_payload).to_json()

    # Then: the workflow-facing output sends the operator to title acquisition.
    title = _checkpoint(checkpoints, "enforcement_title")
    assert checkpoints["schema_version"] == "trustgraph-legal-workflow-checkpoints/v1"
    assert checkpoints["overall_status"] == "hold"
    assert title["status"] == "missing"
    assert title["workflow_gate"] == "title_acquisition_loop"
    assert "missing_enforcement_title" in _string_list(title["reason_codes"])
    assert checkpoints["non_execution_semantics"] == "advisory_only_human_review_required"


def test_missing_service_finality_execution_clause_routes_to_legal_review() -> None:
    # Given: an enforceable title exists, but execution precondition proof is absent.
    graph = _graph(
        _document("doc:title", "payment-order"),
        _field("field:limitation", "limitation_cleared", "reviewed"),
        _field("field:claim", "claim_amount", "KRW 1000", amount_kind="claim_amount"),
        _field("field:principal", "principal_amount", "KRW 1000", amount_kind="principal_amount"),
    )
    stopgate_payload = evaluate_domain_v1_case_graph(graph)

    # When: workflow checkpoints are derived from the StopGate surface.
    checkpoints = evaluate_legal_workflow_checkpoints(stopgate_payload).to_json()

    # Then: service, finality, and execution clause stay in legal-precondition review.
    precondition_ids = {
        "service_proof",
        "finality_proof",
        "execution_clause",
    }
    for checkpoint_id in precondition_ids:
        checkpoint = _checkpoint(checkpoints, checkpoint_id)
        assert checkpoint["status"] == "missing"
        assert checkpoint["workflow_gate"] == "legal_precondition_review"
        assert "missing_service_finality_execution_clause_proof" in _string_list(checkpoint["reason_codes"])


def test_limitation_ambiguity_routes_to_review_hold() -> None:
    # Given: title and execution preconditions exist, but limitation clearance is absent.
    graph = _graph(
        _document("doc:title", "payment-order"),
        _document("doc:service", "service-finality-proof"),
        _field("field:execution", "execution_clause_status", "granted"),
        _field("field:service", "service_status", "served"),
        _field("field:finality", "finality_status", "final"),
        _field("field:claim", "claim_amount", "KRW 1000", amount_kind="claim_amount"),
        _field("field:principal", "principal_amount", "KRW 1000", amount_kind="principal_amount"),
    )
    stopgate_payload = evaluate_domain_v1_case_graph(graph)

    # When: the adapter maps legal StopGates to workflow gates.
    checkpoints = evaluate_legal_workflow_checkpoints(stopgate_payload).to_json()

    # Then: limitation ambiguity remains a review hold and is not cleared by inference.
    limitation = _checkpoint(checkpoints, "limitation")
    assert checkpoints["overall_status"] == "hold"
    assert limitation["status"] == "review_required"
    assert limitation["workflow_gate"] == "limitation_review_hold"
    assert limitation["cleared_by"] == "static_stopgate_result_only"


def test_protected_asset_signal_blocks_enforcement_readiness() -> None:
    # Given: an otherwise mature case targets protected public-benefit material.
    graph = _graph(
        _document("doc:title", "payment-order"),
        _document("doc:service", "service-finality-proof"),
        _field("field:execution", "execution_clause_status", "granted"),
        _field("field:service", "service_status", "served"),
        _field("field:finality", "finality_status", "final"),
        _field("field:limitation", "limitation_cleared", "reviewed"),
        _field("field:protected", "protected_benefit_signal", "protected public benefit"),
        _field("field:claim", "claim_amount", "KRW 1000", amount_kind="claim_amount"),
        _field("field:principal", "principal_amount", "KRW 1000", amount_kind="principal_amount"),
    )
    stopgate_payload = evaluate_domain_v1_case_graph(graph)

    # When: legal workflow checkpoints are generated.
    checkpoints = evaluate_legal_workflow_checkpoints(stopgate_payload).to_json()

    # Then: protected-asset review blocks enforcement readiness.
    protected_asset = _checkpoint(checkpoints, "insolvency_or_protected_asset")
    assert protected_asset["status"] == "blocked"
    assert protected_asset["workflow_gate"] == "protected_asset_review_hold"
    assert protected_asset["blocks_enforcement_readiness"] is True
    assert checkpoints["ready_for_enforcement_advisory"] is False


def _checkpoint(payload: JsonObject, checkpoint_id: str) -> JsonObject:
    checkpoints = payload["checkpoints"]
    assert isinstance(checkpoints, list)
    for item in checkpoints:
        assert isinstance(item, dict)
        if item.get("checkpoint_id") == checkpoint_id:
            return item
    raise AssertionError("missing checkpoint {}".format(checkpoint_id))


def _string_list(value: JsonValue) -> list[str]:
    assert isinstance(value, list)
    items: list[str] = []
    for item in value:
        assert isinstance(item, str)
        items.append(item)
    return items


def _graph(*entities: JsonObject) -> JsonObject:
    return {
        "schema_version": "trustgraph-legal-case-graph/v1",
        "case_packets": [
            {
                "id": "case:legal-workflow",
                "entities": list(entities),
                "edges": [],
                "findings": [],
                "evidence_keys": [],
            }
        ],
    }


def _document(identifier: str, document_type: str) -> JsonObject:
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
    amount_kind: str | None = None,
) -> JsonObject:
    payload: JsonObject = {
        "id": identifier,
        "entity_type": "SourceSpan",
        "ontology_class": "source-span",
        "value": value,
        "field_name": field_name,
        "provenance": _provenance(identifier, "field", field_name),
    }
    if amount_kind is not None:
        payload["ontology_class"] = "amount"
        payload["amount_kind"] = amount_kind
    return payload


def _provenance(identifier: str, chunk_id: str, field_name: str | None = None) -> JsonObject:
    payload: JsonObject = {
        "document_id": "doc-for-{}".format(identifier),
        "source_ref": "fixture:{}".format(identifier),
        "chunk_id": chunk_id,
        "line_start": 1,
        "line_end": 1,
        "confidence": 0.91,
        "extractor_version": "test",
        "source_module": "test_legal_workflow_checkpoints_v1",
    }
    if field_name is not None:
        payload["field_name"] = field_name
    return payload
