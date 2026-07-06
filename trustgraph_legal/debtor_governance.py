from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Sequence
from typing import Protocol, TYPE_CHECKING

from trustgraph_legal.debtor_governance_models import (
    DebtorGovernancePayload,
    JsonObject,
    ManualFactReviewDecision,
    RecordDraft,
    record,
)
from trustgraph_legal.debtor_governance_sources import (
    legal_source_reason_codes,
    missing_text,
    unknown_document_type,
)

if TYPE_CHECKING:
    from trustgraph_legal.debtor_context_types import DebtorGraphPayload, FactAssertion

__all__ = ["ManualFactReviewDecision", "build_debtor_governance_payload"]
ROUTE_REVIEW_STATUSES = frozenset({"blocked", "review_required"})
APPROVAL_DECISIONS = frozenset({"accepted", "approved", "verified"})


class _RouteLike(Protocol):
    @property
    def route_id(self) -> str: ...

    @property
    def status(self) -> str: ...

    @property
    def legal_source_refs(self) -> tuple[str, ...]: ...

    @property
    def source_fact_ids(self) -> tuple[str, ...]: ...


def build_debtor_governance_payload(
    graph: DebtorGraphPayload,
    manual_decisions: Sequence[ManualFactReviewDecision] = (),
) -> DebtorGovernancePayload:
    records = (
        _unknown_assembly_records(graph)
        + _identity_records(graph)
        + _conflict_records(graph.fact_assertions)
        + _route_records(graph)
        + _legal_source_records(graph)
        + tuple(_manual_record(decision) for decision in manual_decisions)
    )
    return DebtorGovernancePayload(
        debtor_graph_id=graph.debtor_graph_id,
        graph_snapshot_id=graph.graph_snapshot.graph_snapshot_id,
        records=tuple(sorted(records, key=lambda item: str(item["record_id"]))),
    )


def _unknown_assembly_records(graph: DebtorGraphPayload) -> tuple[JsonObject, ...]:
    return tuple(
        record(
            RecordDraft(
                "unknown_assembly",
                assembly.assembly_id,
                "unknown_assembly",
                "medium",
                "review_required",
                assembly.source_refs,
                "Route assembly to document-type governance review before legal-risk use.",
            )
        )
        for assembly in graph.document_assemblies
        if unknown_document_type(assembly.canonical_document_type)
    )


def _identity_records(graph: DebtorGraphPayload) -> tuple[JsonObject, ...]:
    status = graph.identity_resolution.get("status")
    if not isinstance(status, str) or "unresolved" not in status.lower():
        return ()
    return (
        record(
            RecordDraft(
                "identity_unresolved",
                graph.debtor_graph_id,
                "identity_unresolved",
                "high",
                "review_required",
                _graph_source_refs(graph),
                "Require identity evidence before merging debtor context across source bundles.",
                _fact_ids_for_predicate(graph.fact_assertions, "debtor_identity"),
            )
        ),
    )


def _conflict_records(facts: Iterable[FactAssertion]) -> tuple[JsonObject, ...]:
    by_predicate: dict[str, list[FactAssertion]] = {}
    for fact in facts:
        by_predicate.setdefault(fact.predicate, []).append(fact)
    return tuple(
        _conflict_record(predicate, group)
        for predicate, group in sorted(by_predicate.items())
        if len({_fact_value_fingerprint(fact) for fact in group}) > 1
    )


def _conflict_record(predicate: str, facts: Sequence[FactAssertion]) -> JsonObject:
    severity = "high" if predicate in {"claim_balance", "debtor_identity"} else "medium"
    return record(
        RecordDraft(
            "conflicting_fact_signal",
            "predicate:{}".format(predicate),
            "conflicting_fact_values",
            severity,
            "review_required",
            tuple(source_ref for fact in facts for source_ref in fact.source_refs),
            "Review source-backed fact values and accept one value before route use.",
            tuple(sorted(fact.fact_id for fact in facts)),
        )
    )


def _route_records(graph: DebtorGraphPayload) -> tuple[JsonObject, ...]:
    return tuple(_route_record(route) for route in graph.route_candidates if route.status in ROUTE_REVIEW_STATUSES)


def _route_record(route: _RouteLike) -> JsonObject:
    blocked = route.status == "blocked"
    return record(
        RecordDraft(
            "blocked_route" if blocked else "route_review_required",
            route.route_id,
            "route_{}".format(route.status),
            "high" if blocked else "medium",
            "review_required",
            route.legal_source_refs,
            "Keep route advisory-only until blockers and legal-source review states clear.",
            route.source_fact_ids,
        )
    )


def _legal_source_records(graph: DebtorGraphPayload) -> tuple[JsonObject, ...]:
    records: list[JsonObject] = []
    for route in graph.route_candidates:
        for source_ref in route.legal_source_refs:
            records.extend(_legal_source_records_for_ref(source_ref, route.source_fact_ids))
    return tuple(records)


def _legal_source_records_for_ref(source_ref: str, source_fact_ids: tuple[str, ...]) -> tuple[JsonObject, ...]:
    return tuple(
        record(
            RecordDraft(
                "legal_source_review",
                source_ref.split("|", 1)[0],
                reason_code,
                "high",
                "review_required",
                (source_ref,),
                "Review legal-source metadata before treating the route as cleared.",
                source_fact_ids,
            )
        )
        for reason_code in legal_source_reason_codes(source_ref)
    )


def _manual_record(decision: ManualFactReviewDecision) -> JsonObject:
    review_status = decision.decision
    reason_code = decision.reason_code
    action = "Record manual fact review service-side; do not mutate graph facts automatically."
    if decision.decision in APPROVAL_DECISIONS and missing_text(decision.approval_evidence_ref):
        review_status = "rejected"
        reason_code = "missing_manual_fact_approval_metadata"
        action = "Attach approval_evidence_ref before accepting a manual fact decision."
    return record(
        RecordDraft(
            "manual_fact_review",
            decision.fact_id,
            reason_code,
            "high" if review_status == "rejected" else "medium",
            review_status,
            decision.source_refs,
            action,
            (decision.fact_id,),
            decision.reviewer_ref,
            decision.reviewed_at,
            decision.reviewed_at,
        )
    )


def _graph_source_refs(graph: DebtorGraphPayload) -> tuple[str, ...]:
    refs = [source_ref for assembly in graph.document_assemblies for source_ref in assembly.source_refs]
    return tuple(refs + [source_ref for packet in graph.case_packets for source_ref in _json_source_refs(packet)])


def _json_source_refs(value: JsonObject) -> tuple[str, ...]:
    refs = value.get("source_refs")
    if isinstance(refs, list):
        return tuple(item for item in refs if isinstance(item, str))
    source_ref = value.get("source_ref")
    return (source_ref,) if isinstance(source_ref, str) else ()


def _fact_ids_for_predicate(facts: Iterable[FactAssertion], predicate: str) -> tuple[str, ...]:
    return tuple(sorted(fact.fact_id for fact in facts if fact.predicate == predicate))


def _fact_value_fingerprint(fact: FactAssertion) -> str:
    payload = json.dumps(fact.object_value, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
