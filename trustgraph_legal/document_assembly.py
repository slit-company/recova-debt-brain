from __future__ import annotations

import argparse
import json
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
    materialize_pages,
    page_id,
)

JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject = dict[str, JsonValue]

SCHEMA_VERSION: Final = "recova-document-assembly/v0"
EXTRACTOR_VERSION: Final = "trustgraph_legal.document_assembly@{}".format(__version__)

__all__ = [
    "DocumentAssemblyInputError",
    "DocumentAssemblyPayload",
    "build_document_assembly",
    "main",
]


@dataclass(frozen=True, slots=True)
class DocumentAssemblyPayload:
    document_pages: tuple[DocumentPage, ...]
    document_assemblies: tuple[DocumentAssembly, ...]
    sensitive_shape_pages: int

    def to_json(self) -> JsonObject:
        needs_review = sum(
            1 for item in self.document_assemblies if item.review_status == DEFAULT_REVIEW_STATUS
        )
        return {
            "schema_version": SCHEMA_VERSION,
            "extractor_version": EXTRACTOR_VERSION,
            "summary": {
                "document_pages": len(self.document_pages),
                "document_assemblies": len(self.document_assemblies),
                "needs_review": needs_review,
            },
            "document_pages": [page.to_json() for page in self.document_pages],
            "document_assemblies": [assembly.to_json() for assembly in self.document_assemblies],
            "pii_profile": {
                "raw_text_included": False,
                "source_text_included": False,
                "sensitive_shape_pages": self.sensitive_shape_pages,
            },
        }


def build_document_assembly(pages_dir: Path, repo_root: Path | None = None) -> DocumentAssemblyPayload:
    root = repo_root if repo_root is not None else Path.cwd()
    materialized_pages = materialize_pages(pages_dir, root)
    document_pages = tuple(page.to_document_page() for page in materialized_pages)
    return DocumentAssemblyPayload(
        document_pages=document_pages,
        document_assemblies=_assemblies(materialized_pages),
        sensitive_shape_pages=sum(1 for page in materialized_pages if page.sensitive_shape_count > 0),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m trustgraph_legal.document_assembly")
    _ = parser.add_argument("--pages", required=True)
    _ = parser.add_argument("--out", required=True)
    _ = parser.add_argument("--repo-root", default=".")
    args = parser.parse_args(argv)
    payload = build_document_assembly(Path(args.pages), Path(args.repo_root))
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _ = output_path.write_text(
        json.dumps(payload.to_json(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {"document_pages": len(payload.document_pages), "document_assemblies": len(payload.document_assemblies), "evidence": str(output_path)},
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


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
    canonical_document_type = _assembly_document_type(pages)
    review_status = _assembly_review_status(canonical_document_type, pages)
    return DocumentAssembly(
        assembly_id="assembly:{}".format(document_id),
        document_id="document:{}".format(document_id),
        canonical_document_type=canonical_document_type,
        page_ids=tuple(page_id(page.source.document_id, page.source.page_order) for page in pages),
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


if __name__ == "__main__":
    raise SystemExit(main())
