from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import TypeAlias


REPO_ROOT = Path(__file__).resolve().parents[3]
DECISIONS_PATH = REPO_ROOT / "resources" / "decision_tables" / "debt_collection_route_decisions_v1.json"
ROUTES_PATH = REPO_ROOT / "resources" / "legal_routes" / "debt_collection_routes_v1.json"
SOURCES_PATH = REPO_ROOT / "resources" / "legal_rules" / "debt_collection_domain_sources_v1.json"
WORKFLOW_PATH = REPO_ROOT / "resources" / "workflows" / "debt_collection_workflow_v1.json"
FINANCE_PATH = REPO_ROOT / "resources" / "finance" / "claim_finance_model_v1.json"
VALIDATOR_PATH = REPO_ROOT / "scripts" / "legal_ontology" / "validate_route_decisions_v1.py"
REQUIRED_STATUSES = {"possible", "review_required", "blocked", "missing_facts"}
ALLOWED_PACKET_TYPES = {
    "evidence_request",
    "legal_action_review",
    "finance_review",
    "contact_review",
    "monitoring_retry",
    "insolvency_recovery_review",
}
JsonScalar: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]


def load_json_object(path: Path) -> JsonObject:
    raw: JsonValue = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    return raw


def object_list(entry: JsonObject, field: str) -> list[JsonObject]:
    value = entry[field]
    assert isinstance(value, list)
    objects: list[JsonObject] = []
    for item in value:
        assert isinstance(item, dict)
        objects.append(item)
    return objects


def int_field(entry: JsonObject, field: str) -> int:
    value = entry[field]
    assert isinstance(value, int)
    return value


def string_list_field(entry: JsonObject, field: str) -> list[str]:
    value = entry[field]
    assert isinstance(value, list)
    strings: list[str] = []
    for item in value:
        assert isinstance(item, str)
        strings.append(item)
    return strings


def run_validator(decisions_path: Path = DECISIONS_PATH) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR_PATH),
            str(decisions_path),
            str(ROUTES_PATH),
            str(SOURCES_PATH),
            str(WORKFLOW_PATH),
            str(FINANCE_PATH),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_validator_accepts_route_decision_table_v1() -> None:
    # Given: the Todo 7 decision table and its route/source/workflow/finance dependencies.
    result = run_validator()

    # When: the validator checks cross-resource references and scoring metadata.
    assert result.returncode == 0

    # Then: every route has a deterministic advisory decision row.
    assert "PASS route_decisions recova-debt-collection-route-decisions@v1.0.0" in result.stdout
    assert "decisions=32" in result.stdout
    assert "score_components=" in result.stdout
    assert "reason_codes=" in result.stdout


def test_decision_resource_links_every_route_and_stays_advisory() -> None:
    # Given: the v1 route catalog and v1 decision table.
    decisions = load_json_object(DECISIONS_PATH)
    routes = load_json_object(ROUTES_PATH)

    # When: route and decision IDs are compared.
    decision_route_ids = {str(entry["route_id"]) for entry in object_list(decisions, "route_decisions")}
    route_ids = {str(entry["route_id"]) for entry in object_list(routes, "routes")}

    # Then: the table is complete, advisory-only, and uses known future action packet types.
    assert decision_route_ids == route_ids
    assert decisions["no_direct_execution"] is True
    assert decisions["direct_execution_allowed"] is False
    assert decisions["execution_semantics"] == "advisory_decision_support_only"
    status_catalog = {str(entry["status"]) for entry in object_list(decisions, "status_catalog")}
    assert status_catalog >= REQUIRED_STATUSES
    assert {
        str(entry["next_step_action_packet_type"])
        for entry in object_list(decisions, "route_decisions")
    } <= ALLOWED_PACKET_TYPES


def test_evaluator_returns_possible_missing_blocked_and_review_required() -> None:
    # Given: a route decision table loaded through the evaluator boundary.
    from trustgraph_legal.route_decisions import (
        RouteDecisionRequest,
        SourceReviewStatus,
        evaluate_route_decision,
        load_decision_table,
    )

    table = load_decision_table(DECISIONS_PATH)
    approved = (
        SourceReviewStatus(source_id="kr-law-l009290-m268837-a223", review_status="approved_static_v1"),
        SourceReviewStatus(source_id="kr-law-l009290-m268837-a229", review_status="approved_static_v1"),
        SourceReviewStatus(source_id="kr-law-l009290-m268837-a246", review_status="approved_static_v1"),
        SourceReviewStatus(source_id="kr-law-l010910-m268669-a12", review_status="approved_static_v1"),
    )

    # When: the bank account route has all required facts and approved sources.
    possible = evaluate_route_decision(
        table,
        RouteDecisionRequest(
            route_id="bank_account_attachment",
            workflow_state="execution_route_selection",
            fact_handles=("enforceable_title", "financial_account_hint"),
            legal_source_reviews=approved,
        ),
    ).to_json()

    # Then: it is possible, scored, sourced, and still non-executing.
    assert possible["status"] == "possible"
    assert int_field(possible, "priority_score") > 0
    assert possible["next_step_action_packet_type"] == "legal_action_review"
    assert possible["non_execution_semantics"] == "advisory_only_human_review_required"
    assert {str(reason["reason_code"]) for reason in object_list(possible, "reasons")} >= {"required_facts_present"}
    assert possible["source_refs"]

    # When: one required fact is absent.
    missing = evaluate_route_decision(
        table,
        RouteDecisionRequest(
            route_id="bank_account_attachment",
            workflow_state="execution_route_selection",
            fact_handles=("enforceable_title",),
            legal_source_reviews=approved,
        ),
    ).to_json()

    # Then: the missing handle is explicit.
    assert missing["status"] == "missing_facts"
    assert missing["missing_fact_handles"] == ["financial_account_hint"]

    # When: a StopGate-style blocker fact is present.
    blocked = evaluate_route_decision(
        table,
        RouteDecisionRequest(
            route_id="bank_account_attachment",
            workflow_state="execution_route_selection",
            fact_handles=("enforceable_title", "financial_account_hint", "insolvency_stay"),
            legal_source_reviews=approved,
        ),
    ).to_json()

    # Then: it becomes advisory blocked with traceable reason metadata.
    assert blocked["status"] == "blocked"
    assert "insolvency_stay" in string_list_field(blocked, "blocking_fact_handles")
    assert {str(reason["reason_code"]) for reason in object_list(blocked, "reasons")} >= {
        "discharge_proceeding_detected",
    }

    # When: a legal source review status is not approved.
    review_required = evaluate_route_decision(
        table,
        RouteDecisionRequest(
            route_id="bank_account_attachment",
            workflow_state="execution_route_selection",
            fact_handles=("enforceable_title", "financial_account_hint"),
            legal_source_reviews=(
                SourceReviewStatus(source_id="kr-law-l009290-m268837-a223", review_status="needs_legal_review"),
            ),
        ),
    ).to_json()

    # Then: legal-source uncertainty is review-required, not hidden in the score.
    assert review_required["status"] == "review_required"
    assert {str(reason["reason_code"]) for reason in object_list(review_required, "reasons")} >= {
        "domain_legal_source_unapproved",
    }


def test_validator_rejects_unknown_route_ref(tmp_path: Path) -> None:
    # Given: a generated decision copy with an unknown route id.
    decisions = load_json_object(DECISIONS_PATH)
    first_decision = object_list(decisions, "route_decisions")[0]
    first_decision["route_id"] = "unknown_route"
    invalid_path = tmp_path / "unknown-route-decisions.json"
    invalid_path.write_text(json.dumps(decisions, ensure_ascii=False), encoding="utf-8")

    # When: the validator checks the generated copy.
    result = run_validator(invalid_path)

    # Then: it rejects the missing route reference.
    assert result.returncode != 0
    assert "unknown route_id unknown_route" in result.stderr


def test_validator_rejects_untraceable_reason(tmp_path: Path) -> None:
    # Given: a generated decision copy with a reason stripped of source refs.
    decisions = load_json_object(DECISIONS_PATH)
    first_decision = object_list(decisions, "route_decisions")[0]
    reasons = object_list(first_decision, "reason_templates")
    reasons[0]["source_refs"] = []
    invalid_path = tmp_path / "untraceable-reason-decisions.json"
    invalid_path.write_text(json.dumps(decisions, ensure_ascii=False), encoding="utf-8")

    # When: the validator checks the generated copy.
    result = run_validator(invalid_path)

    # Then: it requires every score/reason to stay source-traceable.
    assert result.returncode != 0
    assert "source_refs must be a non-empty string list" in result.stderr
