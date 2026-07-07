from __future__ import annotations

import json
import typing
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

from typing_extensions import TypeAlias, override

from trustgraph_legal.route_decisions import (
    RouteDecision,
    RouteDecisionRequest,
    RouteDecisionTable,
    SourceReviewStatus,
    evaluate_route_decision,
    load_decision_table,
)

if TYPE_CHECKING:
    JsonValue: TypeAlias = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]

    def _loads_json(_raw_text: str) -> JsonValue: ...
else:
    JsonValue: TypeAlias = typing.Union[None, bool, int, float, str, list["JsonValue"], dict[str, "JsonValue"]]

    def _loads_json(_raw_text: str) -> JsonValue:
        return json.loads(_raw_text)
JsonObject: TypeAlias = dict[str, JsonValue]
REPO_ROOT: Final = Path(__file__).resolve().parents[1]
DECISIONS_PATH: Final = REPO_ROOT / "resources" / "decision_tables" / "debt_collection_route_decisions_v1.json"
SOURCES_PATH: Final = REPO_ROOT / "resources" / "legal_rules" / "debt_collection_domain_sources_v1.json"
ACTION_PACKETS_PATH: Final = REPO_ROOT / "resources" / "action_packets" / "debt_collection_action_packets_v1.json"
WORKFLOW_PATH: Final = REPO_ROOT / "resources" / "workflows" / "debt_collection_workflow_v1.json"
FINANCE_PATH: Final = REPO_ROOT / "resources" / "finance" / "claim_finance_model_v1.json"
STOPGATE_PATH: Final = REPO_ROOT / "resources" / "legal_rules" / "debt_collection_stopgate_domain_v1.json"
NON_EXECUTION_SEMANTICS: Final = "advisory_only_human_review_required"


@dataclass(frozen=True)
class DomainDecisionError(Exception):
    location: str
    reason_code: str
    message: str

    @override
    def __str__(self) -> str:
        return "{}: {}".format(self.reason_code, self.message)


@dataclass(frozen=True)
class DomainDecisionRequest:
    claim_domain_payload: JsonObject
    workflow_state: str
    route_ids: tuple[str, ...] = ()
    finance_review_codes: tuple[str, ...] = ()
    expected_domain_source_version: str | None = None
    decisions_path: Path = DECISIONS_PATH
    sources_path: Path = SOURCES_PATH
    action_packets_path: Path = ACTION_PACKETS_PATH
    workflow_path: Path = WORKFLOW_PATH
    finance_path: Path = FINANCE_PATH
    stopgate_path: Path = STOPGATE_PATH


@dataclass(frozen=True)
class ResourceBundle:
    decision_table: RouteDecisionTable
    source_reviews: tuple[SourceReviewStatus, ...]
    action_packets_by_type: dict[str, JsonObject]
    versions: JsonObject


def evaluate_claim_domain_decision(request: DomainDecisionRequest) -> JsonObject:
    if text(request.claim_domain_payload.get("schema_version")) != "trustgraph-claim-domain-adapter/v1":
        raise DomainDecisionError("claim_domain_payload.schema_version", "invalid_adapter_payload", "claim-domain adapter payload v1 is required")
    resources = _load_resources(request)
    _require_workflow_state(request.workflow_state, request.workflow_path)
    claim_ref = _claim_ref(request.claim_domain_payload)
    route_ids = _route_ids(request)
    fact_handles = _fact_handles(request.claim_domain_payload)
    route_decision_items: list[RouteDecision] = []
    for index, route_id in enumerate(route_ids):
        if route_id not in resources.decision_table.decisions_by_route:
            raise DomainDecisionError("route_ids[{}]".format(index), "unknown_route_id", "route id is not in decision table v1")
        route_decision_items.append(
            evaluate_route_decision(
                resources.decision_table,
                RouteDecisionRequest(
                    route_id=route_id,
                    workflow_state=request.workflow_state,
                    fact_handles=fact_handles,
                    legal_source_reviews=resources.source_reviews,
                    finance_review_codes=request.finance_review_codes,
                ),
            )
        )
    route_decisions = tuple(route_decision_items)
    review_items = tuple(_review_items(route_decisions, request.finance_review_codes))
    action_candidates = tuple(_action_candidate(decision, resources, claim_ref) for decision in route_decisions)
    return {
        "schema_version": "trustgraph-claim-domain-decision/v1",
        "claim_ref": claim_ref,
        "workflow_state": request.workflow_state,
        "route_decisions": [decision.to_json() for decision in route_decisions],
        "review_items": list(review_items),
        "action_packet_candidates": list(action_candidates),
        "source_refs": list(_source_refs(request.claim_domain_payload, route_decisions, review_items, action_candidates)),
        "resource_versions": resources.versions,
        "pii_profile": {
            "raw_text_included": False,
            "source_text_included": False,
            "debtor_contact_payload_included": False,
            "filing_destination_included": False,
        },
        "non_execution_semantics": NON_EXECUTION_SEMANTICS,
    }


def _load_resources(request: DomainDecisionRequest) -> ResourceBundle:
    table = load_decision_table(request.decisions_path)
    sources = _load_json(request.sources_path)
    actions = _load_json(request.action_packets_path)
    finance = _load_json(request.finance_path)
    stopgate = _load_json(request.stopgate_path)
    source_version = text(sources.get("rule_source_version"))
    finance_version = text(finance.get("model_version"))
    _require_source_version(source_version, text(table.root.get("domain_source_version")), request.expected_domain_source_version)
    if finance_version != text(table.root.get("finance_model_version")):
        raise DomainDecisionError("resources/finance/claim_finance_model_v1.json", "stale_finance_model_version", "finance model version does not match the decision table")
    return ResourceBundle(
        table,
        tuple(
            SourceReviewStatus(
                source_id=text(source.get("source_id")),
                review_status=text(source.get("review_status")),
            )
            for source in json_objects(sources.get("sources"))
            if text(source.get("source_id"))
        ),
        {text(schema.get("packet_type")): schema for schema in json_objects(actions.get("packet_schemas")) if text(schema.get("packet_type"))},
        {
            "decision_table_version": text(table.root.get("decision_table_version")),
            "domain_source_version": source_version,
            "workflow_version": text(table.root.get("workflow_version")),
            "finance_model_version": finance_version,
            "action_packet_version": text(actions.get("action_packet_version")),
            "stopgate_rule_source_version": text(stopgate.get("rule_source_version")),
        },
    )


def _require_workflow_state(workflow_state: str, workflow_path: Path) -> None:
    workflow = _load_json(workflow_path)
    valid_states = {text(state.get("state_id")) for state in json_objects(workflow.get("states"))}
    if workflow_state not in valid_states:
        raise DomainDecisionError("workflow_state", "unknown_workflow_state", "workflow state is not in workflow v1")


def _require_source_version(actual: str, expected: str, requested: str | None) -> None:
    if actual != expected or (requested is not None and actual != requested):
        raise DomainDecisionError(
            "resources/legal_rules/debt_collection_domain_sources_v1.json",
            "stale_legal_source_version",
            "domain legal-source version does not match the decision table",
        )


def _review_items(route_decisions: tuple[RouteDecision, ...], finance_review_codes: tuple[str, ...]) -> tuple[JsonObject, ...]:
    items: list[JsonObject] = []
    for decision in route_decisions:
        items.extend(_missing_fact_items(decision))
        items.extend(_blocked_route_items(decision))
        items.extend(_legal_review_items(decision))
    refs = _unique(tuple(source_ref for decision in route_decisions for source_ref in decision.source_refs))
    items.extend(_review_item(code, "finance", "", (), refs) for code in finance_review_codes)
    return tuple(items)


def _missing_fact_items(decision: RouteDecision) -> tuple[JsonObject, ...]:
    return tuple(
        _review_item("missing_route_fact", "evidence", decision.route_id, (fact_handle,), decision.source_refs)
        for fact_handle in decision.missing_fact_handles
    )


def _blocked_route_items(decision: RouteDecision) -> tuple[JsonObject, ...]:
    return tuple(
        _review_item("route_blocked", "stopgate", decision.route_id, (fact_handle,), decision.source_refs)
        for fact_handle in decision.blocking_fact_handles
    )


def _legal_review_items(decision: RouteDecision) -> tuple[JsonObject, ...]:
    return tuple(
        _review_item(reason.reason_code, "legal_source", decision.route_id, (), reason.source_refs)
        for reason in decision.reasons
        if reason.reason_code == "domain_legal_source_unapproved"
    )


def _review_item(
    code: str,
    category: str,
    route_id: str,
    fact_handles: tuple[str, ...],
    source_refs: tuple[str, ...],
) -> JsonObject:
    return {
        "code": code,
        "category": category,
        "route_id": route_id,
        "fact_handles": list(fact_handles),
        "review_status": "human_review_required",
        "source_refs": list(source_refs),
    }


def _action_candidate(decision: RouteDecision, resources: ResourceBundle, claim_ref: str) -> JsonObject:
    schema = resources.action_packets_by_type.get(decision.next_step_action_packet_type, {})
    return {
        "schema_version": "trustgraph-action-packet-candidate/v1",
        "claim_ref": claim_ref,
        "route_id": decision.route_id,
        "route_status": decision.status,
        "packet_type": decision.next_step_action_packet_type,
        "review_status": text(schema.get("review_status")) or "human_review_required",
        "required_inputs": list(strings(schema.get("required_inputs"))),
        "source_refs": list(_unique((*decision.source_refs, *strings(schema.get("source_refs"))))),
        "direct_execution_allowed": False,
        "non_execution_semantics": NON_EXECUTION_SEMANTICS,
        "pii_profile": {
            "raw_text_included": False,
            "source_text_included": False,
            "debtor_contact_payload_included": False,
            "filing_destination_included": False,
        },
    }


def _claim_ref(payload: JsonObject) -> str:
    claim_root = json_object(payload.get("claim_root"))
    claim_ref = text(claim_root.get("claim_ref")) or text(claim_root.get("claim_id"))
    if not claim_ref:
        raise DomainDecisionError("claim_root.claim_ref", "missing_claim_ref", "claim_ref or claim_id is required")
    return claim_ref


def _route_ids(request: DomainDecisionRequest) -> tuple[str, ...]:
    if request.route_ids:
        return request.route_ids
    route_ids = tuple(
        text(route.get("domain_route_id")) or text(route.get("route_id"))
        for route in json_objects(request.claim_domain_payload.get("route_candidates"))
    )
    return _unique(tuple(route_id for route_id in route_ids if route_id))


def _fact_handles(payload: JsonObject) -> tuple[str, ...]:
    return _unique(tuple(text(fact.get("fact_handle")) for fact in json_objects(payload.get("fact_handles")) if text(fact.get("fact_handle"))))


def _source_refs(
    payload: JsonObject,
    decisions: tuple[RouteDecision, ...],
    review_items: tuple[JsonObject, ...],
    action_candidates: tuple[JsonObject, ...],
) -> tuple[str, ...]:
    values: list[str] = []
    values.extend(strings(payload.get("source_refs")))
    values.extend(source_ref for fact in json_objects(payload.get("fact_handles")) for source_ref in strings(fact.get("source_refs")))
    values.extend(source_ref for decision in decisions for source_ref in decision.source_refs)
    values.extend(source_ref for item in review_items for source_ref in strings(item.get("source_refs")))
    values.extend(source_ref for candidate in action_candidates for source_ref in strings(candidate.get("source_refs")))
    return _unique(tuple(values))


def _load_json(path: Path) -> JsonObject:
    raw = _loads_json(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise DomainDecisionError(path.name, "invalid_json_resource", "resource root must be an object")
    return raw


def json_object(value: JsonValue) -> JsonObject:
    return value if isinstance(value, dict) else {}


def json_objects(value: JsonValue) -> tuple[JsonObject, ...]:
    return tuple(item for item in value if isinstance(item, dict)) if isinstance(value, list) else ()


def strings(value: JsonValue) -> tuple[str, ...]:
    return tuple(item for item in value if isinstance(item, str) and item) if isinstance(value, list) else ()


def text(value: JsonValue) -> str:
    return value if isinstance(value, str) else ""


def _unique(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))
