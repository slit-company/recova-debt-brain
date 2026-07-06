from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import List

from trustgraph_legal.debtor_context import build_debtor_context
from trustgraph_legal.debtor_context_cli import _assembly_payload_from_json as assembly_payload_from_json
from trustgraph_legal.debtor_context_types import DebtorGraphPayload, JsonObject, JsonValue
from trustgraph_legal.debtor_snapshots import replay_snapshot, validate_snapshot_provenance
from trustgraph_legal.document_assembly import DocumentAssemblyPayload, build_document_assembly
from trustgraph_legal.mcp_inputs import object_list, path_arg, str_arg
from trustgraph_legal.route_candidates import LEGAL_SOURCES_PATH, ROUTES_PATH, evaluate_route_candidates, load_route_templates


def assemble_debtor_documents(args: JsonObject, root: Path) -> JsonObject:
    return _assembly_payload(args, root).to_json(_bool_arg(args, "summary_only"))


def build_debtor_context_graph(args: JsonObject, root: Path) -> JsonObject:
    return _debtor_graph(args, root).to_json()


def get_debtor_graph_snapshot(args: JsonObject, root: Path) -> JsonObject:
    graph = _graph_json(args, root)
    snapshot = _json_object(graph.get("graph_snapshot"))
    replay = replay_snapshot(graph).to_json()
    provenance = validate_snapshot_provenance(graph).to_json()
    return {
        "graph_snapshot_id": _text_or(snapshot.get("graph_snapshot_id"), _text_or(graph.get("graph_snapshot_id"), "")),
        "graph_snapshot": snapshot,
        "snapshot_replay": replay,
        "provenance": provenance,
    }


def list_debtor_route_candidates(args: JsonObject, root: Path) -> JsonObject:
    graph = _graph_json(args, root)
    routes = object_list(graph.get("route_candidates"))
    return {
        "graph_snapshot_id": _text_or(graph.get("graph_snapshot_id"), ""),
        "route_count": len(routes),
        "route_candidates": _json_list(routes),
    }


def explain_debtor_route_candidate(args: JsonObject, root: Path) -> JsonObject:
    route_id = str_arg(args, "route_id", "")
    routes = object_list(_graph_json(args, root).get("route_candidates"))
    for route in routes:
        if route.get("route_id") == route_id:
            return {
                "route_id": route_id,
                "route_label": _text_or(route.get("route_label"), route_id),
                "status": _text_or(route.get("status"), "unknown"),
                "review_status": _text_or(route.get("review_status"), "review_required"),
                "required_facts": _json_array(route.get("required_facts")),
                "missing_facts": _json_array(route.get("missing_facts")),
                "blocking_facts": _json_array(route.get("blocking_facts")),
                "legal_source_refs": _json_array(route.get("legal_source_refs")),
                "source_fact_ids": _json_array(route.get("source_fact_ids")),
                "no_direct_execution": _bool_value(route.get("no_direct_execution"), True),
            }
    return {"status": "not_found", "route_id": route_id, "available_route_ids": _route_ids(routes)}


def _debtor_graph(args: JsonObject, root: Path) -> DebtorGraphPayload:
    graph = build_debtor_context(_assembly_payload(args, root), root)
    routes = evaluate_route_candidates(
        graph,
        templates=load_route_templates(path_arg(args, "route_resources", root) or ROUTES_PATH),
        legal_sources_path=path_arg(args, "legal_sources", root) or LEGAL_SOURCES_PATH,
    )
    snapshot = replace(graph.graph_snapshot, route_candidate_ids=tuple(route.route_id for route in routes))
    return replace(graph, graph_snapshot=snapshot, route_candidates=routes)


def _assembly_payload(args: JsonObject, root: Path) -> DocumentAssemblyPayload:
    ocr_root = path_arg(args, "ocr_root", root)
    if ocr_root is not None:
        return build_document_assembly(ocr_root, root)
    assembly_path = path_arg(args, "assembly_path", root)
    if assembly_path is not None:
        return assembly_payload_from_json(assembly_path)
    raise PermissionError("debtor_graph_input_required")


def _graph_json(args: JsonObject, root: Path) -> JsonObject:
    supplied = args.get("graph")
    if isinstance(supplied, dict):
        return supplied
    graph_path = path_arg(args, "graph_path", root)
    if graph_path is None:
        return _debtor_graph(args, root).to_json()
    raw = json.loads(graph_path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def _json_object(value: JsonValue) -> JsonObject:
    return value if isinstance(value, dict) else {}


def _json_array(value: JsonValue) -> List[JsonValue]:
    return [item for item in value] if isinstance(value, list) else []


def _json_list(items: List[JsonObject]) -> List[JsonValue]:
    return [item for item in items]


def _route_ids(routes: List[JsonObject]) -> List[JsonValue]:
    return [route_id for route in routes if isinstance(route_id := route.get("route_id"), str)]


def _text_or(value: JsonValue, default: str) -> str:
    return value if isinstance(value, str) and value else default


def _bool_value(value: JsonValue, default: bool) -> bool:
    return value if isinstance(value, bool) else default


def _bool_arg(args: JsonObject, key: str) -> bool:
    return _bool_value(args.get(key), False)
