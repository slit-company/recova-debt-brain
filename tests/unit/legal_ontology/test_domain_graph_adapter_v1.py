from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from trustgraph_legal.debtor_context import build_debtor_context
from trustgraph_legal.debtor_governance import build_debtor_governance_payload
from trustgraph_legal.document_assembly import build_document_assembly
from trustgraph_legal.domain_graph_adapter import (
    DomainGraphAdapterError,
    adapt_debtor_graph_to_claim_domain,
)
from trustgraph_legal.route_candidates import evaluate_route_candidates
from trustgraph_legal.stop_gates_domain_v1 import evaluate_domain_v1_case_graph

REPO_ROOT = Path(__file__).resolve().parents[3]
PAGES_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "legal-ocr-pages"
JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject = dict[str, JsonValue]


def test_adapter_maps_debtor_graph_to_claim_domain_without_raw_text() -> None:
    # Given: an existing DebtorContextGraph with v0 route candidates and governance records.
    graph = _route_ready_graph()
    governance = build_debtor_governance_payload(graph)
    original_graph = graph.to_json()

    # When: the compatibility adapter projects it into claim-domain v1 handles.
    payload = adapt_debtor_graph_to_claim_domain(graph, governance_records=governance.records).to_json()
    claim_root = _object_value(payload["claim_root"])
    snapshot = _object_value(payload["graph_snapshot"])
    fact_handles = _object_list(payload["fact_handles"])
    routes = _object_list(payload["route_candidates"])
    records = _object_list(payload["governance_records"])

    # Then: graph identity and source-bundle metadata are preserved at the claim root.
    assert payload["schema_version"] == "trustgraph-claim-domain-adapter/v1"
    assert payload["domain_ontology_version"] == "recova-debt-collection-v1@1.0.0"
    assert payload["debtor_graph_id"] == graph.debtor_graph_id
    assert payload["graph_snapshot_id"] == graph.graph_snapshot.graph_snapshot_id
    assert payload["source_bundle_hash"] == graph.graph_snapshot.source_bundle_hash
    assert claim_root["ontology_class"] == "Claim"
    assert claim_root["runtime_memory_root"] == "DebtorContextGraph"
    assert claim_root["debtor_graph_id"] == graph.debtor_graph_id
    assert claim_root["graph_snapshot_id"] == graph.graph_snapshot.graph_snapshot_id
    assert claim_root["source_bundle_hash"] == graph.graph_snapshot.source_bundle_hash
    assert snapshot["graph_snapshot_id"] == graph.graph_snapshot.graph_snapshot_id
    assert snapshot["source_bundle_hash"] == graph.graph_snapshot.source_bundle_hash

    # Then: facts, routes, and governance records become claim-scoped handles without raw OCR text.
    assert {str(handle["fact_id"]) for handle in fact_handles} == {
        fact.fact_id for fact in graph.fact_assertions
    }
    assert {str(route["route_id"]) for route in routes} == {
        route.route_id for route in graph.route_candidates
    }
    assert {str(record["record_id"]) for record in records} == {
        str(record["record_id"]) for record in governance.records
    }
    assert all(handle["claim_id"] == claim_root["claim_id"] for handle in fact_handles)
    assert all(route["claim_id"] == claim_root["claim_id"] for route in routes)
    assert all(record["claim_id"] == claim_root["claim_id"] for record in records)
    assert all(handle["source_refs"] for handle in fact_handles)
    assert payload["pii_profile"] == {"raw_text_included": False, "source_text_included": False}
    encoded = json.dumps(payload, ensure_ascii=False)
    assert "Synthetic OCR Page" not in encoded
    assert "[DEBTOR_PERSON_REDACTED]" not in encoded
    assert _contains_key(payload, "raw_text") is False
    assert _contains_key(payload, "source_text") is False

    # Then: adapting does not mutate or rewrite the v0 graph contract.
    assert graph.to_json() == original_graph


def test_adapter_outputs_domain_stopgate_compatible_route_entities() -> None:
    # Given: a debtor graph with route candidates whose legacy legal refs include v0 metadata.
    graph = _route_ready_graph()

    # When: the adapter emits its domain case graph projection.
    payload = adapt_debtor_graph_to_claim_domain(graph).to_json()
    case_graph = _object_value(payload["case_graph"])
    stopgate_payload = evaluate_domain_v1_case_graph(case_graph).to_json()
    reason_codes = {
        str(gate["reason_code"])
        for gate in _object_list(stopgate_payload["stop_gates"])
    }
    packet = _object_list(case_graph["case_packets"])[0]
    route_entities = [
        entity
        for entity in _object_list(packet["entities"])
        if entity["ontology_class"] == "route-candidate"
    ]
    legal_source_entities = [
        entity
        for entity in _object_list(packet["entities"])
        if entity["ontology_class"] == "legal-source"
    ]

    # Then: route entities use v1 legal-source ids while retaining legacy refs for traceability.
    assert route_entities
    bank = next(entity for entity in route_entities if entity["route_id"] == "bank_account_attachment")
    assert bank["legal_source_refs"] == [
        "kr-law-l009290-m268837-a223",
        "kr-law-l009290-m268837-a229",
        "kr-law-l009290-m268837-a246",
    ]
    bank_source_refs = _string_list(bank["legal_source_refs"])
    bank_source_statuses = {
        str(entity["source_id"]): str(entity["review_status"])
        for entity in legal_source_entities
        if str(entity["source_id"]) in bank_source_refs
    }
    assert bank_source_statuses == {
        "kr-law-l009290-m268837-a223": "approved_static_v1",
        "kr-law-l009290-m268837-a229": "approved_static_v1",
        "kr-law-l009290-m268837-a246": "approved_static_v1",
    }
    assert all("|review_status=approved_static_v0" in ref for ref in _string_list(bank["legacy_legal_source_refs"]))
    assert "unsupported_contact_or_recovery_route" not in reason_codes


def test_adapter_rejects_fact_without_source_ref() -> None:
    # Given: a serialized graph whose first fact lost its provenance source refs.
    graph_json = _route_ready_graph().to_json()
    facts = _object_list(graph_json["fact_assertions"])
    facts[0]["source_ref"] = ""
    facts[0]["source_refs"] = []

    # When / Then: the adapter refuses to produce claim-domain handles.
    with pytest.raises(DomainGraphAdapterError) as error:
        _ = adapt_debtor_graph_to_claim_domain(graph_json)

    assert error.value.reason_code == "missing_source_ref"
    assert error.value.location == "fact_assertions[0]"


def test_adapter_rejects_unsupported_claim_identity() -> None:
    # Given: a graph with an explicit claim object that lacks a usable claim id.
    graph_json = _route_ready_graph().to_json()
    graph_json["claims"] = [{"fact_ids": []}]

    # When / Then: the adapter names the claim identity contract breach.
    with pytest.raises(DomainGraphAdapterError) as error:
        _ = adapt_debtor_graph_to_claim_domain(graph_json)

    assert error.value.reason_code == "unsupported_claim_identity"
    assert error.value.location == "claims[0]"


def _route_ready_graph():
    assembly_payload = build_document_assembly(PAGES_FIXTURE, REPO_ROOT)
    base = build_debtor_context(assembly_payload, repo_root=REPO_ROOT)
    routes = evaluate_route_candidates(base)
    snapshot = replace(
        base.graph_snapshot,
        route_candidate_ids=tuple(route.route_id for route in routes),
    )
    return replace(base, graph_snapshot=snapshot, route_candidates=routes)


def _object_value(value: JsonValue) -> JsonObject:
    assert isinstance(value, dict)
    return value


def _object_list(value: JsonValue) -> list[JsonObject]:
    assert isinstance(value, list)
    objects: list[JsonObject] = []
    for item in value:
        assert isinstance(item, dict)
        objects.append(item)
    return objects


def _string_list(value: JsonValue) -> list[str]:
    assert isinstance(value, list)
    strings: list[str] = []
    for item in value:
        assert isinstance(item, str)
        strings.append(item)
    return strings


def _contains_key(value: JsonValue, key_name: str) -> bool:
    if isinstance(value, dict):
        return key_name in value or any(_contains_key(item, key_name) for item in value.values())
    if isinstance(value, list):
        return any(_contains_key(item, key_name) for item in value)
    return False
