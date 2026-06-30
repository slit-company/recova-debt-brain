from __future__ import annotations

import json
from pathlib import Path

from trustgraph_legal.fields import (
    DocumentInput,
    extract_fields,
    extract_manifest_fields,
    normalize_document_type,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = REPO_ROOT / "tests" / "fixtures" / "legal-ocr" / "manifest.json"


def _document(document_type: str, fixture_name: str) -> DocumentInput:
    path = REPO_ROOT / "tests" / "fixtures" / "legal-ocr" / "snippets" / fixture_name
    document_stem = fixture_name[:-3] if fixture_name.endswith(".md") else fixture_name
    return DocumentInput(
        document_id=f"test-{document_stem}",
        document_type=document_type,
        source_ref=f"fixture:{fixture_name}",
        text=path.read_text(encoding="utf-8"),
    )


def test_normalizes_snake_case_fixture_type_before_extracting_fields() -> None:
    # Given: a fixture manifest label that uses snake_case spelling.
    document = _document("judgment_payment_order", "judgment_payment_order.md")

    # When: extracting normalized fields.
    result = extract_fields(document)

    # Then: output uses the canonical v0 document type and accepted source spans.
    assert result.document_type == "payment-order"
    assert result.review_status == "accepted"
    assert result.confidence >= 0.9
    assert {field.name for field in result.fields} >= {
        "court_case_number",
        "creditor_role",
        "debtor_role",
        "principal_amount",
        "interest_rate",
    }
    principal = next(field for field in result.fields if field.name == "principal_amount")
    assert principal.normalized_value == "KRW 3400000"
    assert principal.document_id == document.document_id
    assert principal.source_ref == "fixture:judgment_payment_order.md"
    assert principal.chunk_id == "line-8"
    assert "Principal" in principal.reason


def test_manifest_extraction_covers_representative_todo_5_fields() -> None:
    # Given: the synthetic legal OCR fixture manifest.
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    # When: extracting fields from every manifest document.
    payload = extract_manifest_fields(MANIFEST_PATH, REPO_ROOT)

    # Then: every manifest document has canonical type output and field evidence.
    assert payload.schema_version == "trustgraph-legal-field-extraction/v1"
    assert len(payload.documents) == len(manifest["documents"])
    accepted = {doc.document_type: {field.name for field in doc.fields} for doc in payload.documents}
    assert accepted["attachment-collection-order"] >= {
        "court_case_number",
        "creditor_role",
        "debtor_role",
        "third_party_debtor_role",
        "claim_amount",
        "attachment_target",
    }
    assert accepted["service-finality-proof"] >= {
        "linked_title_case_number",
        "service_result",
        "finality_result",
        "execution_clause_status",
    }
    assert accepted["assignment-succession"] >= {
        "assignor_role",
        "assignee_role",
        "assigned_claim_token",
        "notice_status",
        "succession_authority",
    }
    assert accepted["identity-evidence"] >= {
        "party_identity_key",
        "organization_status",
        "representative_role",
    }
    assert accepted["insolvency-credit-recovery"] >= {
        "procedure_type",
        "procedure_status",
        "linked_claim_token",
    }
    assert accepted["asset-evidence"] >= {
        "asset_class",
        "priority_status",
        "attachment_suitability",
        "exemption_review_status",
    }
    assert accepted["ledger-recovery"] >= {
        "ledger_event",
        "recovery_amount",
        "cost_amount",
    }
    assert accepted["amount-interest-calculation"] >= {
        "principal_amount",
        "interest_rate",
        "calculation_start",
        "calculation_end",
        "claimed_total",
    }


def test_low_signal_text_returns_review_without_accepted_fields() -> None:
    # Given: OCR text that does not contain enough legal field evidence.
    document = DocumentInput(
        document_id="low-signal-doc",
        document_type="unknown",
        source_ref="fixture:low-signal.md",
        text="memo\nunclear scan fragment\n",
    )

    # When: extracting fields.
    result = extract_fields(document)

    # Then: no fields are accepted and a review state explains why.
    assert result.document_type == "unknown"
    assert result.review_status == "needs_review"
    assert result.confidence == 0.0
    assert result.fields == ()
    assert result.review_reason == "low_signal_no_supported_fields"


def test_source_span_json_is_pii_safe() -> None:
    # Given: an identity fixture with safe placeholders only.
    document = _document("identity_evidence", "identity_evidence.md")

    # When: serializing extraction output.
    evidence_json = json.dumps(extract_fields(document).to_json(), ensure_ascii=False)

    # Then: output keeps placeholders and source refs, not raw sensitive shapes.
    assert "[DATE_TOKEN]" in evidence_json
    for banned in ("주민" + "등록번호", "resi" + "dent"):
        assert banned not in evidence_json
