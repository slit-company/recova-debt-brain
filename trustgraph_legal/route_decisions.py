from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Union

from typing_extensions import TypeAlias


JsonScalar: TypeAlias = Union[None, bool, int, float, str]
JsonValue: TypeAlias = Union[JsonScalar, list["JsonValue"], dict[str, "JsonValue"]]
JsonObject: TypeAlias = dict[str, JsonValue]

DECISION_SCHEMA_VERSION: Final = "trustgraph-route-decisions/v1"
DECISION_TABLE_VERSION: Final = "recova-debt-collection-route-decisions@v1.0.0"
POSSIBLE: Final = "possible"
REVIEW_REQUIRED: Final = "review_required"
BLOCKED: Final = "blocked"
MISSING_FACTS: Final = "missing_facts"
APPROVED_SOURCE_STATUS: Final = "approved_static_v1"
NON_EXECUTION_SEMANTICS: Final = "advisory_only_human_review_required"


@dataclass(frozen=True)
class RouteDecisionTableError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True)
class SourceReviewStatus:
    source_id: str
    review_status: str


@dataclass(frozen=True)
class RouteDecisionRequest:
    route_id: str
    workflow_state: str
    fact_handles: tuple[str, ...]
    legal_source_reviews: tuple[SourceReviewStatus, ...] = ()
    finance_review_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class DecisionReason:
    reason_code: str
    message: str
    source_refs: tuple[str, ...]

    def to_json(self) -> JsonObject:
        return {
            "reason_code": self.reason_code,
            "message": self.message,
            "source_refs": list(self.source_refs),
        }


@dataclass(frozen=True)
class RouteDecision:
    route_id: str
    status: str
    priority_score: int
    missing_fact_handles: tuple[str, ...]
    blocking_fact_handles: tuple[str, ...]
    reasons: tuple[DecisionReason, ...]
    source_refs: tuple[str, ...]
    next_step_action_packet_type: str

    def to_json(self) -> JsonObject:
        return {
            "schema_version": "trustgraph-route-decision-result/v1",
            "route_id": self.route_id,
            "status": self.status,
            "priority_score": self.priority_score,
            "missing_fact_handles": list(self.missing_fact_handles),
            "blocking_fact_handles": list(self.blocking_fact_handles),
            "reasons": [reason.to_json() for reason in self.reasons],
            "source_refs": list(self.source_refs),
            "next_step_action_packet_type": self.next_step_action_packet_type,
            "non_execution_semantics": NON_EXECUTION_SEMANTICS,
            "pii_profile": {"raw_text_included": False, "source_text_included": False},
        }


@dataclass(frozen=True)
class RouteDecisionTable:
    root: JsonObject
    decisions_by_route: dict[str, JsonObject]

    def decision_for(self, route_id: str) -> JsonObject:
        decision = self.decisions_by_route.get(route_id)
        if decision is None:
            raise RouteDecisionTableError(f"unknown route_id {route_id}")
        return decision


@dataclass(frozen=True)
class EvaluationContext:
    entry: JsonObject
    request: RouteDecisionRequest
    present_facts: frozenset[str]
    missing_facts: tuple[str, ...]
    blocking_facts: tuple[str, ...]
    legal_review_required: bool
    finance_review_required: bool
    workflow_met: bool


def load_decision_table(path: Path) -> RouteDecisionTable:
    with path.open(encoding="utf-8") as handle:
        raw: JsonValue = json.load(handle)
    if not isinstance(raw, dict):
        raise RouteDecisionTableError("decision table root must be an object")
    if text_value(raw, "schema_version") != DECISION_SCHEMA_VERSION:
        raise RouteDecisionTableError(f"schema_version must be {DECISION_SCHEMA_VERSION}")
    decisions = object_list(raw, "route_decisions")
    decisions_by_route = {text_value(entry, "route_id"): entry for entry in decisions if text_value(entry, "route_id")}
    return RouteDecisionTable(root=raw, decisions_by_route=decisions_by_route)


def evaluate_route_decision(table: RouteDecisionTable, request: RouteDecisionRequest) -> RouteDecision:
    entry = table.decision_for(request.route_id)
    present_facts = frozenset(request.fact_handles)
    required_facts = string_list(entry, "required_fact_handles")
    blocking_facts = tuple(fact for fact in string_list(entry, "blocking_fact_handles") if fact in present_facts)
    missing_facts = tuple(fact for fact in required_facts if fact not in present_facts)
    workflow_met = request.workflow_state in string_list(entry, "workflow_preconditions")
    context = EvaluationContext(
        entry=entry,
        request=request,
        present_facts=present_facts,
        missing_facts=missing_facts,
        blocking_facts=blocking_facts,
        legal_review_required=needs_legal_review(entry, request),
        finance_review_required=bool(request.finance_review_codes),
        workflow_met=workflow_met,
    )
    status = decision_status(context)
    reasons = tuple(build_reasons(context, status))
    return RouteDecision(
        route_id=request.route_id,
        status=status,
        priority_score=priority_score(context, status),
        missing_fact_handles=missing_facts,
        blocking_fact_handles=blocking_facts,
        reasons=reasons,
        source_refs=unique_strings((*string_list(entry, "legal_source_refs"), *string_list(entry, "compliance_source_refs"), *reason_refs(reasons))),
        next_step_action_packet_type=text_value(entry, "next_step_action_packet_type"),
    )


def decision_status(context: EvaluationContext) -> str:
    if context.blocking_facts:
        return BLOCKED
    if context.missing_facts or not context.workflow_met:
        return MISSING_FACTS
    if context.legal_review_required or context.finance_review_required:
        return REVIEW_REQUIRED
    return POSSIBLE


def needs_legal_review(entry: JsonObject, request: RouteDecisionRequest) -> bool:
    review_by_source = {review.source_id: review.review_status for review in request.legal_source_reviews}
    for requirement in object_list(entry, "legal_source_review_requirements"):
        source_id = text_value(requirement, "source_id")
        accepted = set(string_list(requirement, "accepted_review_statuses"))
        fallback_status = text_value(requirement, "static_review_status")
        review_status = review_by_source.get(source_id, fallback_status)
        if review_status not in accepted:
            return True
    return False


def build_reasons(context: EvaluationContext, status: str) -> list[DecisionReason]:
    templates = {text_value(template, "reason_code"): template for template in object_list(context.entry, "reason_templates")}
    codes = reason_codes_for(context, status)
    return [reason_from_template(templates[code]) for code in codes if code in templates]


def reason_codes_for(context: EvaluationContext, status: str) -> tuple[str, ...]:
    if status == BLOCKED:
        return blocker_reason_codes(context)
    if status == MISSING_FACTS and context.missing_facts:
        return ("required_fact_missing",)
    if status == MISSING_FACTS:
        return ("workflow_precondition_missing",)
    if context.legal_review_required:
        return ("domain_legal_source_unapproved",)
    if context.finance_review_required:
        return ("ambiguous_or_excessive_balance",)
    return ("required_facts_present",)


def blocker_reason_codes(context: EvaluationContext) -> tuple[str, ...]:
    blocker_reasons: list[str] = []
    for blocker in object_list(context.entry, "stopgate_blockers"):
        if text_value(blocker, "blocker_fact_handle") in context.blocking_facts:
            blocker_reasons.append(text_value(blocker, "reason_code"))
    return tuple(code for code in blocker_reasons if code)


def reason_from_template(template: JsonObject) -> DecisionReason:
    return DecisionReason(
        reason_code=text_value(template, "reason_code"),
        message=text_value(template, "message"),
        source_refs=tuple(string_list(template, "source_refs")),
    )


Trigger = Callable[[EvaluationContext], bool]


def priority_score(context: EvaluationContext, status: str) -> int:
    if status == BLOCKED:
        return 0
    score_spec = object_value(context.entry, "priority_score")
    base_points = int_value(score_spec, "base_points")
    trigger_handlers = trigger_handler_map()
    score = base_points
    for component in object_list(score_spec, "components"):
        trigger = text_value(component, "trigger")
        handler = trigger_handlers.get(trigger)
        if handler is not None and handler(context):
            score += int_value(component, "points")
    max_score = min(100, int_value(score_spec, "max_score"))
    return max(0, min(score, max_score))


def trigger_handler_map() -> dict[str, Trigger]:
    return {
        "required_facts_present": lambda context: not context.missing_facts,
        "workflow_precondition_met": lambda context: context.workflow_met,
        "no_stopgate_blockers": lambda context: not context.blocking_facts,
        "legal_sources_approved": lambda context: not context.legal_review_required,
        "finance_review_clear": lambda context: not context.finance_review_required,
        "asset_signal_present": has_asset_signal,
    }


def has_asset_signal(context: EvaluationContext) -> bool:
    asset_handles = tuple(handle for handle in string_list(context.entry, "required_fact_handles") if handle.endswith("_hint") or handle.endswith("_asset"))
    return bool(asset_handles) and any(handle in context.present_facts for handle in asset_handles)


def text_value(entry: JsonObject, field: str) -> str:
    value = entry.get(field)
    if isinstance(value, str):
        return value
    return ""


def int_value(entry: JsonObject, field: str) -> int:
    value = entry.get(field)
    if isinstance(value, int):
        return value
    return 0


def object_value(entry: JsonObject, field: str) -> JsonObject:
    value = entry.get(field)
    if isinstance(value, dict):
        return value
    return {}


def object_list(entry: JsonObject, field: str) -> list[JsonObject]:
    value = entry.get(field)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def string_list(entry: JsonObject, field: str) -> tuple[str, ...]:
    value = entry.get(field)
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item)


def reason_refs(reasons: tuple[DecisionReason, ...]) -> tuple[str, ...]:
    return tuple(source_ref for reason in reasons for source_ref in reason.source_refs)


def unique_strings(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))
