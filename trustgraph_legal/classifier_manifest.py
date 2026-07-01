from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple

from trustgraph_legal.classifier_rules import classify_text
from trustgraph_legal.classifier_types import (
    ClassificationPayload,
    ClassifierInputError,
    JsonValue,
    ManifestDocument,
)


def classify_manifest(manifest_path: Path) -> ClassificationPayload:
    documents = _manifest_documents(manifest_path)
    records = [
        classify_text(
            document_id=document.document_id,
            source_ref=document.source_fixture_path,
            text=_resolve_source_path(manifest_path, document.source_fixture_path).read_text(encoding="utf-8"),
        )
        for document in documents
    ]
    return ClassificationPayload(records=tuple(records))


def _manifest_documents(manifest_path: Path) -> Tuple[ManifestDocument, ...]:
    raw: JsonValue = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ClassifierInputError("manifest root must be a JSON object")
    documents = raw.get("documents")
    if not isinstance(documents, list):
        raise ClassifierInputError("manifest must contain documents list")
    parsed: List[ManifestDocument] = []
    for index, item in enumerate(documents):
        if not isinstance(item, dict):
            raise ClassifierInputError(f"manifest document {index} must be an object")
        document_id = item.get("document_id")
        source_fixture_path = item.get("source_fixture_path")
        if not isinstance(document_id, str) or not isinstance(source_fixture_path, str):
            raise ClassifierInputError(
                f"manifest document {index} is missing document_id or source_fixture_path"
            )
        parsed.append(
            ManifestDocument(
                document_id=document_id,
                source_fixture_path=source_fixture_path,
            )
        )
    return tuple(parsed)


def _resolve_source_path(manifest_path: Path, source_fixture_path: str) -> Path:
    raw_path = Path(source_fixture_path)
    if raw_path.is_absolute() and raw_path.exists():
        return raw_path
    search_roots = (Path.cwd(), *manifest_path.parents)
    for root in search_roots:
        candidate = root / raw_path
        if candidate.exists():
            return candidate
    raise ClassifierInputError(f"source fixture not found: {source_fixture_path}")
