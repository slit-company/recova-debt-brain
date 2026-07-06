from __future__ import annotations

from dataclasses import replace
from typing import Dict, List, Union

from trustgraph_legal.debtor_context_types import (
    DebtorGraphPayload,
    FactAssertion,
    GraphSnapshot,
    RouteCandidate,
)
from trustgraph_legal.debtor_snapshots import (
    diff_snapshots,
    replay_snapshot,
    validate_snapshot_provenance,
)

JsonScalar = Union[str, int, float, bool, type(None)]
JsonValue = Union[JsonScalar, List["JsonValue"], Dict[str, "JsonValue"]]


def test_replay_snapshot_is_stable_and_changes_when_fact_content_changes() -> None:
    # Given: two equivalent graph payloads and one payload with the same fact id but changed semantics.
    baseline = _graph(_fact("fact:title", "enforceable_title", True))
    equivalent = _graph(_fact("fact:title", "enforceable_title", True))
    changed = _graph(_fact("fact:title", "enforceable_title", "needs_review"))

    # When: snapshot replay digests are rebuilt from the graph payloads.
    baseline_replay = replay_snapshot(baseline)
    equivalent_replay = replay_snapshot(equivalent)
    changed_replay = replay_snapshot(changed)
    diff = diff_snapshots(baseline, changed)

    # Then: stable input replays to the same id, while a semantic fact change is visible.
    assert baseline_replay.replay_snapshot_id == equivalent_replay.replay_snapshot_id
    assert baseline_replay.replay_snapshot_id != changed_replay.replay_snapshot_id
    assert diff.changed_fact_ids == ("fact:title",)
    assert diff.added_fact_ids == ()
    assert diff.removed_fact_ids == ()


def test_diff_surfaces_source_bundle_route_and_version_changes() -> None:
    # Given: graph snapshots whose bundle hash, route state, and legal rule-source version changed.
    route = _route("bank_account_attachment", "possible")
    previous = _graph(_fact("fact:title", "enforceable_title", True), route_candidates=(route,))
    current = _graph(
        _fact("fact:title", "enforceable_title", True),
        source_bundle_hash="sha256:changed-bundle",
        legal_rule_source_version="recova-legal-rule-sources@v1",
        route_candidates=(replace(route, status="review_required"),),
    )

    # When: the two replay snapshots are compared.
    diff = diff_snapshots(previous, current)
    version_changes = {change.field_name: change for change in diff.version_changes}

    # Then: every non-bundle semantic change appears in the diff contract.
    assert diff.source_bundle_changed is True
    assert diff.previous_source_bundle_hash == "sha256:bundle"
    assert diff.current_source_bundle_hash == "sha256:changed-bundle"
    assert diff.changed_route_candidate_ids == ("bank_account_attachment",)
    assert version_changes["legal_rule_source_version"].previous_value == "recova-legal-rule-sources@v0"
    assert version_changes["legal_rule_source_version"].current_value == "recova-legal-rule-sources@v1"
    assert diff.legacy_graph_snapshot_id_collision is True


def test_provenance_validation_accepts_source_grounded_facts() -> None:
    # Given: a graph with a non-derived fact carrying source refs and span metadata.
    graph = _graph(_fact("fact:title", "enforceable_title", True))

    # When: snapshot provenance is validated.
    report = validate_snapshot_provenance(graph)

    # Then: the graph is accepted without issues.
    assert report.valid is True
    assert report.issues == ()


def test_provenance_validation_reports_missing_and_placeholder_sources() -> None:
    # Given: serialized graph facts with missing and placeholder provenance.
    graph = _graph(
        _fact("fact:missing", "enforceable_title", True),
        _fact("fact:placeholder", "third_party_debtor_bank_hint", True),
    ).to_json()
    facts = graph["fact_assertions"]
    assert isinstance(facts, list)
    first_fact = facts[0]
    second_fact = facts[1]
    assert isinstance(first_fact, dict)
    assert isinstance(second_fact, dict)
    first_fact.pop("source_ref")
    first_fact["source_refs"] = []
    second_fact["source_ref"] = "missing"
    second_fact["source_refs"] = ["missing"]

    # When: snapshot provenance is validated from the JSON boundary.
    report = validate_snapshot_provenance(graph)

    # Then: both invalid provenance shapes are explicit and deterministic.
    assert report.valid is False
    assert {(issue.fact_id, issue.reason_code) for issue in report.issues} == {
        ("fact:missing", "missing_source_ref"),
        ("fact:placeholder", "placeholder_source_ref"),
    }


def test_provenance_validation_reports_invalid_source_metadata() -> None:
    # Given: serialized facts with invalid source metadata beyond source_ref.
    graph = _graph(
        _fact("fact:bad-source", "enforceable_title", True),
        _fact("fact:bad-span", "third_party_debtor_bank_hint", True),
    ).to_json()
    facts = graph["fact_assertions"]
    assert isinstance(facts, list)
    first_fact = facts[0]
    second_fact = facts[1]
    assert isinstance(first_fact, dict)
    assert isinstance(second_fact, dict)
    first_fact["source_document_id"] = "placeholder:doc"
    first_fact["source_hash"] = "not-a-sha"
    first_fact["chunk_id"] = "missing"
    first_fact["extractor_version"] = ""
    first_fact["ontology_version"] = "todo"
    first_fact["confidence"] = 1.4
    first_fact["review_status"] = ""
    second_fact["line_start"] = 8
    second_fact["line_end"] = 3

    # When: snapshot provenance is validated from the JSON boundary.
    report = validate_snapshot_provenance(graph)

    # Then: each invalid provenance contract field is visible for review.
    assert report.valid is False
    assert {(issue.fact_id, issue.reason_code) for issue in report.issues} >= {
        ("fact:bad-source", "placeholder_source_document_id"),
        ("fact:bad-source", "invalid_source_hash"),
        ("fact:bad-source", "placeholder_chunk_id"),
        ("fact:bad-source", "missing_extractor_version"),
        ("fact:bad-source", "placeholder_ontology_version"),
        ("fact:bad-source", "invalid_confidence"),
        ("fact:bad-source", "missing_review_status"),
        ("fact:bad-span", "invalid_line_span"),
    }


def test_derived_facts_require_source_or_derivation_evidence() -> None:
    # Given: one derived fact with explicit derivation evidence and one without evidence.
    graph = _graph(
        _fact("fact:derived-ok", "enforceable_title", True, derived=True),
        _fact("fact:derived-missing", "third_party_debtor_bank_hint", True, derived=True),
    ).to_json()
    facts = graph["fact_assertions"]
    assert isinstance(facts, list)
    ok_fact = facts[0]
    missing_fact = facts[1]
    assert isinstance(ok_fact, dict)
    assert isinstance(missing_fact, dict)
    ok_fact["source_refs"] = []
    ok_fact["source_ref"] = ""
    ok_fact["derivation_evidence"] = {
        "source_fact_ids": ["fact:source"],
        "derivation_method": "document_type_projection",
    }
    missing_fact["source_refs"] = []
    missing_fact["source_ref"] = ""

    # When: derived fact provenance is validated.
    report = validate_snapshot_provenance(graph)

    # Then: only the derived fact without derivation evidence is rejected.
    assert report.valid is False
    assert {(issue.fact_id, issue.reason_code) for issue in report.issues} == {
        ("fact:derived-missing", "missing_derivation_evidence"),
    }


def test_replay_snapshot_ignores_raw_text_fields() -> None:
    # Given: two serialized graphs that only differ by raw text-like fields.
    previous = _graph(_fact("fact:title", "enforceable_title", True)).to_json()
    current = _graph(_fact("fact:title", "enforceable_title", True)).to_json()
    previous_facts = previous["fact_assertions"]
    current_facts = current["fact_assertions"]
    assert isinstance(previous_facts, list)
    assert isinstance(current_facts, list)
    previous_fact = previous_facts[0]
    current_fact = current_facts[0]
    assert isinstance(previous_fact, dict)
    assert isinstance(current_fact, dict)
    previous_fact["raw_text"] = "RAW OCR SHOULD NOT BE SNAPSHOTTED"
    current_fact["raw_text"] = "CHANGED RAW OCR SHOULD STILL BE IGNORED"

    # When: replay snapshots and diffs are built.
    previous_replay = replay_snapshot(previous)
    current_replay = replay_snapshot(current)
    diff = diff_snapshots(previous, current)

    # Then: raw text fields do not affect replay ids or changed-fact reporting.
    assert previous_replay.replay_snapshot_id == current_replay.replay_snapshot_id
    assert diff.changed_fact_ids == ()


def _graph(
    *facts: FactAssertion,
    source_bundle_hash: str = "sha256:bundle",
    legal_rule_source_version: str = "recova-legal-rule-sources@v0",
    route_candidates: tuple[RouteCandidate, ...] = (),
) -> DebtorGraphPayload:
    snapshot = GraphSnapshot(
        graph_snapshot_id="snapshot:bundle-only",
        source_bundle_hash=source_bundle_hash,
        generated_at="2026-07-06T00:00:00Z",
        fact_assertion_ids=tuple(fact.fact_id for fact in facts),
        route_candidate_ids=tuple(candidate.route_id for candidate in route_candidates),
        legal_rule_source_version=legal_rule_source_version,
    )
    return DebtorGraphPayload(
        debtor_graph_id="debtor-graph:test",
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
        stop_gates=(),
        route_candidates=route_candidates,
        review_items=(),
    )


def _fact(fact_id: str, predicate: str, value: JsonValue, derived: bool = False) -> FactAssertion:
    return FactAssertion(
        fact_id=fact_id,
        subject_id="debtor-graph:test",
        predicate=predicate,
        object_value=value,
        confidence=0.91,
        source_refs=("fixture:snapshot.md#L1",),
        source_document_id="document:snapshot",
        source_hash="sha256:1111111111111111111111111111111111111111111111111111111111111111",
        chunk_id="chunk:snapshot:1",
        line_start=1,
        line_end=1,
        review_status="accepted",
        derived=derived,
    )


def _route(route_id: str, status: str) -> RouteCandidate:
    return RouteCandidate(
        route_id=route_id,
        route_label="Bank account attachment",
        status=status,
        required_facts=("enforceable_title", "third_party_debtor_bank_hint"),
        missing_facts=(),
        blocking_facts=(),
        legal_source_refs=("kr-law-l009290-m268837-a223",),
        source_fact_ids=("fact:title",),
        confidence=0.84,
        review_status=status,
    )
