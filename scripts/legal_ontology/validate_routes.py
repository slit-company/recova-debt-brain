#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Sequence

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

RouteIssue = DomainSourceIssue

ROUTES_SCHEMA_VERSION: Final = "trustgraph-legal-routes/v1"
ROUTE_SOURCES_SCHEMA_VERSION: Final = "trustgraph-legal-route-sources/v1"
DOMAIN_SOURCES_SCHEMA_VERSION: Final = "trustgraph-legal-domain-sources/v1"
REQUIRED_ROUTE_TEXT_FIELDS: Final = ("route_id", "family", "status", "review_status", "execution_semantics")
REQUIRED_ROUTE_SOURCE_TEXT_FIELDS: Final = (
    "source_id",
    "law_name",
    "law_id",
    "mst",
    "article",
    "effective_date",
    "retrieved_at",
    "retrieval_status",
    "review_status",
    "graph_use",
)
REQUIRED_DOMAIN_SOURCE_TEXT_FIELDS: Final = (
    "source_id",
    "law_name",
    "effective_date",
    "retrieved_at",
    "retrieval_status",
    "review_status",
    "source_axis",
    "source_ref",
    "evaluation_date",
    "effective_date_decision",
)
ADVISORY_EXECUTION_SEMANTICS: Final = "none_advisory_only"


@dataclass(frozen=True, slots=True)
class RouteSummary:
    route_version: str
    source_version: str
    route_count: int
    legal_source_count: int
    route_legal_ref_count: int


def required_string_list_value(entry: JsonObject, field: str, location: str) -> tuple[list[str], list[RouteIssue]]:
    strings, issues = string_list_value(entry, field, location)
    if not strings:
        issues.append(RouteIssue(location=location, message=f"{field} must be a non-empty string list"))
    return strings, issues


def validate_resource_header(root: JsonObject, location: str, expected_schema: str) -> list[RouteIssue]:
    issues: list[RouteIssue] = []
    if text_value(root, "schema_version") != expected_schema:
        issues.append(RouteIssue(location=location, message=f"schema_version must be {expected_schema}"))
    if not text_value(root, "review_status"):
        issues.append(RouteIssue(location=location, message="missing review_status"))
    if bool_value(root, "no_direct_execution") is not True:
        issues.append(RouteIssue(location=location, message="no_direct_execution must be true"))
    return issues


def validate_sources_header(root: JsonObject) -> tuple[str, list[RouteIssue]]:
    schema_version = text_value(root, "schema_version")
    if schema_version not in (ROUTE_SOURCES_SCHEMA_VERSION, DOMAIN_SOURCES_SCHEMA_VERSION):
        return schema_version, [
            RouteIssue(
                location="legal_sources",
                message=f"schema_version must be {ROUTE_SOURCES_SCHEMA_VERSION} or {DOMAIN_SOURCES_SCHEMA_VERSION}",
            ),
        ]
    return schema_version, validate_resource_header(root, "legal_sources", schema_version)


def source_text_fields(schema_version: str) -> tuple[str, ...]:
    if schema_version == DOMAIN_SOURCES_SCHEMA_VERSION:
        return REQUIRED_DOMAIN_SOURCE_TEXT_FIELDS
    return REQUIRED_ROUTE_SOURCE_TEXT_FIELDS


def collect_source_ids(sources: Sequence[JsonObject], schema_version: str) -> tuple[set[str], list[RouteIssue]]:
    source_ids: list[str] = []
    issues: list[RouteIssue] = []
    for index, source in enumerate(sources):
        location = f"legal_sources.sources[{index}]"
        for field in source_text_fields(schema_version):
            if not text_value(source, field):
                issues.append(RouteIssue(location=location, message=f"missing {field}"))
        source_id = text_value(source, "source_id")
        if source_id:
            source_ids.append(source_id)

    issues.extend(validate_unique_ids(source_ids, "legal_sources.sources"))
    return set(source_ids), issues


def collect_fact_handles(root: JsonObject) -> tuple[set[str], list[RouteIssue]]:
    if "fact_handle_catalog" not in root:
        return set(), []
    fact_handles, issues = required_string_list_value(root, "fact_handle_catalog", "routes")
    issues.extend(validate_unique_ids(fact_handles, "routes.fact_handle_catalog"))
    return set(fact_handles), issues


def validate_known_fact_handles(
    fact_handles: Sequence[str],
    catalog: set[str],
    location: str,
) -> list[RouteIssue]:
    if not catalog:
        return []
    issues: list[RouteIssue] = []
    for fact_handle in fact_handles:
        if fact_handle not in catalog:
            issues.append(RouteIssue(location=location, message=f"unknown fact handle {fact_handle}"))
    return issues


def validate_route_source_refs(
    route: JsonObject,
    location: str,
    legal_source_ids: set[str],
) -> tuple[int, list[RouteIssue]]:
    legal_refs, issues = required_string_list_value(route, "legal_source_refs", location)
    compliance_refs, compliance_issues = required_string_list_value(route, "compliance_source_refs", location)
    issues.extend(compliance_issues)

    for source_ref in legal_refs + compliance_refs:
        if source_ref not in legal_source_ids:
            issues.append(RouteIssue(location=location, message=f"unknown legal source {source_ref}"))
    return len(legal_refs), issues


def validate_route(
    route: JsonObject,
    index: int,
    legal_source_ids: set[str],
    fact_handle_catalog: set[str],
) -> tuple[int, list[RouteIssue]]:
    location = f"routes.routes[{index}]"
    issues: list[RouteIssue] = []

    for field in REQUIRED_ROUTE_TEXT_FIELDS:
        if not text_value(route, field):
            issues.append(RouteIssue(location=location, message=f"missing {field}"))
    required, required_issues = required_string_list_value(route, "required_fact_handles", location)
    missing, missing_issues = required_string_list_value(route, "missing_fact_handles", location)
    blocking, blocking_issues = required_string_list_value(route, "blocking_fact_handles", location)
    issues.extend(required_issues)
    issues.extend(missing_issues)
    issues.extend(blocking_issues)
    issues.extend(validate_known_fact_handles((*required, *missing, *blocking), fact_handle_catalog, location))
    for required_fact in required:
        if required_fact not in missing:
            issues.append(RouteIssue(location=location, message=f"missing_fact_handles must include {required_fact}"))

    if bool_value(route, "no_direct_execution") is not True:
        issues.append(RouteIssue(location=location, message="no_direct_execution must be true"))
    if bool_value(route, "direct_execution_allowed") is not False:
        issues.append(RouteIssue(location=location, message="direct_execution_allowed must be false"))
    if text_value(route, "execution_semantics") != ADVISORY_EXECUTION_SEMANTICS:
        issues.append(RouteIssue(location=location, message=f"execution_semantics must be {ADVISORY_EXECUTION_SEMANTICS}"))

    legal_ref_count, source_issues = validate_route_source_refs(route, location, legal_source_ids)
    issues.extend(source_issues)
    return legal_ref_count, issues


def validate_routes(routes_root: JsonObject, sources_root: JsonObject) -> tuple[RouteSummary | None, list[RouteIssue]]:
    issues: list[RouteIssue] = []
    issues.extend(validate_resource_header(routes_root, "routes", ROUTES_SCHEMA_VERSION))
    source_schema_version, source_header_issues = validate_sources_header(sources_root)
    issues.extend(source_header_issues)

    routes, route_section_issues = object_list_value(routes_root, "routes", "routes")
    sources, source_section_issues = object_list_value(sources_root, "sources", "legal_sources")
    issues.extend(route_section_issues)
    issues.extend(source_section_issues)

    legal_source_ids, source_issues = collect_source_ids(sources, source_schema_version)
    fact_handle_catalog, fact_handle_issues = collect_fact_handles(routes_root)
    issues.extend(source_issues)
    issues.extend(fact_handle_issues)

    route_ids = [text_value(route, "route_id") for route in routes if text_value(route, "route_id")]
    issues.extend(validate_unique_ids(route_ids, "routes.routes"))

    route_legal_ref_count = 0
    for index, route in enumerate(routes):
        legal_ref_count, route_issues = validate_route(route, index, legal_source_ids, fact_handle_catalog)
        route_legal_ref_count += legal_ref_count
        issues.extend(route_issues)

    route_version = text_value(routes_root, "route_source_version")
    source_version = text_value(sources_root, "rule_source_version")
    if not route_version:
        issues.append(RouteIssue(location="routes", message="missing route_source_version"))
    if not source_version:
        issues.append(RouteIssue(location="legal_sources", message="missing rule_source_version"))

    summary = RouteSummary(
        route_version=route_version,
        source_version=source_version,
        route_count=len(routes),
        legal_source_count=len(sources),
        route_legal_ref_count=route_legal_ref_count,
    )
    return summary, issues


def main(argv: Sequence[str]) -> int:
    if len(argv) != 3:
        print("usage: validate_routes.py <routes.json> <legal-sources.json>", file=sys.stderr)
        return 2

    routes_path = Path(argv[1])
    sources_path = Path(argv[2])
    try:
        summary, issues = validate_routes(load_json(routes_path), load_json(sources_path))
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

    if summary is None:
        print("ERROR route summary unavailable", file=sys.stderr)
        return 1

    print(
        "PASS routes "
        f"{summary.route_version} "
        f"sources={summary.source_version} "
        f"routes={summary.route_count} "
        f"legal_sources={summary.legal_source_count} "
        f"legal_refs={summary.route_legal_ref_count}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
