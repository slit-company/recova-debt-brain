from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Union

from trustgraph_legal.stop_gates_domain_v1 import evaluate_domain_v1_case_graph
from trustgraph_legal.stopgate_domain_resources import (
    DOMAIN_STOPGATE_RULES_PATH,
    load_domain_v1_rule_source,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DOMAIN_SOURCES_PATH = REPO_ROOT / "resources" / "legal_rules" / "debt_collection_domain_sources_v1.json"
JsonScalar = Union[str, int, float, bool, type(None)]
JsonValue = Union[JsonScalar, List["JsonValue"], Dict[str, "JsonValue"]]


def test_domain_v1_rule_source_uses_curated_approved_domain_sources() -> None:
    # Given: the curated domain source v1 catalog and the domain StopGate v1 rules.
    domain_sources = json.loads(DOMAIN_SOURCES_PATH.read_text(encoding="utf-8"))
    approved_source_ids = {
        source["source_id"]
        for source in domain_sources["sources"]
        if source["review_status"] == "approved_static_v1"
    }

    # When: the v1 StopGate rule source is loaded through the public helper.
    rule_source = load_domain_v1_rule_source()
    source_ids = {source.source_id for rule in rule_source.rules for source in rule.sources}
    source_statuses = {source.review_status for rule in rule_source.rules for source in rule.sources}

    # Then: rule refs are curated v1 refs, not legacy draft source placeholders.
    assert DOMAIN_STOPGATE_RULES_PATH.name == "debt_collection_stopgate_domain_v1.json"
    assert rule_source.version == "recova-debt-collection-stopgate@v1.0.0"
    assert rule_source.review_status == "approved_static_v1"
    assert source_ids
    assert source_ids <= approved_source_ids
    assert source_statuses == {"approved_static_v1"}


def test_domain_v1_covers_required_advisory_blockers() -> None:
    # Given: a synthetic case graph with every domain-v1 blocker class represented.
    graph = _graph(
        _document("doc:intake", "identity-evidence"),
        _document("doc:insolvency", "insolvency-credit-recovery"),
        _legal_check("check:exemption", "exemption_review_status"),
        _field("field:welfare", "welfare_benefit_signal", "protected public benefit"),
        _field("field:balance", "claim_balance_review_status", "ambiguous excessive balance"),
        _legal_source("source:legacy", "kr-civil-execution-act-v0", "needs_legal_review"),
        _route_candidate(
            "route:direct-contact",
            "direct_sms_recovery",
            "needs_legal_review",
            ["kr-civil-execution-act-v0"],
            direct_execution_allowed=True,
        ),
    )

    # When: the opt-in domain-v1 StopGate surface evaluates it.
    payload = evaluate_domain_v1_case_graph(graph).to_json()
    stop_gates = _object_list(payload["stop_gates"])
    reason_codes = {_str_value(gate["reason_code"]) for gate in stop_gates}
    rule_source = _object_value(payload["rule_source"])
    pii_profile = _object_value(payload["pii_profile"])
    rule_refs = _object_list(payload["rule_refs"])
    source_refs = _object_list(payload["source_refs"])

    # Then: each required blocker is advisory, sourced, and explicit enough for route decisions.
    assert payload["decision"] == "보류"
    assert reason_codes >= {
        "limitation_risk",
        "discharge_proceeding_detected",
        "exempt_claim_targeted",
        "welfare_public_benefit_protected",
        "domain_legal_source_unapproved",
        "missing_enforcement_title",
        "missing_service_finality_execution_clause_proof",
        "ambiguous_or_excessive_balance",
        "unsupported_contact_or_recovery_route",
        "route_legal_source_uncertain",
    }
    assert rule_source["version"] == "recova-debt-collection-stopgate@v1.0.0"
    assert pii_profile["raw_text_included"] is False
    assert all(_str_value(ref["rule_id"]).startswith("dc-stopgate-v1-") for ref in rule_refs)
    assert all("excerpt" not in ref and "text" not in ref for ref in source_refs)


def test_domain_v1_clear_case_preserves_review_safe_possible_decision() -> None:
    # Given: a source-backed advisory packet with title, service/finality, finance, and route source proof.
    graph = _graph(
        _document("doc:title", "payment-order"),
        _document("doc:service", "service-finality-proof"),
        _field("field:execution", "execution_clause_status", "grant"),
        _field("field:service", "service_status", "service"),
        _field("field:finality", "finality_status", "final"),
        _field("field:limitation", "limitation_cleared", "reviewed"),
        _field("field:claim", "claim_amount", "KRW 1000", amount_kind="claim_amount"),
        _field("field:principal", "principal_amount", "KRW 1000", amount_kind="principal_amount"),
        _route_candidate(
            "route:bank",
            "bank_account_attachment",
            "approved_static_v1",
            [
                "kr-law-l009290-m268837-a223",
                "kr-law-l009290-m268837-a229",
                "kr-law-l009290-m268837-a246",
            ],
        ),
    )

    # When: no domain-v1 blocker conditions are present.
    payload = evaluate_domain_v1_case_graph(graph).to_json()

    # Then: the engine only clears advisory recommendation review, not direct execution.
    assert payload["decision"] == "가능"
    assert payload["recommended_action"] == (
        "Legal StopGates are clear for advisory recommendation; external approval still owns execution."
    )
    assert payload["stop_gates"] == []


def test_domain_v1_holds_negated_service_finality_execution_clause_values() -> None:
    # Given: title/service/finality evidence exists but each material proof value is explicitly negated.
    graph = _graph(
        _document("doc:title", "payment-order"),
        _document("doc:service", "service-finality-proof"),
        _field("field:execution", "execution_clause_status", "not granted"),
        _field("field:service", "service_status", "not served"),
        _field("field:finality", "finality_status", "not final"),
        _field("field:limitation", "limitation_cleared", "reviewed"),
        _field("field:claim", "claim_amount", "KRW 1000", amount_kind="claim_amount"),
        _field("field:principal", "principal_amount", "KRW 1000", amount_kind="principal_amount"),
        _route_candidate(
            "route:bank",
            "bank_account_attachment",
            "approved_static_v1",
            [
                "kr-law-l009290-m268837-a223",
                "kr-law-l009290-m268837-a229",
                "kr-law-l009290-m268837-a246",
            ],
        ),
    )

    # When: the domain-v1 StopGate evaluates service, finality, and execution-clause proof.
    payload = evaluate_domain_v1_case_graph(graph).to_json()
    reason_codes = {_str_value(gate["reason_code"]) for gate in _object_list(payload["stop_gates"])}

    # Then: negated or uncertain proof wording keeps the case on hold instead of falsely clearing.
    assert payload["decision"] == "보류"
    assert "missing_service_finality_execution_clause_proof" in reason_codes
    assert payload["recommended_action"] == "Hold advisory recommendation until required preconditions and review items are cleared."


def test_domain_v1_flags_unapproved_or_placeholder_route_sources() -> None:
    # Given: an otherwise source-backed packet with a route tied to legacy and placeholder sources.
    graph = _graph(
        _document("doc:title", "payment-order"),
        _document("doc:service", "service-finality-proof"),
        _field("field:execution", "execution_clause_status", "granted"),
        _field("field:service", "service_status", "served"),
        _field("field:finality", "finality_status", "final"),
        _field("field:limitation", "limitation_cleared", "reviewed"),
        _field("field:claim", "claim_amount", "KRW 1000", amount_kind="claim_amount"),
        _field("field:principal", "principal_amount", "KRW 1000", amount_kind="principal_amount"),
        _legal_source("source:placeholder", "placeholder-source", "needs_legal_review"),
        _route_candidate(
            "route:legacy",
            "real_estate_provisional_attachment",
            "approved_static_v1",
            ["kr-civil-execution-act-v0", "placeholder-source"],
        ),
    )

    # When: the v1 source approval checks evaluate route-specific legal refs.
    payload = evaluate_domain_v1_case_graph(graph).to_json()
    stop_gates = _object_list(payload["stop_gates"])
    reason_codes = {_str_value(gate["reason_code"]) for gate in stop_gates}

    # Then: uncertain legal-source status holds the advisory route without using live law lookups.
    assert payload["decision"] == "보류"
    assert {"domain_legal_source_unapproved", "route_legal_source_uncertain"} <= reason_codes


def _graph(*entities: Dict[str, JsonValue]) -> Dict[str, JsonValue]:
    return {
        "schema_version": "trustgraph-legal-case-graph/v1",
        "case_packets": [
            {
                "id": "case:domain-v1",
                "entities": list(entities),
                "edges": [],
                "findings": [],
                "evidence_keys": [],
            }
        ],
    }


def _object_value(value: JsonValue) -> Dict[str, JsonValue]:
    assert isinstance(value, dict)
    return value


def _object_list(value: JsonValue) -> List[Dict[str, JsonValue]]:
    assert isinstance(value, list)
    objects: List[Dict[str, JsonValue]] = []
    for item in value:
        if isinstance(item, dict):
            objects.append(item)
    return objects


def _str_value(value: JsonValue) -> str:
    assert isinstance(value, str)
    return value


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
    payload: Dict[str, JsonValue] = {
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


def _legal_check(identifier: str, reason: str) -> Dict[str, JsonValue]:
    return {
        "id": identifier,
        "entity_type": "RuleFinding",
        "ontology_class": "legal-check",
        "value": "review required",
        "reason": reason,
        "provenance": _provenance(identifier, "legal-check", reason),
    }


def _legal_source(identifier: str, source_id: str, review_status: str) -> Dict[str, JsonValue]:
    return {
        "id": identifier,
        "entity_type": "LegalSourceStatus",
        "ontology_class": "legal-source",
        "value": source_id,
        "source_id": source_id,
        "review_status": review_status,
        "provenance": _provenance(identifier, "legal-source", "legal_source_status"),
    }


def _route_candidate(
    identifier: str,
    route_id: str,
    review_status: str,
    legal_source_refs: List[str],
    direct_execution_allowed: bool = False,
) -> Dict[str, JsonValue]:
    source_refs: List[JsonValue] = []
    source_refs.extend(legal_source_refs)
    return {
        "id": identifier,
        "entity_type": "RouteCandidate",
        "ontology_class": "route-candidate",
        "value": route_id,
        "route_id": route_id,
        "review_status": review_status,
        "legal_source_refs": source_refs,
        "direct_execution_allowed": direct_execution_allowed,
        "provenance": _provenance(identifier, "route-candidate", "route_candidate"),
    }


def _provenance(identifier: str, chunk_id: str, field_name: Optional[str] = None) -> Dict[str, JsonValue]:
    payload: Dict[str, JsonValue] = {
        "document_id": "doc-for-{}".format(identifier),
        "source_ref": "fixture:{}".format(identifier),
        "chunk_id": chunk_id,
        "line_start": 1,
        "line_end": 1,
        "confidence": 0.91,
        "extractor_version": "test",
        "source_module": "test_stop_gates_domain_v1",
    }
    if field_name is not None:
        payload["field_name"] = field_name
    return payload
