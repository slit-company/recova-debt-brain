from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Final

from trustgraph_legal.debtor_context_types import JsonObject, JsonValue
from trustgraph_legal.domain_graph_adapter_shared import placeholder_source_ref

SCHEMA_VERSION: Final = "trustgraph-evidence-quality-check/v1"
LOW_CONFIDENCE_THRESHOLD: Final = 0.75
NON_EXECUTION_SEMANTICS: Final = "advisory_only_human_review_required"
VALUE_FIELDS: Final = ("object_value", "fact_value", "value")
STALE_STATUSES: Final = frozenset({"stale", "stale_review_required", "outdated", "expired"})


@dataclass(frozen=True, slots=True)
class EvidenceFact:
    fact_id: str
    fact_handle: str
    subject_id: str
    source_refs: tuple[str, ...]
    source_document_id: str
    source_hash: str
    chunk_id: str
    line_start: int
    line_end: int
    confidence: float
    review_status: str
    freshness_status: str
    derived: bool
    value_fingerprint: str


@dataclass(frozen=True, slots=True)
class EvidenceQualitySignal:
    code: str
    category: str
    fact_ids: tuple[str, ...]
    fact_handles: tuple[str, ...]
    source_refs: tuple[str, ...]
    value_fingerprints: tuple[str, ...] = ()

    def to_json(self) -> JsonObject:
        payload: JsonObject = {
            "code": self.code,
            "category": self.category,
            "fact_ids": list(self.fact_ids),
            "fact_handles": list(self.fact_handles),
            "review_status": "human_review_required",
            "source_refs": list(self.source_refs),
        }
        if self.value_fingerprints:
            payload["value_fingerprints"] = list(self.value_fingerprints)
        return payload


@dataclass(frozen=True, slots=True)
class EvidenceQualityCheckpoint:
    facts: tuple[EvidenceFact, ...]
    review_items: tuple[EvidenceQualitySignal, ...]
    hold_items: tuple[EvidenceQualitySignal, ...]

    def to_json(self) -> JsonObject:
        return {
            "schema_version": SCHEMA_VERSION,
            "decision": _decision(self.review_items, self.hold_items),
            "fact_summaries": [_fact_summary(fact) for fact in self.facts],
            "review_items": [item.to_json() for item in self.review_items],
            "hold_items": [item.to_json() for item in self.hold_items],
            "workflow_signals": [item.to_json() for item in (*self.review_items, *self.hold_items)],
            "summary": {
                "facts_checked": len(self.facts),
                "review_items": len(self.review_items),
                "hold_items": len(self.hold_items),
                "lowest_confidence": _lowest_confidence(self.facts),
            },
            "pii_profile": {"raw_text_included": False, "source_text_included": False},
            "non_execution_semantics": NON_EXECUTION_SEMANTICS,
        }


def evaluate_evidence_quality(payload: JsonObject) -> EvidenceQualityCheckpoint:
    facts = tuple(_evidence_fact(item) for item in _fact_items(payload))
    review_items = tuple(item for fact in facts for item in _fact_review_items(fact))
    hold_items = _conflict_hold_items(facts)
    return EvidenceQualityCheckpoint(facts, review_items, hold_items)


def _fact_items(payload: JsonObject) -> tuple[JsonObject, ...]:
    fact_handles = json_objects(payload.get("fact_handles"))
    if fact_handles:
        return fact_handles
    return json_objects(payload.get("fact_assertions"))


def _evidence_fact(item: JsonObject) -> EvidenceFact:
    return EvidenceFact(
        fact_id=text(item.get("fact_id")),
        fact_handle=text(item.get("fact_handle")) or text(item.get("predicate")),
        subject_id=text(item.get("subject_id")) or text(item.get("claim_id")),
        source_refs=strings(item.get("source_refs")) or _single_source_ref(item),
        source_document_id=text(item.get("source_document_id")),
        source_hash=text(item.get("source_hash")),
        chunk_id=text(item.get("chunk_id")),
        line_start=int_value(item.get("line_start")),
        line_end=int_value(item.get("line_end")),
        confidence=confidence(item.get("confidence")),
        review_status=text(item.get("review_status")),
        freshness_status=text(item.get("freshness_status")),
        derived=item.get("derived") is True,
        value_fingerprint=_value_fingerprint(item),
    )


def _fact_review_items(fact: EvidenceFact) -> tuple[EvidenceQualitySignal, ...]:
    signals: list[EvidenceQualitySignal] = []
    if not fact.source_refs:
        signals.append(_signal("missing_source_ref", "evidence", fact))
    for source_ref in fact.source_refs:
        if placeholder_source_ref(source_ref):
            signals.append(_signal("placeholder_source_ref", "evidence", fact))
    if _missing_provenance(fact):
        signals.append(_signal("missing_provenance", "evidence", fact))
    if fact.confidence < LOW_CONFIDENCE_THRESHOLD:
        signals.append(_signal("low_confidence_fact", "evidence", fact))
    if _stale_fact(fact):
        signals.append(_signal("stale_fact", "evidence", fact))
    if fact.derived:
        signals.append(_signal("derived_fact_review", "evidence", fact))
    return tuple(signals)


def _signal(code: str, category: str, fact: EvidenceFact) -> EvidenceQualitySignal:
    return EvidenceQualitySignal(
        code,
        category,
        (fact.fact_id,),
        (fact.fact_handle,),
        fact.source_refs,
    )


def _conflict_hold_items(facts: tuple[EvidenceFact, ...]) -> tuple[EvidenceQualitySignal, ...]:
    by_key: dict[tuple[str, str], list[EvidenceFact]] = {}
    for fact in facts:
        if fact.value_fingerprint:
            key = (fact.subject_id, fact.fact_handle)
            by_key.setdefault(key, []).append(fact)
    items: list[EvidenceQualitySignal] = []
    for grouped in by_key.values():
        fingerprints = unique(tuple(fact.value_fingerprint for fact in grouped))
        if len(fingerprints) > 1:
            items.append(
                EvidenceQualitySignal(
                    "conflicting_fact_values",
                    "evidence_conflict",
                    tuple(fact.fact_id for fact in grouped),
                    unique(tuple(fact.fact_handle for fact in grouped)),
                    unique(tuple(source_ref for fact in grouped for source_ref in fact.source_refs)),
                    fingerprints,
                )
            )
    return tuple(items)


def _fact_summary(fact: EvidenceFact) -> JsonObject:
    return {
        "fact_id": fact.fact_id,
        "fact_handle": fact.fact_handle,
        "source_refs": list(fact.source_refs),
        "confidence": fact.confidence,
        "derived": fact.derived,
        "freshness_status": fact.freshness_status,
        "value_fingerprint": fact.value_fingerprint,
    }


def _decision(review_items: tuple[EvidenceQualitySignal, ...], hold_items: tuple[EvidenceQualitySignal, ...]) -> str:
    if hold_items:
        return "hold"
    if review_items:
        return "review_required"
    return "pass"


def _missing_provenance(fact: EvidenceFact) -> bool:
    return (
        not fact.source_document_id
        or not fact.source_hash
        or not fact.chunk_id
        or fact.line_start < 1
        or fact.line_end < fact.line_start
    )


def _stale_fact(fact: EvidenceFact) -> bool:
    return fact.freshness_status.lower() in STALE_STATUSES or fact.review_status.lower() in STALE_STATUSES


def _lowest_confidence(facts: tuple[EvidenceFact, ...]) -> float:
    return round(min((fact.confidence for fact in facts), default=1.0), 2)


def _value_fingerprint(item: JsonObject) -> str:
    for field_name in VALUE_FIELDS:
        if field_name in item:
            return _hash_json(item[field_name])
    return ""


def _hash_json(value: JsonValue) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:{}".format(hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16])


def _single_source_ref(item: JsonObject) -> tuple[str, ...]:
    source_ref = text(item.get("source_ref"))
    return (source_ref,) if source_ref else ()


def json_objects(value: JsonValue) -> tuple[JsonObject, ...]:
    return tuple(item for item in value if isinstance(item, dict)) if isinstance(value, list) else ()


def strings(value: JsonValue) -> tuple[str, ...]:
    return tuple(item for item in value if isinstance(item, str) and item) if isinstance(value, list) else ()


def text(value: JsonValue) -> str:
    return value if isinstance(value, str) else ""


def int_value(value: JsonValue) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def confidence(value: JsonValue) -> float:
    if isinstance(value, (float, int)) and not isinstance(value, bool) and 0.0 <= value <= 1.0:
        return round(float(value), 2)
    return 0.0


def unique(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))
