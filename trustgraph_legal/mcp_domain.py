from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Final, List, Optional, Tuple

from trustgraph_legal.case_graph import build_case_graph
from trustgraph_legal.classifier import classify_text
from trustgraph_legal.fields import DocumentInput, extract_fields
from trustgraph_legal.governance import attempt_promotion, build_governance_payload
from trustgraph_legal.governance_models import JsonValue, OntologyCandidate
from trustgraph_legal.pii import redact_text
from trustgraph_legal.registry import RegistryOptions, collect_registry_payload
from trustgraph_legal.stop_gates import evaluate_case_graph

JsonObject = Dict[str, JsonValue]
ToolHandler = Callable[[JsonObject, Path], JsonObject]

SCHEMA_VERSION: Final = "trustgraph-legal-mcp-tool-response/v1"
TOOL_CONTRACT_SCHEMA_VERSION: Final = "trustgraph-legal-mcp-tool-contract/v1"
DEFAULT_COLLECTION: Final = "recova-debt-collection"
DEFAULT_MANIFEST: Final = Path("tests/fixtures/legal-ocr/manifest.json")
DEFAULT_ONTOLOGY: Final = Path("resources/ontologies/recova-debt-collection.json")
TOOL_GROUPS: Final[Dict[str, Tuple[str, str]]] = {
    "list_debt_collection_tools": ("read", "read:tools"),
    "ingest_legal_document": ("ingest", "ingest:documents"),
    "ingest_ocr_markdown": ("ingest", "ingest:documents"),
    "get_ingest_status": ("ingest", "ingest:ingest-status"),
    "classify_legal_document": ("graph", "graph:document-classification"),
    "extract_case_packet": ("graph", "graph:case"),
    "get_case_graph": ("graph", "graph:case"),
    "check_case_stop_gates": ("stopgate", "stopgate:check"),
    "check_limitation_status": ("stopgate", "stopgate:check"),
    "check_attachment_target_rules": ("stopgate", "stopgate:check"),
    "summarize_case_ledger": ("read", "read:ledger"),
    "recommend_next_action": ("stopgate", "stopgate:recommend"),
    "list_unknown_document_types": ("governance", "governance:review"),
    "review_extracted_fact": ("governance", "governance:review"),
    "promote_ontology_candidate": ("governance", "governance:review"),
    "reprocess_case": ("governance", "governance:reprocess"),
}


@dataclass(frozen=True)
class ToolDefinition:
    tool_name: str
    group: str
    scope: str
    description: str
    parameters: Tuple[str, ...]
    handler: ToolHandler

    def to_json(self) -> JsonObject:
        return {
            "schema_version": TOOL_CONTRACT_SCHEMA_VERSION,
            "tool_name": self.tool_name,
            "name": self.tool_name,
            "group": self.group,
            "scope": self.scope,
            "description": self.description,
            "parameters": list(self.parameters),
            "input_schema": {
                "type": "object",
                "properties": {name: {"type": "string"} for name in self.parameters},
                "additionalProperties": True,
            },
            "output_schema": {
                "type": "object",
                "required": [
                    "schema_version",
                    "tool_name",
                    "group",
                    "scope",
                    "pii_profile",
                    "redaction",
                    "source_refs",
                    "warnings",
                    "result",
                ],
            },
            "redaction": {
                "default": "redacted",
                "raw_text_included": False,
                "source_text_included": False,
            },
        }


def _tool(
    name: str,
    description: str,
    parameters: Tuple[str, ...],
    handler: ToolHandler,
) -> ToolDefinition:
    group, scope = TOOL_GROUPS[name]
    return ToolDefinition(name, group, scope, description, parameters, handler)


TOOL_DEFINITIONS: Final[Tuple[ToolDefinition, ...]] = (
    _tool("list_debt_collection_tools", "List debt-collection domain tool contracts.", (), lambda args, root: {"tools": list_tools()}),
    _tool("ingest_legal_document", "Prepare a legal document for reviewed ingestion without storing raw PII.", ("zip_path", "workspace", "collection", "limit"), lambda args, root: _ingest_legal_document(args, root)),
    _tool("ingest_ocr_markdown", "Classify and extract OCR markdown into a review-safe queued envelope.", ("markdown_text", "document_id", "source_ref", "document_type"), lambda args, root: _ingest_ocr_markdown(args)),
    _tool("get_ingest_status", "Return deterministic v0 ingest status metadata.", ("document_id", "processing_id"), lambda args, root: _status_result(args)),
    _tool("classify_legal_document", "Classify a legal document with redacted evidence spans.", ("text", "document_id", "source_ref"), lambda args, root: _classify_result(args)),
    _tool("extract_case_packet", "Extract a case-packet projection from text or the fixture manifest.", ("text", "manifest_path", "document_id", "document_type"), lambda args, root: _extract_case_packet(args, root)),
    _tool("get_case_graph", "Return the deterministic redacted case graph.", ("manifest_path", "case_graph"), lambda args, root: _case_graph_result(args, root)),
    _tool("check_case_stop_gates", "Evaluate deterministic legal StopGates for a case graph.", ("case_graph", "case_graph_path", "manifest_path"), lambda args, root: _stopgate_result(args, root, None)),
    _tool("check_limitation_status", "Report limitation-risk StopGate status only.", ("case_graph", "case_graph_path", "manifest_path"), lambda args, root: _stopgate_result(args, root, ("limitation_risk",))),
    _tool("check_attachment_target_rules", "Report attachment-target, exemption, and priority review blockers.", ("case_graph", "case_graph_path", "manifest_path"), lambda args, root: _stopgate_result(args, root, ("exempt_claim_targeted", "unsupported_document_type_review"))),
    _tool("summarize_case_ledger", "Summarize redacted ledger facts from the case graph.", ("case_graph", "case_graph_path", "manifest_path"), lambda args, root: _ledger_summary(args, root)),
    _tool("recommend_next_action", "Recommend a non-executing next advisory action from StopGate status.", ("case_graph", "case_graph_path", "manifest_path"), lambda args, root: _recommend_next_action(args, root)),
    _tool("list_unknown_document_types", "List unknown-type and ontology-gap governance items.", ("manifest_path",), lambda args, root: _unknown_document_types(args, root)),
    _tool("review_extracted_fact", "Queue or record a reviewed fact decision without mutating production ontology.", ("fact_id", "decision", "reviewer", "reason"), lambda args, root: _review_fact(args)),
    _tool("promote_ontology_candidate", "Evaluate ontology promotion metadata and return accepted/rejected status only.", ("candidate_id", "approval_metadata", "ontology_path"), lambda args, root: _promote_candidate(args, root)),
    _tool("reprocess_case", "Return a reviewed reprocess plan; no production job is executed by this tool.", ("case_packet_id", "manifest_path"), lambda args, root: _reprocess_case(args, root)),
)


def list_tools() -> List[JsonObject]:
    return [definition.to_json() for definition in TOOL_DEFINITIONS]


def invoke_tool(
    tool_name: str,
    arguments: Optional[JsonObject] = None,
    repo_root: Optional[Path] = None,
) -> JsonObject:
    args = {} if arguments is None else arguments
    root = _repo_root(repo_root)
    definition = _definition(tool_name)
    if definition is None:
        return _envelope(
            tool_name,
            "read",
            "read:tools",
            {"status": "unknown_tool"},
            ["unknown_tool"],
        )
    try:
        result = _redact_json(definition.handler(args, root))
    except PermissionError as exc:
        return _envelope(
            definition.tool_name,
            definition.group,
            definition.scope,
            {"status": "rejected", "reason": str(exc)},
            [str(exc)],
        )
    source_refs = _source_refs(result)
    return _envelope(definition.tool_name, definition.group, definition.scope, result, [], source_refs)


def _definition(tool_name: str) -> Optional[ToolDefinition]:
    for definition in TOOL_DEFINITIONS:
        if definition.tool_name == tool_name:
            return definition
    return None


def _envelope(
    tool_name: str,
    group: str,
    scope: str,
    result: JsonValue,
    warnings: List[str],
    source_refs: Optional[List[JsonValue]] = None,
) -> JsonObject:
    profile = _pii_profile(result)
    return {
        "schema_version": SCHEMA_VERSION,
        "tool_name": tool_name,
        "group": group,
        "scope": scope,
        "pii_profile": profile,
        "redaction": {
            "status": "redacted",
            "default": "redacted",
            "raw_text_included": False,
            "source_text_included": False,
            "counts": profile.get("redacted", {}),
        },
        "source_refs": [] if source_refs is None else source_refs,
        "warnings": warnings,
        "result": result,
    }


def _ingest_legal_document(args: JsonObject, root: Path) -> JsonObject:
    zip_path = _path_arg(args, "zip_path", root)
    if zip_path is not None:
        options = RegistryOptions(
            limit=_int_arg(args, "limit"),
            workspace=_str_arg(args, "workspace", "default"),
            collection=_str_arg(args, "collection", DEFAULT_COLLECTION),
        )
        return collect_registry_payload(zip_path, options).to_json()
    return {
        "status": "not_configured",
        "message": "v0 MCP domain layer does not write to TrustGraph storage directly",
        "accepted_operations": ["dry-run zip registry", "review queue"],
        "no_execution_actions": True,
    }


def _ingest_ocr_markdown(args: JsonObject) -> JsonObject:
    text = _str_arg(args, "markdown_text", _str_arg(args, "text", ""))
    document_id = _document_id(args, text)
    source_ref = _str_arg(args, "source_ref", "mcp:ocr-markdown")
    classification = classify_text(document_id, source_ref, text)
    document_type = _str_arg(
        args,
        "document_type",
        str(classification.document_type.value),
    )
    fields = extract_fields(DocumentInput(document_id, document_type, source_ref, text))
    return {
        "status": "queued_for_review",
        "document_id": document_id,
        "source_hash": _hash_text(text),
        "classification": classification.to_json(),
        "field_extraction": fields.to_json(),
        "no_execution_actions": True,
    }


def _status_result(args: JsonObject) -> JsonObject:
    return {
        "status": "not_configured",
        "document_id": _str_arg(args, "document_id", ""),
        "processing_id": _str_arg(args, "processing_id", ""),
        "message": "No production ingest backend is attached to the v0 domain tool layer.",
    }


def _classify_result(args: JsonObject) -> JsonObject:
    text = _str_arg(args, "text", "")
    return classify_text(_document_id(args, text), _str_arg(args, "source_ref", "mcp:text"), text).to_json()


def _extract_case_packet(args: JsonObject, root: Path) -> JsonObject:
    text = _str_arg(args, "text", "")
    if text:
        document_id = _document_id(args, text)
        source_ref = _str_arg(args, "source_ref", "mcp:text")
        classification = classify_text(document_id, source_ref, text)
        document_type = _str_arg(
            args,
            "document_type",
            str(classification.document_type.value),
        )
        fields = extract_fields(DocumentInput(document_id, document_type, source_ref, text))
        return {"document_id": document_id, "classification": classification.to_json(), "field_extraction": fields.to_json()}
    graph = _case_graph(args, root)
    packets = graph.get("case_packets")
    return packets[0] if isinstance(packets, list) and packets else {"status": "not_found"}


def _case_graph_result(args: JsonObject, root: Path) -> JsonObject:
    return _case_graph(args, root)


def _stopgate_result(args: JsonObject, root: Path, reason_codes: Optional[Tuple[str, ...]]) -> JsonObject:
    payload = evaluate_case_graph(_case_graph(args, root)).to_json()
    if reason_codes is None:
        return _normalize_stopgate_payload(payload)
    gates = [gate for gate in _object_list(payload.get("stop_gates")) if gate.get("reason_code") in reason_codes]
    return {
        "case_id": _stopgate_case_id(payload),
        "decision": "보류" if gates else "가능",
        "risk_flags": _risk_flags(gates),
        "source_refs": _source_refs(gates),
        "stop_gates": gates,
        "all_case_decision": payload["decision"],
        "rule_refs": payload["rule_refs"],
    }


def _normalize_stopgate_payload(payload: JsonObject) -> JsonObject:
    gates = _object_list(payload.get("stop_gates"))
    normalized = dict(payload)
    normalized["case_id"] = _stopgate_case_id(payload)
    normalized["risk_flags"] = _risk_flags(gates)
    normalized["source_refs"] = _source_refs(gates)
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


def _ledger_summary(args: JsonObject, root: Path) -> JsonObject:
    entries = [
        entity for entity in _packet_entities(_case_graph(args, root))
        if entity.get("ontology_class") in {"operational-ledger", "ledger-entry", "recovery-transaction", "cost-entry"}
    ]
    return {"status": "summarized", "ledger_entries": entries, "entry_count": len(entries)}


def _recommend_next_action(args: JsonObject, root: Path) -> JsonObject:
    checks = evaluate_case_graph(_case_graph(args, root)).to_json()
    blocked = checks["decision"] != "가능"
    return {
        "decision": checks["decision"],
        "recommended_next_action": "hold_for_review" if blocked else "prepare_advisory_package_for_external_approval",
        "blocked_reasons": checks["blocked_reasons"],
        "required_preconditions": checks["required_preconditions"],
        "no_direct_filing_contact_or_collection": True,
    }


def _unknown_document_types(args: JsonObject, root: Path) -> JsonObject:
    governance = build_governance_payload(_manifest_path(args, root), root, _ontology_path(args, root)).to_json()
    return {
        "candidates": [item for item in _object_list(governance.get("candidates")) if "unknown" in str(item.get("reason", "")) or item.get("candidate_type") == "document_type"],
        "review_items": [item for item in _object_list(governance.get("review_items")) if item.get("queue_id") in {"unknown-document-type", "ontology-candidate"}],
        "reprocess_plans": governance["reprocess_plans"],
    }


def _review_fact(args: JsonObject) -> JsonObject:
    return {
        "status": "queued_for_review",
        "fact_id": _str_arg(args, "fact_id", ""),
        "decision": _str_arg(args, "decision", "needs_review"),
        "reviewer": _str_arg(args, "reviewer", "mcp-caller"),
        "reason": _str_arg(args, "reason", "manual_review_requested"),
        "production_graph_modified": False,
    }


def _promote_candidate(args: JsonObject, root: Path) -> JsonObject:
    candidate = _candidate(args)
    metadata = args.get("approval_metadata")
    result = attempt_promotion(candidate, metadata if isinstance(metadata, dict) else {}, _ontology_path(args, root))
    return result.to_json()


def _reprocess_case(args: JsonObject, root: Path) -> JsonObject:
    governance = build_governance_payload(_manifest_path(args, root), root, _ontology_path(args, root)).to_json()
    return {"status": "planned", "case_packet_id": _str_arg(args, "case_packet_id", ""), "plans": governance["reprocess_plans"], "production_job_started": False}


def _case_graph(args: JsonObject, root: Path) -> JsonObject:
    supplied = args.get("case_graph")
    if isinstance(supplied, dict):
        return supplied
    graph_path = _path_arg(args, "case_graph_path", root)
    if graph_path is not None:
        raw = json.loads(graph_path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    return build_case_graph(_manifest_path(args, root), root).to_json()


def _candidate(args: JsonObject) -> OntologyCandidate:
    return OntologyCandidate(
        candidate_id=_str_arg(args, "candidate_id", "candidate:mcp-review"),
        candidate_type=_str_arg(args, "candidate_type", "document_type"),
        proposed_id=_str_arg(args, "proposed_id", "mcp-reviewed-candidate"),
        proposed_label=_str_arg(args, "proposed_label", "MCP Reviewed Candidate"),
        reason=_str_arg(args, "reason", "mcp_promotion_review"),
        status="draft-review-required",
        source_refs=(_str_arg(args, "source_ref", "mcp:ontology-candidate"),),
        provenance={"source_ref": _str_arg(args, "source_ref", "mcp:ontology-candidate")},
        risk_flags=("no-auto-promotion",),
    )


def _manifest_path(args: JsonObject, root: Path) -> Path:
    return _path_arg(args, "manifest_path", root) or root / DEFAULT_MANIFEST


def _ontology_path(args: JsonObject, root: Path) -> Path:
    return _path_arg(args, "ontology_path", root) or root / DEFAULT_ONTOLOGY


def _packet_entities(graph: JsonObject) -> List[JsonObject]:
    return [entity for packet in _object_list(graph.get("case_packets")) for entity in _object_list(packet.get("entities"))]


def _object_list(value: JsonValue) -> List[JsonObject]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _path_arg(args: JsonObject, key: str, root: Path) -> Optional[Path]:
    value = args.get(key)
    if not isinstance(value, str) or not value:
        return None
    path = Path(value)
    candidate = path if path.is_absolute() else root / path
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        raise PermissionError("path_outside_repo_root")
    return resolved


def _repo_root(repo_root: Optional[Path]) -> Path:
    return (Path.cwd() if repo_root is None else repo_root).resolve()


def _str_arg(args: JsonObject, key: str, default: str) -> str:
    value = args.get(key)
    return value if isinstance(value, str) else default


def _int_arg(args: JsonObject, key: str) -> Optional[int]:
    value = args.get(key)
    return value if isinstance(value, int) else None


def _document_id(args: JsonObject, text: str) -> str:
    return _str_arg(args, "document_id", "mcp-doc-{}".format(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]))


def _hash_text(text: str) -> str:
    return "sha256:{}".format(hashlib.sha256(text.encode("utf-8")).hexdigest())


def _redact_json(value: JsonValue) -> JsonValue:
    if isinstance(value, str):
        return redact_text(value).text
    if isinstance(value, list):
        return [_redact_json(item) for item in value]
    if isinstance(value, dict):
        return {key: _redact_json(item) for key, item in value.items()}
    return value


def _pii_profile(value: JsonValue) -> JsonObject:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True)
    redaction = redact_text(encoded)
    return {"raw_text_included": False, "source_text_included": False, "redacted": redaction.counts}


def _source_refs(value: JsonValue) -> List[JsonValue]:
    refs: Dict[str, JsonValue] = {}
    _collect_source_refs(value, refs)
    return [refs[key] for key in sorted(refs)]


def _collect_source_refs(value: JsonValue, refs: Dict[str, JsonValue]) -> None:
    if isinstance(value, list):
        for item in value:
            _collect_source_refs(item, refs)
    if isinstance(value, dict):
        source_ref = value.get("source_ref")
        if isinstance(source_ref, str):
            safe_ref = redact_text(source_ref).text
            refs[safe_ref] = safe_ref
        nested = value.get("source_refs")
        if isinstance(nested, list):
            for item in nested:
                key = json.dumps(item, ensure_ascii=False, sort_keys=True)
                refs[key] = _redact_json(item)
        for item in value.values():
            _collect_source_refs(item, refs)


__all__ = ["SCHEMA_VERSION", "TOOL_DEFINITIONS", "invoke_tool", "list_tools"]
