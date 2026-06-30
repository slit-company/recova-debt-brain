from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Final, Iterable, List, Optional, Tuple, Union

JsonScalar = Optional[Union[str, int, float, bool]]
JsonValue = Union[JsonScalar, List["JsonValue"], Dict[str, "JsonValue"]]
JsonObject = Dict[str, JsonValue]
SCHEMA_VERSION: Final = "trustgraph-legal-stopgate-check/v1"


@dataclass(frozen=True)
class FactRef:
    fact_id: str
    fact_type: str
    source_ref: str
    document_id: str
    chunk_id: str
    line_start: int
    line_end: int
    confidence: float

    def to_json(self) -> JsonObject:
        return {
            "fact_id": self.fact_id,
            "fact_type": self.fact_type,
            "source_ref": self.source_ref,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class FieldFact:
    name: str
    value: str
    ref: FactRef


@dataclass(frozen=True)
class RuleSource:
    source_id: str
    statute_ref: str
    effective_date: str
    review_status: str
    source_ref: str

    def to_json(self) -> JsonObject:
        return {
            "source_id": self.source_id,
            "statute_ref": self.statute_ref,
            "effective_date": self.effective_date,
            "review_status": self.review_status,
            "source_ref": self.source_ref,
        }


@dataclass(frozen=True)
class StopGateRule:
    rule_id: str
    stopgate_id: str
    reason_code: str
    decision: str
    condition: str
    blocked_reason: str
    recommended_action: str
    required_preconditions: Tuple[str, ...]
    missing_evidence: Tuple[str, ...]
    risk_flags: Tuple[str, ...]
    sources: Tuple[RuleSource, ...]
    statute_refs: Tuple[str, ...]
    effective_date: str


@dataclass(frozen=True)
class StopGateFinding:
    rule: StopGateRule
    facts: Tuple[FactRef, ...]
    confidence: float

    def to_json(self) -> JsonObject:
        return {
            "stopgate_id": self.rule.stopgate_id,
            "decision": self.rule.decision,
            "reason_code": self.rule.reason_code,
            "blocked_reason": self.rule.blocked_reason,
            "recommended_action": self.rule.recommended_action,
            "required_preconditions": list(self.rule.required_preconditions),
            "missing_evidence": list(self.rule.missing_evidence),
            "risk_flags": list(self.rule.risk_flags),
            "source_refs": [fact.to_json() for fact in _dedupe_facts(self.facts)],
            "rule_refs": [_rule_ref(self.rule)],
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class RuleSourceSet:
    version: str
    review_status: str
    effective_date: str
    curation_policy: str
    rules: Tuple[StopGateRule, ...]

    def to_json(self) -> JsonObject:
        return {
            "version": self.version,
            "review_status": self.review_status,
            "effective_date": self.effective_date,
            "curation_policy": self.curation_policy,
        }


@dataclass(frozen=True)
class StopGatePayload:
    case_packet_ids: Tuple[str, ...]
    rule_source: RuleSourceSet
    findings: Tuple[StopGateFinding, ...]

    def to_json(self) -> JsonObject:
        decision = _aggregate_decision(self.findings)
        return {
            "schema_version": SCHEMA_VERSION,
            "decision": decision,
            "case_packet_ids": list(self.case_packet_ids),
            "recommended_action": _recommended_action(decision),
            "required_preconditions": _unique_text(
                item for finding in self.findings for item in finding.rule.required_preconditions
            ),
            "blocked_reasons": _unique_text(finding.rule.blocked_reason for finding in self.findings),
            "missing_evidence": _unique_text(
                item for finding in self.findings for item in finding.rule.missing_evidence
            ),
            "risk_flags": _unique_text(item for finding in self.findings for item in finding.rule.risk_flags),
            "source_refs": _unique_sources(self.findings),
            "rule_refs": _unique_rule_refs(self.findings),
            "confidence": _payload_confidence(self.findings),
            "review_queue_items": _review_items(self.findings),
            "stop_gates": [finding.to_json() for finding in self.findings],
            "rule_source": self.rule_source.to_json(),
            "pii_profile": {"raw_text_included": False, "source_text_included": False},
        }


def _rule_ref(rule: StopGateRule) -> JsonObject:
    return {
        "rule_id": rule.rule_id,
        "stopgate_id": rule.stopgate_id,
        "statute_refs": list(rule.statute_refs),
        "effective_date": rule.effective_date,
        "sources": [source.to_json() for source in rule.sources],
    }


def _aggregate_decision(findings: Tuple[StopGateFinding, ...]) -> str:
    decisions = {finding.rule.decision for finding in findings}
    if "불가능" in decisions:
        return "불가능"
    if "보류" in decisions:
        return "보류"
    return "가능"


def _recommended_action(decision: str) -> str:
    if decision == "가능":
        return "Legal StopGates are clear for advisory recommendation; external approval still owns execution."
    return "Hold advisory recommendation until required preconditions and review items are cleared."


def _payload_confidence(findings: Tuple[StopGateFinding, ...]) -> float:
    return round(min((finding.confidence for finding in findings), default=0.95), 2)


def _unique_text(values: Iterable[str]) -> List[str]:
    return sorted(set(values))


def _unique_sources(findings: Tuple[StopGateFinding, ...]) -> List[JsonObject]:
    by_key: Dict[str, JsonObject] = {}
    for finding in findings:
        for fact in finding.facts:
            by_key["{}:{}:{}".format(fact.source_ref, fact.document_id, fact.chunk_id)] = fact.to_json()
    return [by_key[key] for key in sorted(by_key)]


def _unique_rule_refs(findings: Tuple[StopGateFinding, ...]) -> List[JsonObject]:
    by_id = {finding.rule.rule_id: _rule_ref(finding.rule) for finding in findings}
    return [by_id[key] for key in sorted(by_id)]


def _review_items(findings: Tuple[StopGateFinding, ...]) -> List[JsonObject]:
    return [
        {
            "review_reason": finding.rule.reason_code,
            "stopgate_id": finding.rule.stopgate_id,
            "required_preconditions": list(finding.rule.required_preconditions),
            "source_refs": [fact.to_json() for fact in _dedupe_facts(finding.facts)],
        }
        for finding in findings
    ]


def _dedupe_facts(facts: Tuple[FactRef, ...]) -> Tuple[FactRef, ...]:
    by_key = {
        "{}:{}:{}:{}".format(fact.fact_id, fact.source_ref, fact.document_id, fact.chunk_id): fact
        for fact in facts
    }
    return tuple(by_key[key] for key in sorted(by_key))
