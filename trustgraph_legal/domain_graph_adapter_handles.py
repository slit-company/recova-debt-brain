from __future__ import annotations

from collections.abc import Sequence
from typing import Final

from trustgraph_legal.debtor_context_types import JsonObject
from trustgraph_legal.domain_graph_adapter_shared import (
    DomainGraphAdapterError,
    digest,
    int_value,
    json_objects,
    number_value,
    required_source_refs,
    required_text,
    source_refs,
    strings,
    text,
    unique,
)
from trustgraph_legal.stopgate_domain_resources import APPROVED_STATUS, load_route_catalog

SOURCE_BUNDLE_FALLBACK: Final = "source_bundle_hash_fallback"
ROUTE_APPROVED_STATUSES: Final = frozenset({"possible", "missing_facts"})
V0_ROUTE_ID_MAP: Final[dict[str, str]] = {
    "business_receivable_attachment": "trade_receivable_attachment",
    "card_pg_platform_settlement_attachment": "pg_platform_settlement_attachment",
    "debtor_default_registry": "property_disclosure_inquiry_registry",
    "fraudulent_transfer_lawsuit": "fraudulent_transfer_cancellation_lawsuit",
    "inheritance_review_and_share_attachment": "inheritance_share_attachment",
    "insolvency_review_or_cease_collection": "insolvency_discharge_review",
    "insurance_refund_or_claim_attachment": "insurance_refund_claim_attachment",
    "lease_deposit_attachment": "residential_lease_deposit_attachment",
    "limitation_extension_lawsuit": "partial_payment_acknowledgment",
    "property_disclosure": "property_disclosure_inquiry_registry",
    "property_inquiry": "property_disclosure_inquiry_registry",
    "real_estate_auction": "real_estate_compulsory_auction",
    "severance_attachment": "severance_or_retirement_attachment",
    "tax_refund_or_public_receivable_attachment": "tax_refund_or_compensation_attachment",
    "title_acquisition_payment_order": "payment_order_title_acquisition",
    "vehicle_attachment": "vehicle_or_heavy_equipment_attachment",
}


def claim_roots(
    graph: JsonObject,
    debtor_graph_id: str,
    graph_snapshot_id: str,
    source_bundle_hash: str,
) -> tuple[JsonObject, ...]:
    claims = json_objects(graph.get("claims"))
    if not claims:
        return (
            _claim_root(
                "claim:from-debtor-graph:{}".format(digest("{}|{}".format(debtor_graph_id, source_bundle_hash))),
                debtor_graph_id,
                graph_snapshot_id,
                source_bundle_hash,
                SOURCE_BUNDLE_FALLBACK,
                _graph_source_refs(graph),
                _fact_ids(graph),
            ),
        )
    roots: list[JsonObject] = []
    for index, claim in enumerate(claims):
        claim_id = text(claim.get("claim_id"))
        if not claim_id:
            raise DomainGraphAdapterError("claims[{}]".format(index), "unsupported_claim_identity", "claim_id is required")
        roots.append(
            _claim_root(
                claim_id,
                debtor_graph_id,
                graph_snapshot_id,
                source_bundle_hash,
                "explicit_graph_claim",
                _claim_source_refs(claim, graph),
                strings(claim.get("fact_ids")),
            )
        )
    return tuple(roots)


def fact_handles(graph: JsonObject, primary_claim_id: str) -> tuple[JsonObject, ...]:
    handles: list[JsonObject] = []
    for index, fact in enumerate(json_objects(graph.get("fact_assertions"))):
        location = "fact_assertions[{}]".format(index)
        refs = required_source_refs(fact, location)
        fact_id = required_text(fact, "fact_id", location)
        handles.append(
            {
                "fact_id": fact_id,
                "claim_id": _claim_id_for_subject(text(fact.get("subject_id")), primary_claim_id),
                "fact_handle": required_text(fact, "predicate", location),
                "subject_id": text(fact.get("subject_id")),
                "source_refs": list(refs),
                "source_document_id": text(fact.get("source_document_id")),
                "source_hash": text(fact.get("source_hash")),
                "chunk_id": text(fact.get("chunk_id")),
                "line_start": int_value(fact.get("line_start")),
                "line_end": int_value(fact.get("line_end")),
                "confidence": number_value(fact.get("confidence")),
                "review_status": text(fact.get("review_status")),
                "derived": fact.get("derived") is True,
            }
        )
    return tuple(handles)


def route_handles(graph: JsonObject, primary_claim_id: str) -> tuple[JsonObject, ...]:
    routes: list[JsonObject] = []
    catalog = load_route_catalog()
    for route in json_objects(graph.get("route_candidates")):
        route_id = text(route.get("route_id"))
        mapped_route_id = V0_ROUTE_ID_MAP.get(route_id)
        domain_route_id = mapped_route_id if mapped_route_id is not None else route_id
        legacy_refs = strings(route.get("legal_source_refs"))
        catalog_entry = catalog.get(domain_route_id)
        legal_source_refs = _source_ids(legacy_refs)
        domain_refs = catalog_entry.legal_source_refs if catalog_entry is not None else legal_source_refs
        routes.append(
            {
                "route_id": route_id,
                "legacy_route_id": route_id,
                "domain_route_id": domain_route_id,
                "domain_route_supported": catalog_entry is not None,
                "claim_id": primary_claim_id,
                "status": text(route.get("status")),
                "required_fact_handles": list(strings(route.get("required_facts"))),
                "missing_fact_handles": list(strings(route.get("missing_facts"))),
                "blocking_fact_handles": list(strings(route.get("blocking_facts"))),
                "legal_source_refs": list(legal_source_refs),
                "domain_legal_source_refs": list(domain_refs),
                "legacy_legal_source_refs": list(legacy_refs),
                "source_fact_ids": list(strings(route.get("source_fact_ids"))),
                "confidence": number_value(route.get("confidence")),
                "review_status": text(route.get("review_status")),
                "domain_review_status": _domain_route_status(route),
                "no_direct_execution": route.get("no_direct_execution") is True,
                "direct_execution_allowed": False,
            }
        )
    return tuple(routes)


def governance_handles(records: Sequence[JsonObject], primary_claim_id: str) -> tuple[JsonObject, ...]:
    return tuple(
        {
            "record_id": text(record.get("record_id")),
            "claim_id": primary_claim_id,
            "kind": text(record.get("kind")),
            "reason_code": text(record.get("reason_code")),
            "severity": text(record.get("severity")),
            "review_status": text(record.get("review_status")),
            "source_refs": list(strings(record.get("source_refs"))),
            "source_fact_ids": list(strings(record.get("source_fact_ids"))),
        }
        for record in records
    )


def snapshot_handle(snapshot: JsonObject) -> JsonObject:
    return {
        "graph_snapshot_id": text(snapshot.get("graph_snapshot_id")),
        "source_bundle_hash": text(snapshot.get("source_bundle_hash")),
        "generated_at": text(snapshot.get("generated_at")),
        "fact_assertion_ids": list(strings(snapshot.get("fact_assertion_ids"))),
        "route_candidate_ids": list(strings(snapshot.get("route_candidate_ids"))),
        "extractor_versions": list(strings(snapshot.get("extractor_versions"))),
        "ontology_version": text(snapshot.get("ontology_version")),
        "route_version": text(snapshot.get("route_version")),
        "legal_rule_source_version": text(snapshot.get("legal_rule_source_version")),
    }


def source_refs_from_handles(
    fact_items: tuple[JsonObject, ...],
    governance_items: tuple[JsonObject, ...],
) -> tuple[str, ...]:
    refs: list[str] = []
    refs.extend(source_ref for fact in fact_items for source_ref in strings(fact.get("source_refs")))
    refs.extend(source_ref for record in governance_items for source_ref in strings(record.get("source_refs")))
    return unique(refs)


def legal_source_ids(route_items: tuple[JsonObject, ...]) -> tuple[str, ...]:
    return unique(source_id for route in route_items for source_id in strings(route.get("domain_legal_source_refs")))


def _claim_root(
    claim_id: str,
    debtor_graph_id: str,
    graph_snapshot_id: str,
    source_bundle_hash: str,
    identity_method: str,
    refs: tuple[str, ...],
    source_fact_ids: tuple[str, ...],
) -> JsonObject:
    return {
        "claim_id": claim_id,
        "claim_ref": claim_id,
        "receivable_ref": claim_id.replace("claim:", "receivable:", 1),
        "ontology_class": "Claim",
        "root_type": "Claim/Receivable",
        "runtime_memory_root": "DebtorContextGraph",
        "debtor_graph_id": debtor_graph_id,
        "graph_snapshot_id": graph_snapshot_id,
        "source_bundle_hash": source_bundle_hash,
        "claim_identity_method": identity_method,
        "source_refs": list(refs),
        "source_fact_ids": list(source_fact_ids),
    }


def _graph_source_refs(graph: JsonObject) -> tuple[str, ...]:
    refs: list[str] = []
    refs.extend(source_ref for fact in json_objects(graph.get("fact_assertions")) for source_ref in source_refs(fact))
    refs.extend(source_ref for packet in json_objects(graph.get("case_packets")) for source_ref in strings(packet.get("source_refs")))
    return unique(refs)


def _claim_source_refs(claim: JsonObject, graph: JsonObject) -> tuple[str, ...]:
    refs = strings(claim.get("source_refs"))
    return refs if refs else _graph_source_refs(graph)


def _fact_ids(graph: JsonObject) -> tuple[str, ...]:
    return tuple(text(fact.get("fact_id")) for fact in json_objects(graph.get("fact_assertions")) if text(fact.get("fact_id")))


def _source_ids(source_refs_value: tuple[str, ...]) -> tuple[str, ...]:
    return unique(ref.split("|", 1)[0] for ref in source_refs_value if ref)


def _domain_route_status(route: JsonObject) -> str:
    status = text(route.get("status"))
    if status in ROUTE_APPROVED_STATUSES and route.get("no_direct_execution") is True:
        return APPROVED_STATUS
    return "needs_review"


def _claim_id_for_subject(subject_id: str, primary_claim_id: str) -> str:
    return subject_id if subject_id.startswith("claim:") else primary_claim_id
