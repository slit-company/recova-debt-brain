from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from trustgraph_legal.document_assembly import (
    DocumentAssemblyInputError,
    build_document_assembly,
    main,
)

JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


def test_directory_pages_build_deterministic_inventory_and_assemblies(tmp_path: Path) -> None:
    # Given: OCR page markdown files and a page manifest compatible with D fixtures.
    pages_dir = _write_pages_fixture(tmp_path)

    # When: the builder inventories pages and assembles document-level records.
    payload = build_document_assembly(pages_dir, tmp_path).to_json()

    # Then: output is deterministic, source-grounded, and free of raw OCR text.
    assert payload["schema_version"] == "recova-document-assembly/v0"
    summary = _object(payload, "summary")
    assert summary["pages"] == 3
    assert summary["assemblies"] == 2
    assert summary["document_pages"] == 3
    assert summary["document_assemblies"] == 2
    assert summary["needs_review"] == 1
    assert [page["page_id"] for page in _items(payload, "document_pages")] == [
        "page:doc-payment:0001",
        "page:doc-payment:0002",
        "page:doc-service:0001",
    ]
    assert [page["relative_path"] for page in _items(payload, "document_pages")] == [
        "legal-ocr-pages/payment/page-001.md",
        "legal-ocr-pages/payment/page-002.md",
        "legal-ocr-pages/service/page-001.md",
    ]
    payment = _assembly(payload, "document:doc-payment")
    assert payment["canonical_document_type"] == "payment-order"
    assert payment["page_ids"] == ["page:doc-payment:0001", "page:doc-payment:0002"]
    assert payment["source_hashes"] == [
        _sha256("Payment page one\nLine two\n"),
        _sha256("Payment page two\n"),
    ]
    encoded = json.dumps(payload, ensure_ascii=False)
    assert "Payment page one" not in encoded
    assert "900101" + "-1234567" not in encoded
    assert payload["pii_profile"] == {
        "raw_text_included": False,
        "source_text_included": False,
        "sensitive_shape_pages": 1,
    }


def test_manifest_rejects_page_outside_fixture_root(tmp_path: Path) -> None:
    # Given: a manifest entry that tries to point outside the fixture directory.
    pages_dir = tmp_path / "legal-ocr-pages"
    pages_dir.mkdir()
    _ = (pages_dir / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "legal-ocr-page-manifest/v1",
                "pages": [
                    {
                        "document_id": "doc-outside",
                        "canonical_document_type": "payment-order",
                        "relative_path": "../outside.md",
                        "page_order": 1,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # When / Then: boundary parsing refuses the unsafe source path.
    with pytest.raises(DocumentAssemblyInputError) as error:
        _ = build_document_assembly(pages_dir, tmp_path)

    assert "page path escapes fixture root" in str(error.value)


def test_directory_without_manifest_uses_stable_file_order(tmp_path: Path) -> None:
    # Given: a D-style page folder before manifest metadata is available.
    pages_dir = tmp_path / "legal-ocr-pages"
    (pages_dir / "loose").mkdir(parents=True)
    _ = (pages_dir / "loose" / "page-002.md").write_text("Second\n", encoding="utf-8")
    _ = (pages_dir / "loose" / "page-001.md").write_text("First\n", encoding="utf-8")

    # When: the builder scans markdown files directly.
    payload = build_document_assembly(pages_dir, tmp_path).to_json()

    # Then: pages and the fallback assembly are ordered by relative path.
    assert [page["page_id"] for page in _items(payload, "document_pages")] == [
        "page:loose:0001",
        "page:loose:0002",
    ]
    assembly = _items(payload, "document_assemblies")[0]
    assert assembly["document_id"] == "document:loose"
    assert assembly["canonical_document_type"] == "unknown"
    assert assembly["review_status"] == "needs_review"


def test_cli_ocr_root_summary_only_writes_redacted_summary(tmp_path: Path) -> None:
    # Given: the preferred Todo 5 CLI invocation for local OCR roots.
    pages_dir = _write_pages_fixture(tmp_path)
    evidence_path = tmp_path / "task-5-document-assembly-summary.json"

    # When: the module CLI writes a summary-only payload.
    exit_code = main(
        ["--ocr-root", str(pages_dir), "--out", str(evidence_path), "--summary-only", "--repo-root", str(tmp_path)]
    )

    # Then: evidence is aggregate-only and keeps the required redaction contract.
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    summary = _object(payload, "summary")
    assert exit_code == 0
    assert payload["schema_version"] == "recova-document-assembly/v0"
    assert summary["pages"] == 3
    assert summary["assemblies"] == 2
    assert payload["pii_profile"] == {
        "raw_text_included": False,
        "source_text_included": False,
        "sensitive_shape_pages": 1,
    }
    assert "document_pages" not in payload
    assert "Payment page one" not in json.dumps(payload, ensure_ascii=False)


def test_module_entrypoint_preserves_pages_compatibility(tmp_path: Path) -> None:
    # Given: a fixture folder and the previous --pages CLI surface.
    pages_dir = _write_pages_fixture(tmp_path)
    evidence_path = tmp_path / "subprocess-assembly.json"

    # When: python runs the document assembly module.
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "trustgraph_legal.document_assembly",
            "--pages",
            str(pages_dir),
            "--out",
            str(evidence_path),
            "--repo-root",
            str(tmp_path),
        ],
        cwd=Path(__file__).resolve().parents[3],
        check=False,
        capture_output=True,
        text=True,
    )

    # Then: the command succeeds and points at the PII-safe evidence file.
    assert result.returncode == 0
    assert str(evidence_path) in result.stdout
    assert evidence_path.exists()


def test_manifest_tsv_normalizes_prefixed_document_and_assembly_ids(tmp_path: Path) -> None:
    # Given: a TSV manifest whose document_id is already document-prefixed.
    ocr_root = tmp_path / "ocr-root"
    (ocr_root / "pages").mkdir(parents=True)
    _ = (ocr_root / "pages" / "prefixed.md").write_text("Prefixed payment page\n", encoding="utf-8")
    manifest_tsv = tmp_path / "manifest.tsv"
    _ = manifest_tsv.write_text(
        "document_id\tcanonical_document_type\trelative_path\tpage_order\tconfidence\treview_status\n"
        "document:prefixed-payment\tpayment-order\tpages/prefixed.md\t1\t0.9\tassembled\n",
        encoding="utf-8",
    )
    evidence_path = tmp_path / "prefixed-assembly.json"

    # When: the CLI bridges the TSV manifest to document assemblies.
    exit_code = main(
        [
            "--ocr-root",
            str(ocr_root),
            "--manifest-tsv",
            str(manifest_tsv),
            "--out",
            str(evidence_path),
            "--repo-root",
            str(tmp_path),
        ]
    )

    # Then: document and assembly identifiers are normalized once.
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    assembly = _items(payload, "document_assemblies")[0]
    assert exit_code == 0
    assert assembly["document_id"] == "document:prefixed-payment"
    assert assembly["assembly_id"] == "assembly:prefixed-payment"
    encoded = json.dumps(payload, ensure_ascii=False)
    assert "document:document:" not in encoded
    assert "assembly:document:" not in encoded


def test_module_entrypoint_reports_controlled_input_errors(tmp_path: Path) -> None:
    # Given: invalid local CLI inputs.
    pages_dir = _write_pages_fixture(tmp_path)
    cases = [
        (
            ["--ocr-root", str(tmp_path / "missing-root"), "--out", str(tmp_path / "missing.json")],
            "OCR root not found",
            tmp_path / "missing.json",
        ),
        (
            ["--ocr-root", str(pages_dir), "--limit", "0", "--out", str(tmp_path / "limit.json")],
            "--limit must be >= 1",
            tmp_path / "limit.json",
        ),
    ]

    for args, expected_error, output_path in cases:
        # When: python runs the document assembly module with invalid input.
        result = subprocess.run(
            [sys.executable, "-m", "trustgraph_legal.document_assembly", *args],
            cwd=Path(__file__).resolve().parents[3],
            check=False,
            capture_output=True,
            text=True,
        )

        # Then: it fails cleanly without writing partial output.
        assert result.returncode != 0
        assert expected_error in result.stderr
        assert not output_path.exists()


def _write_pages_fixture(tmp_path: Path) -> Path:
    pages_dir = tmp_path / "legal-ocr-pages"
    sensitive_id = "900101" + "-1234567"
    (pages_dir / "payment").mkdir(parents=True)
    (pages_dir / "service").mkdir(parents=True)
    _ = (pages_dir / "payment" / "page-001.md").write_text(
        "Payment page one\nLine two\n",
        encoding="utf-8",
    )
    _ = (pages_dir / "payment" / "page-002.md").write_text("Payment page two\n", encoding="utf-8")
    _ = (pages_dir / "service" / "page-001.md").write_text(
        "Service proof {}\n".format(sensitive_id),
        encoding="utf-8",
    )
    _ = (pages_dir / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "legal-ocr-page-manifest/v1",
                "pages": [
                    {
                        "document_id": "doc-payment",
                        "canonical_document_type": "payment-order",
                        "relative_path": "payment/page-001.md",
                        "page_order": 1,
                        "confidence": 0.93,
                        "review_status": "assembled",
                    },
                    {
                        "document_id": "doc-payment",
                        "canonical_document_type": "payment-order",
                        "relative_path": "payment/page-002.md",
                        "page_order": 2,
                        "confidence": 0.91,
                        "review_status": "assembled",
                    },
                    {
                        "document_id": "doc-service",
                        "canonical_document_type": "service-finality-proof",
                        "relative_path": "service/page-001.md",
                        "page_order": 1,
                        "confidence": 0.88,
                        "review_status": "needs_review",
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return pages_dir


def _items(payload: dict[str, JsonValue], key: str) -> list[dict[str, JsonValue]]:
    value = payload[key]
    assert isinstance(value, list)
    items: list[dict[str, JsonValue]] = []
    for item in value:
        assert isinstance(item, dict)
        items.append(item)
    return items


def _object(payload: dict[str, JsonValue], key: str) -> dict[str, JsonValue]:
    value = payload[key]
    assert isinstance(value, dict)
    return value


def _assembly(payload: dict[str, JsonValue], document_id: str) -> dict[str, JsonValue]:
    for assembly in _items(payload, "document_assemblies"):
        if assembly["document_id"] == document_id:
            return assembly
    raise AssertionError("missing assembly {}".format(document_id))


def _sha256(text: str) -> str:
    return "sha256:{}".format(hashlib.sha256(text.encode("utf-8")).hexdigest())
