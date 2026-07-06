#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "scripts.legal_ontology"

from .domain_sources_v1_common import (
    DomainSourceIssue,
    DomainSourceSummary,
    JsonObject,
    bool_value,
    load_json,
    object_list_value,
    string_list_value,
    text_value,
    validate_known_ids,
    validate_unique_ids,
)

DOMAIN_SOURCES_SCHEMA_VERSION: Final = "trustgraph-legal-domain-sources/v1"
REQUIRED_ROOT_TEXT_FIELDS: Final = ("schema_version", "rule_source_version", "review_status", "evaluation_date", "retrieved_at")
REQUIRED_SOURCE_TEXT_FIELDS: Final = (
    "source_id", "law_name", "effective_date", "retrieved_at", "retrieval_status", "review_status", "source_axis",
    "source_ref", "evaluation_date", "effective_date_decision",
)
REQUIRED_VERIFIED_LAW_FIELDS: Final = ("law_id", "mst", "article")
USAGE_FIELDS: Final = ("route_usage", "workflow_usage", "stopgate_usage")
ROUTE_REF_FIELDS: Final = ("legal_source_refs", "compliance_source_refs")
ADVISORY_EXECUTION_POLICY: Final = "advisory_sources_only_no_live_law_calls_in_tests"
NEEDS_REVIEW_STATUS: Final = "needs_legal_review"


def collect_route_ids(routes_root: JsonObject) -> tuple[set[str], int, int, list[DomainSourceIssue]]:
    routes, issues = object_list_value(routes_root, "routes", "routes")
    route_ids: list[str] = []
    source_ref_count = 0
    for index, route in enumerate(routes):
        location = f"routes.routes[{index}]"
        route_id = text_value(route, "route_id")
        if route_id:
            route_ids.append(route_id)
        for field in ROUTE_REF_FIELDS:
            source_refs, source_issues = string_list_value(route, field, location)
            source_ref_count += len(source_refs)
            issues.extend(source_issues)
    issues.extend(validate_unique_ids(route_ids, "routes.routes"))
    return set(route_ids), len(routes), source_ref_count, issues


def collect_stopgate_ids(stopgates_root: JsonObject) -> tuple[set[str], int, int, list[DomainSourceIssue]]:
    rules, issues = object_list_value(stopgates_root, "rules", "stopgates")
    stopgate_ids: list[str] = []
    source_ref_count = 0
    for index, rule in enumerate(rules):
        location = f"stopgates.rules[{index}]"
        stopgate_id = text_value(rule, "stopgate_id")
        if stopgate_id:
            stopgate_ids.append(stopgate_id)
        source_ids, source_issues = string_list_value(rule, "source_ids", location)
        source_ref_count += len(source_ids)
        issues.extend(source_issues)
    return set(stopgate_ids), len(rules), source_ref_count, issues


def collect_workflow_ids(root: JsonObject) -> tuple[set[str], list[DomainSourceIssue]]:
    workflow_state_ids, issues = string_list_value(root, "workflow_state_ids", "domain_sources")
    if not workflow_state_ids:
        issues.append(DomainSourceIssue(location="domain_sources", message="workflow_state_ids must not be empty"))
    issues.extend(validate_unique_ids(workflow_state_ids, "domain_sources.workflow_state_ids"))
    return set(workflow_state_ids), issues


def validate_root(root: JsonObject) -> list[DomainSourceIssue]:
    issues: list[DomainSourceIssue] = []
    for field in REQUIRED_ROOT_TEXT_FIELDS:
        if not text_value(root, field):
            issues.append(DomainSourceIssue(location="domain_sources", message=f"missing {field}"))
    if text_value(root, "schema_version") != DOMAIN_SOURCES_SCHEMA_VERSION:
        issues.append(
            DomainSourceIssue(
                location="domain_sources",
                message=f"schema_version must be {DOMAIN_SOURCES_SCHEMA_VERSION}",
            ),
        )
    if text_value(root, "execution_policy") != ADVISORY_EXECUTION_POLICY:
        issues.append(DomainSourceIssue(location="domain_sources", message="unexpected execution_policy"))
    if bool_value(root, "no_direct_execution") is not True:
        issues.append(DomainSourceIssue(location="domain_sources", message="no_direct_execution must be true"))
    return issues


def collect_source_ids(
    root: JsonObject,
    route_ids: set[str],
    workflow_ids: set[str],
    stopgate_ids: set[str],
) -> tuple[set[str], int, list[DomainSourceIssue]]:
    sources, issues = object_list_value(root, "sources", "domain_sources")
    source_ids: list[str] = []
    usage_targets = {
        "route_usage": (route_ids, "route_id"),
        "workflow_usage": (workflow_ids, "workflow_state_id"),
        "stopgate_usage": (stopgate_ids, "stopgate_id"),
    }
    for index, source in enumerate(sources):
        location = f"domain_sources.sources[{index}]"
        for field in REQUIRED_SOURCE_TEXT_FIELDS:
            if not text_value(source, field):
                issues.append(DomainSourceIssue(location=location, message=f"missing {field}"))

        review_status = text_value(source, "review_status")
        if review_status != NEEDS_REVIEW_STATUS:
            for field in REQUIRED_VERIFIED_LAW_FIELDS:
                if not text_value(source, field):
                    issues.append(DomainSourceIssue(location=location, message=f"missing {field}"))
        elif not text_value(source, "candidate_note"):
            issues.append(DomainSourceIssue(location=location, message="missing candidate_note"))

        source_id = text_value(source, "source_id")
        if source_id:
            source_ids.append(source_id)

        usage_count = 0
        for field in USAGE_FIELDS:
            usage, usage_issues = string_list_value(source, field, location)
            usage_count += len(usage)
            issues.extend(usage_issues)
            known_ids, label = usage_targets[field]
            issues.extend(validate_known_ids(usage, known_ids, location, label))
        if usage_count == 0:
            issues.append(DomainSourceIssue(location=location, message="at least one usage field must be non-empty"))

    issues.extend(validate_unique_ids(source_ids, "domain_sources.sources"))
    return set(source_ids), len(sources), issues


def validate_source_refs(
    refs: Sequence[str],
    source_ids: set[str],
    location: str,
) -> list[DomainSourceIssue]:
    issues: list[DomainSourceIssue] = []
    for source_ref in refs:
        if source_ref not in source_ids:
            issues.append(DomainSourceIssue(location=location, message=f"unknown source_id {source_ref}"))
    return issues


def validate_route_source_refs(routes_root: JsonObject, source_ids: set[str]) -> list[DomainSourceIssue]:
    routes, issues = object_list_value(routes_root, "routes", "routes")
    for index, route in enumerate(routes):
        location = f"routes.routes[{index}]"
        for field in ROUTE_REF_FIELDS:
            source_refs, source_issues = string_list_value(route, field, location)
            issues.extend(source_issues)
            issues.extend(validate_source_refs(source_refs, source_ids, location))
    return issues


def validate_stopgate_source_refs(stopgates_root: JsonObject, source_ids: set[str]) -> list[DomainSourceIssue]:
    rules, issues = object_list_value(stopgates_root, "rules", "stopgates")
    for index, rule in enumerate(rules):
        location = f"stopgates.rules[{index}]"
        source_refs, source_issues = string_list_value(rule, "source_ids", location)
        issues.extend(source_issues)
        issues.extend(validate_source_refs(source_refs, source_ids, location))
    return issues


def validate_workflow_source_refs(
    root: JsonObject,
    source_ids: set[str],
    workflow_ids: set[str],
) -> tuple[int, int, list[DomainSourceIssue]]:
    workflow_refs, issues = object_list_value(root, "workflow_source_refs", "domain_sources")
    source_ref_count = 0
    for index, workflow_ref in enumerate(workflow_refs):
        location = f"domain_sources.workflow_source_refs[{index}]"
        workflow_id = text_value(workflow_ref, "workflow_state_id")
        if not workflow_id:
            issues.append(DomainSourceIssue(location=location, message="missing workflow_state_id"))
        elif workflow_id not in workflow_ids:
            issues.append(DomainSourceIssue(location=location, message=f"unknown workflow_state_id {workflow_id}"))
        source_refs, source_issues = string_list_value(workflow_ref, "source_ids", location)
        source_ref_count += len(source_refs)
        issues.extend(source_issues)
        issues.extend(validate_source_refs(source_refs, source_ids, location))
    return len(workflow_refs), source_ref_count, issues


def validate_domain_sources(
    sources_root: JsonObject,
    routes_root: JsonObject,
    stopgates_root: JsonObject,
) -> tuple[DomainSourceSummary, list[DomainSourceIssue]]:
    issues = validate_root(sources_root)
    route_ids, route_count, route_source_ref_count, route_issues = collect_route_ids(routes_root)
    stopgate_ids, stopgate_count, stopgate_source_ref_count, stopgate_issues = collect_stopgate_ids(stopgates_root)
    workflow_ids, workflow_issues = collect_workflow_ids(sources_root)
    issues.extend(route_issues)
    issues.extend(stopgate_issues)
    issues.extend(workflow_issues)

    source_ids, source_count, source_issues = collect_source_ids(sources_root, route_ids, workflow_ids, stopgate_ids)
    issues.extend(source_issues)
    issues.extend(validate_route_source_refs(routes_root, source_ids))
    issues.extend(validate_stopgate_source_refs(stopgates_root, source_ids))
    workflow_ref_count, workflow_source_ref_count, workflow_source_issues = validate_workflow_source_refs(
        sources_root,
        source_ids,
        workflow_ids,
    )
    issues.extend(workflow_source_issues)

    source_version = text_value(sources_root, "rule_source_version")
    summary = DomainSourceSummary(
        source_version=source_version,
        source_count=source_count,
        route_count=route_count,
        route_source_ref_count=route_source_ref_count,
        stopgate_count=stopgate_count,
        stopgate_source_ref_count=stopgate_source_ref_count,
        workflow_ref_count=workflow_ref_count,
        workflow_source_ref_count=workflow_source_ref_count,
    )
    return summary, issues


def main(argv: Sequence[str]) -> int:
    if len(argv) != 4:
        print("usage: validate_domain_sources_v1.py <domain-sources.json> <routes.json> <stopgates.json>", file=sys.stderr)
        return 2

    sources_path = Path(argv[1])
    routes_path = Path(argv[2])
    stopgates_path = Path(argv[3])
    try:
        summary, issues = validate_domain_sources(
            load_json(sources_path),
            load_json(routes_path),
            load_json(stopgates_path),
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
        for issue in issues:
            print(f"ERROR {issue.format()}", file=sys.stderr)
        return 1

    message = (
        f"PASS domain_sources {summary.source_version} "
        f"legal_sources={summary.source_count} routes={summary.route_count} "
        f"route_source_refs={summary.route_source_ref_count} stopgates={summary.stopgate_count} "
        f"stopgate_source_refs={summary.stopgate_source_ref_count} workflow_refs={summary.workflow_ref_count} "
        f"workflow_source_refs={summary.workflow_source_ref_count}"
    )
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
