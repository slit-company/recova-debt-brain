from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from trustgraph_legal.governance import (
    CONTRACT_DOCUMENT_TYPE_GAPS,
    OntologyCandidate,
    attempt_promotion,
    build_governance_payload,
    main,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
ONTOLOGY_PATH = REPO_ROOT / "resources" / "ontologies" / "recova-debt-collection.json"


def test_low_confidence_unknown_fixture_creates_candidate_review_and_reprocess(
    tmp_path: Path,
) -> None:
    # Given: a low-signal OCR fixture that includes sensitive shapes.
    fixture_path = _unknown_fixture(tmp_path)
    manifest_path = _manifest(tmp_path, fixture_path)
    before = ONTOLOGY_PATH.read_bytes()

    # When: governance processes the fixture against the production ontology.
    payload = build_governance_payload(manifest_path, tmp_path, ONTOLOGY_PATH)
    data = payload.to_json()

    # Then: unknown classification becomes governance state, not ontology mutation.
    unknown_candidates = [
        item
        for item in data["candidates"]
        if item["reason"] == "classifier_returned_unknown"
    ]
    unknown_reviews = [
        item
        for item in data["review_items"]
        if item["queue_id"] == "unknown-document-type"
    ]
    assert unknown_candidates
    assert unknown_reviews
    assert any(
        plan["reason"] == "classifier_returned_unknown"
        for plan in data["reprocess_plans"]
    )
    assert data["production_ontology_modified"] is False
    assert "ontology_nodes" not in data
    assert ONTOLOGY_PATH.read_bytes() == before


def test_contract_document_type_gaps_are_explicit_candidates(
    tmp_path: Path,
) -> None:
    # Given: a manifest with one unknown document.
    manifest_path = _manifest(tmp_path, _unknown_fixture(tmp_path))

    # When: governance builds its candidate queue.
    data = build_governance_payload(manifest_path, tmp_path, ONTOLOGY_PATH).to_json()
    gap_candidates = {
        item["proposed_id"]: item
        for item in data["candidates"]
        if item["reason"]
        == "domain_contract_type_not_production_supported_in_v0_classifier"
    }

    # Then: domain-contract types outside the 9-bucket classifier are not silent.
    assert set(CONTRACT_DOCUMENT_TYPE_GAPS) <= set(gap_candidates)
    for doc_type in CONTRACT_DOCUMENT_TYPE_GAPS:
        assert gap_candidates[doc_type]["status"] == "v0-excluded-review-required"
        assert "classifier-coverage-gap" in gap_candidates[doc_type]["risk_flags"]
        assert any(
            plan["reason"]
            == "domain_contract_type_not_production_supported_in_v0_classifier"
            and plan["changed_versions"]["ontology_version"] == f"proposed:{doc_type}"
            for plan in data["reprocess_plans"]
        )
    assert {
        item["candidate_value"]
        for item in data["review_items"]
        if item["queue_id"] == "ontology-candidate"
    } >= set(CONTRACT_DOCUMENT_TYPE_GAPS)


def test_promotion_without_required_metadata_is_rejected(
    tmp_path: Path,
) -> None:
    # Given: an ontology candidate and incomplete approval metadata.
    candidate = _candidate()

    # When: promotion is attempted without regression/approval fields.
    result = attempt_promotion(candidate, {}, ONTOLOGY_PATH).to_json()

    # Then: promotion is rejected and the production ontology remains untouched.
    assert result["status"] == "rejected"
    assert result["reason"] == "missing_required_approval_metadata"
    assert set(result["missing_fields"]) >= {
        "approved_by",
        "approval_evidence_ref",
        "regression_run_id",
        "fixture_set_id",
    }
    assert result["production_ontology_modified"] is False


def test_promotion_with_approval_metadata_returns_next_version_without_mutation() -> None:
    # Given: a complete reviewed promotion packet.
    before = ONTOLOGY_PATH.read_bytes()
    metadata = {
        "approved_by": "reviewer:legal-ops",
        "approved_at": "2026-06-30T00:00:00Z",
        "approval_evidence_ref": "artifact:regression-approved",
        "regression_run_id": "regression:todo-8",
        "fixture_set_id": "legal-ocr-fixtures:v0",
        "changed_versions": ["ontology:next"],
        "regression_result": "pass",
        "unresolved_risk_summary": "none",
    }

    # When: promotion is evaluated.
    result = attempt_promotion(_candidate(), metadata, ONTOLOGY_PATH).to_json()

    # Then: it approves only a next-version proposal and never writes production.
    assert result["status"] == "approved-for-next-version"
    assert result["proposed_version"] == "recova-debt-collection@v0-next"
    assert result["production_ontology_modified"] is False
    assert ONTOLOGY_PATH.read_bytes() == before


def test_cli_writes_pii_safe_governance_evidence(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Given: a low-signal fixture with sensitive shapes.
    manifest_path = _manifest(tmp_path, _unknown_fixture(tmp_path))
    evidence_path = tmp_path / "governance.json"

    # When: the public module CLI writes governance evidence.
    exit_code = main(
        [
            "--manifest",
            str(manifest_path),
            "--repo-root",
            str(tmp_path),
            "--ontology",
            str(ONTOLOGY_PATH),
            "--evidence",
            str(evidence_path),
        ]
    )
    evidence = evidence_path.read_text(encoding="utf-8")
    data = json.loads(evidence)
    captured = capsys.readouterr()
    stdout = captured.out
    sensitive_number = "900101" + "-1234567"
    sensitive_phone = "010" + "-1234" + "-5678"

    # Then: governance evidence is structured and does not leak raw sensitive data.
    assert exit_code == 0
    assert data["schema_version"] == "trustgraph-legal-ontology-governance/v1"
    assert data["summary"]["candidates"] >= 1
    assert json.loads(stdout)["candidate_ids"]
    assert sensitive_number not in stdout
    assert sensitive_phone not in stdout
    assert sensitive_number not in evidence
    assert sensitive_phone not in evidence
    assert data["pii_profile"]["raw_text_included"] is False


def _unknown_fixture(tmp_path: Path) -> Path:
    fixture_path = tmp_path / "unknown.md"
    sensitive_number = "900101" + "-1234567"
    sensitive_phone = "010" + "-1234" + "-5678"
    fixture_path.write_text(
        "\n".join(
            [
                "Unclear scan fragment",
                f"identity: {sensitive_number}",
                f"phone: {sensitive_phone}",
                "No reliable legal document type markers.",
            ]
        ),
        encoding="utf-8",
    )
    return fixture_path


def _manifest(tmp_path: Path, fixture_path: Path) -> Path:
    text = fixture_path.read_text(encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "legal-ocr-fixture-manifest/v1",
                "ontology_version": "recova-debt-collection@v0",
                "prompt_version": "legal-ontology-extraction@v0",
                "documents": [
                    {
                        "document_id": "legal-ocr-synth-unknown-001",
                        "document_type": "unknown_doc_type",
                        "source_fixture_path": fixture_path.name,
                        "source_hash": "sha256:{}".format(
                            hashlib.sha256(text.encode("utf-8")).hexdigest()
                        ),
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return manifest_path


def _candidate() -> OntologyCandidate:
    return OntologyCandidate(
        candidate_id="candidate:test",
        candidate_type="document_type",
        proposed_id="new-document-type",
        proposed_label="New Document Type",
        reason="test",
        status="draft-review-required",
        source_refs=("fixture:unknown.md",),
        provenance={"source_ref": "fixture:unknown.md"},
        risk_flags=("no-auto-promotion",),
    )
