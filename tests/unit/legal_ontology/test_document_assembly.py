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
    assert payload["summary"] == {
        "document_pages": 3,
        "document_assemblies": 2,
        "needs_review": 1,
    }
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


def test_cli_writes_pii_safe_document_assembly_evidence(tmp_path: Path) -> None:
    # Given: the public module invocation for task-2 evidence generation.
    pages_dir = _write_pages_fixture(tmp_path)
    evidence_path = tmp_path / "task-2-document-assembly.json"

    # When: the module CLI builds the document assembly payload.
    exit_code = main(["--pages", str(pages_dir), "--out", str(evidence_path), "--repo-root", str(tmp_path)])

    # Then: evidence is written with no raw OCR text.
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["schema_version"] == "recova-document-assembly/v0"
    assert payload["summary"]["document_assemblies"] == 2
    assert "Payment page one" not in json.dumps(payload, ensure_ascii=False)


def test_module_entrypoint_writes_evidence_from_subprocess(tmp_path: Path) -> None:
    # Given: a fixture folder and the documented module entrypoint.
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


def _assembly(payload: dict[str, JsonValue], document_id: str) -> dict[str, JsonValue]:
    for assembly in _items(payload, "document_assemblies"):
        if assembly["document_id"] == document_id:
            return assembly
    raise AssertionError("missing assembly {}".format(document_id))


def _sha256(text: str) -> str:
    return "sha256:{}".format(hashlib.sha256(text.encode("utf-8")).hexdigest())
