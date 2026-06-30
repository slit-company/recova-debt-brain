from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from trustgraph_legal.classifier import (
    FIXTURE_BUCKET_TO_DOCUMENT_TYPE,
    CanonicalDocumentType,
    FixtureBucket,
    classify_manifest,
    classify_text,
    main,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = REPO_ROOT / "tests" / "fixtures" / "legal-ocr" / "manifest.json"


def test_classifier_labels_manifest_documents_with_evidence() -> None:
    # Given: the synthetic legal OCR manifest with expected fixture labels.
    expected_buckets = {
        document["document_id"]: FixtureBucket(document["document_type"])
        for document in json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))["documents"]
    }

    # When: the deterministic classifier reads the manifest.
    payload = classify_manifest(MANIFEST_PATH)
    records = payload.to_json()["records"]

    # Then: every document receives the expected label with confidence and source evidence.
    assert len(records) == len(expected_buckets)
    for record in records:
        fixture_bucket = expected_buckets[record["document_id"]]
        assert record["fixture_document_type"] == fixture_bucket.value
        assert record["document_type"] == FIXTURE_BUCKET_TO_DOCUMENT_TYPE[fixture_bucket].value
        assert record["confidence"] >= 0.75
        assert record["review_status"] == "classified"
        assert record["reason_signals"]
        assert record["evidence_spans"]
        assert record["pii_profile"]["raw_text_included"] is False


def test_fixture_buckets_map_to_canonical_document_types() -> None:
    # Given: Todo 5 snake_case fixture buckets and the v0 domain-contract labels.
    expected_mapping = {
        FixtureBucket.ATTACHMENT_COLLECTION_ORDER: CanonicalDocumentType.ATTACHMENT_COLLECTION_ORDER,
        FixtureBucket.JUDGMENT_PAYMENT_ORDER: CanonicalDocumentType.PAYMENT_ORDER,
        FixtureBucket.SERVICE_FINALITY_EXECUTION_CLAUSE: CanonicalDocumentType.SERVICE_FINALITY_PROOF,
        FixtureBucket.ASSIGNMENT_SUCCESSION: CanonicalDocumentType.ASSIGNMENT_SUCCESSION,
        FixtureBucket.IDENTITY_EVIDENCE: CanonicalDocumentType.IDENTITY_EVIDENCE,
        FixtureBucket.INSOLVENCY_CREDIT_RECOVERY: CanonicalDocumentType.INSOLVENCY_CREDIT_RECOVERY,
        FixtureBucket.ASSET_EVIDENCE: CanonicalDocumentType.ASSET_EVIDENCE,
        FixtureBucket.OPERATIONAL_LEDGER: CanonicalDocumentType.LEDGER_RECOVERY,
        FixtureBucket.AMOUNT_INTEREST: CanonicalDocumentType.AMOUNT_INTEREST_CALCULATION,
        FixtureBucket.UNKNOWN_DOC_TYPE: CanonicalDocumentType.UNKNOWN,
    }

    # When: the classifier exposes the compatibility mapping.
    mapping = dict(FIXTURE_BUCKET_TO_DOCUMENT_TYPE)

    # Then: the mapping is explicit and covers every fixture bucket exactly once.
    assert mapping == expected_mapping


def test_classifier_marks_low_signal_document_for_review() -> None:
    # Given: text that has no legal-document bucket signal.
    text = "short neutral note without legal bucket markers"

    # When: the classifier evaluates it.
    result = classify_text(
        document_id="low-signal-doc",
        source_ref="tmp/low-signal.md",
        text=text,
    )
    record = result.to_json()

    # Then: it refuses a confident label and preserves review evidence.
    assert record["fixture_document_type"] == "unknown_doc_type"
    assert record["document_type"] == "unknown"
    assert record["review_status"] == "needs_review_unknown_doc_type"
    assert record["confidence"] < 0.5
    assert record["evidence_spans"]
    assert record["reason_signals"] == ["insufficient_document_type_signals"]


def test_cli_writes_pii_safe_evidence_json(tmp_path: Path) -> None:
    # Given: a target evidence path for the fixture manifest run.
    evidence_path = tmp_path / "classifier-evidence.json"

    # When: the module CLI classifies the manifest.
    exit_code = main(
        [
            "--manifest",
            str(MANIFEST_PATH),
            "--evidence",
            str(evidence_path),
        ]
    )

    # Then: PII-safe JSON evidence is written for every fixture document.
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["schema_version"] == "trustgraph-legal-document-classifier/v1"
    assert payload["summary"]["records"] == 9
    assert payload["summary"]["unknown_doc_type"] == 0
    assert {record["fixture_document_type"] for record in payload["records"]} == {
        "attachment_collection_order",
        "judgment_payment_order",
        "service_finality_execution_clause",
        "assignment_succession",
        "identity_evidence",
        "insolvency_credit_recovery",
        "asset_evidence",
        "operational_ledger",
        "amount_interest",
    }
    assert {record["document_type"] for record in payload["records"]} == {
        "attachment-collection-order",
        "payment-order",
        "service-finality-proof",
        "assignment-succession",
        "identity-evidence",
        "insolvency-credit-recovery",
        "asset-evidence",
        "ledger-recovery",
        "amount-interest-calculation",
    }
    for record in payload["records"]:
        assert record["pii_profile"]["raw_text_included"] is False


def test_evidence_json_redacts_sensitive_shapes(tmp_path: Path) -> None:
    # Given: a temporary source with a clear document marker and sensitive shapes.
    source_path = tmp_path / "sensitive.md"
    sensitive_number = "900101" + "-1234567"
    sensitive_phone = "010" + "-1234" + "-5678"
    source_path.write_text(
        "\n".join(
            [
                "Document marker: 채권압류 및 추심명령 결정",
                f"identity: {sensitive_number}",
                f"phone: {sensitive_phone}",
            ]
        ),
        encoding="utf-8",
    )

    # When: the classifier result is serialized.
    result = classify_text(
        document_id="sensitive-doc",
        source_ref=str(source_path),
        text=source_path.read_text(encoding="utf-8"),
    )
    encoded = json.dumps(result.to_json(), ensure_ascii=False)

    # Then: source evidence is present but sensitive shapes are redacted away.
    assert result.document_type is CanonicalDocumentType.ATTACHMENT_COLLECTION_ORDER
    assert result.fixture_document_type is FixtureBucket.ATTACHMENT_COLLECTION_ORDER
    assert sensitive_number not in encoded
    assert sensitive_phone not in encoded
    assert "[NATIONAL_ID_REDACTED]" in encoded
    assert "[PHONE_REDACTED]" in encoded


def test_module_entrypoint_writes_evidence_from_subprocess(tmp_path: Path) -> None:
    # Given: the public module invocation expected by Todo 5 QA.
    evidence_path = tmp_path / "subprocess-evidence.json"

    # When: python runs the classifier module entrypoint.
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "trustgraph_legal.classifier",
            "--manifest",
            str(MANIFEST_PATH),
            "--evidence",
            str(evidence_path),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    # Then: the command exits cleanly and points at the written evidence.
    assert result.returncode == 0
    assert str(evidence_path) in result.stdout
    assert evidence_path.exists()
