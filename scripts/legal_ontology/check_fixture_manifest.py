#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Union

JsonValue = Union[None, bool, int, float, str, List["JsonValue"], Dict[str, "JsonValue"]]
JsonObject = Dict[str, JsonValue]

REQUIRED_TOP_LEVEL = (
    "schema_version",
    "ontology_version",
    "prompt_version",
    "ocr_corpus",
    "pii_policy",
    "documents",
)
REQUIRED_ENTRY_FIELDS = (
    "document_id",
    "document_type",
    "source_fixture_path",
    "ocr",
    "ontology_version",
    "prompt_version",
    "confidence",
    "review_status",
    "notes",
    "source_category",
)
REQUIRED_OCR_FIELDS = ("engine", "corpus", "corpus_date", "markdown_format")
COVERAGE_BUCKETS = {
    "attachment_collection_order",
    "judgment_payment_order",
    "service_finality_execution_clause",
    "identity_evidence",
    "insolvency_credit_recovery",
    "assignment_succession",
    "operational_ledger",
    "asset_evidence",
    "amount_interest",
}
REVIEW_STATUSES = {"synthetic_reviewed", "redacted_reviewed", "needs_review"}
HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
FORBIDDEN_PATTERNS = (
    re.compile(r"\b\d{6}-\d{7}\b"),
    re.compile(r"\b01[016789]-\d{3,4}-\d{4}\b"),
    re.compile(r"\b\d{2,4}-\d{2,6}-\d{4,8}\b"),
    re.compile(r"\b\d{10,16}\b"),
)


@dataclass(frozen=True)
class ValidationContext:
    manifest_path: Path
    ontology_version: str
    prompt_version: str


@dataclass(frozen=True)
class ManifestReadError(Exception):
    path: Path
    detail: str

    def __str__(self) -> str:
        return f"{self.path}: {self.detail}"


@dataclass(frozen=True)
class ManifestIssue:
    location: str
    message: str

    def format(self) -> str:
        return f"{self.location}: {self.message}"


def load_manifest(path: Path) -> JsonObject:
    with path.open(encoding="utf-8") as handle:
        raw = json.load(handle)

    if not isinstance(raw, dict):
        raise ManifestReadError(path=path, detail="root must be a JSON object")
    return raw


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def resolve_fixture_path(manifest_path: Path, source_path: str) -> Path:
    candidate = Path(source_path)
    if candidate.is_absolute():
        return candidate

    cwd_candidate = Path.cwd() / candidate
    if cwd_candidate.exists():
        return cwd_candidate
    return manifest_path.parent / candidate


def text_value(entry: JsonObject, field: str) -> str:
    value = entry.get(field)
    if isinstance(value, str):
        return value
    return ""


def validate_text_field(entry: JsonObject, field: str, location: str) -> List[ManifestIssue]:
    value = entry.get(field)
    if not isinstance(value, str) or not value.strip():
        return [ManifestIssue(location=location, message=f"{field} must be a non-empty string")]
    return []


def validate_hash(entry: JsonObject, fixture_path: Path, location: str) -> List[ManifestIssue]:
    source_hash = text_value(entry, "source_hash")
    synthetic_hash = text_value(entry, "synthetic_hash")
    expected_hash = source_hash or synthetic_hash
    if not expected_hash:
        return [ManifestIssue(location=location, message="missing source_hash or synthetic_hash")]
    if not HASH_PATTERN.fullmatch(expected_hash):
        return [ManifestIssue(location=location, message="hash must use sha256:<64 lowercase hex>")]
    if not fixture_path.exists():
        return [ManifestIssue(location=location, message=f"fixture not found: {fixture_path}")]

    actual_hash = sha256_file(fixture_path)
    if actual_hash != expected_hash:
        return [ManifestIssue(location=location, message="fixture hash mismatch")]
    return []


def validate_fixture_text(fixture_path: Path, location: str) -> List[ManifestIssue]:
    if not fixture_path.exists():
        return []

    text = fixture_path.read_text(encoding="utf-8")
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.search(text):
            return [ManifestIssue(location=location, message="forbidden personal data pattern in fixture")]
    return []


def validate_ocr(entry: JsonObject, location: str) -> List[ManifestIssue]:
    ocr = entry.get("ocr")
    if not isinstance(ocr, dict):
        return [ManifestIssue(location=location, message="ocr must be an object")]

    issues: List[ManifestIssue] = []
    for field in REQUIRED_OCR_FIELDS:
        issues.extend(validate_text_field(ocr, field, f"{location}.ocr"))
    return issues


def validate_confidence(entry: JsonObject, location: str) -> List[ManifestIssue]:
    value = entry.get("confidence")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return [ManifestIssue(location=location, message="confidence must be a number")]
    if value < 0 or value > 1:
        return [ManifestIssue(location=location, message="confidence must be between 0 and 1")]
    return []


def validate_review_status(entry: JsonObject, location: str) -> List[ManifestIssue]:
    status = text_value(entry, "review_status")
    if status not in REVIEW_STATUSES:
        return [ManifestIssue(location=location, message="review_status is not recognized")]
    return []


def validate_document(
    context: ValidationContext,
    entry: JsonObject,
    index: int,
) -> List[ManifestIssue]:
    location = f"documents[{index}]"
    issues: List[ManifestIssue] = []
    for field in REQUIRED_ENTRY_FIELDS:
        if field not in entry:
            issues.append(ManifestIssue(location=location, message=f"missing {field}"))

    for field in ("document_id", "document_type", "source_fixture_path", "notes", "source_category"):
        issues.extend(validate_text_field(entry, field, location))

    if text_value(entry, "ontology_version") != context.ontology_version:
        issues.append(ManifestIssue(location=location, message="ontology_version must match manifest"))
    if text_value(entry, "prompt_version") != context.prompt_version:
        issues.append(ManifestIssue(location=location, message="prompt_version must match manifest"))

    fixture_path = resolve_fixture_path(context.manifest_path, text_value(entry, "source_fixture_path"))
    issues.extend(validate_hash(entry, fixture_path, location))
    issues.extend(validate_fixture_text(fixture_path, location))
    issues.extend(validate_ocr(entry, location))
    issues.extend(validate_confidence(entry, location))
    issues.extend(validate_review_status(entry, location))
    return issues


def validate_manifest(manifest_path: Path) -> List[ManifestIssue]:
    manifest = load_manifest(manifest_path)
    issues: List[ManifestIssue] = []
    for field in REQUIRED_TOP_LEVEL:
        if field not in manifest:
            issues.append(ManifestIssue(location="manifest", message=f"missing {field}"))

    documents = manifest.get("documents")
    if not isinstance(documents, list):
        issues.append(ManifestIssue(location="manifest", message="documents must be an array"))
        return issues

    context = ValidationContext(
        manifest_path=manifest_path,
        ontology_version=text_value(manifest, "ontology_version"),
        prompt_version=text_value(manifest, "prompt_version"),
    )
    seen_ids: set[str] = set()
    source_categories: set[str] = set()

    for index, item in enumerate(documents):
        location = f"documents[{index}]"
        if not isinstance(item, dict):
            issues.append(ManifestIssue(location=location, message="entry must be an object"))
            continue

        document_id = text_value(item, "document_id")
        if document_id in seen_ids:
            issues.append(ManifestIssue(location=location, message=f"duplicate document_id {document_id}"))
        if document_id:
            seen_ids.add(document_id)

        source_category = text_value(item, "source_category")
        if source_category:
            source_categories.add(source_category)

        issues.extend(
            validate_document(
                context=context,
                entry=item,
                index=index,
            )
        )

    for bucket in sorted(COVERAGE_BUCKETS - source_categories):
        issues.append(ManifestIssue(location="manifest", message=f"missing source_category {bucket}"))
    return issues


def main(argv: Sequence[str]) -> int:
    if len(argv) != 2:
        print("usage: check_fixture_manifest.py <manifest.json>", file=sys.stderr)
        return 2

    manifest_path = Path(argv[1])
    try:
        issues = validate_manifest(manifest_path)
    except json.JSONDecodeError as error:
        print(f"ERROR {manifest_path}: invalid JSON: {error}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"ERROR {manifest_path}: {error}", file=sys.stderr)
        return 1
    except ManifestReadError as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 1

    if issues:
        for issue in issues:
            print(f"ERROR {issue.format()}", file=sys.stderr)
        return 1

    print("PASS manifest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
