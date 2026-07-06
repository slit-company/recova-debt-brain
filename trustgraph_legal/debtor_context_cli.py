from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Final

from trustgraph_legal.debtor_context_builder import DebtorContextInputError, build_debtor_context
from trustgraph_legal.debtor_context_types import DebtorGraphPayload, DocumentAssembly, DocumentPage, JsonObject, JsonValue
from trustgraph_legal.debtor_snapshots import replay_snapshot, validate_snapshot_provenance
from trustgraph_legal.document_assembly import DocumentAssemblyPayload, build_document_assembly_payload
from trustgraph_legal.document_assembly_pages import DocumentAssemblyInputError, MaterializedPage, materialize_pages
from trustgraph_legal.route_candidates import (
    LEGAL_SOURCES_PATH,
    ROUTES_PATH,
    RouteResourceError,
    evaluate_route_candidates,
    load_route_templates,
)

UNKNOWN_DOCUMENT_TYPE: Final = "unknown"


@dataclass(frozen=True, slots=True)
class DebtorContextCliError(Exception):
    location: str
    detail: str

    def __str__(self) -> str:
        return "{}: {}".format(self.location, self.detail)


@dataclass(frozen=True, slots=True)
class _CliRequest:
    ocr_root: Path | None
    assembly: Path | None
    out: Path
    repo_root: Path
    route_resources: Path
    legal_sources: Path
    summary_only: bool
    limit: int | None


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        request = _request(args)
        graph = _graph(_assembly_payload(request), request)
        output = _output_json(graph, request.summary_only)
        request.out.parent.mkdir(parents=True, exist_ok=True)
        _ = request.out.write_text(
            json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (
        DebtorContextCliError, DebtorContextInputError, DocumentAssemblyInputError,
        RouteResourceError, OSError, json.JSONDecodeError,
    ) as error:
        print("error: {}".format(error), file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "debtor_graph_id": graph.debtor_graph_id,
                "evidence": str(request.out),
                "route_candidates": len(graph.route_candidates),
                "summary_only": request.summary_only,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python3 -m trustgraph_legal.debtor_context")
    _ = parser.add_argument("--ocr-root")
    _ = parser.add_argument("--assembly")
    _ = parser.add_argument("--out", required=True)
    _ = parser.add_argument("--route-resources", default=str(ROUTES_PATH))
    _ = parser.add_argument("--legal-sources", default=str(LEGAL_SOURCES_PATH))
    _ = parser.add_argument("--repo-root", default=".")
    _ = parser.add_argument("--summary-only", action="store_true")
    _ = parser.add_argument("--limit", type=int)
    return parser


def _request(args: argparse.Namespace) -> _CliRequest:
    ocr_root = Path(args.ocr_root) if args.ocr_root is not None else None
    assembly = Path(args.assembly) if args.assembly is not None else None
    if (ocr_root is None) == (assembly is None):
        raise DebtorContextCliError("input", "provide exactly one of --ocr-root or --assembly")
    return _CliRequest(
        ocr_root, assembly, Path(args.out), Path(args.repo_root),
        Path(args.route_resources), Path(args.legal_sources), args.summary_only, args.limit,
    )


def _assembly_payload(request: _CliRequest) -> DocumentAssemblyPayload:
    if request.limit is not None and request.limit < 1:
        raise DebtorContextCliError("limit", "--limit must be >= 1")
    if request.assembly is not None:
        return _limit_payload(_assembly_payload_from_json(request.assembly), request.limit)
    if request.ocr_root is None:
        raise DebtorContextCliError("input", "--ocr-root is required")
    if not request.ocr_root.exists():
        raise DocumentAssemblyInputError(request.ocr_root, "OCR root not found")
    if not request.ocr_root.is_dir():
        raise DocumentAssemblyInputError(request.ocr_root, "OCR root is not a directory")
    pages = materialize_pages(request.ocr_root, request.repo_root)
    return build_document_assembly_payload(_limit_pages(pages, request.limit))


def _graph(assembly_payload: DocumentAssemblyPayload, request: _CliRequest) -> DebtorGraphPayload:
    graph = build_debtor_context(assembly_payload, request.repo_root)
    routes = evaluate_route_candidates(
        graph,
        templates=load_route_templates(request.route_resources),
        legal_sources_path=request.legal_sources,
    )
    snapshot = replace(graph.graph_snapshot, route_candidate_ids=tuple(route.route_id for route in routes))
    return replace(graph, graph_snapshot=snapshot, route_candidates=routes)


def _assembly_payload_from_json(path: Path) -> DocumentAssemblyPayload:
    data = _json_object(json.loads(path.read_text(encoding="utf-8")), str(path))
    pages = tuple(
        _document_page(page, "document_pages[{}]".format(index))
        for index, page in enumerate(_json_objects(data.get("document_pages"), "document_pages"))
    )
    assemblies = tuple(
        _document_assembly(assembly, "document_assemblies[{}]".format(index))
        for index, assembly in enumerate(_json_objects(data.get("document_assemblies"), "document_assemblies"))
    )
    if not pages or not assemblies:
        raise DebtorContextCliError(str(path), "full DocumentAssembly JSON is required")
    pii_profile = _json_object(data.get("pii_profile"), "pii_profile")
    return DocumentAssemblyPayload(pages, assemblies, _optional_int(pii_profile.get("sensitive_shape_pages"), 0))


def _document_page(data: JsonObject, location: str) -> DocumentPage:
    return DocumentPage(
        page_id=_text(data, "page_id", location),
        source_ref=_text(data, "source_ref", location),
        source_hash=_text(data, "source_hash", location),
        relative_path=_text(data, "relative_path", location),
        page_order=_int(data, "page_order", location),
        classifier_document_type=_text(data, "classifier_document_type", location),
        review_status=_text(data, "review_status", location),
        line_count=_int(data, "line_count", location),
        char_count=_int(data, "char_count", location),
    )


def _document_assembly(data: JsonObject, location: str) -> DocumentAssembly:
    return DocumentAssembly(
        assembly_id=_text(data, "assembly_id", location),
        document_id=_text(data, "document_id", location),
        canonical_document_type=_text(data, "canonical_document_type", location),
        page_ids=_strings(data, "page_ids", location),
        source_refs=_strings(data, "source_refs", location),
        source_hashes=_strings(data, "source_hashes", location),
        confidence=_float(data, "confidence", location),
        review_status=_text(data, "review_status", location),
        assembly_method=_text(data, "assembly_method", location),
        procedure_episode_id=_optional_text(data.get("procedure_episode_id")),
    )


def _limit_pages(
    pages: tuple[MaterializedPage, ...],
    limit: int | None,
) -> tuple[MaterializedPage, ...]:
    return pages if limit is None else pages[:limit]


def _limit_payload(payload: DocumentAssemblyPayload, limit: int | None) -> DocumentAssemblyPayload:
    if limit is None:
        return payload
    selected_pages = payload.document_pages[:limit]
    pages_by_id = {page.page_id: page for page in selected_pages}
    assemblies = tuple(
        _limit_assembly(assembly, pages_by_id)
        for assembly in payload.document_assemblies
        if any(page_id in pages_by_id for page_id in assembly.page_ids)
    )
    return DocumentAssemblyPayload(selected_pages, assemblies, payload.sensitive_shape_pages)


def _limit_assembly(assembly: DocumentAssembly, pages_by_id: dict[str, DocumentPage]) -> DocumentAssembly:
    page_ids = tuple(page_id for page_id in assembly.page_ids if page_id in pages_by_id)
    return replace(
        assembly, page_ids=page_ids,
        source_refs=tuple(pages_by_id[page_id].source_ref for page_id in page_ids),
        source_hashes=tuple(pages_by_id[page_id].source_hash for page_id in page_ids),
    )


def _output_json(graph: DebtorGraphPayload, summary_only: bool) -> JsonObject:
    if summary_only:
        return {
            "schema_version": "recova-debtor-context-summary/v1",
            "debtor_graph_id": graph.debtor_graph_id,
            "graph_snapshot_id": graph.graph_snapshot.graph_snapshot_id,
            "identity_resolution": graph.identity_resolution,
            "summary": _summary(graph),
            "pii_profile": {"raw_text_included": False, "source_text_included": False},
        }
    output = graph.to_json()
    output["summary"] = _summary(graph)
    return output


def _summary(graph: DebtorGraphPayload) -> JsonObject:
    replay = replay_snapshot(graph)
    provenance = validate_snapshot_provenance(graph)
    return {
        "case_packets": len(graph.case_packets),
        "document_pages": len(graph.document_pages),
        "document_assemblies": len(graph.document_assemblies),
        "unknown_assemblies": sum(
            1 for assembly in graph.document_assemblies if assembly.canonical_document_type == UNKNOWN_DOCUMENT_TYPE
        ),
        "fact_assertions": len(graph.fact_assertions),
        "route_candidates": len(graph.route_candidates),
        "route_status_counts": _route_status_counts(graph),
        "review_items": len(graph.review_items),
        "snapshot_replay_id": replay.replay_snapshot_id,
        "provenance_valid": provenance.valid,
        "provenance_issues": len(provenance.issues),
    }


def _route_status_counts(graph: DebtorGraphPayload) -> JsonObject:
    counts: dict[str, JsonValue] = {}
    for candidate in graph.route_candidates:
        counts[candidate.status] = _int_value(counts.get(candidate.status)) + 1
    return counts


def _json_objects(value: JsonValue, location: str) -> tuple[JsonObject, ...]:
    if not isinstance(value, list):
        raise DebtorContextCliError(location, "must be a list")
    return tuple(_json_object(item, "{}[{}]".format(location, index)) for index, item in enumerate(value))


def _json_object(value: JsonValue, location: str) -> JsonObject:
    if isinstance(value, dict):
        return value
    raise DebtorContextCliError(location, "must be an object")


def _text(data: JsonObject, field: str, location: str) -> str:
    value = data.get(field)
    if isinstance(value, str) and value:
        return value
    raise DebtorContextCliError(location, "{} must be a non-empty string".format(field))


def _optional_text(value: JsonValue) -> str | None:
    return value if isinstance(value, str) and value else None


def _strings(data: JsonObject, field: str, location: str) -> tuple[str, ...]:
    value = data.get(field)
    if not isinstance(value, list):
        raise DebtorContextCliError(location, "{} must be a list".format(field))
    strings = tuple(item for item in value if isinstance(item, str) and item)
    if len(strings) != len(value):
        raise DebtorContextCliError(location, "{} must contain only non-empty strings".format(field))
    return strings


def _int(data: JsonObject, field: str, location: str) -> int:
    value = data.get(field)
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    raise DebtorContextCliError(location, "{} must be an integer".format(field))


def _optional_int(value: JsonValue, default: int) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else default


def _float(data: JsonObject, field: str, location: str) -> float:
    value = data.get(field)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    raise DebtorContextCliError(location, "{} must be numeric".format(field))


def _int_value(value: JsonValue) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0
