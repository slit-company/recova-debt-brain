from __future__ import annotations

from typing import Dict, List, Union

from trustgraph_legal.debtor_context_types import DebtorGraphPayload, FactAssertion, GraphSnapshot
from trustgraph_legal.route_candidates import evaluate_route_candidates, load_route_templates

JsonScalar = Union[str, int, float, bool, type(None)]
JsonValue = Union[JsonScalar, List["JsonValue"], Dict[str, "JsonValue"]]


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
    assert bank.blocking_facts == ("insolvency_stay",)
    assert bank.source_fact_ids == ("fact:bank", "fact:insolvency-stay", "fact:title")
    assert bank.no_direct_execution is True

    insolvency = candidates["insolvency_review_or_cease_collection"]
    assert insolvency.status == "review_required"
    assert insolvency.missing_facts == ()
    assert insolvency.blocking_facts == ("stay_or_discharge_detected",)
    assert insolvency.no_direct_execution is True


def _candidate(graph: DebtorGraphPayload, route_id: str):
    for candidate in evaluate_route_candidates(graph):
        if candidate.route_id == route_id:
            return candidate
    raise AssertionError("missing route candidate: {}".format(route_id))


def _graph(
    *facts: FactAssertion,
    stop_gates: tuple[Dict[str, JsonValue], ...] = (),
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
        case_packets=(),
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
