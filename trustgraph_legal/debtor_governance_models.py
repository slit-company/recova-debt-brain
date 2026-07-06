from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final, Union

from trustgraph_legal.debtor_governance_sources import safe_text

SCHEMA_VERSION: Final = "recova-debtor-governance/v1"
GENERATED_AT: Final = "2026-07-06T00:00:00Z"
JsonScalar = Union[str, int, float, bool, None]
JsonValue = Union[JsonScalar, list["JsonValue"], dict[str, "JsonValue"]]
JsonObject = dict[str, JsonValue]
__all__ = [
    "DebtorGovernancePayload",
    "JsonObject",
    "JsonValue",
    "ManualFactReviewDecision",
    "RecordDraft",
    "record",
]


@dataclass(frozen=True)
class ManualFactReviewDecision:
    fact_id: str
    decision: str
    reviewer_ref: str
    reason_code: str
    source_refs: tuple[str, ...]
    approval_evidence_ref: str = ""
    reviewed_at: str = GENERATED_AT


@dataclass(frozen=True)
class RecordDraft:
    kind: str
    subject_ref: str
    reason_code: str
    severity: str
    review_status: str
    source_refs: tuple[str, ...]
    suggested_action: str
    source_fact_ids: tuple[str, ...] = ()
    actor_ref: str = ""
    created_at: str = GENERATED_AT
    updated_at: str = GENERATED_AT


@dataclass(frozen=True)
class DebtorGovernancePayload:
    debtor_graph_id: str
    graph_snapshot_id: str
    records: tuple[JsonObject, ...]

    def to_json(self) -> JsonObject:
        return {
            "schema_version": SCHEMA_VERSION,
            "debtor_graph_id": self.debtor_graph_id,
            "graph_snapshot_id": self.graph_snapshot_id,
            "summary": _summary(self.records),
            "production_resources_modified": False,
            "production_ontology_modified": False,
            "production_routes_modified": False,
            "production_legal_sources_modified": False,
            "pii_profile": pii_profile(),
            "records": list(self.records),
        }


def record(draft: RecordDraft) -> JsonObject:
    subject_ref = safe_text(draft.subject_ref)
    source_refs = tuple(sorted({safe_text(source_ref) for source_ref in draft.source_refs if source_ref}))
    source_fact_ids = tuple(sorted(safe_text(fact_id) for fact_id in draft.source_fact_ids))
    return {
        "record_id": _record_id(draft.kind, subject_ref, draft.reason_code, source_refs, source_fact_ids),
        "kind": draft.kind,
        "subject_ref": subject_ref,
        "reason_code": draft.reason_code,
        "severity": draft.severity,
        "review_status": draft.review_status,
        "source_refs": list(source_refs),
        "source_fact_ids": list(source_fact_ids),
        "suggested_action": draft.suggested_action,
        "pii_profile": pii_profile(),
        "audit": _audit(draft),
    }


def pii_profile() -> JsonObject:
    return {"raw_text_included": False, "source_text_included": False}


def _audit(draft: RecordDraft) -> JsonObject:
    return {
        "created_at": draft.created_at,
        "updated_at": draft.updated_at,
        "actor_ref": draft.actor_ref,
        "resource_mutation": False,
        "production_ontology_modified": False,
        "production_routes_modified": False,
        "production_legal_sources_modified": False,
        "no_direct_execution": True,
    }


def _record_id(
    kind: str,
    subject_ref: str,
    reason_code: str,
    source_refs: tuple[str, ...],
    source_fact_ids: tuple[str, ...],
) -> str:
    encoded = json.dumps(
        {
            "kind": kind,
            "reason_code": reason_code,
            "source_fact_ids": list(source_fact_ids),
            "source_refs": list(source_refs),
            "subject_ref": subject_ref,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return "governance:{}:{}".format(kind, hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:20])


def _summary(records: tuple[JsonObject, ...]) -> JsonObject:
    return {
        "records": len(records),
        "by_kind": _counts(_record_text(record_item, "kind") for record_item in records),
        "by_review_status": _counts(_record_text(record_item, "review_status") for record_item in records),
        "by_severity": _counts(_record_text(record_item, "severity") for record_item in records),
    }


def _record_text(record_item: JsonObject, field: str) -> str:
    value = record_item.get(field)
    return value if isinstance(value, str) else ""


def _counts(values: Iterable[str]) -> JsonObject:
    counts: dict[str, JsonValue] = {}
    for value in values:
        current = counts.get(value)
        counts[value] = current + 1 if isinstance(current, int) and not isinstance(current, bool) else 1
    return counts
