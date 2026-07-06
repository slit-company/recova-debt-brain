#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "scripts.legal_ontology"

from .domain_sources_v1_common import (
    DomainSourceIssue,
    JsonObject,
    bool_value,
    load_json,
    object_list_value,
    string_list_value,
    text_value,
    validate_unique_ids,
)

WORKFLOW_SCHEMA_VERSION: Final = "trustgraph-legal-workflow/v1"
DOMAIN_SOURCES_SCHEMA_VERSION: Final = "trustgraph-legal-domain-sources/v1"
WORKFLOW_VERSION: Final = "recova-debt-collection-workflow@v1.0.0"
ROUTE_LINK_SEMANTICS: Final = "workflow_precondition_only_no_route_decision_logic"
NON_EXECUTION_SEMANTICS: Final = "descriptive_only_no_collection_action"
REQUIRED_STATE_IDS: Final = (
    "intake", "identity_evidence_package", "limitation_review", "title_acquisition",
    "service_finality_execution_clause", "voluntary_recovery", "provisional_remedy", "asset_discovery",
    "execution_route_selection", "insolvency_discharge_review", "monitoring_retry", "closure",
)
REQUIRED_REVIEW_STATES: Final = frozenset(
    {"needs_evidence", "human_review_required", "blocked", "monitoring", "ready_for_next_state", "closed", "rejected"},
)
REQUIRED_ROOT_TEXT_FIELDS: Final = (
    "schema_version", "workflow_version", "ontology_ref", "domain_source_version", "evaluation_date", "review_status",
    "execution_policy",
)
REQUIRED_STATE_TEXT_FIELDS: Final = (
    "state_id", "label", "category", "status", "purpose", "route_link_semantics", "non_execution_semantics",
)
REQUIRED_TRANSITION_TEXT_FIELDS: Final = (
    "transition_id", "from_state", "to_state", "trigger", "transition_kind", "review_status",
)
REQUIRED_LOOP_TEXT_FIELDS: Final = ("loop_id", "loop_kind", "monitor_state", "review_status")
STATE_LIST_FIELDS: Final = ("preconditions", "exit_conditions", "required_evidence", "review_states", "source_refs")
TRANSITION_LIST_FIELDS: Final = ("preconditions", "exit_conditions", "required_evidence", "source_refs")
LOOP_LIST_FIELDS: Final = ("entry_states", "return_states", "blocking_review_states", "required_evidence", "source_refs")


@dataclass(frozen=True, slots=True)
class WorkflowSummary:
    workflow_version: str
    state_count: int
    transition_count: int
    loop_count: int
    source_ref_count: int


@dataclass(frozen=True, slots=True)
class ValidationContext:
    source_ids: set[str]
    state_sources: dict[str, tuple[str, ...]]
    review_catalog: set[str]
    state_ids: set[str] = field(default_factory=set)


def issue(location: str, message: str) -> DomainSourceIssue:
    return DomainSourceIssue(location=location, message=message)


def require_text_fields(entry: JsonObject, fields: Sequence[str], location: str) -> list[DomainSourceIssue]:
    return [issue(location, f"missing {field}") for field in fields if not text_value(entry, field)]


def collect_domain_source_refs(root: JsonObject) -> tuple[set[str], dict[str, tuple[str, ...]], list[DomainSourceIssue]]:
    issues: list[DomainSourceIssue] = []
    if text_value(root, "schema_version") != DOMAIN_SOURCES_SCHEMA_VERSION:
        issues.append(issue("domain_sources", f"schema_version must be {DOMAIN_SOURCES_SCHEMA_VERSION}"))

    sources, source_issues = object_list_value(root, "sources", "domain_sources")
    workflow_state_ids, state_id_issues = string_list_value(root, "workflow_state_ids", "domain_sources")
    refs, ref_issues = object_list_value(root, "workflow_source_refs", "domain_sources")
    issues.extend(source_issues)
    issues.extend(state_id_issues)
    issues.extend(ref_issues)
    if tuple(workflow_state_ids) != REQUIRED_STATE_IDS:
        issues.append(issue("domain_sources.workflow_state_ids", "must match required workflow state ids"))

    state_sources: dict[str, tuple[str, ...]] = {}
    for index, ref in enumerate(refs):
        location = f"domain_sources.workflow_source_refs[{index}]"
        state_id = text_value(ref, "workflow_state_id")
        source_refs, source_issues = string_list_value(ref, "source_ids", location)
        issues.extend(source_issues)
        state_sources[state_id] = tuple(source_refs)
    source_ids = {text_value(source, "source_id") for source in sources if text_value(source, "source_id")}
    return source_ids, state_sources, issues


def validate_root(root: JsonObject, source_root: JsonObject) -> list[DomainSourceIssue]:
    issues = require_text_fields(root, REQUIRED_ROOT_TEXT_FIELDS, "workflow")
    if text_value(root, "schema_version") != WORKFLOW_SCHEMA_VERSION:
        issues.append(issue("workflow", f"schema_version must be {WORKFLOW_SCHEMA_VERSION}"))
    if text_value(root, "workflow_version") != WORKFLOW_VERSION:
        issues.append(issue("workflow", f"workflow_version must be {WORKFLOW_VERSION}"))
    if text_value(root, "domain_source_version") != text_value(source_root, "rule_source_version"):
        issues.append(issue("workflow.domain_source_version", "must match domain source version"))
    if bool_value(root, "no_direct_execution") is not True:
        issues.append(issue("workflow", "no_direct_execution must be true"))
    if bool_value(root, "route_decision_logic_excluded") is not True:
        issues.append(issue("workflow", "route_decision_logic_excluded must be true"))
    return issues


def validate_review_catalog(root: JsonObject) -> tuple[set[str], list[DomainSourceIssue]]:
    catalog, issues = object_list_value(root, "review_state_catalog", "workflow")
    review_states = {text_value(entry, "review_state") for entry in catalog if text_value(entry, "review_state")}
    for review_state in sorted(REQUIRED_REVIEW_STATES.difference(review_states)):
        issues.append(issue("workflow.review_state_catalog", f"missing review_state {review_state}"))
    return review_states, issues


def validate_source_refs(refs: Sequence[str], context: ValidationContext, location: str) -> list[DomainSourceIssue]:
    return [issue(location, f"unknown source_id {ref}") for ref in refs if ref not in context.source_ids]


def validate_state_lists(state: JsonObject, context: ValidationContext, location: str) -> tuple[int, list[DomainSourceIssue]]:
    source_ref_count = 0
    issues: list[DomainSourceIssue] = []
    for field in STATE_LIST_FIELDS:
        values, value_issues = string_list_value(state, field, location)
        issues.extend(value_issues)
        if field == "source_refs":
            source_ref_count = len(values)
            issues.extend(validate_source_refs(values, context, location))
            expected = context.state_sources.get(text_value(state, "state_id"), ())
            if tuple(values) != expected:
                issues.append(issue(location, "source_refs must match domain_sources.workflow_source_refs"))
        if field == "review_states":
            for review_state in sorted(set(values).difference(context.review_catalog)):
                issues.append(issue(location, f"unknown review_state {review_state}"))
    return source_ref_count, issues


def validate_states(root: JsonObject, context: ValidationContext) -> tuple[set[str], int, list[DomainSourceIssue]]:
    states, issues = object_list_value(root, "states", "workflow")
    ids = [text_value(state, "state_id") for state in states if text_value(state, "state_id")]
    if tuple(ids) != REQUIRED_STATE_IDS:
        issues.append(issue("workflow.states", "state order must match required workflow state ids"))
    issues.extend(validate_unique_ids(ids, "workflow.states"))

    source_ref_count = 0
    for index, state in enumerate(states):
        location = f"workflow.states[{index}]"
        issues.extend(require_text_fields(state, REQUIRED_STATE_TEXT_FIELDS, location))
        if text_value(state, "route_link_semantics") != ROUTE_LINK_SEMANTICS:
            issues.append(issue(location, f"route_link_semantics must be {ROUTE_LINK_SEMANTICS}"))
        if text_value(state, "non_execution_semantics") != NON_EXECUTION_SEMANTICS:
            issues.append(issue(location, f"non_execution_semantics must be {NON_EXECUTION_SEMANTICS}"))
        state_source_ref_count, state_issues = validate_state_lists(state, context, location)
        source_ref_count += state_source_ref_count
        issues.extend(state_issues)
    return set(ids), source_ref_count, issues


def validate_transitions(root: JsonObject, context: ValidationContext) -> tuple[int, int, list[DomainSourceIssue]]:
    transitions, issues = object_list_value(root, "transitions", "workflow")
    ids = [text_value(transition, "transition_id") for transition in transitions if text_value(transition, "transition_id")]
    issues.extend(validate_unique_ids(ids, "workflow.transitions"))
    source_ref_count = 0
    for index, transition in enumerate(transitions):
        location = f"workflow.transitions[{index}]"
        issues.extend(require_text_fields(transition, REQUIRED_TRANSITION_TEXT_FIELDS, location))
        transition_source_count, transition_issues = validate_transition_refs(transition, context, location)
        source_ref_count += transition_source_count
        issues.extend(transition_issues)
    return len(transitions), source_ref_count, issues


def validate_transition_refs(
    transition: JsonObject,
    context: ValidationContext,
    location: str,
) -> tuple[int, list[DomainSourceIssue]]:
    issues: list[DomainSourceIssue] = []
    if text_value(transition, "from_state") not in context.state_ids:
        issues.append(issue(location, f"unknown from_state {text_value(transition, 'from_state')}"))
    source_ref_count = 0
    to_state = text_value(transition, "to_state")
    if to_state and to_state not in context.state_ids:
        issues.append(issue(location, f"unknown to_state {to_state}"))
    for field in TRANSITION_LIST_FIELDS:
        values, value_issues = string_list_value(transition, field, location)
        issues.extend(value_issues)
        if field == "source_refs":
            source_ref_count += len(values)
            issues.extend(validate_source_refs(values, context, location))
    return source_ref_count, issues


def validate_loop_refs(loop: JsonObject, context: ValidationContext, location: str) -> tuple[int, list[DomainSourceIssue]]:
    source_ref_count = 0
    issues: list[DomainSourceIssue] = []
    monitor_state = text_value(loop, "monitor_state")
    if monitor_state and monitor_state not in context.state_ids:
        issues.append(issue(location, f"unknown monitor_state {monitor_state}"))
    for field in LOOP_LIST_FIELDS:
        values, value_issues = string_list_value(loop, field, location)
        issues.extend(value_issues)
        if field in {"entry_states", "return_states"}:
            issues.extend(issue(location, f"unknown loop state {state_id}") for state_id in values if state_id not in context.state_ids)
        if field == "blocking_review_states":
            issues.extend(issue(location, f"unknown review_state {state}") for state in values if state not in context.review_catalog)
        if field == "source_refs":
            source_ref_count += len(values)
            issues.extend(validate_source_refs(values, context, location))
    return source_ref_count, issues


def validate_loops(root: JsonObject, context: ValidationContext) -> tuple[int, int, list[DomainSourceIssue]]:
    loops, issues = object_list_value(root, "loops", "workflow")
    ids = [text_value(loop, "loop_id") for loop in loops if text_value(loop, "loop_id")]
    issues.extend(validate_unique_ids(ids, "workflow.loops"))
    source_ref_count = 0
    for index, loop in enumerate(loops):
        location = f"workflow.loops[{index}]"
        issues.extend(require_text_fields(loop, REQUIRED_LOOP_TEXT_FIELDS, location))
        loop_source_ref_count, loop_issues = validate_loop_refs(loop, context, location)
        source_ref_count += loop_source_ref_count
        issues.extend(loop_issues)
    return len(loops), source_ref_count, issues


def validate_workflow(root: JsonObject, source_root: JsonObject) -> tuple[WorkflowSummary, list[DomainSourceIssue]]:
    source_ids, state_sources, source_issues = collect_domain_source_refs(source_root)
    review_catalog, review_issues = validate_review_catalog(root)
    context = ValidationContext(source_ids=source_ids, state_sources=state_sources, review_catalog=review_catalog)
    state_ids, state_ref_count, state_issues = validate_states(root, context)
    context = ValidationContext(
        source_ids=source_ids,
        state_sources=state_sources,
        review_catalog=review_catalog,
        state_ids=state_ids,
    )
    transition_count, transition_ref_count, transition_issues = validate_transitions(root, context)
    loop_count, loop_ref_count, loop_issues = validate_loops(root, context)
    issues = validate_root(root, source_root) + source_issues + review_issues + state_issues + transition_issues + loop_issues
    summary = WorkflowSummary(
        workflow_version=text_value(root, "workflow_version"),
        state_count=len(state_ids),
        transition_count=transition_count,
        loop_count=loop_count,
        source_ref_count=state_ref_count + transition_ref_count + loop_ref_count,
    )
    return summary, issues


def main(argv: Sequence[str]) -> int:
    if len(argv) != 3:
        print("usage: validate_workflow_v1.py <workflow.json> <domain-sources.json>", file=sys.stderr)
        return 2
    try:
        summary, issues = validate_workflow(load_json(Path(argv[1])), load_json(Path(argv[2])))
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
        for entry in issues:
            print(f"ERROR {entry.format()}", file=sys.stderr)
        return 1
    print(
        f"PASS workflow {summary.workflow_version} states={summary.state_count} "
        f"transitions={summary.transition_count} loops={summary.loop_count} source_refs={summary.source_ref_count}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
