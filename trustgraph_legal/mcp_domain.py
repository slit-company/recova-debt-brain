from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Final, List, Optional, Tuple

from trustgraph_legal import mcp_handlers
from trustgraph_legal.governance_models import JsonValue
from trustgraph_legal.mcp_envelope import (
    SCHEMA_VERSION,
    EnvelopeRequest,
    build_envelope,
    redact_json,
    source_refs,
)
from trustgraph_legal.mcp_inputs import repo_root as resolve_repo_root

JsonObject = Dict[str, JsonValue]
ToolHandler = Callable[[JsonObject, Path], JsonObject]

TOOL_CONTRACT_SCHEMA_VERSION: Final = "trustgraph-legal-mcp-tool-contract/v1"
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
    "assemble_debtor_documents": ("debtor_graph", "debtor_graph:assembly"),
    "build_debtor_context_graph": ("debtor_graph", "debtor_graph:build"),
    "get_debtor_graph_snapshot": ("debtor_graph", "debtor_graph:read"),
    "list_debtor_route_candidates": ("debtor_graph", "debtor_graph:routes"),
    "explain_debtor_route_candidate": ("debtor_graph", "debtor_graph:routes"),
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
    _tool("list_debt_collection_tools", "List debt-collection domain tool contracts.", (), lambda args, root: {"tools": _tools_json()}),
    _tool("ingest_legal_document", "Prepare a legal document for reviewed ingestion without storing raw PII.", ("zip_path", "workspace", "collection", "limit"), mcp_handlers.ingest_legal_document),
    _tool("ingest_ocr_markdown", "Classify and extract OCR markdown into a review-safe queued envelope.", ("markdown_text", "document_id", "source_ref", "document_type"), lambda args, root: mcp_handlers.ingest_ocr_markdown(args)),
    _tool("get_ingest_status", "Return deterministic v0 ingest status metadata.", ("document_id", "processing_id"), lambda args, root: mcp_handlers.status_result(args)),
    _tool("classify_legal_document", "Classify a legal document with redacted evidence spans.", ("text", "document_id", "source_ref"), lambda args, root: mcp_handlers.classify_result(args)),
    _tool("extract_case_packet", "Extract a case-packet projection from text or the fixture manifest.", ("text", "manifest_path", "document_id", "document_type"), mcp_handlers.extract_case_packet),
    _tool("get_case_graph", "Return the deterministic redacted case graph.", ("manifest_path", "case_graph"), mcp_handlers.case_graph_result),
    _tool("check_case_stop_gates", "Evaluate deterministic legal StopGates for a case graph.", ("case_graph", "case_graph_path", "manifest_path"), lambda args, root: mcp_handlers.stopgate_result(args, root, None)),
    _tool("check_limitation_status", "Report limitation-risk StopGate status only.", ("case_graph", "case_graph_path", "manifest_path"), lambda args, root: mcp_handlers.stopgate_result(args, root, ("limitation_risk",))),
    _tool("check_attachment_target_rules", "Report attachment-target, exemption, and priority review blockers.", ("case_graph", "case_graph_path", "manifest_path"), lambda args, root: mcp_handlers.stopgate_result(args, root, ("exempt_claim_targeted", "unsupported_document_type_review"))),
    _tool("summarize_case_ledger", "Summarize redacted ledger facts from the case graph.", ("case_graph", "case_graph_path", "manifest_path"), mcp_handlers.ledger_summary),
    _tool("recommend_next_action", "Recommend a non-executing next advisory action from StopGate status.", ("case_graph", "case_graph_path", "manifest_path"), mcp_handlers.recommend_next_action),
    _tool("list_unknown_document_types", "List unknown-type and ontology-gap governance items.", ("manifest_path",), mcp_handlers.unknown_document_types),
    _tool("review_extracted_fact", "Queue or record a reviewed fact decision without mutating production ontology.", ("fact_id", "decision", "reviewer", "reason"), lambda args, root: mcp_handlers.review_fact(args)),
    _tool("promote_ontology_candidate", "Evaluate ontology promotion metadata and return accepted/rejected status only.", ("candidate_id", "approval_metadata", "ontology_path"), mcp_handlers.promote_candidate),
    _tool("reprocess_case", "Return a reviewed reprocess plan; no production job is executed by this tool.", ("case_packet_id", "manifest_path"), mcp_handlers.reprocess_case),
    _tool("assemble_debtor_documents", "Assemble OCR pages into a redacted debtor document assembly.", ("ocr_root", "summary_only"), mcp_handlers.assemble_debtor_documents),
    _tool("build_debtor_context_graph", "Build a redacted debtor context graph and advisory route candidates.", ("ocr_root", "assembly_path", "route_resources", "legal_sources"), mcp_handlers.build_debtor_context_graph),
    _tool("get_debtor_graph_snapshot", "Return snapshot replay and provenance metadata for a debtor context graph.", ("graph", "graph_path", "ocr_root", "assembly_path"), mcp_handlers.get_debtor_graph_snapshot),
    _tool("list_debtor_route_candidates", "List advisory route candidates for a debtor context graph.", ("graph", "graph_path", "ocr_root", "assembly_path"), mcp_handlers.list_debtor_route_candidates),
    _tool("explain_debtor_route_candidate", "Explain one advisory route candidate using existing route fields.", ("graph", "graph_path", "ocr_root", "assembly_path", "route_id"), mcp_handlers.explain_debtor_route_candidate),
)


def list_tools() -> List[JsonObject]:
    return [definition.to_json() for definition in TOOL_DEFINITIONS]


def _tools_json() -> List[JsonValue]:
    return [tool for tool in list_tools()]


def invoke_tool(
    tool_name: str,
    arguments: Optional[JsonObject] = None,
    repo_root: Optional[Path] = None,
) -> JsonObject:
    args = {} if arguments is None else arguments
    root = repo_root_path(repo_root)
    definition = _definition(tool_name)
    if definition is None:
        return build_envelope(
            EnvelopeRequest(
                tool_name=tool_name,
                group="read",
                scope="read:tools",
                result={"status": "unknown_tool"},
                warnings=["unknown_tool"],
                source_refs=[],
            )
        )
    try:
        result = redact_json(definition.handler(args, root))
    except PermissionError as exc:
        return build_envelope(
            EnvelopeRequest(
                tool_name=definition.tool_name,
                group=definition.group,
                scope=definition.scope,
                result={"status": "rejected", "reason": str(exc)},
                warnings=[str(exc)],
                source_refs=[],
            )
        )
    return build_envelope(
        EnvelopeRequest(
            tool_name=definition.tool_name,
            group=definition.group,
            scope=definition.scope,
            result=result,
            warnings=[],
            source_refs=source_refs(result),
        )
    )


def _definition(tool_name: str) -> Optional[ToolDefinition]:
    for definition in TOOL_DEFINITIONS:
        if definition.tool_name == tool_name:
            return definition
    return None


def repo_root_path(repo_root: Optional[Path]) -> Path:
    return resolve_repo_root(repo_root)


__all__ = ["SCHEMA_VERSION", "TOOL_DEFINITIONS", "invoke_tool", "list_tools"]
