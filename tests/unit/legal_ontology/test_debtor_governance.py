from __future__ import annotations

import json

from trustgraph_legal.debtor_context_types import (
    DebtorGraphPayload,
    DocumentAssembly,
    FactAssertion,
    GraphSnapshot,
    RouteCandidate,
)
from trustgraph_legal.debtor_governance import (
    ManualFactReviewDecision,
    build_debtor_governance_payload,
)
from trustgraph_legal.debtor_governance_models import JsonObject, JsonValue


def test_builds_redacted_service_records_for_graph_review_states() -> None:
    # Given: a debtor graph with unknown assembly, unresolved identity, conflicting facts, and a blocked route.
    graph = _graph(
        _fact("fact:identity-a", "debtor_identity", "identity-value-alpha", source_ref="fixture:contact-token-a.md#L1"),
        _fact("fact:identity-b", "debtor_identity", "identity-value-beta", source_ref="fixture:contact-token-b.md#L2"),
        assemblies=(
            _assembly(
                "assembly:unknown",
                "unknown",
                ("fixture:unknown-contact-token.md#L1",),
            ),
        ),
        routes=(
            _route(
                "bank_account_attachment",
                "blocked",
                blocking_facts=("insolvency_stay",),
                source_fact_ids=("fact:identity-a",),
            ),
        ),
    )

    # When: service-side governance records are built from graph outputs.
    payload = build_debtor_governance_payload(graph)
    serialized = payload.to_json()

    # Then: every expected review signal becomes a stable redacted record.
    records = _records(serialized)
    by_kind = {str(record["kind"]): record for record in records}
    assert {"unknown_assembly", "identity_unresolved", "conflicting_fact_signal", "blocked_route"} <= set(by_kind)
    for record in by_kind.values():
        assert {
            "record_id",
            "kind",
            "subject_ref",
            "reason_code",
            "severity",
            "review_status",
            "source_refs",
            "suggested_action",
            "pii_profile",
            "audit",
        } <= set(record)
        assert record["pii_profile"] == {"raw_text_included": False, "source_text_included": False}
        assert _json_object(record["audit"])["resource_mutation"] is False
    encoded = json.dumps(serialized, ensure_ascii=False)
    assert "identity-value-alpha" not in encoded
    assert "identity-value-beta" not in encoded
    assert "RAW OCR" not in encoded
    assert serialized["production_resources_modified"] is False


def test_legal_source_review_states_are_recorded_without_mutating_resources() -> None:
    # Given: a route candidate carrying draft, future, and unretrieved legal-source metadata.
    graph = _graph(
        _fact("fact:title", "enforceable_title", True),
        routes=(
            _route(
                "bank_account_attachment",
                "review_required",
                legal_source_refs=(
                    "kr-law-a|retrieval_status=draft|review_status=approved_static_v0|effective_date=2026-01-01",
                    "kr-law-b|retrieval_status=retrieved|review_status=approved_static_v0|effective_date=2999-01-01",
                    "kr-law-c|retrieval_status=unretrieved|review_status=approved_static_v0|effective_date=2026-01-01",
                ),
            ),
        ),
    )

    # When: governance records are derived.
    payload = build_debtor_governance_payload(graph).to_json()

    # Then: legal-source records name review reasons and keep the resources read-only.
    source_records = [record for record in _records(payload) if record["kind"] == "legal_source_review"]
    assert {str(record["reason_code"]) for record in source_records} == {
        "legal_source_review_status",
        "legal_source_future_effective_date",
        "legal_source_unretrieved",
    }
    assert all(record["review_status"] == "review_required" for record in source_records)
    assert payload["production_resources_modified"] is False


def test_manual_fact_review_decisions_are_serializable_service_records() -> None:
    # Given: a manual reviewer decision over a fact id and source refs only.
    decision = ManualFactReviewDecision(
        fact_id="fact:claim-balance",
        decision="rejected",
        reviewer_ref="reviewer:legal-ops",
        reason_code="amount_conflicts_with_source",
        source_refs=("fixture:claim.md#L7",),
    )

    # When: the decision is included in the governance payload.
    payload = build_debtor_governance_payload(_graph(), manual_decisions=(decision,)).to_json()

    # Then: the decision is preserved as an audit-safe record, not a production mutation.
    manual_records = [record for record in _records(payload) if record["kind"] == "manual_fact_review"]
    assert len(manual_records) == 1
    record = manual_records[0]
    assert record["subject_ref"] == "fact:claim-balance"
    assert record["review_status"] == "rejected"
    assert record["reason_code"] == "amount_conflicts_with_source"
    audit = _json_object(record["audit"])
    assert audit["actor_ref"] == "reviewer:legal-ops"
    assert audit["resource_mutation"] is False


def _graph(
    *facts: FactAssertion,
    assemblies: tuple[DocumentAssembly, ...] = (),
    routes: tuple[RouteCandidate, ...] = (),
) -> DebtorGraphPayload:
    return DebtorGraphPayload(
        debtor_graph_id="debtor-graph:governance",
        graph_snapshot=GraphSnapshot(
            graph_snapshot_id="snapshot:governance",
            source_bundle_hash="sha256:governance-bundle",
            generated_at="2026-07-06T00:00:00Z",
            fact_assertion_ids=tuple(fact.fact_id for fact in facts),
            route_candidate_ids=tuple(route.route_id for route in routes),
        ),
        identity_resolution={
            "status": "identity_unresolved",
            "source_bundle_hash": "sha256:governance-bundle",
        },
        case_packets=(
            {
                "case_packet_id": "case-packet:governance",
                "source_refs": ["fixture:case.md#L1"],
            },
        ),
        document_pages=(),
        document_assemblies=assemblies,
        fact_assertions=facts,
        claims=(),
        enforcement_titles=(),
        procedure_episodes=(),
        asset_hints=(),
        stop_gates=(),
        route_candidates=routes,
        review_items=(
            {
                "review_item_id": "review:identity-unresolved",
                "reason_code": "identity_unresolved",
            },
        ),
    )


def _fact(
    fact_id: str,
    predicate: str,
    value: JsonValue,
    *,
    source_ref: str = "fixture:governance.md#L1",
) -> FactAssertion:
    return FactAssertion(
        fact_id=fact_id,
        subject_id="debtor-graph:governance",
        predicate=predicate,
        object_value=value,
        confidence=0.91,
        source_refs=(source_ref,),
        source_document_id="document:governance",
        source_hash="sha256:governance",
        chunk_id="chunk:governance:1",
        line_start=1,
        line_end=1,
        review_status="verified",
    )


def _assembly(
    assembly_id: str,
    document_type: str,
    source_refs: tuple[str, ...],
) -> DocumentAssembly:
    return DocumentAssembly(
        assembly_id=assembly_id,
        document_id="document:{}".format(assembly_id.rsplit(":", 1)[-1]),
        canonical_document_type=document_type,
        page_ids=("page:governance",),
        source_refs=source_refs,
        source_hashes=("sha256:unknown",),
        confidence=0.44,
        review_status="needs_review",
    )


def _route(
    route_id: str,
    status: str,
    *,
    blocking_facts: tuple[str, ...] = (),
    source_fact_ids: tuple[str, ...] = (),
    legal_source_refs: tuple[str, ...] = ("kr-law-ok|retrieval_status=retrieved|review_status=approved_static_v0|effective_date=2026-01-01",),
) -> RouteCandidate:
    return RouteCandidate(
        route_id=route_id,
        route_label=route_id.replace("_", " ").title(),
        status=status,
        required_facts=("enforceable_title",),
        missing_facts=(),
        blocking_facts=blocking_facts,
        legal_source_refs=legal_source_refs,
        source_fact_ids=source_fact_ids,
        confidence=0.82,
        review_status=status,
    )


def _records(payload: JsonObject) -> list[JsonObject]:
    value = payload["records"]
    assert isinstance(value, list)
    return [_json_object(item) for item in value]


def _json_object(value: JsonValue) -> JsonObject:
    assert isinstance(value, dict)
    return value
