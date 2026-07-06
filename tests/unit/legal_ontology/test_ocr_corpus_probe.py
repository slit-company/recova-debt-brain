from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Final, TypeAlias

from pydantic import JsonValue as PydanticJsonValue
from pydantic import TypeAdapter

from scripts.legal_ontology.summarize_ocr_corpus import (
    SCHEMA_VERSION,
    SENSITIVE_PATTERNS,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "legal-ocr-pages"
MANIFEST_PATH = FIXTURE_ROOT / "manifest.json"
SCRIPT_PATH = REPO_ROOT / "scripts" / "legal_ontology" / "summarize_ocr_corpus.py"
FORBIDDEN_KEYS = {"raw_text", "source_text", "excerpt", "matched_text"}
JsonValue: TypeAlias = PydanticJsonValue
JsonObject: TypeAlias = dict[str, JsonValue]
JSON_OBJECT_ADAPTER: Final = TypeAdapter[JsonObject](JsonObject)


def test_page_fixture_manifest_is_hash_valid_and_pii_safe() -> None:
    # Given: D-owned minimized page-level OCR fixtures.
    manifest = load_json_object(MANIFEST_PATH)

    # When: the manifest pages are checked against their markdown files.
    pages = list_object_field(manifest, "pages")
    page_orders = [int_field(page, "page_order") for page in pages]
    fixture_text = "\n".join(
        (FIXTURE_ROOT / str_field(page, "relative_path")).read_text(encoding="utf-8")
        for page in pages
    )

    # Then: the fixture contract is deterministic, redacted, and hash-addressed.
    assert manifest["schema_version"] == "legal-ocr-pages-fixture-manifest/v1"
    assert bool_field(object_field(manifest, "pii_profile"), "real_ocr_text_copied") is False
    assert page_orders == [1, 2, 3, 4, 5]
    assert [str_field(page, "document_id") for page in pages] == [
        "document:synthetic-payment-order",
        "document:synthetic-payment-order",
        "document:synthetic-service-finality",
        "document:synthetic-unknown-review",
        "document:synthetic-attachment-order",
    ]
    assert [str_field(page, "canonical_document_type") for page in pages] == [
        "payment_order",
        "payment_order",
        "service_finality_execution_clause",
        "unknown",
        "attachment_collection_order",
    ]
    assert _contains_forbidden_key(manifest) is False
    assert all(_page_hash_matches(page) for page in pages)
    assert all(_page_counts_match(page) for page in pages)
    assert all(pattern.search(fixture_text) is None for pattern in SENSITIVE_PATTERNS.values())
    assert "[DEBTOR_PERSON_REDACTED]" in fixture_text
    assert "[CASE_PACKET_TOKEN_ALPHA]" in fixture_text


def test_probe_writes_aggregate_only_summary(tmp_path: Path) -> None:
    # Given: a local OCR-like folder with markdown pages and safe placeholder text.
    corpus_root = tmp_path / "ocr-corpus"
    markdown_root = corpus_root / "markdown_flat"
    markdown_root.mkdir(parents=True)
    _ = (markdown_root / "page_alpha.md").write_text(
        "payment order\n[DEBTOR_PERSON_REDACTED]\n",
        encoding="utf-8",
    )
    _ = (markdown_root / "page_beta.md").write_text(
        "service finality\n[CASE_PACKET_TOKEN_ALPHA]\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "summary.json"

    # When: the CLI probe summarizes the folder.
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--ocr-root",
            str(corpus_root),
            "--out",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    # Then: the saved JSON contains aggregate counts only, never page names or text.
    payload = load_json_object(output_path)
    payload_dump = json.dumps(payload, ensure_ascii=False)
    assert result.returncode == 0
    assert str_field(payload, "schema_version") == SCHEMA_VERSION
    assert str_field(payload, "summary_kind") == "aggregate_only"
    assert bool_field(object_field(payload, "pii_profile"), "raw_text_included") is False
    assert bool_field(object_field(payload, "pii_profile"), "source_paths_included") is False
    assert int_field(object_field(payload, "summary"), "pages") == 2
    assert int_field(object_field(payload, "signal_page_counts"), "payment_order") == 1
    assert int_field(object_field(payload, "signal_page_counts"), "service_finality") == 1
    assert int_field(object_field(payload, "possible_sensitive_pattern_counts"), "resident_registration") == 0
    assert "page_alpha" not in payload_dump
    assert "DEBTOR_PERSON_REDACTED" not in payload_dump


def test_probe_rejects_missing_corpus_without_partial_output(tmp_path: Path) -> None:
    # Given: a missing OCR corpus root.
    output_path = tmp_path / "missing-summary.json"

    # When: the CLI probe is pointed at that missing root.
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--ocr-root",
            str(tmp_path / "missing-root"),
            "--out",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    # Then: it fails clearly and writes no partial summary.
    assert result.returncode == 1
    assert "ocr root does not exist" in result.stderr
    assert not output_path.exists()


def load_json_object(path: Path) -> JsonObject:
    return JSON_OBJECT_ADAPTER.validate_json(path.read_bytes())


def object_field(value: JsonObject, key: str) -> JsonObject:
    field = value[key]
    assert isinstance(field, dict)
    return field


def list_object_field(value: JsonObject, key: str) -> list[JsonObject]:
    field = value[key]
    assert isinstance(field, list)
    assert all(isinstance(item, dict) for item in field)
    return [item for item in field if isinstance(item, dict)]


def str_field(value: JsonObject, key: str) -> str:
    field = value[key]
    assert isinstance(field, str)
    return field


def int_field(value: JsonObject, key: str) -> int:
    field = value[key]
    assert isinstance(field, int)
    assert not isinstance(field, bool)
    return field


def bool_field(value: JsonObject, key: str) -> bool:
    field = value[key]
    assert isinstance(field, bool)
    return field


def _page_hash_matches(page: JsonObject) -> bool:
    page_path = FIXTURE_ROOT / str_field(page, "relative_path")
    digest = hashlib.sha256(page_path.read_bytes()).hexdigest()
    return str_field(page, "source_hash") == f"sha256:{digest}"


def _page_counts_match(page: JsonObject) -> bool:
    page_text = (FIXTURE_ROOT / str_field(page, "relative_path")).read_text(encoding="utf-8")
    return int_field(page, "line_count") == len(page_text.splitlines()) and int_field(page, "char_count") == len(page_text)


def _contains_forbidden_key(value: JsonValue) -> bool:
    if isinstance(value, dict):
        return any(key in FORBIDDEN_KEYS or _contains_forbidden_key(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_key(item) for item in value)
    return False
