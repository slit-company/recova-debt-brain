from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Final

from .domain_sources_v1_common import (
    DomainSourceIssue,
    JsonObject,
    bool_value,
    object_list_value,
    string_list_value,
    text_value,
    validate_known_ids,
    validate_unique_ids,
)

DECISION_SCHEMA_VERSION: Final = "trustgraph-route-decisions/v1"
DECISION_TABLE_VERSION: Final = "recova-debt-collection-route-decisions@v1.0.0"
ROUTES_SCHEMA_VERSION: Final = "trustgraph-legal-routes/v1"
DOMAIN_SOURCES_SCHEMA_VERSION: Final = "trustgraph-legal-domain-sources/v1"
WORKFLOW_SCHEMA_VERSION: Final = "trustgraph-legal-workflow/v1"
FINANCE_SCHEMA_VERSION: Final = "trustgraph-claim-finance-model/v1"
ADVISORY_EXECUTION_SEMANTICS: Final = "advisory_decision_support_only"
NON_EXECUTION_SEMANTICS: Final = "advisory_only_human_review_required"
APPROVED_SOURCE_STATUS: Final = "approved_static_v1"
REQUIRED_STATUSES: Final = frozenset({"possible", "review_required", "blocked", "missing_facts"})
REQUIRED_TIE_BREAKERS: Final = (
    "status_priority",
    "priority_score_desc",
    "legal_source_review_status",
    "workflow_state_order",
    "route_id_asc",
)
ALLOWED_PACKET_TYPES: Final = frozenset(
    {
        "evidence_request",
        "legal_action_review",
        "finance_review",
        "contact_review",
        "monitoring_retry",
        "insolvency_recovery_review",
    },
)
REQUIRED_ROOT_TEXT_FIELDS: Final = (
    "schema_version",
    "decision_table_version",
    "route_source_version",
    "domain_source_version",
    "workflow_version",
    "finance_model_version",
    "evaluation_date",
    "review_status",
    "execution_semantics",
    "non_execution_semantics",
)


@dataclass(frozen=True, slots=True)
class DecisionSummary:
    decision_table_version: str
    decision_count: int
    score_component_count: int
    reason_code_count: int


@dataclass(frozen=True, slots=True)
class ValidationContext:
    route_ids: set[str]
    source_ids: set[str]
    workflow_state_ids: set[str]
    finance_review_codes: set[str]
    finance_component_ids: set[str]
    fact_handles: set[str]
    route_by_id: dict[str, JsonObject]
    source_review_by_id: dict[str, str]
    action_packet_types: set[str]
    score_component_ids: set[str] = field(default_factory=set)


@dataclass(frozen=True, slots=True)
class DependencyRoots:
    routes_root: JsonObject
    sources_root: JsonObject
    workflow_root: JsonObject
    finance_root: JsonObject


def issue(location: str, message: str) -> DomainSourceIssue:
    return DomainSourceIssue(location=location, message=message)


def require_text_fields(entry: JsonObject, fields: Sequence[str], location: str) -> list[DomainSourceIssue]:
    return [issue(location, f"missing {field}") for field in fields if not text_value(entry, field)]


def build_context(roots: DependencyRoots) -> tuple[ValidationContext, list[DomainSourceIssue]]:
    issues: list[DomainSourceIssue] = []
    routes, route_issues = object_list_value(roots.routes_root, "routes", "routes")
    sources, source_issues = object_list_value(roots.sources_root, "sources", "domain_sources")
    states, state_issues = object_list_value(roots.workflow_root, "states", "workflow")
    triggers, trigger_issues = object_list_value(roots.finance_root, "review_triggers", "finance_model")
    components, component_issues = object_list_value(roots.finance_root, "component_types", "finance_model")
    issues.extend(route_issues + source_issues + state_issues + trigger_issues + component_issues)
    route_by_id = {text_value(route, "route_id"): route for route in routes if text_value(route, "route_id")}
    source_review_by_id = {
        text_value(source, "source_id"): text_value(source, "review_status")
        for source in sources
        if text_value(source, "source_id")
    }
    fact_handles, fact_issues = string_list_value(roots.routes_root, "fact_handle_catalog", "routes")
    issues.extend(fact_issues)
    return (
        ValidationContext(
            route_ids=set(route_by_id),
            source_ids=set(source_review_by_id),
            workflow_state_ids={text_value(state, "state_id") for state in states if text_value(state, "state_id")},
            finance_review_codes={text_value(trigger, "code") for trigger in triggers if text_value(trigger, "code")},
            finance_component_ids={
                text_value(component, "component_id")
                for component in components
                if text_value(component, "component_id")
            },
            fact_handles=set(fact_handles),
            route_by_id=route_by_id,
            source_review_by_id=source_review_by_id,
            action_packet_types=set(ALLOWED_PACKET_TYPES),
        ),
        issues,
    )


def validate_roots(decisions_root: JsonObject, roots: DependencyRoots) -> list[DomainSourceIssue]:
    issues = require_text_fields(decisions_root, REQUIRED_ROOT_TEXT_FIELDS, "route_decisions")
    expected = (
        ("schema_version", DECISION_SCHEMA_VERSION),
        ("decision_table_version", DECISION_TABLE_VERSION),
        ("route_source_version", text_value(roots.routes_root, "route_source_version")),
        ("domain_source_version", text_value(roots.sources_root, "rule_source_version")),
        ("workflow_version", text_value(roots.workflow_root, "workflow_version")),
        ("finance_model_version", text_value(roots.finance_root, "model_version")),
        ("execution_semantics", ADVISORY_EXECUTION_SEMANTICS),
        ("non_execution_semantics", NON_EXECUTION_SEMANTICS),
    )
    for field, expected_value in expected:
        if text_value(decisions_root, field) != expected_value:
            issues.append(issue(f"route_decisions.{field}", f"must be {expected_value}"))
    issues.extend(validate_dependency_headers(roots))
    if bool_value(decisions_root, "no_direct_execution") is not True:
        issues.append(issue("route_decisions", "no_direct_execution must be true"))
    if bool_value(decisions_root, "direct_execution_allowed") is not False:
        issues.append(issue("route_decisions", "direct_execution_allowed must be false"))
    return issues


def validate_dependency_headers(roots: DependencyRoots) -> list[DomainSourceIssue]:
    checks = (
        ("routes.schema_version", text_value(roots.routes_root, "schema_version"), ROUTES_SCHEMA_VERSION),
        ("domain_sources.schema_version", text_value(roots.sources_root, "schema_version"), DOMAIN_SOURCES_SCHEMA_VERSION),
        ("workflow.schema_version", text_value(roots.workflow_root, "schema_version"), WORKFLOW_SCHEMA_VERSION),
        ("finance_model.schema_version", text_value(roots.finance_root, "schema_version"), FINANCE_SCHEMA_VERSION),
    )
    return [issue(location, f"must be {expected}") for location, actual, expected in checks if actual != expected]


def validate_catalogs(root: JsonObject, context: ValidationContext) -> tuple[ValidationContext, list[DomainSourceIssue]]:
    issues: list[DomainSourceIssue] = []
    statuses, status_issues = object_list_value(root, "status_catalog", "route_decisions")
    components, component_issues = object_list_value(root, "score_component_catalog", "route_decisions")
    packet_types, packet_issues = string_list_value(root, "action_packet_type_catalog", "route_decisions")
    tie_breakers, tie_issues = string_list_value(root, "tie_breaker_order", "route_decisions")
    issues.extend(status_issues + component_issues + packet_issues + tie_issues)
    status_ids = {text_value(status, "status") for status in statuses if text_value(status, "status")}
    for required_status in sorted(REQUIRED_STATUSES.difference(status_ids)):
        issues.append(issue("route_decisions.status_catalog", f"missing status {required_status}"))
    if tuple(tie_breakers) != REQUIRED_TIE_BREAKERS:
        issues.append(issue("route_decisions.tie_breaker_order", "must match deterministic tie-breaker order"))
    if set(packet_types) != context.action_packet_types:
        issues.append(issue("route_decisions.action_packet_type_catalog", "must match allowed action packet types"))
    component_ids = [text_value(component, "component_id") for component in components if text_value(component, "component_id")]
    issues.extend(validate_unique_ids(component_ids, "route_decisions.score_component_catalog"))
    for index, component in enumerate(components):
        location = f"route_decisions.score_component_catalog[{index}]"
        source_refs, source_issues = string_list_value(component, "source_refs", location)
        issues.extend(source_issues)
        issues.extend(validate_known_ids(source_refs, context.source_ids, location, "source_id"))
    return (replace_score_components(context, set(component_ids)), issues)


def replace_score_components(context: ValidationContext, score_component_ids: set[str]) -> ValidationContext:
    return ValidationContext(
        route_ids=context.route_ids,
        source_ids=context.source_ids,
        workflow_state_ids=context.workflow_state_ids,
        finance_review_codes=context.finance_review_codes,
        finance_component_ids=context.finance_component_ids,
        fact_handles=context.fact_handles,
        route_by_id=context.route_by_id,
        source_review_by_id=context.source_review_by_id,
        action_packet_types=context.action_packet_types,
        score_component_ids=score_component_ids,
    )
