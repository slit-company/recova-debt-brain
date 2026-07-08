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

PLAYBOOK_SCHEMA_VERSION: Final = "trustgraph-collection-operator-playbook/v1"
PLAYBOOK_VERSION: Final = "recova-debt-collection-operator-playbook@v1.0.0"
WORKFLOW_VERSION: Final = "recova-debt-collection-workflow@v1.0.0"
NON_EXECUTION_SEMANTICS: Final = "advisory_only_human_review_required"
REQUIRED_STAGE_IDS: Final = (
    "intake", "evidence_completion", "title_acquisition", "asset_discovery",
    "execution_route_selection", "enforcement_ready", "monitoring",
    "settlement_restructuring", "insolvency_protected_asset_review", "closure",
)
REQUIRED_ROOT_TEXT_FIELDS: Final = (
    "schema_version", "playbook_version", "workflow_version", "domain_source_version",
    "evaluation_date", "review_status", "execution_policy", "non_execution_semantics",
)
REQUIRED_STAGE_TEXT_FIELDS: Final = (
    "stage_id", "label", "operator_question", "operational_posture", "decision_rule",
    "non_execution_semantics",
)
STAGE_LIST_FIELDS: Final = (
    "workflow_state_ids", "entry_signals", "next_action_types", "premature_action_reasons",
    "missing_inputs", "required_checkpoint_inputs", "remediation_loops", "ready_when", "source_refs",
)


@dataclass(frozen=True, slots=True)
class PlaybookSummary:
    playbook_version: str
    stage_count: int
    action_type_count: int
    remediation_loop_count: int
    source_ref_count: int


@dataclass(frozen=True, slots=True)
class ValidationContext:
    workflow_state_ids: set[str]
    source_ids: set[str]
    action_types: set[str] = field(default_factory=set)
    premature_reasons: set[str] = field(default_factory=set)
    checkpoint_inputs: set[str] = field(default_factory=set)
    remediation_loops: set[str] = field(default_factory=set)


def issue(location: str, message: str) -> DomainSourceIssue:
    return DomainSourceIssue(location=location, message=message)


def require_text_fields(entry: JsonObject, fields: Sequence[str], location: str) -> list[DomainSourceIssue]:
    return [issue(location, f"missing {field}") for field in fields if not text_value(entry, field)]


def catalog_ids(root: JsonObject, field: str, id_field: str) -> tuple[set[str], list[DomainSourceIssue]]:
    entries, issues = object_list_value(root, field, "operator_playbook")
    ids = [text_value(entry, id_field) for entry in entries if text_value(entry, id_field)]
    issues.extend(validate_unique_ids(ids, f"operator_playbook.{field}"))
    return set(ids), issues


def collect_workflow_state_ids(workflow: JsonObject) -> tuple[set[str], list[DomainSourceIssue]]:
    issues: list[DomainSourceIssue] = []
    if text_value(workflow, "workflow_version") != WORKFLOW_VERSION:
        issues.append(issue("workflow", f"workflow_version must be {WORKFLOW_VERSION}"))
    states, state_issues = object_list_value(workflow, "states", "workflow")
    issues.extend(state_issues)
    return {text_value(state, "state_id") for state in states if text_value(state, "state_id")}, issues


def collect_source_ids(sources: JsonObject) -> set[str]:
    entries, _ = object_list_value(sources, "sources", "domain_sources")
    return {text_value(entry, "source_id") for entry in entries if text_value(entry, "source_id")}


def validate_root(root: JsonObject, workflow: JsonObject, sources: JsonObject) -> list[DomainSourceIssue]:
    issues = require_text_fields(root, REQUIRED_ROOT_TEXT_FIELDS, "operator_playbook")
    if text_value(root, "schema_version") != PLAYBOOK_SCHEMA_VERSION:
        issues.append(issue("operator_playbook", f"schema_version must be {PLAYBOOK_SCHEMA_VERSION}"))
    if text_value(root, "playbook_version") != PLAYBOOK_VERSION:
        issues.append(issue("operator_playbook", f"playbook_version must be {PLAYBOOK_VERSION}"))
    if text_value(root, "workflow_version") != text_value(workflow, "workflow_version"):
        issues.append(issue("operator_playbook.workflow_version", "must match workflow resource"))
    if text_value(root, "domain_source_version") != text_value(sources, "rule_source_version"):
        issues.append(issue("operator_playbook.domain_source_version", "must match domain source version"))
    if text_value(root, "non_execution_semantics") != NON_EXECUTION_SEMANTICS:
        issues.append(issue("operator_playbook", f"non_execution_semantics must be {NON_EXECUTION_SEMANTICS}"))
    stage_order, stage_order_issues = string_list_value(root, "stage_order", "operator_playbook")
    issues.extend(stage_order_issues)
    if tuple(stage_order) != REQUIRED_STAGE_IDS:
        issues.append(issue("operator_playbook.stage_order", "must match required operator stage ids"))
    if bool_value(root, "no_direct_execution") is not True:
        issues.append(issue("operator_playbook", "no_direct_execution must be true"))
    if bool_value(root, "direct_execution_allowed") is not False:
        issues.append(issue("operator_playbook", "direct_execution_allowed must be false"))
    return issues


def validate_catalogs(root: JsonObject) -> tuple[ValidationContext, list[DomainSourceIssue]]:
    action_types, action_issues = catalog_ids(root, "next_action_type_catalog", "action_type")
    premature_reasons, reason_issues = catalog_ids(root, "premature_action_reason_catalog", "reason")
    checkpoint_inputs, checkpoint_issues = catalog_ids(root, "checkpoint_input_catalog", "checkpoint_input")
    remediation_loops, loop_issues = catalog_ids(root, "remediation_loop_catalog", "loop")
    issues = action_issues + reason_issues + checkpoint_issues + loop_issues
    context = ValidationContext(
        workflow_state_ids=set(),
        source_ids=set(),
        action_types=action_types,
        premature_reasons=premature_reasons,
        checkpoint_inputs=checkpoint_inputs,
        remediation_loops=remediation_loops,
    )
    return context, issues


def validate_stage_lists(stage: JsonObject, context: ValidationContext, location: str) -> tuple[int, list[DomainSourceIssue]]:
    issues: list[DomainSourceIssue] = []
    source_ref_count = 0
    for field in STAGE_LIST_FIELDS:
        values, value_issues = string_list_value(stage, field, location)
        issues.extend(value_issues)
        if field == "workflow_state_ids":
            issues.extend(issue(location, f"unknown workflow_state_id {value}") for value in values if value not in context.workflow_state_ids)
        if field == "next_action_types":
            issues.extend(issue(location, f"unknown action_type {value}") for value in values if value not in context.action_types)
        if field == "premature_action_reasons":
            issues.extend(issue(location, f"unknown premature_action_reason {value}") for value in values if value not in context.premature_reasons)
        if field == "required_checkpoint_inputs":
            issues.extend(issue(location, f"unknown checkpoint_input {value}") for value in values if value not in context.checkpoint_inputs)
        if field == "remediation_loops":
            issues.extend(issue(location, f"unknown remediation_loop {value}") for value in values if value not in context.remediation_loops)
        if field == "source_refs":
            source_ref_count = len(values)
            issues.extend(issue(location, f"unknown source_id {value}") for value in values if value not in context.source_ids)
    return source_ref_count, issues


def validate_stages(root: JsonObject, context: ValidationContext) -> tuple[int, list[DomainSourceIssue]]:
    stages, issues = object_list_value(root, "stages", "operator_playbook")
    ids = [text_value(stage, "stage_id") for stage in stages if text_value(stage, "stage_id")]
    if tuple(ids) != REQUIRED_STAGE_IDS:
        issues.append(issue("operator_playbook.stages", "stage order must match required operator stage ids"))
    issues.extend(validate_unique_ids(ids, "operator_playbook.stages"))
    source_ref_count = 0
    for index, stage in enumerate(stages):
        location = f"operator_playbook.stages[{index}]"
        issues.extend(require_text_fields(stage, REQUIRED_STAGE_TEXT_FIELDS, location))
        if bool_value(stage, "human_review_required") is not True:
            issues.append(issue(location, "human_review_required must be true"))
        if text_value(stage, "non_execution_semantics") != NON_EXECUTION_SEMANTICS:
            issues.append(issue(location, f"non_execution_semantics must be {NON_EXECUTION_SEMANTICS}"))
        stage_source_ref_count, stage_issues = validate_stage_lists(stage, context, location)
        source_ref_count += stage_source_ref_count
        issues.extend(stage_issues)
    return source_ref_count, issues


def validate_operator_playbook(
    root: JsonObject,
    workflow: JsonObject,
    sources: JsonObject,
) -> tuple[PlaybookSummary, list[DomainSourceIssue]]:
    workflow_state_ids, workflow_issues = collect_workflow_state_ids(workflow)
    catalog_context, catalog_issues = validate_catalogs(root)
    context = ValidationContext(
        workflow_state_ids=workflow_state_ids,
        source_ids=collect_source_ids(sources),
        action_types=catalog_context.action_types,
        premature_reasons=catalog_context.premature_reasons,
        checkpoint_inputs=catalog_context.checkpoint_inputs,
        remediation_loops=catalog_context.remediation_loops,
    )
    stage_source_ref_count, stage_issues = validate_stages(root, context)
    summary = PlaybookSummary(
        playbook_version=text_value(root, "playbook_version"),
        stage_count=len(REQUIRED_STAGE_IDS),
        action_type_count=len(context.action_types),
        remediation_loop_count=len(context.remediation_loops),
        source_ref_count=stage_source_ref_count,
    )
    issues = validate_root(root, workflow, sources) + workflow_issues + catalog_issues + stage_issues
    return summary, issues


def main(argv: Sequence[str]) -> int:
    if len(argv) != 4:
        print("usage: validate_operator_playbook_v1.py <playbook.json> <workflow.json> <domain-sources.json>", file=sys.stderr)
        return 2
    try:
        summary, issues = validate_operator_playbook(load_json(Path(argv[1])), load_json(Path(argv[2])), load_json(Path(argv[3])))
    except json.JSONDecodeError as error:
        print(f"ERROR invalid JSON: {error}", file=sys.stderr)
        return 1
    except (OSError, TypeError) as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 1
    if issues:
        for entry in issues:
            print(f"ERROR {entry.format()}", file=sys.stderr)
        return 1
    print(
        f"PASS operator_playbook {summary.playbook_version} stages={summary.stage_count} "
        f"action_types={summary.action_type_count} remediation_loops={summary.remediation_loop_count} "
        f"source_refs={summary.source_ref_count}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
