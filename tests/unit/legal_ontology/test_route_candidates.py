from __future__ import annotations

import json
from pathlib import Path
from typing import Final, TypeAlias

import pytest
from pydantic import JsonValue as PydanticJsonValue
from pydantic import TypeAdapter

from trustgraph_legal.debtor_context_types import DebtorGraphPayload, FactAssertion, GraphSnapshot, RouteCandidate
from trustgraph_legal.route_candidates import evaluate_route_candidates, load_route_templates

JsonValue: TypeAlias = PydanticJsonValue
JsonObject = dict[str, JsonValue]
JSON_OBJECT_ADAPTER: Final = TypeAdapter[JsonObject](JsonObject)


def test_route_templates_load_advisory_resource_contract() -> None:
    # Given: the curated Todo 4 route resources.
    templates = load_route_templates()

    # When: route templates are normalized for matching.
    by_id = {template.route_id: template for template in templates}

    # Then: all 18 route candidates remain advisory-only and sourced.
    assert len(templates) == 18
    assert by_id["bank_account_attachment"].required_fact_handles == (
        "enforceable_title",
        "third_party_debtor_bank_hint",
    )
    assert by_id["bank_account_attachment"].legal_source_refs == (
        "kr-law-l009290-m268837-a223",
        "kr-law-l009290-m268837-a229",
        "kr-law-l009290-m268837-a246",
    )
    assert all(template.no_direct_execution for template in templates)
    assert all(template.direct_execution_allowed is False for template in templates)


def test_bank_route_is_possible_when_title_and_bank_hint_are_sourced() -> None:
    # Given: a debtor graph with source-backed title and bank-account hint facts.
    graph = _graph(
        _fact("fact:title", "enforceable_title", 0.91),
        _fact("fact:bank", "third_party_debtor_bank_hint", 0.84),
    )

    # When: route candidates are evaluated from the curated resource contract.
    candidate = _candidate(graph, "bank_account_attachment")

    # Then: the bank route is advisory-possible without claiming direct execution.
    assert candidate.status == "possible"
    assert candidate.route_label == "Bank account attachment"
    assert candidate.required_facts == (
        "enforceable_title",
        "third_party_debtor_bank_hint",
    )
    assert candidate.missing_facts == ()
    assert candidate.blocking_facts == ()
    assert candidate.source_fact_ids == ("fact:bank", "fact:title")
    assert candidate.confidence == 0.84
    assert candidate.no_direct_execution is True


def test_bank_route_attaches_curated_law_metadata() -> None:
    # Given: a debtor graph with source-backed title and bank-account hint facts.
    graph = _graph(
        _fact("fact:title", "enforceable_title", 0.91),
        _fact("fact:bank", "third_party_debtor_bank_hint", 0.84),
    )

    # When: route candidates are evaluated from the curated legal source map.
    candidate = _candidate(graph, "bank_account_attachment")

    # Then: each legal ref carries the law id, MST, and article metadata needed for review.
    assert candidate.status == "possible"
    assert candidate.legal_source_refs == (
        "kr-law-l009290-m268837-a223|lawId=009290|MST=268837|article=제223조|effective_date=2026-02-01|retrieval_status=retrieved|review_status=approved_static_v0",
        "kr-law-l009290-m268837-a229|lawId=009290|MST=268837|article=제229조|effective_date=2026-02-01|retrieval_status=retrieved|review_status=approved_static_v0",
        "kr-law-l009290-m268837-a246|lawId=009290|MST=268837|article=제246조|effective_date=2026-02-01|retrieval_status=retrieved|review_status=approved_static_v0",
    )
    assert candidate.no_direct_execution is True


def test_asset_routes_surface_missing_facts_instead_of_false_possible() -> None:
    # Given: a debtor graph with only an enforceable title.
    graph = _graph(_fact("fact:title", "enforceable_title", 0.91))

    # When: asset and income route candidates are evaluated.
    candidates = {candidate.route_id: candidate for candidate in evaluate_route_candidates(graph)}

    # Then: each route names the exact missing handle instead of becoming possible.
    assert candidates["bank_account_attachment"].status == "missing_facts"
    assert candidates["bank_account_attachment"].missing_facts == ("third_party_debtor_bank_hint",)
    assert candidates["wage_attachment"].status == "missing_facts"
    assert candidates["wage_attachment"].missing_facts == ("employer_hint",)
    assert candidates["real_estate_auction"].status == "missing_facts"
    assert candidates["real_estate_auction"].missing_facts == ("real_estate_registry_asset",)


def test_case_stopgate_reason_codes_are_route_blockers() -> None:
    # Given: a debtor graph with route facts and a case packet that fails StopGate checks.
    graph = _graph(
        _fact("fact:title", "enforceable_title", 0.91),
        _fact("fact:bank", "third_party_debtor_bank_hint", 0.84),
        case_packets=(_case_packet_missing_execution_clause(),),
    )

    # When: route candidates are evaluated.
    bank = _candidate(graph, "bank_account_attachment")

    # Then: evaluated StopGate reason codes become review blockers on the route.
    assert bank.status == "review_required"
    assert "missing_execution_clause" in bank.blocking_facts
    assert bank.no_direct_execution is True


def test_stopgate_reason_codes_do_not_block_unaffected_title_routes() -> None:
    # Given: a title-acquisition route with its facts plus an unrelated execution StopGate.
    graph = _graph(
        _fact("fact:claim", "claim_basis", 0.91),
        _fact("fact:identity", "debtor_identity", 0.88),
        _fact("fact:service", "service_path", 0.86),
        case_packets=(_case_packet_missing_execution_clause(),),
    )

    # When: route candidates are evaluated.
    candidate = _candidate(graph, "title_acquisition_payment_order")

    # Then: execution-clause StopGates do not review-block title acquisition.
    assert candidate.status == "possible"
    assert "missing_execution_clause" not in candidate.blocking_facts


def test_insolvency_signal_blocks_collection_and_marks_cease_route_for_review() -> None:
    # Given: a debtor graph with a bank route's required facts plus insolvency risk.
    graph = _graph(
        _fact("fact:title", "enforceable_title", 0.91),
        _fact("fact:bank", "third_party_debtor_bank_hint", 0.84),
        _fact("fact:insolvency-stay", "insolvency_stay", 0.93),
        _fact("fact:insolvency-signal", "insolvency_signal", 0.88),
        stop_gates=(
            {
                "reason_code": "stay_or_discharge_detected",
                "confidence": 0.93,
            },
        ),
    )

    # When: route candidates are evaluated.
    candidates = {candidate.route_id: candidate for candidate in evaluate_route_candidates(graph)}

    # Then: direct collection routes are blocked and the cease/review route is review-only.
    bank = candidates["bank_account_attachment"]
    assert bank.status == "blocked"
    assert bank.blocking_facts == ("insolvency_stay", "stay_or_discharge_detected")
    assert bank.source_fact_ids == ("fact:bank", "fact:insolvency-stay", "fact:title")
    assert bank.no_direct_execution is True

    insolvency = candidates["insolvency_review_or_cease_collection"]
    assert insolvency.status == "review_required"
    assert insolvency.missing_facts == ()
    assert insolvency.blocking_facts == ("stay_or_discharge_detected",)
    assert insolvency.no_direct_execution is True


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("review_status", "draft"),
        ("review_status", "deprecated"),
        ("review_status", "future-only"),
        ("retrieval_status", "draft"),
        ("effective_date", "2999-01-01"),
    ],
)
def test_unapproved_route_legal_source_status_requires_review(tmp_path: Path, field: str, value: str) -> None:
    # Given: an otherwise possible bank route whose first law source is not approved for routing.
    legal_sources_path = _route_sources_with_source_field(tmp_path, field, value)
    graph = _graph(
        _fact("fact:title", "enforceable_title", 0.91),
        _fact("fact:bank", "third_party_debtor_bank_hint", 0.84),
    )

    # When: route candidates are evaluated with that curated source map.
    candidate = _candidate(
        graph,
        "bank_account_attachment",
        legal_sources_path=legal_sources_path,
    )

    # Then: draft/deprecated/future-only law sources cannot clear a route.
    assert candidate.status == "review_required"
    assert candidate.no_direct_execution is True
    assert "{}={}".format(field, value) in candidate.legal_source_refs[0]


def _candidate(
    graph: DebtorGraphPayload,
    route_id: str,
    *,
    legal_sources_path: Path | None = None,
) -> RouteCandidate:
    if legal_sources_path is None:
        candidates = evaluate_route_candidates(graph)
    else:
        candidates = evaluate_route_candidates(graph, legal_sources_path=legal_sources_path)
    for candidate in candidates:
        if candidate.route_id == route_id:
            return candidate
    raise AssertionError("missing route candidate: {}".format(route_id))


def _graph(
    *facts: FactAssertion,
    stop_gates: tuple[JsonObject, ...] = (),
    case_packets: tuple[JsonObject, ...] = (),
) -> DebtorGraphPayload:
    snapshot = GraphSnapshot(
        graph_snapshot_id="snapshot:routes-test",
        source_bundle_hash="sha256:route-test-bundle",
        generated_at="2026-07-06T00:00:00Z",
        fact_assertion_ids=tuple(fact.fact_id for fact in facts),
        route_candidate_ids=(),
    )
    return DebtorGraphPayload(
        debtor_graph_id="debtor-graph:routes-test",
        graph_snapshot=snapshot,
        identity_resolution={"status": "synthetic"},
        case_packets=case_packets,
        document_pages=(),
        document_assemblies=(),
        fact_assertions=facts,
        claims=(),
        enforcement_titles=(),
        procedure_episodes=(),
        asset_hints=(),
        stop_gates=stop_gates,
        route_candidates=(),
        review_items=(),
    )


def _fact(fact_id: str, predicate: str, confidence: float) -> FactAssertion:
    return FactAssertion(
        fact_id=fact_id,
        subject_id="debtor-graph:routes-test",
        predicate=predicate,
        object_value=True,
        confidence=confidence,
        source_refs=("fixture:route-candidates.md#L1",),
        source_document_id="document:route-candidates",
        source_hash="sha256:route-candidates",
        chunk_id="chunk:route-candidates:1",
        line_start=1,
        line_end=1,
        review_status="confirmed",
    )


def _case_packet_missing_execution_clause() -> JsonObject:
    return {
        "id": "case:route-stopgate",
        "entities": [
            {
                "id": "doc:title",
                "entity_type": "Document",
                "ontology_class": "legal-document",
                "value": "payment-order",
                "provenance": _case_provenance("doc:title"),
            },
        ],
        "edges": [],
        "findings": [],
        "evidence_keys": [],
    }


def _case_provenance(identifier: str) -> JsonObject:
    return {
        "document_id": "doc-for-{}".format(identifier),
        "source_ref": "fixture:route-stopgate.md#L1",
        "chunk_id": "chunk:route-stopgate:1",
        "line_start": 1,
        "line_end": 1,
        "confidence": 0.91,
    }


def _route_sources_with_source_field(tmp_path: Path, field: str, value: str) -> Path:
    source_path = Path("resources/legal_rules/debt_collection_route_sources_v0.json")
    payload = JSON_OBJECT_ADAPTER.validate_json(source_path.read_bytes())
    sources = payload["sources"]
    assert isinstance(sources, list)
    first_source = sources[0]
    assert isinstance(first_source, dict)
    first_source[field] = value
    target = tmp_path / "route-sources.json"
    _ = target.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return target
