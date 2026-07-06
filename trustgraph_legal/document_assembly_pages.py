from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final, override

from trustgraph_legal.debtor_context_types import DocumentPage
from trustgraph_legal.pii import redact_text

JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]

MANIFEST_NAME: Final = "manifest.json"
DEFAULT_DOCUMENT_TYPE: Final = "unknown"
DEFAULT_REVIEW_STATUS: Final = "needs_review"


@dataclass(frozen=True, slots=True)
class PageSource:
    document_id: str
    canonical_document_type: str
    relative_path: str
    page_order: int
    confidence: float
    review_status: str


@dataclass(frozen=True, slots=True)
class MaterializedPage:
    source: PageSource
    repo_relative_path: str
    source_ref: str
    source_hash: str
    line_count: int
    char_count: int
    sensitive_shape_count: int

    def to_document_page(self) -> DocumentPage:
        return DocumentPage(
            page_id=page_id(self.source.document_id, self.source.page_order),
            source_ref=self.source_ref,
            source_hash=self.source_hash,
            relative_path=self.repo_relative_path,
            page_order=self.source.page_order,
            classifier_document_type=self.source.canonical_document_type,
            review_status=self.source.review_status,
            line_count=self.line_count,
            char_count=self.char_count,
        )


@dataclass(frozen=True, slots=True)
class DocumentAssemblyInputError(Exception):
    input_path: Path
    detail: str

    @override
    def __str__(self) -> str:
        return "{}: {}".format(self.input_path, self.detail)


def materialize_pages(pages_dir: Path, repo_root: Path) -> tuple[MaterializedPage, ...]:
    manifest_path = pages_dir / MANIFEST_NAME
    sources = _manifest_sources(manifest_path) if manifest_path.exists() else _directory_sources(pages_dir)
    return tuple(_materialize_page(source, pages_dir, repo_root) for source in sources)


def page_id(document_id: str, page_order: int) -> str:
    return "page:{}:{:04d}".format(document_id, page_order)


def _manifest_sources(manifest_path: Path) -> tuple[PageSource, ...]:
    raw: JsonValue = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise DocumentAssemblyInputError(manifest_path, "manifest root must be an object")
    pages = raw.get("pages")
    if not isinstance(pages, list):
        raise DocumentAssemblyInputError(manifest_path, "manifest must contain pages list")
    sources = [_manifest_source(manifest_path, index, item) for index, item in enumerate(pages)]
    return tuple(sorted(sources, key=_source_sort_key))


def _manifest_source(manifest_path: Path, index: int, item: JsonValue) -> PageSource:
    if not isinstance(item, dict):
        raise DocumentAssemblyInputError(manifest_path, "page {} must be an object".format(index))
    document_id = item.get("document_id")
    canonical_document_type = item.get("canonical_document_type")
    relative_path = item.get("relative_path")
    page_order = item.get("page_order")
    if (
        not isinstance(document_id, str)
        or not isinstance(canonical_document_type, str)
        or not isinstance(relative_path, str)
        or not isinstance(page_order, int)
    ):
        raise DocumentAssemblyInputError(manifest_path, "page {} has invalid metadata".format(index))
    review_status = item.get("review_status")
    return PageSource(
        document_id=document_id,
        canonical_document_type=canonical_document_type,
        relative_path=relative_path,
        page_order=page_order,
        confidence=_confidence(item.get("confidence")),
        review_status=review_status if isinstance(review_status, str) else DEFAULT_REVIEW_STATUS,
    )


def _directory_sources(pages_dir: Path) -> tuple[PageSource, ...]:
    counters: dict[str, int] = {}
    sources: list[PageSource] = []
    paths = sorted(path for path in pages_dir.rglob("*.md") if path.is_file())
    for path in paths:
        relative_path = path.relative_to(pages_dir).as_posix()
        document_id = _fallback_document_id(Path(relative_path))
        counters[document_id] = counters.get(document_id, 0) + 1
        sources.append(
            PageSource(
                document_id=document_id,
                canonical_document_type=DEFAULT_DOCUMENT_TYPE,
                relative_path=relative_path,
                page_order=counters[document_id],
                confidence=0.0,
                review_status=DEFAULT_REVIEW_STATUS,
            )
        )
    return tuple(sources)


def _materialize_page(source: PageSource, pages_dir: Path, repo_root: Path) -> MaterializedPage:
    path = _resolve_page_path(pages_dir, source.relative_path)
    text = path.read_text(encoding="utf-8")
    repo_relative_path = _repo_relative_path(path, repo_root)
    return MaterializedPage(
        source=source,
        repo_relative_path=repo_relative_path,
        source_ref="fixture:{}#page={}".format(repo_relative_path, source.page_order),
        source_hash="sha256:{}".format(hashlib.sha256(text.encode("utf-8")).hexdigest()),
        line_count=len(text.splitlines()),
        char_count=len(text),
        sensitive_shape_count=redact_text(text).total,
    )


def _resolve_page_path(pages_dir: Path, relative_path: str) -> Path:
    root = pages_dir.resolve()
    path = (pages_dir / relative_path).resolve()
    if root != path and root not in path.parents:
        raise DocumentAssemblyInputError(pages_dir, "page path escapes fixture root: {}".format(relative_path))
    if not path.is_file():
        raise DocumentAssemblyInputError(pages_dir, "page file not found: {}".format(relative_path))
    return path


def _repo_relative_path(path: Path, repo_root: Path) -> str:
    resolved_root = repo_root.resolve()
    resolved_path = path.resolve()
    if resolved_root == resolved_path or resolved_root in resolved_path.parents:
        return resolved_path.relative_to(resolved_root).as_posix()
    return resolved_path.name


def _confidence(value: JsonValue) -> float:
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, int):
        return float(value)
    if isinstance(value, float):
        return value
    return 0.0


def _fallback_document_id(relative_path: Path) -> str:
    if len(relative_path.parts) > 1:
        return relative_path.parts[0]
    return relative_path.stem


def _source_sort_key(source: PageSource) -> tuple[str, int, str]:
    return (source.document_id, source.page_order, source.relative_path)
