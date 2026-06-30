from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from trustgraph_legal.stopgate_rules import RULES_PATH, StopGateInputError, load_rule_source
from trustgraph_legal.stopgate_types import (
    FactRef,
    FieldFact,
    JsonObject,
    JsonValue,
    RuleSourceSet,
    StopGateFinding,
    StopGatePayload,
)

SUPPORTED_DOCUMENT_TYPES = {
    "attachment-collection-application",
    "attachment-collection-order",
    "payment-order",
    "judgment-or-decision",
    "service-finality-proof",
    "assignment-succession",
    "identity-evidence",
    "insolvency-credit-recovery",
    "attachment-target-priority",
    "asset-evidence",
    "ledger-recovery",
    "amount-interest-calculation",
    "legal-rule-source",
}
TITLE_DOCUMENT_TYPES = {"payment-order", "judgment-or-decision"}


@dataclass(frozen=True)
class CaseIndex:
    packet_id: str
    documents: Tuple[FieldFact, ...]
    fields: Dict[str, Tuple[FieldFact, ...]]
    legal_checks: Dict[str, Tuple[FieldFact, ...]]
    findings: Tuple[FieldFact, ...]
    invalid_facts: Tuple[FactRef, ...]


@dataclass
class IndexCollector:
    documents: List[FieldFact]
    fields: Dict[str, List[FieldFact]]
    legal_checks: Dict[str, List[FieldFact]]
    invalid: List[FactRef]


def check_case_graph(case_path: Path) -> StopGatePayload:
    raw = json.loads(case_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise StopGateInputError(case_path, "case graph root must be an object")
    return evaluate_case_graph(raw)


def evaluate_case_graph(graph: JsonObject, rule_source: Optional[RuleSourceSet] = None) -> StopGatePayload:
    active_rule_source = load_rule_source() if rule_source is None else rule_source
    packets = tuple(_case_indexes(graph))
    findings = tuple(
        finding
        for packet in packets
        for finding in _evaluate_packet(packet, active_rule_source)
    )
    return StopGatePayload(tuple(packet.packet_id for packet in packets), active_rule_source, findings)


def _evaluate_packet(packet: CaseIndex, rule_source: RuleSourceSet) -> Tuple[StopGateFinding, ...]:
    evaluators = _evaluators(rule_source)
    findings: List[StopGateFinding] = []
    for rule in rule_source.rules:
        facts = evaluators[rule.condition](packet)
        if facts:
            confidence = round(min((fact.confidence for fact in facts), default=0.7), 2)
            findings.append(StopGateFinding(rule, facts, confidence))
    return tuple(findings)


def _evaluators(rule_source: RuleSourceSet) -> Dict[str, Callable[[CaseIndex], Tuple[FactRef, ...]]]:
    return {
        "invalid_provenance": lambda packet: packet.invalid_facts,
        "rule_source_unapproved": lambda packet: _rule_source_unapproved(packet, rule_source),
        "missing_execution_clause": _missing_execution_clause,
        "discharge_proceeding_detected": _discharge_proceeding_detected,
        "limitation_risk": _limitation_risk,
        "exempt_claim_targeted": _exempt_claim_targeted,
        "assignment_chain_broken": _assignment_chain_broken,
        "amount_mismatch": _amount_mismatch,
        "identity_uncertain": _identity_uncertain,
        "missing_enforcement_title": _missing_enforcement_title,
        "unknown_document_type": _unknown_document_type,
        "unsupported_document_type_review": _unsupported_document_type_review,
    }


def _missing_execution_clause(packet: CaseIndex) -> Tuple[FactRef, ...]:
    clauses = packet.fields.get("execution_clause_status", ())
    valid = any("grant" in field.value.lower() or "issued" in field.value.lower() for field in clauses)
    return () if valid else _refs(_title_or_packet_docs(packet))


def _rule_source_unapproved(packet: CaseIndex, rule_source: RuleSourceSet) -> Tuple[FactRef, ...]:
    statuses = {rule_source.review_status}
    statuses.update(source.review_status for rule in rule_source.rules for source in rule.sources)
    if statuses == {"approved"}:
        return ()
    return (
        FactRef(
            "rule-source:{}".format(rule_source.version),
            "rule-source",
            "curated://recova/stopgate-rules/{}".format(rule_source.version),
            packet.packet_id,
            "rule-source",
            0,
            0,
            1.0,
        ),
    )


def _discharge_proceeding_detected(packet: CaseIndex) -> Tuple[FactRef, ...]:
    facts = list(packet.legal_checks.get("procedure_status", ()))
    facts.extend(_documents(packet, {"insolvency-credit-recovery"}))
    return _refs(tuple(facts))


def _limitation_risk(packet: CaseIndex) -> Tuple[FactRef, ...]:
    if packet.fields.get("limitation_cleared") or packet.legal_checks.get("limitation_cleared"):
        return ()
    facts = packet.fields.get("claim_amount", ()) + packet.fields.get("principal_amount", ())
    return _refs(facts or _title_or_packet_docs(packet))


def _exempt_claim_targeted(packet: CaseIndex) -> Tuple[FactRef, ...]:
    facts = list(packet.legal_checks.get("exemption_review_status", ()))
    facts.extend(_documents(packet, {"attachment-target-priority"}))
    facts.extend(packet.fields.get("priority_status", ()))
    return _refs(tuple(facts))


def _assignment_chain_broken(packet: CaseIndex) -> Tuple[FactRef, ...]:
    assignment_docs = _documents(packet, {"assignment-succession"})
    if not assignment_docs:
        return ()
    if packet.fields.get("notice_status") and packet.fields.get("succession_authority"):
        return ()
    return _refs(assignment_docs)


def _amount_mismatch(packet: CaseIndex) -> Tuple[FactRef, ...]:
    claim = packet.fields.get("claim_amount", ())
    principal = packet.fields.get("principal_amount", ())
    if claim and principal and {field.value for field in claim} != {field.value for field in principal}:
        return _refs(claim + principal)
    return ()


def _identity_uncertain(packet: CaseIndex) -> Tuple[FactRef, ...]:
    names = {"identity_uncertain", "name_only_without_identity_evidence"}
    return _refs(tuple(fact for fact in packet.findings if fact.name in names))


def _missing_enforcement_title(packet: CaseIndex) -> Tuple[FactRef, ...]:
    return () if _documents(packet, TITLE_DOCUMENT_TYPES) else _refs(packet.documents)


def _unknown_document_type(packet: CaseIndex) -> Tuple[FactRef, ...]:
    return _refs(tuple(document for document in packet.documents if document.value == "unknown"))


def _unsupported_document_type_review(packet: CaseIndex) -> Tuple[FactRef, ...]:
    return _refs(
        tuple(
            document
            for document in packet.documents
            if document.value != "unknown" and document.value not in SUPPORTED_DOCUMENT_TYPES
        )
    )


def _case_indexes(graph: JsonObject) -> List[CaseIndex]:
    return [_case_index(raw_packet) for raw_packet in _object_list(graph.get("case_packets"))]


def _case_index(packet: JsonObject) -> CaseIndex:
    collector = IndexCollector([], {}, {}, [])
    for item in _object_list(packet.get("entities")):
        _index_entity(item, collector)
    findings = _findings(packet, collector)
    return CaseIndex(
        _str_or(packet.get("id"), "case-packet:missing"),
        tuple(collector.documents),
        {name: tuple(values) for name, values in collector.fields.items()},
        {name: tuple(values) for name, values in collector.legal_checks.items()},
        findings,
        tuple(collector.invalid),
    )


def _index_entity(item: JsonObject, collector: IndexCollector) -> None:
    ref = _fact_ref(item, _str_or(item.get("id"), "entity"), _str_or(item.get("ontology_class"), "entity"), collector)
    if ref is None:
        return
    ontology_class = _str_or(item.get("ontology_class"), "")
    name = _str_or(item.get("field_name"), _str_or(_provenance(item).get("field_name"), ""))
    value = _str_or(item.get("value"), "")
    if ontology_class == "legal-document":
        collector.documents.append(FieldFact("document_type", value, ref))
    if name:
        collector.fields.setdefault(name, []).append(FieldFact(name, value, ref))
    if ontology_class == "amount":
        amount_kind = _str_or(item.get("amount_kind"), name)
        collector.fields.setdefault(amount_kind, []).append(FieldFact(amount_kind, value, ref))
    if ontology_class == "legal-check":
        reason = _str_or(item.get("reason"), name)
        collector.legal_checks.setdefault(reason, []).append(FieldFact(reason, value, ref))


def _findings(packet: JsonObject, collector: IndexCollector) -> Tuple[FieldFact, ...]:
    findings: List[FieldFact] = []
    for item in _object_list(packet.get("findings")):
        name = _str_or(item.get("reason"), "finding")
        ref = _fact_ref(item, name, "finding", collector)
        if ref is not None:
            findings.append(FieldFact(name, "", ref))
    return tuple(findings)


def _fact_ref(item: JsonObject, fallback_id: str, fact_type: str, collector: IndexCollector) -> Optional[FactRef]:
    if item.get("derived") is True:
        return None
    provenance = _provenance(item)
    source_ref = provenance.get("source_ref")
    document_id = provenance.get("document_id")
    chunk_id = provenance.get("chunk_id")
    if not _present_source_value(source_ref) or not _present_source_value(document_id) or not _present_source_value(chunk_id):
        ref = FactRef(fallback_id, fact_type, "missing", "missing", "missing", 0, 0, 0.0)
        collector.invalid.append(ref)
        return ref
    line_start = provenance.get("line_start")
    line_end = provenance.get("line_end")
    confidence = provenance.get("confidence")
    if not isinstance(line_start, int) or not isinstance(line_end, int):
        ref = FactRef(fallback_id, fact_type, source_ref, document_id, chunk_id, 0, 0, 0.0)
        collector.invalid.append(ref)
        return ref
    score = confidence if isinstance(confidence, float) else 0.8
    return FactRef(fallback_id, fact_type, source_ref, document_id, chunk_id, line_start, line_end, score)


def _documents(packet: CaseIndex, document_types: set[str]) -> Tuple[FieldFact, ...]:
    return tuple(document for document in packet.documents if document.value in document_types)


def _title_or_packet_docs(packet: CaseIndex) -> Tuple[FieldFact, ...]:
    return _documents(packet, TITLE_DOCUMENT_TYPES) or packet.documents


def _refs(facts: Tuple[FieldFact, ...]) -> Tuple[FactRef, ...]:
    by_key = {"{}:{}:{}".format(fact.ref.fact_id, fact.ref.source_ref, fact.ref.chunk_id): fact.ref for fact in facts}
    return tuple(by_key[key] for key in sorted(by_key))


def _provenance(item: JsonObject) -> JsonObject:
    provenance = item.get("provenance")
    return provenance if isinstance(provenance, dict) else {}


def _object_list(value: JsonValue) -> List[JsonObject]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _present_source_value(value: JsonValue) -> bool:
    return isinstance(value, str) and value not in {"", "missing"}


def _str_or(value: JsonValue, default: str) -> str:
    return value if isinstance(value, str) else default
