from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from trustgraph_legal.debtor_context import (
    DebtorContextInputError,
    build_debtor_context,
)
from trustgraph_legal.debtor_context_types import PLACEHOLDER_SOURCE_REFS, FactAssertion, JsonObject
from trustgraph_legal.document_assembly import DocumentAssemblyPayload, build_document_assembly
from trustgraph_legal.route_candidates import evaluate_route_candidates

REPO_ROOT = Path(__file__).resolve().parents[3]
PAGES_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "legal-ocr-pages"


def test_builds_stable_debtor_graph_with_source_grounded_review_item() -> None:
    # Given: the synthetic assembled OCR page fixture with no identity-evidence document.
    assembly_payload = build_document_assembly(PAGES_FIXTURE, REPO_ROOT)
    expected_bundle_hash = _bundle_hash(tuple(sorted(page.source_hash for page in assembly_payload.document_pages)))

    # When: building the debtor context graph twice from the same assembly.
    first = build_debtor_context(assembly_payload, repo_root=REPO_ROOT)
    second = build_debtor_context(assembly_payload, repo_root=REPO_ROOT)
    graph = first.to_json()

    # Then: graph identifiers and source bundle metadata are deterministic.
    assert first.debtor_graph_id == second.debtor_graph_id
    assert first.graph_snapshot.graph_snapshot_id == second.graph_snapshot.graph_snapshot_id
    assert first.graph_snapshot.source_bundle_hash == second.graph_snapshot.source_bundle_hash
    assert first.debtor_graph_id == "debtor-graph:{}".format(expected_bundle_hash.removeprefix("sha256:")[:16])
    assert first.graph_snapshot.graph_snapshot_id == "snapshot:{}".format(expected_bundle_hash.removeprefix("sha256:")[:16])
    assert first.graph_snapshot.source_bundle_hash == expected_bundle_hash
    assert first.graph_snapshot.generated_at == second.graph_snapshot.generated_at
    assert first.case_packets

    # Then: fact assertions are grounded to non-placeholder source refs.
    assert first.fact_assertions
    for fact in first.fact_assertions:
        _assert_material_fact(fact)

    # Then: route-facing predicates include handles consumed by the Todo 8 matcher.
    predicates = {fact.predicate for fact in first.fact_assertions}
    assert {"enforceable_title", "third_party_debtor_bank_hint"} <= predicates
    bank_route = next(candidate for candidate in evaluate_route_candidates(first) if candidate.route_id == "bank_account_attachment")
    assert bank_route.status == "possible"
    assert "enforceable_title" not in bank_route.missing_facts
    assert "third_party_debtor_bank_hint" not in bank_route.missing_facts

    # Then: weak identity produces an explicit review item without persisting raw OCR text.
    assert any(item.get("reason_code") == "identity_unresolved" for item in first.review_items)
    assert graph["pii_profile"] == {"raw_text_included": False, "source_text_included": False}
    encoded = json.dumps(graph, ensure_ascii=False)
    assert "Synthetic OCR Page" not in encoded
    assert "[DEBTOR_PERSON_REDACTED]" not in encoded


def test_rejects_summary_only_assembly_inputs() -> None:
    # Given: summary-only assembly shapes that do not carry page or assembly provenance.
    summary_json: JsonObject = {
        "schema_version": "recova-document-assembly/v0",
        "summary": {"document_pages": 2, "document_assemblies": 1},
    }
    empty_payload = DocumentAssemblyPayload(document_pages=(), document_assemblies=(), sensitive_shape_pages=0)

    # When / Then: the graph builder refuses both with controlled input errors.
    with pytest.raises(DebtorContextInputError) as json_error:
        build_debtor_context(summary_json)
    with pytest.raises(DebtorContextInputError) as payload_error:
        build_debtor_context(empty_payload)

    assert "summary-only JSON is not accepted" in str(json_error.value)
    assert "document_pages and document_assemblies are required" in str(payload_error.value)


def test_weak_identity_source_bundle_fallback_does_not_name_only_merge(tmp_path: Path) -> None:
    # Given: two similar debtor-name fixtures with no identity-evidence document or case token.
    first_root = _write_single_debtor_pages(tmp_path, "alpha", "[DEBTOR_KIM_MIN_SU]", "KRW 1000")
    second_root = _write_single_debtor_pages(tmp_path, "beta", "[DEBTOR_KIM_MINSU]", "KRW 1000")

    # When: each source bundle is built into a debtor context graph.
    first = build_debtor_context(build_document_assembly(first_root, tmp_path), repo_root=tmp_path)
    second = build_debtor_context(build_document_assembly(second_root, tmp_path), repo_root=tmp_path)

    # Then: weak identity stays unresolved and graph ids remain source-bundle specific.
    assert first.debtor_graph_id != second.debtor_graph_id
    assert first.identity_resolution["status"] == "identity_unresolved"
    assert second.identity_resolution["status"] == "identity_unresolved"
    assert any(item.get("reason_code") == "identity_unresolved" for item in first.review_items)
    assert any(item.get("reason_code") == "identity_unresolved" for item in second.review_items)


def _bundle_hash(source_hashes: tuple[str, ...]) -> str:
    return "sha256:{}".format(hashlib.sha256("\n".join(source_hashes).encode("utf-8")).hexdigest())


def _assert_material_fact(fact: FactAssertion) -> None:
    assert fact.source_refs
    assert fact.source_document_id.startswith("document:")
    assert fact.source_hash.startswith("sha256:")
    assert fact.chunk_id
    assert fact.line_start >= 1
    assert fact.line_end >= fact.line_start
    assert fact.extractor_version
    assert fact.ontology_version
    assert 0.0 <= fact.confidence <= 1.0
    assert fact.review_status in {"verified", "needs_review"}
    assert all(not _placeholder_source_ref(source_ref) for source_ref in fact.source_refs)


def _placeholder_source_ref(source_ref: str) -> bool:
    normalized = source_ref.strip().lower()
    return normalized in PLACEHOLDER_SOURCE_REFS or normalized.startswith("placeholder:")


def _write_single_debtor_pages(tmp_path: Path, fixture_id: str, debtor_token: str, amount: str) -> Path:
    pages_dir = tmp_path / "weak-identity" / fixture_id
    page_path = pages_dir / "pages" / "payment.md"
    page_path.parent.mkdir(parents=True)
    _ = page_path.write_text(
        "\n".join(
            [
                "# Synthetic weak identity payment order",
                "Document marker: payment order",
                "Court: [COURT_REDACTED]",
                "Debtor role: {}".format(debtor_token),
                "Principal amount: {}".format(amount),
                "No identity evidence document is included.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _ = (pages_dir / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "legal-ocr-page-manifest/v1",
                "pages": [
                    {
                        "document_id": "weak-{}".format(fixture_id),
                        "canonical_document_type": "payment_order",
                        "relative_path": "pages/payment.md",
                        "page_order": 1,
                        "confidence": 0.91,
                        "review_status": "assembled",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return pages_dir
