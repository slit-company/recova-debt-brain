from __future__ import annotations

from trustgraph_legal.debtor_context_types import JsonObject, JsonValue
from trustgraph_legal.domain_graph_adapter_handles import legal_source_ids
from trustgraph_legal.domain_graph_adapter_shared import digest, pii_profile, strings, text
from trustgraph_legal.stopgate_domain_resources import load_domain_source_statuses


def case_graph(
    debtor_graph_id: str,
    graph_snapshot_id: str,
    source_bundle_hash: str,
    claim_roots: tuple[JsonObject, ...],
    fact_handles: tuple[JsonObject, ...],
    route_handles: tuple[JsonObject, ...],
    governance_handles: tuple[JsonObject, ...],
) -> JsonObject:
    entities = _claim_entities(claim_roots) + _fact_entities(fact_handles) + _route_entities(route_handles) + _governance_entities(governance_handles)
    packet_id = "case-packet:claim-domain:{}".format(digest("{}|{}".format(debtor_graph_id, graph_snapshot_id)))
    entities_value: list[JsonValue] = [entity for entity in entities]
    packet: JsonObject = {
        "id": packet_id,
        "case_packet_id": packet_id,
        "debtor_graph_id": debtor_graph_id,
        "graph_snapshot_id": graph_snapshot_id,
        "source_bundle_hash": source_bundle_hash,
        "entities": entities_value,
        "edges": [],
        "findings": [],
        "evidence_keys": [],
    }
    case_packets: list[JsonValue] = [packet]
    return {
        "schema_version": "trustgraph-legal-case-graph/v1",
        "case_packets": case_packets,
        "pii_profile": pii_profile(),
    }


def _claim_entities(claim_roots: tuple[JsonObject, ...]) -> list[JsonObject]:
    return [
        {
            "id": text(claim.get("claim_id")),
            "entity_type": "Claim",
            "ontology_class": "claim",
            "value": text(claim.get("claim_id")),
            "claim_id": text(claim.get("claim_id")),
            "provenance": _provenance(text(claim.get("claim_id")), "claim-root", strings(claim.get("source_refs"))),
        }
        for claim in claim_roots
    ]


def _fact_entities(fact_handles: tuple[JsonObject, ...]) -> list[JsonObject]:
    entities: list[JsonObject] = []
    for handle in fact_handles:
        fact_handle = text(handle.get("fact_handle"))
        entities.append(
            {
                "id": text(handle.get("fact_id")),
                "entity_type": "FactAssertion",
                "ontology_class": _fact_class(fact_handle),
                "value": fact_handle,
                "field_name": fact_handle,
                "claim_id": text(handle.get("claim_id")),
                "provenance": _provenance(text(handle.get("fact_id")), "fact-assertion", strings(handle.get("source_refs"))),
            }
        )
    return entities


def _route_entities(route_handles: tuple[JsonObject, ...]) -> list[JsonObject]:
    entities: list[JsonObject] = []
    for route in route_handles:
        if route.get("domain_route_supported") is not True:
            continue
        route_id = text(route.get("domain_route_id"))
        entities.append(
            {
                "id": "route-candidate:{}".format(route_id),
                "entity_type": "RouteCandidate",
                "ontology_class": "route-candidate",
                "value": route_id,
                "route_id": route_id,
                "legacy_route_id": text(route.get("legacy_route_id")),
                "review_status": text(route.get("domain_review_status")),
                "legal_source_refs": list(strings(route.get("domain_legal_source_refs"))),
                "legacy_legal_source_refs": list(strings(route.get("legacy_legal_source_refs"))),
                "direct_execution_allowed": False,
                "provenance": _provenance(route_id, "route-candidate", strings(route.get("legacy_legal_source_refs"))),
            }
        )
    entities.extend(_legal_source_entities(route_handles))
    return entities


def _legal_source_entities(route_handles: tuple[JsonObject, ...]) -> list[JsonObject]:
    status_by_id = load_domain_source_statuses()
    return [
        {
            "id": "legal-source:{}".format(source_id),
            "entity_type": "LegalSourceStatus",
            "ontology_class": "legal-source",
            "value": source_id,
            "source_id": source_id,
            "review_status": status_by_id.get(source_id, "needs_legal_review"),
            "provenance": _provenance(source_id, "legal-source", (source_id,)),
        }
        for source_id in legal_source_ids(route_handles)
    ]


def _governance_entities(governance_handles: tuple[JsonObject, ...]) -> list[JsonObject]:
    return [
        {
            "id": text(record.get("record_id")),
            "entity_type": "GovernanceRecord",
            "ontology_class": "governance-record",
            "value": text(record.get("reason_code")),
            "reason": text(record.get("reason_code")),
            "review_status": text(record.get("review_status")),
            "provenance": _provenance(text(record.get("record_id")), "governance-record", strings(record.get("source_refs"))),
        }
        for record in governance_handles
    ]


def _fact_class(fact_handle: str) -> str:
    if "amount" in fact_handle or "balance" in fact_handle:
        return "amount"
    if fact_handle.endswith("_status") or fact_handle.endswith("_review"):
        return "legal-check"
    return "source-span"


def _provenance(identifier: str, field_name: str, source_refs: tuple[str, ...]) -> JsonObject:
    source_ref = source_refs[0] if source_refs else "adapter:{}".format(identifier)
    return {
        "source_ref": source_ref,
        "source_refs": list(source_refs) if source_refs else [source_ref],
        "field_name": field_name,
        "confidence": 1.0,
    }
