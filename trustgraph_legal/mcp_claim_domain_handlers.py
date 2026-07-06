from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from trustgraph_legal.domain_decisions import (
    DomainDecisionError,
    DomainDecisionRequest,
    evaluate_claim_domain_decision as run_domain_decision,
)
from trustgraph_legal.governance_models import JsonValue
from trustgraph_legal.mcp_inputs import path_arg, str_arg

JsonObject = dict[str, JsonValue]
ROUTES_PATH: Final = Path("resources/legal_routes/debt_collection_routes_v1.json")
WORKFLOW_PATH: Final = Path("resources/workflows/debt_collection_workflow_v1.json")
DECISIONS_PATH: Final = Path("resources/decision_tables/debt_collection_route_decisions_v1.json")
SOURCES_PATH: Final = Path("resources/legal_rules/debt_collection_domain_sources_v1.json")
ACTION_PACKETS_PATH: Final = Path("resources/action_packets/debt_collection_action_packets_v1.json")
FINANCE_PATH: Final = Path("resources/finance/claim_finance_model_v1.json")
STOPGATE_PATH: Final = Path("resources/legal_rules/debt_collection_stopgate_domain_v1.json")
NON_EXECUTION_SEMANTICS: Final = "advisory_only_human_review_required"


def list_claim_domain_routes(args: JsonObject, root: Path) -> JsonObject:
    routes = _load_json(_resource_path(args, root, "routes_path", ROUTES_PATH))
    family = str_arg(args, "family", "")
    route_summaries: list[JsonObject] = [
        _route_summary(route)
        for route in _object_list(routes.get("routes"))
        if not family or _text(route.get("family")) == family
    ]
    return {
        "schema_version": "trustgraph-claim-domain-routes-mcp/v1",
        "route_resource_version": _text(routes.get("route_catalog_version")) or _text(routes.get("schema_version")),
        "route_count": len(route_summaries),
        "routes": _json_object_values(route_summaries),
        "source_refs": _json_strings(_unique(
            tuple(source_ref for route in route_summaries for source_ref in _strings(route.get("source_refs")))
        )),
        "non_execution_semantics": NON_EXECUTION_SEMANTICS,
    }


def explain_collection_workflow_state(args: JsonObject, root: Path) -> JsonObject:
    workflow = _load_json(_resource_path(args, root, "workflow_path", WORKFLOW_PATH))
    requested_state_id = str_arg(args, "state_id", "intake")
    states = _object_list(workflow.get("states"))
    for state in states:
        if _text(state.get("state_id")) == requested_state_id:
            return {
                "schema_version": "trustgraph-claim-domain-workflow-state-mcp/v1",
                "workflow_version": _text(workflow.get("workflow_version")),
                "state_id": requested_state_id,
                "label": _text(state.get("label")),
                "category": _text(state.get("category")),
                "purpose": _text(state.get("purpose")),
                "preconditions": _json_strings(_strings(state.get("preconditions"))),
                "exit_conditions": _json_strings(_strings(state.get("exit_conditions"))),
                "required_evidence": _json_strings(_strings(state.get("required_evidence"))),
                "review_states": _json_strings(_strings(state.get("review_states"))),
                "route_link_semantics": _text(state.get("route_link_semantics")),
                "source_refs": _json_strings(_strings(state.get("source_refs"))),
                "state_non_execution_semantics": _text(state.get("non_execution_semantics")),
                "non_execution_semantics": NON_EXECUTION_SEMANTICS,
            }
    return {
        "schema_version": "trustgraph-claim-domain-workflow-state-mcp/v1",
        "status": "not_found",
        "state_id": requested_state_id,
        "available_state_ids": _json_strings(
            tuple(_text(state.get("state_id")) for state in states if _text(state.get("state_id")))
        ),
        "source_refs": [],
        "non_execution_semantics": NON_EXECUTION_SEMANTICS,
    }


def evaluate_claim_domain_decision(args: JsonObject, root: Path) -> JsonObject:
    payload = _claim_domain_payload(args, root)
    try:
        return run_domain_decision(
            DomainDecisionRequest(
                claim_domain_payload=payload,
                workflow_state=str_arg(args, "workflow_state", "execution_route_selection"),
                route_ids=tuple(_strings(args.get("route_ids"))),
                finance_review_codes=tuple(_strings(args.get("finance_review_codes"))),
                expected_domain_source_version=_optional_text(args.get("expected_domain_source_version")),
                decisions_path=_resource_path(args, root, "decisions_path", DECISIONS_PATH),
                sources_path=_resource_path(args, root, "sources_path", SOURCES_PATH),
                action_packets_path=_resource_path(args, root, "action_packets_path", ACTION_PACKETS_PATH),
                workflow_path=_resource_path(args, root, "workflow_path", WORKFLOW_PATH),
                finance_path=_resource_path(args, root, "finance_path", FINANCE_PATH),
                stopgate_path=_resource_path(args, root, "stopgate_path", STOPGATE_PATH),
            )
        )
    except DomainDecisionError as exc:
        return {
            "schema_version": "trustgraph-claim-domain-decision-mcp/v1",
            "status": "rejected",
            "reason_code": exc.reason_code,
            "location": exc.location,
            "reason": str(exc),
            "source_refs": [],
            "non_execution_semantics": NON_EXECUTION_SEMANTICS,
        }


def explain_claim_action_packet(args: JsonObject, root: Path) -> JsonObject:
    packets = _load_json(_resource_path(args, root, "action_packets_path", ACTION_PACKETS_PATH))
    packet_type = str_arg(args, "packet_type", "legal_action_review")
    for schema in _object_list(packets.get("packet_schemas")):
        if _text(schema.get("packet_type")) == packet_type:
            return {
                "schema_version": "trustgraph-claim-action-packet-explanation-mcp/v1",
                "action_packet_version": _text(packets.get("action_packet_version")),
                "packet_type": packet_type,
                "label": _text(schema.get("label")),
                "purpose": _text(schema.get("purpose")),
                "review_status": _text(schema.get("review_status")),
                "no_direct_execution": _bool_value(schema.get("no_direct_execution"), True),
                "direct_execution_allowed": False,
                "required_inputs": _json_strings(_strings(schema.get("required_inputs"))),
                "permitted_next_states": _json_strings(_strings(schema.get("permitted_next_states"))),
                "source_refs": _json_strings(_strings(schema.get("source_refs"))),
                "route_decision_linkage": _linkage_summary(schema.get("route_decision_linkage")),
                "forbidden_field_count": len(_strings(schema.get("forbidden_fields"))),
                "pii_profile": _pii_profile(schema.get("pii_profile")),
                "non_execution_semantics": NON_EXECUTION_SEMANTICS,
            }
    return {
        "schema_version": "trustgraph-claim-action-packet-explanation-mcp/v1",
        "status": "not_found",
        "packet_type": packet_type,
        "available_packet_types": _json_strings(
            tuple(
                _text(schema.get("packet_type"))
                for schema in _object_list(packets.get("packet_schemas"))
                if _text(schema.get("packet_type"))
            )
        ),
        "source_refs": [],
        "non_execution_semantics": NON_EXECUTION_SEMANTICS,
    }


def _claim_domain_payload(args: JsonObject, root: Path) -> JsonObject:
    supplied = args.get("claim_domain_payload")
    if isinstance(supplied, dict):
        return supplied
    payload_path = path_arg(args, "claim_domain_payload_path", root)
    if payload_path is not None:
        return _load_json(payload_path)
    return {}


def _resource_path(args: JsonObject, root: Path, key: str, default_path: Path) -> Path:
    return path_arg(args, key, root) or root / default_path


def _route_summary(route: JsonObject) -> JsonObject:
    source_refs = _unique((*_strings(route.get("legal_source_refs")), *_strings(route.get("compliance_source_refs"))))
    return {
        "route_id": _text(route.get("route_id")),
        "family": _text(route.get("family")),
        "review_status": _text(route.get("review_status")),
        "workflow_state_refs": _json_strings(_strings(route.get("workflow_state_refs"))),
        "required_fact_handles": _json_strings(_strings(route.get("required_fact_handles"))),
        "missing_fact_handles": _json_strings(_strings(route.get("missing_fact_handles"))),
        "blocking_fact_handles": _json_strings(_strings(route.get("blocking_fact_handles"))),
        "source_refs": _json_strings(source_refs),
        "no_direct_execution": _bool_value(route.get("no_direct_execution"), True),
        "direct_execution_allowed": False,
        "execution_semantics": _text(route.get("execution_semantics")),
        "non_execution_semantics": NON_EXECUTION_SEMANTICS,
    }


def _linkage_summary(value: JsonValue) -> JsonObject:
    linkage = value if isinstance(value, dict) else {}
    route_ids = _strings(linkage.get("route_ids"))
    return {
        "decision_table_version": _text(linkage.get("decision_table_version")),
        "route_decision_packet_type": _text(linkage.get("route_decision_packet_type")),
        "route_count": len(route_ids),
    }


def _pii_profile(value: JsonValue) -> JsonObject:
    profile = value if isinstance(value, dict) else {}
    return {
        "raw_text_included": _bool_value(profile.get("raw_text_included"), False),
        "source_text_included": _bool_value(profile.get("source_text_included"), False),
        "contact_payload_included": False,
        "court_destination_included": False,
        "redaction_required": _bool_value(profile.get("redaction_required"), True),
    }


def _load_json(path: Path) -> JsonObject:
    raw: JsonValue = json.loads(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def _object_list(value: JsonValue) -> list[JsonObject]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _strings(value: JsonValue) -> tuple[str, ...]:
    return tuple(item for item in value if isinstance(item, str) and item) if isinstance(value, list) else ()


def _json_strings(values: tuple[str, ...]) -> list[JsonValue]:
    return [value for value in values]


def _json_object_values(values: list[JsonObject]) -> list[JsonValue]:
    return [value for value in values]


def _text(value: JsonValue) -> str:
    return value if isinstance(value, str) else ""


def _optional_text(value: JsonValue) -> str | None:
    text = _text(value)
    return text if text else None


def _bool_value(value: JsonValue, default: bool) -> bool:
    return value if isinstance(value, bool) else default


def _unique(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))
