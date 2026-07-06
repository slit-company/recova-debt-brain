from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Union

import pytest

from trustgraph_legal.debtor_context_types import (
    SCHEMA_VERSION,
    DocumentAssembly,
    DocumentPage,
    DebtorGraphPayload,
    FactAssertion,
    FactAssertionSourceRefError,
    GraphSnapshot,
    ProcedureEpisode,
    RouteCandidate,
)

JsonScalar = Union[str, int, float, bool, type(None)]
JsonValue = Union[JsonScalar, List["JsonValue"], Dict[str, "JsonValue"]]


def test_debtor_graph_payload_serializes_stable_redacted_contract() -> None:
    # Given: a synthetic debtor context graph with source-ref based facts.
    payload = _synthetic_payload()

    # When: the graph is serialized for downstream agents.
    graph = payload.to_json()

    # Then: the v0 contract has stable top-level sections and excludes raw OCR text.
    assert graph["schema_version"] == SCHEMA_VERSION
    assert graph["debtor_graph_id"] == "debtor-graph:synthetic-001"
    assert graph["graph_snapshot_id"] == "snapshot:synthetic-001"
    assert graph["pii_profile"] == {
        "raw_text_included": False,
        "source_text_included": False,
    }
    assert {
        "identity_resolution",
        "case_packets",
        "document_assemblies",
        "fact_assertions",
        "claims",
        "enforcement_titles",
        "procedure_episodes",
        "asset_hints",
        "stop_gates",
        "route_candidates",
        "review_items",
    } <= set(graph)
    assert _contains_key(graph, "raw_text") is False
    assert _contains_key(graph, "source_text") is False
    assert "RAW OCR" not in json.dumps(graph, ensure_ascii=False)


def test_fact_assertion_rejects_missing_source_refs() -> None:
    # Given: fact inputs with no provenance source pointer.
    source_refs: tuple[str, ...] = ()

    # When / Then: constructing the fact rejects it before serialization.
    with pytest.raises(FactAssertionSourceRefError) as error:
        FactAssertion(
            fact_id="fact:missing-source",
            subject_id="claim:synthetic",
            predicate="has_claim_balance",
            object_value="KRW_REDACTED",
            confidence=0.86,
            source_refs=source_refs,
            source_document_id="document:payment-order",
            source_hash="sha256:abc123",
            chunk_id="chunk:1",
            line_start=10,
            line_end=12,
            review_status="needs_review",
        )

    assert str(error.value) == "fact fact:missing-source has no source_refs"


def test_fact_assertion_rejects_placeholder_source_refs() -> None:
    # Given: a fact that points at a placeholder instead of real evidence.
    source_refs = ("missing",)

    # When / Then: the fact validation fails with the offending placeholder.
    with pytest.raises(FactAssertionSourceRefError) as error:
        FactAssertion(
            fact_id="fact:placeholder-source",
            subject_id="claim:synthetic",
            predicate="has_claim_balance",
            object_value="KRW_REDACTED",
            confidence=0.86,
            source_refs=source_refs,
            source_document_id="document:payment-order",
            source_hash="sha256:abc123",
            chunk_id="chunk:1",
            line_start=10,
            line_end=12,
            review_status="needs_review",
        )

    assert str(error.value) == "fact fact:placeholder-source has placeholder source_ref missing"


def test_json_contract_can_be_written_as_pretty_json(tmp_path: Path) -> None:
    # Given: the public JSON contract payload.
    output_path = tmp_path / "task-1-schema-happy.json"

    # When: evidence generation writes it to disk.
    output_path.write_text(
        json.dumps(_synthetic_payload().to_json(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Then: the saved JSON remains loadable and PII safe.
    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved["schema_version"] == "recova-debtor-context-graph/v1"
    assert saved["pii_profile"]["raw_text_included"] is False


def _synthetic_payload() -> DebtorGraphPayload:
    page = DocumentPage(
        page_id="page:payment-order:1",
        source_ref="fixture:legal-ocr/payment-order.md#page=1",
        source_hash="sha256:pagehash001",
        relative_path="tests/fixtures/legal-ocr/payment-order.md",
        page_order=1,
        classifier_document_type="payment-order",
        review_status="classified",
        line_count=42,
        char_count=2048,
    )
    assembly = DocumentAssembly(
        assembly_id="assembly:payment-order",
        document_id="document:payment-order",
        canonical_document_type="payment-order",
        page_ids=(page.page_id,),
        source_refs=(page.source_ref,),
        source_hashes=(page.source_hash,),
        confidence=0.93,
        review_status="assembled",
    )
    episode = ProcedureEpisode(
        episode_id="episode:payment-order",
        episode_type="payment_order",
        document_ids=(assembly.document_id,),
        source_refs=assembly.source_refs,
        sequence_order=1,
        review_status="needs_review",
    )
    fact = FactAssertion(
        fact_id="fact:claim-balance",
        subject_id="claim:synthetic",
        predicate="has_claim_balance",
        object_value="KRW_REDACTED",
        confidence=0.86,
        source_refs=assembly.source_refs,
        source_document_id=assembly.document_id,
        source_hash=page.source_hash,
        chunk_id="chunk:payment-order:1",
        line_start=10,
        line_end=12,
        review_status="needs_review",
    )
    route = RouteCandidate(
        route_id="bank_account_attachment",
        route_label="Bank account attachment",
        status="missing_facts",
        required_facts=("enforceable_title", "third_party_debtor_bank_hint"),
        missing_facts=("third_party_debtor_bank_hint",),
        blocking_facts=(),
        legal_source_refs=("legal-source:civil-execution-act-223",),
        source_fact_ids=(fact.fact_id,),
        confidence=0.62,
        review_status="review_required",
    )
    snapshot = GraphSnapshot(
        graph_snapshot_id="snapshot:synthetic-001",
        source_bundle_hash="sha256:bundlehash001",
        generated_at="2026-07-06T00:00:00Z",
        fact_assertion_ids=(fact.fact_id,),
        route_candidate_ids=(route.route_id,),
    )
    return DebtorGraphPayload(
        debtor_graph_id="debtor-graph:synthetic-001",
        graph_snapshot=snapshot,
        identity_resolution={
            "status": "identity_unresolved",
            "method": "synthetic_bundle_hash",
            "review_items": ["identity_unresolved"],
        },
        case_packets=(
            {
                "case_packet_id": "case-packet:synthetic-001",
                "source_refs": list(assembly.source_refs),
            },
        ),
        document_pages=(page,),
        document_assemblies=(assembly,),
        fact_assertions=(fact,),
        claims=(
            {
                "claim_id": "claim:synthetic",
                "fact_ids": [fact.fact_id],
            },
        ),
        enforcement_titles=(
            {
                "enforcement_title_id": "title:payment-order",
                "source_refs": list(assembly.source_refs),
            },
        ),
        procedure_episodes=(episode,),
        asset_hints=(),
        stop_gates=(),
        route_candidates=(route,),
        review_items=(
            {
                "review_item_id": "review:identity-unresolved",
                "reason": "identity_unresolved",
            },
        ),
    )


def _contains_key(value: JsonValue, key_name: str) -> bool:
    if isinstance(value, dict):
        return key_name in value or any(_contains_key(item, key_name) for item in value.values())
    if isinstance(value, list):
        return any(_contains_key(item, key_name) for item in value)
    return False
