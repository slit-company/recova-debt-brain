from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Set, Tuple

from trustgraph_legal.stop_gates import (
    CaseIndex,
    IndexCollector,
    _case_indexes,
    _evaluators,
    _fact_ref,
    _object_list,
    _refs,
)
from trustgraph_legal.stopgate_domain_resources import (
    APPROVED_STATUS,
    DOMAIN_STOPGATE_RULES_PATH,
    LEGAL_SOURCE_CLASS,
    ROUTE_CANDIDATE_CLASS,
    DomainContext,
    LegalSourceStatusFact,
    RouteCandidateFact,
    load_domain_context,
    load_domain_v1_rule_source,
    string_tuple,
    text_value,
)
from trustgraph_legal.stopgate_rules import StopGateInputError
from trustgraph_legal.stopgate_types import (
    FactRef,
    FieldFact,
    JsonObject,
    JsonValue,
    RuleSourceSet,
    StopGateFinding,
    StopGatePayload,
)



@dataclass(frozen=True)
class DomainCaseIndex:
    legal_sources: Tuple[LegalSourceStatusFact, ...]
    route_candidates: Tuple[RouteCandidateFact, ...]


DomainEvaluator = Callable[[CaseIndex, DomainCaseIndex], Tuple[FactRef, ...]]


def evaluate_domain_v1_case_graph(
    graph: JsonObject,
    rule_source: Optional[RuleSourceSet] = None,
    domain_context: Optional[DomainContext] = None,
) -> StopGatePayload:
    active_rule_source = load_domain_v1_rule_source() if rule_source is None else rule_source
    active_context = load_domain_context() if domain_context is None else domain_context
    raw_packets = _object_list(graph.get("case_packets"))
    raw_by_id = {
        packet_id: packet
        for packet in raw_packets
        for packet_id in [_packet_id(packet)]
    }
    packets = tuple(_case_indexes(graph))
    base_evaluators = _evaluators(active_rule_source)
    domain_evaluators = _domain_evaluators(active_rule_source, active_context)
    findings: List[StopGateFinding] = []
    for packet in packets:
        domain_packet = _domain_case_index(raw_by_id.get(packet.packet_id, {}))
        for rule in active_rule_source.rules:
            facts = _evaluate_rule(packet, domain_packet, rule.condition, base_evaluators, domain_evaluators)
            if facts:
                confidence = round(min((fact.confidence for fact in facts), default=0.7), 2)
                findings.append(StopGateFinding(rule, facts, confidence))
    return StopGatePayload(tuple(packet.packet_id for packet in packets), active_rule_source, tuple(findings))


def _evaluate_rule(
    packet: CaseIndex,
    domain_packet: DomainCaseIndex,
    condition: str,
    base_evaluators: Dict[str, Callable[[CaseIndex], Tuple[FactRef, ...]]],
    domain_evaluators: Dict[str, DomainEvaluator],
) -> Tuple[FactRef, ...]:
    domain_evaluator = domain_evaluators.get(condition)
    if domain_evaluator is not None:
        return domain_evaluator(packet, domain_packet)
    base_evaluator = base_evaluators.get(condition)
    if base_evaluator is not None:
        return base_evaluator(packet)
    raise StopGateInputError(DOMAIN_STOPGATE_RULES_PATH, "unsupported domain-v1 condition {}".format(condition))


def _packet_id(packet: JsonObject) -> str:
    value = packet.get("id")
    return value if isinstance(value, str) else "case-packet:missing"


def _domain_evaluators(rule_source: RuleSourceSet, context: DomainContext) -> Dict[str, DomainEvaluator]:
    return {
        "domain_rule_source_unapproved": lambda packet, domain_packet: _domain_rule_source_unapproved(
            packet,
            rule_source,
        ),
        "welfare_public_benefit_protected": _welfare_public_benefit_protected,
        "domain_legal_source_unapproved": _domain_legal_source_unapproved,
        "missing_service_finality_execution_clause_proof": _missing_service_finality_execution_clause_proof,
        "ambiguous_or_excessive_balance": _ambiguous_or_excessive_balance,
        "unsupported_contact_or_recovery_route": lambda packet, domain_packet: _unsupported_contact_or_recovery_route(
            domain_packet,
            context,
        ),
        "route_legal_source_uncertain": lambda packet, domain_packet: _route_legal_source_uncertain(
            domain_packet,
            context,
        ),
    }


def _domain_case_index(packet: JsonObject) -> DomainCaseIndex:
    collector = IndexCollector([], {}, {}, [])
    route_candidates: List[RouteCandidateFact] = []
    legal_sources: List[LegalSourceStatusFact] = []
    for item in _object_list(packet.get("entities")):
        ontology_class = text_value(item.get("ontology_class"), "")
        if ontology_class == ROUTE_CANDIDATE_CLASS:
            route_candidate = _route_candidate(item, collector)
            if route_candidate is not None:
                route_candidates.append(route_candidate)
        if ontology_class == LEGAL_SOURCE_CLASS:
            legal_source = _legal_source_status(item, collector)
            if legal_source is not None:
                legal_sources.append(legal_source)
    return DomainCaseIndex(tuple(legal_sources), tuple(route_candidates))


def _route_candidate(item: JsonObject, collector: IndexCollector) -> Optional[RouteCandidateFact]:
    fallback_id = text_value(item.get("id"), "route-candidate")
    ref = _fact_ref(item, fallback_id, "route-candidate", collector)
    if ref is None:
        return None
    route_id = text_value(item.get("route_id"), text_value(item.get("value"), ""))
    return RouteCandidateFact(
        route_id,
        text_value(item.get("review_status"), ""),
        string_tuple(item.get("legal_source_refs")),
        item.get("direct_execution_allowed") is True,
        ref,
    )


def _legal_source_status(item: JsonObject, collector: IndexCollector) -> Optional[LegalSourceStatusFact]:
    fallback_id = text_value(item.get("id"), "legal-source")
    ref = _fact_ref(item, fallback_id, "legal-source", collector)
    if ref is None:
        return None
    source_id = text_value(item.get("source_id"), text_value(item.get("value"), ""))
    return LegalSourceStatusFact(source_id, text_value(item.get("review_status"), ""), ref)


def _domain_rule_source_unapproved(packet: CaseIndex, rule_source: RuleSourceSet) -> Tuple[FactRef, ...]:
    statuses: Set[str] = {rule_source.review_status}
    statuses.update(source.review_status for rule in rule_source.rules for source in rule.sources)
    if statuses == {APPROVED_STATUS}:
        return ()
    return (
        FactRef(
            "rule-source:{}".format(rule_source.version),
            "domain-rule-source",
            "curated://recova/stopgate-rules/{}".format(rule_source.version),
            packet.packet_id,
            "domain-rule-source",
            0,
            0,
            1.0,
        ),
    )


def _welfare_public_benefit_protected(packet: CaseIndex, domain_packet: DomainCaseIndex) -> Tuple[FactRef, ...]:
    facts = list(
        _field_facts(
            packet,
            {
                "welfare_benefit_signal",
                "public_benefit_signal",
                "protected_benefit_signal",
                "exempt_property_signal",
            },
        )
    )
    facts.extend(
        FieldFact("route_candidate", candidate.route_id, candidate.ref)
        for candidate in domain_packet.route_candidates
        if candidate.route_id == "welfare_public_benefit_exclusion_review"
    )
    return _refs(tuple(facts))


def _domain_legal_source_unapproved(packet: CaseIndex, domain_packet: DomainCaseIndex) -> Tuple[FactRef, ...]:
    return tuple(
        source.ref
        for source in domain_packet.legal_sources
        if source.source_id in {"", "missing"} or source.review_status != APPROVED_STATUS
    )


def _missing_service_finality_execution_clause_proof(
    packet: CaseIndex,
    domain_packet: DomainCaseIndex,
) -> Tuple[FactRef, ...]:
    service_docs = tuple(document for document in packet.documents if document.value == "service-finality-proof")
    execution_valid = _has_positive_proof(packet.fields.get("execution_clause_status", ()), {"grant", "issued"})
    service_valid = _has_positive_proof(packet.fields.get("service_status", ()), {"served", "service"})
    finality_valid = _has_positive_proof(packet.fields.get("finality_status", ()), {"final", "confirmed"})
    if service_docs and execution_valid and service_valid and finality_valid:
        return ()
    return _refs(packet.documents or tuple(_field_facts(packet, {"execution_clause_status", "service_status", "finality_status"})))


def _ambiguous_or_excessive_balance(packet: CaseIndex, domain_packet: DomainCaseIndex) -> Tuple[FactRef, ...]:
    review_names = {
        "ambiguous_balance",
        "claim_balance_review_status",
        "disputed_amount",
        "excessive_balance",
        "needs_finance_review",
        "payment_allocation_conflict",
    }
    facts = tuple(fact for fact in _field_facts(packet, review_names) if _balance_review_value(fact.value))
    return _refs(facts)


def _unsupported_contact_or_recovery_route(
    domain_packet: DomainCaseIndex,
    context: DomainContext,
) -> Tuple[FactRef, ...]:
    unsupported: List[FactRef] = []
    for candidate in domain_packet.route_candidates:
        catalog_entry = context.route_by_id.get(candidate.route_id)
        if (
            candidate.direct_execution_allowed
            or catalog_entry is None
            or candidate.review_status != APPROVED_STATUS
            or catalog_entry.direct_execution_allowed
            or catalog_entry.review_status != APPROVED_STATUS
        ):
            unsupported.append(candidate.ref)
    return tuple(unsupported)


def _route_legal_source_uncertain(
    domain_packet: DomainCaseIndex,
    context: DomainContext,
) -> Tuple[FactRef, ...]:
    uncertain: List[FactRef] = []
    for candidate in domain_packet.route_candidates:
        source_refs = _candidate_source_refs(candidate, context)
        if not source_refs or any(context.source_status_by_id.get(source_id) != APPROVED_STATUS for source_id in source_refs):
            uncertain.append(candidate.ref)
    return tuple(uncertain)


def _candidate_source_refs(candidate: RouteCandidateFact, context: DomainContext) -> Tuple[str, ...]:
    if candidate.legal_source_refs:
        return candidate.legal_source_refs
    catalog_entry = context.route_by_id.get(candidate.route_id)
    return () if catalog_entry is None else catalog_entry.legal_source_refs


def _field_facts(packet: CaseIndex, names: Set[str]) -> Tuple[FieldFact, ...]:
    facts: List[FieldFact] = []
    for name in names:
        facts.extend(packet.fields.get(name, ()))
        facts.extend(packet.legal_checks.get(name, ()))
    return tuple(facts)


def _has_positive_proof(facts: Tuple[FieldFact, ...], tokens: Set[str]) -> bool:
    return any(any(token in fact.value.lower() for token in tokens) for fact in facts)


def _balance_review_value(value: str) -> bool:
    lowered = value.lower()
    return any(
        token in lowered
        for token in (
            "ambiguous",
            "disputed",
            "excessive",
            "needs_finance_review",
            "unreconciled",
        )
    )
