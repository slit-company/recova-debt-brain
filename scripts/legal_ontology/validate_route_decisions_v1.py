#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "scripts.legal_ontology"

from .domain_sources_v1_common import (
    DomainSourceIssue,
    JsonObject,
    load_json,
    object_list_value,
    string_list_value,
    text_value,
    validate_known_ids,
    validate_unique_ids,
)
from .route_decision_validation_common import (
    APPROVED_SOURCE_STATUS,
    DependencyRoots,
    DecisionSummary,
    ValidationContext,
    build_context,
    issue,
    require_text_fields,
    validate_catalogs,
    validate_roots,
)

REQUIRED_DECISION_LIST_FIELDS: Final = (
    "workflow_preconditions",
    "required_fact_handles",
    "missing_fact_handles",
    "blocking_fact_handles",
    "legal_source_refs",
    "compliance_source_refs",
)


@dataclass(frozen=True, slots=True)
class KnownListCheck:
    field: str
    values: Sequence[str]
    route: JsonObject
    location: str


def validate_route_decision(entry: JsonObject, context: ValidationContext, index: int) -> list[DomainSourceIssue]:
    location = f"route_decisions.route_decisions[{index}]"
    issues = require_text_fields(entry, ("route_id", "next_step_action_packet_type"), location)
    route_id = text_value(entry, "route_id")
    route = context.route_by_id.get(route_id)
    if route is None:
        issues.append(issue(location, f"unknown route_id {route_id}"))
        route = {}
    if text_value(entry, "next_step_action_packet_type") not in context.action_packet_types:
        issues.append(issue(location, "unknown next_step_action_packet_type"))
    for field in REQUIRED_DECISION_LIST_FIELDS:
        values, value_issues = string_list_value(entry, field, location)
        issues.extend(value_issues)
        issues.extend(validate_known_list(KnownListCheck(field, values, route, location), context))
    issues.extend(validate_legal_reviews(entry, context, location))
    issues.extend(validate_stopgate_blockers(entry, context, location))
    issues.extend(validate_finance_preconditions(entry, context, location))
    issues.extend(validate_priority_score(entry, context, location))
    issues.extend(validate_reason_templates(entry, context, location))
    return issues


def validate_known_list(check: KnownListCheck, context: ValidationContext) -> list[DomainSourceIssue]:
    issues: list[DomainSourceIssue] = []
    known_by_field = {
        "workflow_preconditions": context.workflow_state_ids,
        "required_fact_handles": context.fact_handles,
        "missing_fact_handles": context.fact_handles,
        "blocking_fact_handles": context.fact_handles,
        "legal_source_refs": context.source_ids,
        "compliance_source_refs": context.source_ids,
    }
    label_by_field = {
        "workflow_preconditions": "workflow_state",
        "required_fact_handles": "fact_handle",
        "missing_fact_handles": "fact_handle",
        "blocking_fact_handles": "fact_handle",
        "legal_source_refs": "source_id",
        "compliance_source_refs": "source_id",
    }
    issues.extend(validate_known_ids(check.values, known_by_field[check.field], check.location, label_by_field[check.field]))
    route_values = check.route.get(check.field)
    if isinstance(route_values, list) and tuple(check.values) != tuple(item for item in route_values if isinstance(item, str)):
        issues.append(issue(check.location, f"{check.field} must match route catalog"))
    return issues


def validate_legal_reviews(entry: JsonObject, context: ValidationContext, location: str) -> list[DomainSourceIssue]:
    reviews, issues = object_list_value(entry, "legal_source_review_requirements", location)
    source_refs = set((*string_values(entry, "legal_source_refs"), *string_values(entry, "compliance_source_refs")))
    review_refs = {text_value(review, "source_id") for review in reviews if text_value(review, "source_id")}
    if review_refs != source_refs:
        issues.append(issue(location, "legal_source_review_requirements must cover all legal and compliance refs"))
    for index, review in enumerate(reviews):
        review_location = f"{location}.legal_source_review_requirements[{index}]"
        source_id = text_value(review, "source_id")
        accepted, accepted_issues = string_list_value(review, "accepted_review_statuses", review_location)
        issues.extend(accepted_issues)
        if source_id not in context.source_ids:
            issues.append(issue(review_location, f"unknown source_id {source_id}"))
        if APPROVED_SOURCE_STATUS not in accepted:
            issues.append(issue(review_location, f"accepted_review_statuses must include {APPROVED_SOURCE_STATUS}"))
        if text_value(review, "static_review_status") != context.source_review_by_id.get(source_id, ""):
            issues.append(issue(review_location, "static_review_status must match domain source review_status"))
    return issues


def validate_stopgate_blockers(entry: JsonObject, context: ValidationContext, location: str) -> list[DomainSourceIssue]:
    blockers, issues = object_list_value(entry, "stopgate_blockers", location)
    for index, blocker in enumerate(blockers):
        blocker_location = f"{location}.stopgate_blockers[{index}]"
        issues.extend(require_text_fields(blocker, ("blocker_fact_handle", "reason_code", "advisory_decision"), blocker_location))
        if text_value(blocker, "advisory_decision") != "보류":
            issues.append(issue(blocker_location, "advisory_decision must be 보류"))
        blocker_fact = text_value(blocker, "blocker_fact_handle")
        if blocker_fact not in string_values(entry, "blocking_fact_handles"):
            issues.append(issue(blocker_location, f"unknown blocker_fact_handle {blocker_fact}"))
        source_refs, source_issues = string_list_value(blocker, "source_refs", blocker_location)
        issues.extend(source_issues)
        issues.extend(validate_known_ids(source_refs, context.source_ids, blocker_location, "source_id"))
    return issues


def validate_finance_preconditions(entry: JsonObject, context: ValidationContext, location: str) -> list[DomainSourceIssue]:
    preconditions, issues = object_list_value(entry, "finance_preconditions", location)
    if not preconditions:
        issues.append(issue(location, "finance_preconditions must not be empty"))
    for index, precondition in enumerate(preconditions):
        precondition_location = f"{location}.finance_preconditions[{index}]"
        issues.extend(require_text_fields(precondition, ("precondition_id", "status_if_triggered"), precondition_location))
        if text_value(precondition, "status_if_triggered") != "review_required":
            issues.append(issue(precondition_location, "status_if_triggered must be review_required"))
        fact_handles, fact_issues = string_list_value(precondition, "required_fact_handles", precondition_location)
        trigger_codes, trigger_issues = string_list_value(precondition, "review_trigger_codes", precondition_location)
        component_refs, component_issues = string_list_value(precondition, "component_refs", precondition_location)
        source_refs, source_issues = string_list_value(precondition, "source_refs", precondition_location)
        issues.extend(fact_issues + trigger_issues + component_issues + source_issues)
        issues.extend(validate_known_ids(fact_handles, context.fact_handles, precondition_location, "fact_handle"))
        issues.extend(validate_known_ids(trigger_codes, context.finance_review_codes, precondition_location, "finance_review_code"))
        issues.extend(validate_known_ids(component_refs, context.finance_component_ids, precondition_location, "finance_component"))
        issues.extend(validate_known_ids(source_refs, context.source_ids, precondition_location, "source_id"))
    return issues


def validate_priority_score(entry: JsonObject, context: ValidationContext, location: str) -> list[DomainSourceIssue]:
    score = entry.get("priority_score")
    if not isinstance(score, dict):
        return [issue(location, "priority_score must be an object")]
    issues: list[DomainSourceIssue] = []
    base_points = number_value(score, "base_points")
    min_score = number_value(score, "min_score")
    max_score = number_value(score, "max_score")
    if min_score != 0 or max_score != 100 or base_points < 0 or base_points > max_score:
        issues.append(issue(location, "priority score range must be capped 0..100"))
    components, component_issues = object_list_value(score, "components", f"{location}.priority_score")
    issues.extend(component_issues)
    component_total = base_points
    for index, component in enumerate(components):
        component_location = f"{location}.priority_score.components[{index}]"
        component_id = text_value(component, "component_id")
        if component_id not in context.score_component_ids:
            issues.append(issue(component_location, f"unknown score component {component_id}"))
        component_total += number_value(component, "points")
        source_refs, source_issues = string_list_value(component, "source_refs", component_location)
        issues.extend(source_issues)
        issues.extend(validate_known_ids(source_refs, context.source_ids, component_location, "source_id"))
    if component_total > 100:
        issues.append(issue(location, "priority score components exceed cap 100"))
    return issues


def validate_reason_templates(entry: JsonObject, context: ValidationContext, location: str) -> list[DomainSourceIssue]:
    reasons, issues = object_list_value(entry, "reason_templates", location)
    reason_codes = [text_value(reason, "reason_code") for reason in reasons if text_value(reason, "reason_code")]
    issues.extend(validate_unique_ids(reason_codes, f"{location}.reason_templates"))
    for index, reason in enumerate(reasons):
        reason_location = f"{location}.reason_templates[{index}]"
        issues.extend(require_text_fields(reason, ("reason_code", "status_when_triggered", "message"), reason_location))
        source_refs, source_issues = string_list_value(reason, "source_refs", reason_location)
        issues.extend(source_issues)
        if not source_refs:
            issues.append(issue(reason_location, "source_refs must be a non-empty string list"))
        issues.extend(validate_known_ids(source_refs, context.source_ids, reason_location, "source_id"))
    return issues


def validate_route_decisions(decisions_root: JsonObject, roots: DependencyRoots) -> tuple[DecisionSummary, list[DomainSourceIssue]]:
    context, context_issues = build_context(roots)
    context, catalog_issues = validate_catalogs(decisions_root, context)
    decisions, decision_issues = object_list_value(decisions_root, "route_decisions", "route_decisions")
    route_ids = [text_value(decision, "route_id") for decision in decisions if text_value(decision, "route_id")]
    issues = validate_roots(decisions_root, roots)
    issues.extend(context_issues + catalog_issues + decision_issues)
    issues.extend(validate_unique_ids(route_ids, "route_decisions.route_decisions"))
    if set(route_ids) != context.route_ids:
        issues.append(issue("route_decisions.route_decisions", "must include exactly one decision per route"))
    for index, decision in enumerate(decisions):
        issues.extend(validate_route_decision(decision, context, index))
    reason_codes = {
        text_value(reason, "reason_code")
        for decision in decisions
        for reason in object_entries(decision, "reason_templates")
        if text_value(reason, "reason_code")
    }
    return DecisionSummary(text_value(decisions_root, "decision_table_version"), len(decisions), len(context.score_component_ids), len(reason_codes)), issues


def object_entries(entry: JsonObject, field: str) -> list[JsonObject]:
    value = entry.get(field)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def string_values(entry: JsonObject, field: str) -> tuple[str, ...]:
    value = entry.get(field)
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str))


def number_value(entry: JsonObject, field: str) -> int:
    value = entry.get(field)
    if isinstance(value, int):
        return value
    return 0


def main(argv: Sequence[str]) -> int:
    if len(argv) != 6:
        print(
            "usage: validate_route_decisions_v1.py <decisions.json> <routes.json> <sources.json> <workflow.json> <finance.json>",
            file=sys.stderr,
        )
        return 2
    try:
        summary, issues = validate_route_decisions(
            load_json(Path(argv[1])),
            DependencyRoots(
                routes_root=load_json(Path(argv[2])),
                sources_root=load_json(Path(argv[3])),
                workflow_root=load_json(Path(argv[4])),
                finance_root=load_json(Path(argv[5])),
            ),
        )
    except json.JSONDecodeError as error:
        print(f"ERROR invalid JSON: {error}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 1
    except TypeError as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 1
    if issues:
        for validation_issue in issues:
            print(f"ERROR {validation_issue.format()}", file=sys.stderr)
        return 1
    print(
        f"PASS route_decisions {summary.decision_table_version} "
        f"decisions={summary.decision_count} "
        f"score_components={summary.score_component_count} "
        f"reason_codes={summary.reason_code_count}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
