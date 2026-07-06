from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .action_packet_contract_v1 import (
    ACTION_PACKET_SCHEMA_VERSION,
    ACTION_PACKET_VERSION,
    DECISION_TABLE_VERSION,
    EXECUTION_SEMANTICS,
    FORBIDDEN_FIELDS,
    GENERIC_INPUTS,
    NON_EXECUTION_SEMANTICS,
    PII_FALSE_FIELDS,
    REQUIRED_PACKET_LIST_FIELDS,
    REQUIRED_PACKET_TEXT_FIELDS,
    REQUIRED_PACKET_TYPES,
    REQUIRED_ROOT_TEXT_FIELDS,
    REVIEW_STATUS,
)
from .domain_sources_v1_common import (
    DomainSourceIssue,
    JsonObject,
    JsonValue,
    bool_value,
    object_list_value,
    string_list_value,
    text_value,
    validate_known_ids,
    validate_unique_ids,
)


@dataclass(frozen=True, slots=True)
class ActionPacketSummary:
    action_packet_version: str
    packet_type_count: int
    required_input_count: int
    source_ref_count: int


@dataclass(frozen=True, slots=True)
class ValidationContext:
    decision_packet_types: set[str]
    decision_routes_by_packet_type: dict[str, set[str]]
    source_ids: set[str]
    workflow_review_states: set[str]
    known_inputs: set[str]


@dataclass(frozen=True, slots=True)
class DependencyRoots:
    decisions_root: JsonObject
    routes_root: JsonObject
    sources_root: JsonObject
    workflow_root: JsonObject
    finance_root: JsonObject


def issue(location: str, message: str) -> DomainSourceIssue:
    return DomainSourceIssue(location=location, message=message)


def require_text_fields(entry: JsonObject, fields: Sequence[str], location: str) -> list[DomainSourceIssue]:
    return [issue(location, f"missing {field}") for field in fields if not text_value(entry, field)]


def object_value(entry: JsonObject, field: str, location: str) -> tuple[JsonObject, list[DomainSourceIssue]]:
    value = entry.get(field)
    if isinstance(value, dict):
        return value, []
    return {}, [issue(location, f"{field} must be an object")]


def build_context(roots: DependencyRoots) -> tuple[ValidationContext, list[DomainSourceIssue]]:
    issues: list[DomainSourceIssue] = []
    packet_types, packet_type_issues = string_list_value(roots.decisions_root, "action_packet_type_catalog", "route_decisions")
    decisions, decision_issues = object_list_value(roots.decisions_root, "route_decisions", "route_decisions")
    sources, source_issues = object_list_value(roots.sources_root, "sources", "domain_sources")
    review_states, review_state_issues = object_list_value(roots.workflow_root, "review_state_catalog", "workflow")
    fact_handles, fact_issues = string_list_value(roots.routes_root, "fact_handle_catalog", "routes")
    finance_triggers, trigger_issues = object_list_value(roots.finance_root, "review_triggers", "finance_model")
    finance_components, component_issues = object_list_value(roots.finance_root, "component_types", "finance_model")
    issues.extend(
        packet_type_issues
        + decision_issues
        + source_issues
        + review_state_issues
        + fact_issues
        + trigger_issues
        + component_issues
    )
    routes_by_type: dict[str, set[str]] = {packet_type: set() for packet_type in packet_types}
    for decision in decisions:
        packet_type = text_value(decision, "next_step_action_packet_type")
        route_id = text_value(decision, "route_id")
        if packet_type and route_id:
            routes_by_type.setdefault(packet_type, set()).add(route_id)
    finance_inputs = {text_value(trigger, "code") for trigger in finance_triggers if text_value(trigger, "code")}
    finance_inputs.update(
        text_value(component, "component_id") for component in finance_components if text_value(component, "component_id")
    )
    return (
        ValidationContext(
            decision_packet_types=set(packet_types),
            decision_routes_by_packet_type=routes_by_type,
            source_ids={text_value(source, "source_id") for source in sources if text_value(source, "source_id")},
            workflow_review_states={
                text_value(state, "review_state") for state in review_states if text_value(state, "review_state")
            },
            known_inputs=set(fact_handles) | finance_inputs | set(GENERIC_INPUTS),
        ),
        issues,
    )


def validate_action_packets(root: JsonObject, roots: DependencyRoots) -> tuple[ActionPacketSummary, list[DomainSourceIssue]]:
    context, context_issues = build_context(roots)
    packets, packet_issues = object_list_value(root, "packet_schemas", "action_packets")
    packet_types = [text_value(packet, "packet_type") for packet in packets if text_value(packet, "packet_type")]
    issues = validate_root(root, roots, context)
    issues.extend(context_issues + packet_issues)
    issues.extend(validate_unique_ids(packet_types, "action_packets.packet_schemas"))
    if set(packet_types) != set(REQUIRED_PACKET_TYPES):
        issues.append(issue("action_packets.packet_schemas", "must include exactly the required packet types"))
    required_inputs = 0
    source_refs = 0
    for index, packet in enumerate(packets):
        packet_required_inputs, packet_source_refs, packet_validation = validate_packet_schema(packet, context, index)
        required_inputs += packet_required_inputs
        source_refs += packet_source_refs
        issues.extend(packet_validation)
    return (
        ActionPacketSummary(text_value(root, "action_packet_version"), len(packet_types), required_inputs, source_refs),
        issues,
    )


def validate_root(root: JsonObject, roots: DependencyRoots, context: ValidationContext) -> list[DomainSourceIssue]:
    issues = require_text_fields(root, REQUIRED_ROOT_TEXT_FIELDS, "action_packets")
    expected = (
        ("schema_version", ACTION_PACKET_SCHEMA_VERSION),
        ("action_packet_version", ACTION_PACKET_VERSION),
        ("decision_table_version", text_value(roots.decisions_root, "decision_table_version")),
        ("route_source_version", text_value(roots.routes_root, "route_source_version")),
        ("domain_source_version", text_value(roots.sources_root, "rule_source_version")),
        ("workflow_version", text_value(roots.workflow_root, "workflow_version")),
        ("finance_model_version", text_value(roots.finance_root, "model_version")),
        ("execution_semantics", EXECUTION_SEMANTICS),
        ("non_execution_semantics", NON_EXECUTION_SEMANTICS),
    )
    for field, expected_value in expected:
        if text_value(root, field) != expected_value:
            issues.append(issue(f"action_packets.{field}", f"must be {expected_value}"))
    if text_value(roots.decisions_root, "decision_table_version") != DECISION_TABLE_VERSION:
        issues.append(issue("route_decisions.decision_table_version", f"must be {DECISION_TABLE_VERSION}"))
    if bool_value(root, "no_direct_execution") is not True:
        issues.append(issue("action_packets", "no_direct_execution must be true"))
    if bool_value(root, "direct_execution_allowed") is not False:
        issues.append(issue("action_packets", "direct_execution_allowed must be false"))
    packet_catalog, catalog_issues = string_list_value(root, "packet_type_catalog", "action_packets")
    forbidden_catalog, forbidden_issues = string_list_value(root, "forbidden_field_catalog", "action_packets")
    issues.extend(catalog_issues + forbidden_issues)
    if set(packet_catalog) != set(REQUIRED_PACKET_TYPES) or set(packet_catalog) != context.decision_packet_types:
        issues.append(issue("action_packets.packet_type_catalog", "must match required route decision packet types"))
    if not FORBIDDEN_FIELDS.issubset(set(forbidden_catalog)):
        issues.append(issue("action_packets.forbidden_field_catalog", "must include execution-bearing forbidden fields"))
    return issues


def validate_packet_schema(packet: JsonObject, context: ValidationContext, index: int) -> tuple[int, int, list[DomainSourceIssue]]:
    location = f"action_packets.packet_schemas[{index}]"
    issues = require_text_fields(packet, REQUIRED_PACKET_TEXT_FIELDS, location)
    packet_type = text_value(packet, "packet_type")
    if packet_type not in REQUIRED_PACKET_TYPES:
        issues.append(issue(location, f"unknown packet_type {packet_type}"))
    if text_value(packet, "review_status") != REVIEW_STATUS:
        issues.append(issue(location, f"review_status must be {REVIEW_STATUS}"))
    if text_value(packet, "non_execution_semantics") != NON_EXECUTION_SEMANTICS:
        issues.append(issue(location, f"non_execution_semantics must be {NON_EXECUTION_SEMANTICS}"))
    if bool_value(packet, "no_direct_execution") is not True:
        issues.append(issue(location, "no_direct_execution must be true"))
    if bool_value(packet, "direct_execution_allowed") is not False:
        issues.append(issue(location, "direct_execution_allowed must be false"))
    list_values = validate_packet_lists(packet, context, location)
    issues.extend(list_values[2])
    issues.extend(validate_pii_profile(packet, location))
    issues.extend(validate_route_linkage(packet, context, location, packet_type))
    issues.extend(validate_forbidden_keys(packet, location))
    return list_values[0], list_values[1], issues


def validate_packet_lists(packet: JsonObject, context: ValidationContext, location: str) -> tuple[int, int, list[DomainSourceIssue]]:
    issues: list[DomainSourceIssue] = []
    required_input_count = 0
    source_ref_count = 0
    for field in REQUIRED_PACKET_LIST_FIELDS:
        values, value_issues = string_list_value(packet, field, location)
        issues.extend(value_issues)
        if field == "required_inputs":
            required_input_count = len(values)
            issues.extend(validate_known_ids(values, context.known_inputs, location, "required_input"))
        if field == "source_refs":
            source_ref_count = len(values)
            if not values:
                issues.append(issue(location, "source_refs must not be empty"))
            issues.extend(validate_known_ids(values, context.source_ids, location, "source_id"))
        if field == "allowed_output_fields":
            issues.extend(issue(location, f"forbidden output field {value}") for value in values if value in FORBIDDEN_FIELDS)
        if field == "forbidden_fields" and not FORBIDDEN_FIELDS.issubset(set(values)):
            issues.append(issue(location, "forbidden_fields must include execution-bearing fields"))
        if field == "permitted_next_states":
            issues.extend(validate_known_ids(values, context.workflow_review_states, location, "review_state"))
    return required_input_count, source_ref_count, issues


def validate_pii_profile(packet: JsonObject, location: str) -> list[DomainSourceIssue]:
    profile, issues = object_value(packet, "pii_profile", location)
    for field in PII_FALSE_FIELDS:
        if bool_value(profile, field) is not False:
            issues.append(issue(f"{location}.pii_profile", f"{field} must be false"))
    if bool_value(profile, "redaction_required") is not True:
        issues.append(issue(f"{location}.pii_profile", "redaction_required must be true"))
    return issues


def validate_route_linkage(packet: JsonObject, context: ValidationContext, location: str, packet_type: str) -> list[DomainSourceIssue]:
    linkage, issues = object_value(packet, "route_decision_linkage", location)
    if text_value(linkage, "decision_table_version") != DECISION_TABLE_VERSION:
        issues.append(issue(f"{location}.route_decision_linkage", f"decision_table_version must be {DECISION_TABLE_VERSION}"))
    if text_value(linkage, "route_decision_packet_type") != packet_type:
        issues.append(issue(f"{location}.route_decision_linkage", "route_decision_packet_type must match packet_type"))
    route_ids, route_issues = string_list_value(linkage, "route_ids", f"{location}.route_decision_linkage")
    issues.extend(route_issues)
    if set(route_ids) != context.decision_routes_by_packet_type.get(packet_type, set()):
        issues.append(issue(f"{location}.route_decision_linkage", "route_ids must match route decisions for packet type"))
    return issues


def validate_forbidden_keys(value: JsonValue, location: str) -> list[DomainSourceIssue]:
    if not isinstance(value, dict):
        return []
    issues: list[DomainSourceIssue] = []
    for key, child in value.items():
        if key in FORBIDDEN_FIELDS:
            issues.append(issue(location, f"forbidden field key {key}"))
        if isinstance(child, dict):
            issues.extend(validate_forbidden_keys(child, f"{location}.{key}"))
        elif isinstance(child, list):
            for index, item in enumerate(child):
                issues.extend(validate_forbidden_keys(item, f"{location}.{key}[{index}]"))
    return issues
