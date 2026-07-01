from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from trustgraph_legal.case_graph import build_case_graph
from trustgraph_legal.classifier import classify_text
from trustgraph_legal.fields import DocumentInput, extract_fields
from trustgraph_legal.governance import attempt_promotion, build_governance_payload
from trustgraph_legal.governance_models import JsonValue, OntologyCandidate
from trustgraph_legal.mcp_envelope import source_refs
from trustgraph_legal.mcp_inputs import (
    DEFAULT_COLLECTION,
    document_id,
    hash_text,
    int_arg,
    manifest_path,
    object_list,
    ontology_path,
    packet_entities,
    path_arg,
    str_arg,
)
from trustgraph_legal.registry import RegistryOptions, collect_registry_payload
from trustgraph_legal.stop_gates import evaluate_case_graph

JsonObject = Dict[str, JsonValue]


def ingest_legal_document(args: JsonObject, root: Path) -> JsonObject:
    zip_path = path_arg(args, "zip_path", root)
    if zip_path is not None:
        options = RegistryOptions(
            limit=int_arg(args, "limit"),
            workspace=str_arg(args, "workspace", "default"),
            collection=str_arg(args, "collection", DEFAULT_COLLECTION),
        )
        return collect_registry_payload(zip_path, options).to_json()
    return {
        "status": "not_configured",
        "message": "v0 MCP domain layer does not write to TrustGraph storage directly",
        "accepted_operations": ["dry-run zip registry", "review queue"],
        "no_execution_actions": True,
    }


def ingest_ocr_markdown(args: JsonObject) -> JsonObject:
    text = str_arg(args, "markdown_text", str_arg(args, "text", ""))
    doc_id = document_id(args, text)
    source_ref = str_arg(args, "source_ref", "mcp:ocr-markdown")
    classification = classify_text(doc_id, source_ref, text)
    doc_type = str_arg(args, "document_type", str(classification.document_type.value))
    fields = extract_fields(DocumentInput(doc_id, doc_type, source_ref, text))
    return {
        "status": "queued_for_review",
        "document_id": doc_id,
        "source_hash": hash_text(text),
        "classification": classification.to_json(),
        "field_extraction": fields.to_json(),
        "no_execution_actions": True,
    }


def status_result(args: JsonObject) -> JsonObject:
    return {
        "status": "not_configured",
        "document_id": str_arg(args, "document_id", ""),
        "processing_id": str_arg(args, "processing_id", ""),
        "message": "No production ingest backend is attached to the v0 domain tool layer.",
    }


def classify_result(args: JsonObject) -> JsonObject:
    text = str_arg(args, "text", "")
    return classify_text(document_id(args, text), str_arg(args, "source_ref", "mcp:text"), text).to_json()


def extract_case_packet(args: JsonObject, root: Path) -> JsonObject:
    text = str_arg(args, "text", "")
    if text:
        doc_id = document_id(args, text)
        source_ref = str_arg(args, "source_ref", "mcp:text")
        classification = classify_text(doc_id, source_ref, text)
        doc_type = str_arg(args, "document_type", str(classification.document_type.value))
        fields = extract_fields(DocumentInput(doc_id, doc_type, source_ref, text))
        return {"document_id": doc_id, "classification": classification.to_json(), "field_extraction": fields.to_json()}
    graph = case_graph(args, root)
    packets = graph.get("case_packets")
    return packets[0] if isinstance(packets, list) and packets else {"status": "not_found"}


def case_graph_result(args: JsonObject, root: Path) -> JsonObject:
    return case_graph(args, root)


def stopgate_result(args: JsonObject, root: Path, reason_codes: Optional[Tuple[str, ...]]) -> JsonObject:
    payload = evaluate_case_graph(case_graph(args, root)).to_json()
    if reason_codes is None:
        return _normalize_stopgate_payload(payload)
    gates = [gate for gate in object_list(payload.get("stop_gates")) if gate.get("reason_code") in reason_codes]
    return {
        "case_id": _stopgate_case_id(payload),
        "decision": "보류" if gates else "가능",
        "risk_flags": _risk_flags(gates),
        "source_refs": source_refs(gates),
        "stop_gates": gates,
        "all_case_decision": payload["decision"],
        "rule_refs": payload["rule_refs"],
    }


def ledger_summary(args: JsonObject, root: Path) -> JsonObject:
    entries = [
        entity for entity in packet_entities(case_graph(args, root))
        if entity.get("ontology_class") in {"operational-ledger", "ledger-entry", "recovery-transaction", "cost-entry"}
    ]
    return {"status": "summarized", "ledger_entries": entries, "entry_count": len(entries)}


def recommend_next_action(args: JsonObject, root: Path) -> JsonObject:
    checks = evaluate_case_graph(case_graph(args, root)).to_json()
    blocked = checks["decision"] != "가능"
    return {
        "decision": checks["decision"],
        "recommended_next_action": "hold_for_review" if blocked else "prepare_advisory_package_for_external_approval",
        "blocked_reasons": checks["blocked_reasons"],
        "required_preconditions": checks["required_preconditions"],
        "no_direct_filing_contact_or_collection": True,
    }


def unknown_document_types(args: JsonObject, root: Path) -> JsonObject:
    governance = build_governance_payload(manifest_path(args, root), root, ontology_path(args, root)).to_json()
    return {
        "candidates": [
            item for item in object_list(governance.get("candidates"))
            if "unknown" in str(item.get("reason", "")) or item.get("candidate_type") == "document_type"
        ],
        "review_items": [
            item for item in object_list(governance.get("review_items"))
            if item.get("queue_id") in {"unknown-document-type", "ontology-candidate"}
        ],
        "reprocess_plans": governance["reprocess_plans"],
    }


def review_fact(args: JsonObject) -> JsonObject:
    return {
        "status": "queued_for_review",
        "fact_id": str_arg(args, "fact_id", ""),
        "decision": str_arg(args, "decision", "needs_review"),
        "reviewer": str_arg(args, "reviewer", "mcp-caller"),
        "reason": str_arg(args, "reason", "manual_review_requested"),
        "production_graph_modified": False,
    }


def promote_candidate(args: JsonObject, root: Path) -> JsonObject:
    candidate = _candidate(args)
    metadata = args.get("approval_metadata")
    result = attempt_promotion(candidate, metadata if isinstance(metadata, dict) else {}, ontology_path(args, root))
    return result.to_json()


def reprocess_case(args: JsonObject, root: Path) -> JsonObject:
    governance = build_governance_payload(manifest_path(args, root), root, ontology_path(args, root)).to_json()
    return {
        "status": "planned",
        "case_packet_id": str_arg(args, "case_packet_id", ""),
        "plans": governance["reprocess_plans"],
        "production_job_started": False,
    }


def case_graph(args: JsonObject, root: Path) -> JsonObject:
    supplied = args.get("case_graph")
    if isinstance(supplied, dict):
        return supplied
    graph_path = path_arg(args, "case_graph_path", root)
    if graph_path is not None:
        raw = json.loads(graph_path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    return build_case_graph(manifest_path(args, root), root).to_json()


def _normalize_stopgate_payload(payload: JsonObject) -> JsonObject:
    gates = object_list(payload.get("stop_gates"))
    normalized = dict(payload)
    normalized["case_id"] = _stopgate_case_id(payload)
    normalized["risk_flags"] = _risk_flags(gates)
    normalized["source_refs"] = source_refs(gates)
    return normalized


def _stopgate_case_id(payload: JsonObject) -> str:
    value = payload.get("case_id")
    return value if isinstance(value, str) and value else "case:unknown"


def _risk_flags(gates: List[JsonObject]) -> List[JsonValue]:
    flags = {
        str(gate.get("reason_code"))
        for gate in gates
        if gate.get("reason_code")
    }
    return sorted(flags)


def _candidate(args: JsonObject) -> OntologyCandidate:
    return OntologyCandidate(
        candidate_id=str_arg(args, "candidate_id", "candidate:mcp-review"),
        candidate_type=str_arg(args, "candidate_type", "document_type"),
        proposed_id=str_arg(args, "proposed_id", "mcp-reviewed-candidate"),
        proposed_label=str_arg(args, "proposed_label", "MCP Reviewed Candidate"),
        reason=str_arg(args, "reason", "mcp_promotion_review"),
        status="draft-review-required",
        source_refs=(str_arg(args, "source_ref", "mcp:ontology-candidate"),),
        provenance={"source_ref": str_arg(args, "source_ref", "mcp:ontology-candidate")},
        risk_flags=("no-auto-promotion",),
    )
