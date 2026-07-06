from __future__ import annotations

import importlib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from trustgraph_legal import __version__
from trustgraph_legal.debtor_context_types import DocumentAssembly, DocumentPage
from trustgraph_legal.document_assembly_pages import (
    DEFAULT_DOCUMENT_TYPE,
    DEFAULT_REVIEW_STATUS,
    DocumentAssemblyInputError,
    MaterializedPage,
    PageSource,
    materialize_pages,
    page_id,
)

JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject = dict[str, JsonValue]

SCHEMA_VERSION: Final = "recova-document-assembly/v0"
EXTRACTOR_VERSION: Final = "trustgraph_legal.document_assembly@{}".format(__version__)
ID_PREFIXES: Final = ("document:", "assembly:")

__all__ = [
    "DocumentAssemblyInputError",
    "DocumentAssemblyPayload",
    "build_document_assembly",
    "build_document_assembly_payload",
    "main",
]


@dataclass(frozen=True, slots=True)
class DocumentAssemblyPayload:
    document_pages: tuple[DocumentPage, ...]
    document_assemblies: tuple[DocumentAssembly, ...]
    sensitive_shape_pages: int

    def to_json(self, summary_only: bool = False) -> JsonObject:
        needs_review = sum(
            1 for item in self.document_assemblies if item.review_status == DEFAULT_REVIEW_STATUS
        )
        summary: JsonObject = {
            "pages": len(self.document_pages),
            "assemblies": len(self.document_assemblies),
            "document_pages": len(self.document_pages),
            "document_assemblies": len(self.document_assemblies),
            "needs_review": needs_review,
        }
        pii_profile: JsonObject = {
            "raw_text_included": False,
            "source_text_included": False,
            "sensitive_shape_pages": self.sensitive_shape_pages,
        }
        payload: JsonObject = {
            "schema_version": SCHEMA_VERSION,
            "extractor_version": EXTRACTOR_VERSION,
            "summary": summary,
            "pii_profile": pii_profile,
        }
        if summary_only:
            return payload
        payload.update({
            "document_pages": [page.to_json() for page in self.document_pages],
            "document_assemblies": [assembly.to_json() for assembly in self.document_assemblies],
        })
        return payload


def build_document_assembly(
    pages_dir: Path,
    repo_root: Path | None = None,
) -> DocumentAssemblyPayload:
    root = repo_root if repo_root is not None else Path.cwd()
    return build_document_assembly_payload(materialize_pages(pages_dir, root))


def build_document_assembly_payload(
    materialized_pages: tuple[MaterializedPage, ...],
) -> DocumentAssemblyPayload:
    normalized_pages = tuple(_normalize_page(page) for page in materialized_pages)
    document_pages = tuple(page.to_document_page() for page in normalized_pages)
    return DocumentAssemblyPayload(
        document_pages=document_pages,
        document_assemblies=_assemblies(normalized_pages),
        sensitive_shape_pages=sum(1 for page in normalized_pages if page.sensitive_shape_count > 0),
    )


def main(argv: Sequence[str] | None = None) -> int:
    cli = importlib.import_module("trustgraph_legal.document_assembly_cli")
    return cli.main(argv)


def _assemblies(pages: tuple[MaterializedPage, ...]) -> tuple[DocumentAssembly, ...]:
    grouped: dict[str, list[MaterializedPage]] = {}
    for page in pages:
        grouped.setdefault(page.source.document_id, []).append(page)
    assemblies = [
        _assembly(document_id, tuple(sorted(group_pages, key=lambda page: page.source.page_order)))
        for document_id, group_pages in grouped.items()
    ]
    return tuple(sorted(assemblies, key=lambda assembly: assembly.document_id))


def _assembly(document_id: str, pages: tuple[MaterializedPage, ...]) -> DocumentAssembly:
    document_id_suffix = _id_suffix(document_id)
    canonical_document_type = _assembly_document_type(pages)
    review_status = _assembly_review_status(canonical_document_type, pages)
    return DocumentAssembly(
        assembly_id="assembly:{}".format(document_id_suffix),
        document_id="document:{}".format(document_id_suffix),
        canonical_document_type=canonical_document_type,
        page_ids=tuple(page_id(_id_suffix(page.source.document_id), page.source.page_order) for page in pages),
        source_refs=tuple(page.source_ref for page in pages),
        source_hashes=tuple(page.source_hash for page in pages),
        confidence=_assembly_confidence(pages),
        review_status=review_status,
    )


def _assembly_document_type(pages: tuple[MaterializedPage, ...]) -> str:
    document_types = {page.source.canonical_document_type for page in pages}
    if len(document_types) == 1:
        return next(iter(document_types))
    return DEFAULT_DOCUMENT_TYPE


def _assembly_review_status(canonical_document_type: str, pages: tuple[MaterializedPage, ...]) -> str:
    if canonical_document_type == DEFAULT_DOCUMENT_TYPE:
        return DEFAULT_REVIEW_STATUS
    if any(page.source.review_status == DEFAULT_REVIEW_STATUS for page in pages):
        return DEFAULT_REVIEW_STATUS
    return "assembled"


def _assembly_confidence(pages: tuple[MaterializedPage, ...]) -> float:
    if not pages:
        return 0.0
    return round(sum(page.source.confidence for page in pages) / len(pages), 2)


def _normalize_page(page: MaterializedPage) -> MaterializedPage:
    document_id = _id_suffix(page.source.document_id)
    if document_id == page.source.document_id:
        return page
    return MaterializedPage(
        source=PageSource(
            document_id=document_id,
            canonical_document_type=page.source.canonical_document_type,
            relative_path=page.source.relative_path,
            page_order=page.source.page_order,
            confidence=page.source.confidence,
            review_status=page.source.review_status,
        ),
        repo_relative_path=page.repo_relative_path,
        source_ref=page.source_ref,
        source_hash=page.source_hash,
        line_count=page.line_count,
        char_count=page.char_count,
        sensitive_shape_count=page.sensitive_shape_count,
    )


def _id_suffix(value: str) -> str:
    suffix = value.strip()
    previous = ""
    while suffix != previous:
        previous = suffix
        for prefix in ID_PREFIXES:
            if suffix.startswith(prefix):
                suffix = suffix.removeprefix(prefix)
    return suffix


if __name__ == "__main__":
    raise SystemExit(main())
