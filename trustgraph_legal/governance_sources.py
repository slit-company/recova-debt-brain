from __future__ import annotations

import json
from pathlib import Path

from trustgraph_legal.classifier import classify_text
from trustgraph_legal.fields import DocumentInput, extract_fields
from trustgraph_legal.governance_models import ManifestDocument, SourceContext


class GovernanceInputError(Exception):
    def __init__(self, manifest_path: Path, detail: str) -> None:
        self.manifest_path = manifest_path
        self.detail = detail
        super().__init__()

    def __str__(self) -> str:
        return "{}: {}".format(self.manifest_path, self.detail)


def source_contexts(manifest_path: Path, repo_root: Path) -> tuple[SourceContext, ...]:
    return tuple(
        _source_context(document, repo_root)
        for document in _manifest_documents(manifest_path)
    )


def _manifest_documents(manifest_path: Path) -> tuple[ManifestDocument, ...]:
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise GovernanceInputError(manifest_path, "manifest root must be an object")
    raw_documents = raw.get("documents")
    if not isinstance(raw_documents, list):
        raise GovernanceInputError(manifest_path, "missing documents list")
    documents: list[ManifestDocument] = []
    for index, item in enumerate(raw_documents):
        if not isinstance(item, dict):
            raise GovernanceInputError(
                manifest_path,
                "document {} must be an object".format(index),
            )
        document_id = item.get("document_id")
        document_type = item.get("document_type")
        source_fixture_path = item.get("source_fixture_path")
        source_hash = item.get("source_hash")
        if not all(
            isinstance(value, str)
            for value in (document_id, document_type, source_fixture_path, source_hash)
        ):
            raise GovernanceInputError(
                manifest_path,
                "document {} has invalid metadata".format(index),
            )
        documents.append(
            ManifestDocument(
                document_id=document_id,
                document_type=document_type,
                source_fixture_path=source_fixture_path,
                source_hash=source_hash,
            )
        )
    return tuple(documents)


def _source_context(document: ManifestDocument, repo_root: Path) -> SourceContext:
    fixture_path = repo_root / document.source_fixture_path
    text = fixture_path.read_text(encoding="utf-8")
    classifier = classify_text(document.document_id, document.source_fixture_path, text)
    fields = extract_fields(
        DocumentInput(
            document_id=document.document_id,
            document_type=document.document_type,
            source_ref="fixture:{}".format(document.source_fixture_path),
            text=text,
        )
    )
    return SourceContext(document=document, classifier=classifier, fields=fields)
