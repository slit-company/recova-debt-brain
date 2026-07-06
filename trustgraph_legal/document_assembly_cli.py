from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from trustgraph_legal.document_assembly import (
    DocumentAssemblyPayload,
    build_document_assembly_payload,
)
from trustgraph_legal.document_assembly_pages import (
    DEFAULT_REVIEW_STATUS,
    DocumentAssemblyInputError,
    MaterializedPage,
    PageSource,
    materialize_pages,
)
from trustgraph_legal.pii import redact_text

REQUIRED_TSV_COLUMNS: Final = frozenset(
    {"document_id", "canonical_document_type", "relative_path", "page_order"}
)


@dataclass(frozen=True, slots=True)
class _BuildRequest:
    ocr_root: Path
    repo_root: Path
    manifest_tsv: Path | None
    limit: int | None


@dataclass(frozen=True, slots=True)
class _TsvRow:
    manifest_path: Path
    row_number: int
    values: dict[str, str]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m trustgraph_legal.document_assembly")
    _ = parser.add_argument("--ocr-root")
    _ = parser.add_argument("--pages")
    _ = parser.add_argument("--manifest-tsv")
    _ = parser.add_argument("--out", required=True)
    _ = parser.add_argument("--repo-root", default=".")
    _ = parser.add_argument("--summary-only", action="store_true")
    _ = parser.add_argument("--limit", type=int)
    args = parser.parse_args(argv)
    input_root = args.ocr_root if args.ocr_root is not None else args.pages
    if input_root is None:
        parser.error("--ocr-root is required unless --pages is provided")
    request = _BuildRequest(
        ocr_root=Path(input_root),
        repo_root=Path(args.repo_root),
        manifest_tsv=Path(args.manifest_tsv) if args.manifest_tsv is not None else None,
        limit=args.limit,
    )
    output_path = Path(args.out)
    try:
        payload = _build_payload(request)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        _ = output_path.write_text(
            json.dumps(payload.to_json(summary_only=args.summary_only), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except DocumentAssemblyInputError as error:
        print("error: {}".format(error), file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "document_pages": len(payload.document_pages),
                "document_assemblies": len(payload.document_assemblies),
                "evidence": str(output_path),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


def _build_payload(request: _BuildRequest) -> DocumentAssemblyPayload:
    _validate_ocr_root(request.ocr_root)
    if request.manifest_tsv is not None:
        return build_document_assembly_payload(
            _limit_pages(_manifest_tsv_pages(request), request.manifest_tsv, request.limit)
        )
    pages = materialize_pages(request.ocr_root, request.repo_root)
    return build_document_assembly_payload(_limit_pages(pages, request.ocr_root, request.limit))


def _validate_ocr_root(ocr_root: Path) -> None:
    if not ocr_root.exists():
        raise DocumentAssemblyInputError(ocr_root, "OCR root not found")
    if not ocr_root.is_dir():
        raise DocumentAssemblyInputError(ocr_root, "OCR root is not a directory")


def _limit_pages(
    pages: tuple[MaterializedPage, ...],
    input_path: Path,
    limit: int | None,
) -> tuple[MaterializedPage, ...]:
    if limit is None:
        return pages
    if limit < 1:
        raise DocumentAssemblyInputError(input_path, "--limit must be >= 1")
    return pages[:limit]


def _manifest_tsv_pages(request: _BuildRequest) -> tuple[MaterializedPage, ...]:
    manifest_path = request.manifest_tsv
    if manifest_path is None:
        raise DocumentAssemblyInputError(request.ocr_root, "manifest_tsv_invalid: missing path")
    if not manifest_path.is_file():
        raise DocumentAssemblyInputError(manifest_path, "manifest_tsv_invalid: file not found")
    with manifest_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = set(reader.fieldnames or ())
        missing = sorted(REQUIRED_TSV_COLUMNS - fieldnames)
        if missing:
            raise DocumentAssemblyInputError(
                manifest_path,
                "manifest_tsv_invalid: missing columns {}".format(",".join(missing)),
            )
        sources = tuple(
            _tsv_source(_tsv_row(manifest_path, row_number, row))
            for row_number, row in enumerate(reader, start=2)
        )
    return tuple(_materialize_tsv_page(request, source) for source in sorted(sources, key=_source_sort_key))


def _tsv_row(manifest_path: Path, row_number: int, values: dict[str, str | None]) -> _TsvRow:
    normalized = {key: value for key, value in values.items() if value is not None}
    return _TsvRow(manifest_path=manifest_path, row_number=row_number, values=normalized)


def _tsv_source(row: _TsvRow) -> PageSource:
    return PageSource(
        document_id=_required_tsv_value(row, "document_id"),
        canonical_document_type=_required_tsv_value(row, "canonical_document_type"),
        relative_path=_required_tsv_value(row, "relative_path"),
        page_order=_tsv_page_order(row),
        confidence=_tsv_confidence(row.values.get("confidence", "")),
        review_status=row.values.get("review_status", DEFAULT_REVIEW_STATUS) or DEFAULT_REVIEW_STATUS,
    )


def _required_tsv_value(row: _TsvRow, column: str) -> str:
    value = row.values.get(column, "").strip()
    if not value:
        raise DocumentAssemblyInputError(
            row.manifest_path,
            "manifest_tsv_invalid: row {} missing {}".format(row.row_number, column),
        )
    return value


def _tsv_page_order(row: _TsvRow) -> int:
    raw_value = _required_tsv_value(row, "page_order")
    if not raw_value.isdecimal():
        raise DocumentAssemblyInputError(
            row.manifest_path,
            "manifest_tsv_invalid: row {} invalid page_order".format(row.row_number),
        )
    return int(raw_value)


def _tsv_confidence(raw_value: str) -> float:
    try:
        return float(raw_value) if raw_value else 0.0
    except ValueError:
        return 0.0


def _materialize_tsv_page(request: _BuildRequest, source: PageSource) -> MaterializedPage:
    path = _resolve_tsv_page_path(request.ocr_root, source.relative_path)
    text = path.read_text(encoding="utf-8")
    repo_relative_path = _repo_relative_path(path, request.repo_root)
    return MaterializedPage(
        source=source,
        repo_relative_path=repo_relative_path,
        source_ref="ocr:{}#page={}".format(repo_relative_path, source.page_order),
        source_hash="sha256:{}".format(hashlib.sha256(text.encode("utf-8")).hexdigest()),
        line_count=len(text.splitlines()),
        char_count=len(text),
        sensitive_shape_count=redact_text(text).total,
    )


def _resolve_tsv_page_path(ocr_root: Path, relative_path: str) -> Path:
    root = ocr_root.resolve()
    candidate = Path(relative_path)
    path = candidate.resolve() if candidate.is_absolute() else (ocr_root / candidate).resolve()
    if root != path and root not in path.parents:
        raise DocumentAssemblyInputError(ocr_root, "manifest_tsv_invalid: page path escapes OCR root")
    if not path.is_file():
        raise DocumentAssemblyInputError(ocr_root, "manifest_tsv_invalid: page file not found")
    return path


def _repo_relative_path(path: Path, repo_root: Path) -> str:
    resolved_root = repo_root.resolve()
    resolved_path = path.resolve()
    if resolved_root == resolved_path or resolved_root in resolved_path.parents:
        return resolved_path.relative_to(resolved_root).as_posix()
    return resolved_path.name


def _source_sort_key(source: PageSource) -> tuple[str, int, str]:
    return (source.document_id, source.page_order, source.relative_path)
