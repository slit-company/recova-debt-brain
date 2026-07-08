from __future__ import annotations

from trustgraph_legal.debtor_context_types import JsonObject, JsonValue
from trustgraph_legal.workflow_judgments import WorkflowJudgmentRequest
from tests.utils.claim_domain_pipeline_support import Scenario, adapter_payload
from tests.unit.legal_ontology.workflow_judgment_helpers import (
    evidence_clear,
    finance_ready,
    legal_clear,
    route_request,
    route_decision,
    signal,
)


def scenario_workflow_request(scenario: Scenario) -> WorkflowJudgmentRequest:
    requests = {
        "premature_litigation_review": _legal_gate_request(
            scenario,
            "legal_precondition_review",
            "missing_service_finality_execution_clause_proof",
        ),
        "evidence_completion_loop": WorkflowJudgmentRequest(
            claim_domain_payload=adapter_payload(scenario),
            route_decisions=(route_decision("possible", reason_code="required_facts_present"),),
            evidence_checkpoint={
                "schema_version": "trustgraph-evidence-quality-check/v1",
                "decision": "review_required",
                "workflow_signals": [
                    signal("missing_provenance", "evidence", ("fixture:evidence_completion_loop#summary",)),
                ],
                "pii_profile": {"raw_text_included": False, "source_text_included": False},
            },
            finance_bridge=finance_ready(),
            legal_checkpoints=legal_clear(),
        ),
        "title_acquisition_loop": _legal_gate_request(
            scenario,
            "title_acquisition_loop",
            "missing_enforcement_title",
        ),
        "asset_discovery_loop": route_request(
            (
                route_decision(
                    "missing_facts",
                    missing_fact_handles=("financial_account_hint",),
                    reason_code="required_fact_missing",
                ),
            ),
            adapter_payload(scenario),
        ),
        "enforcement_ready_review": route_request(
            (route_decision("possible", reason_code="required_facts_present"),),
            adapter_payload(scenario),
        ),
        "monitoring_low_yield": route_request(
            (route_decision("missing_facts", reason_code="asset_signal_missing_or_low_yield"),),
            adapter_payload(scenario),
        ),
        "finance_reconciliation_hold": WorkflowJudgmentRequest(
            claim_domain_payload=adapter_payload(scenario),
            route_decisions=(route_decision("possible", reason_code="required_facts_present"),),
            evidence_checkpoint=evidence_clear(),
            finance_bridge=_finance_review_bridge(),
            legal_checkpoints=legal_clear(),
        ),
        "insolvency_protected_asset_hold": _legal_gate_request(
            scenario,
            "protected_asset_review_hold",
            "discharge_proceeding_detected",
        ),
    }
    return requests[scenario.scenario_id]


def _legal_gate_request(scenario: Scenario, gate: str, reason_code: str) -> WorkflowJudgmentRequest:
    reason_codes: list[JsonValue] = [reason_code]
    source_refs: list[JsonValue] = ["fixture:{}#legal-checkpoint".format(scenario.scenario_id)]
    checkpoint: JsonObject = {
        "checkpoint_id": "fixture_{}".format(scenario.scenario_id),
        "status": "missing" if gate != "protected_asset_review_hold" else "blocked",
        "workflow_gate": gate,
        "reason_codes": reason_codes,
        "source_refs": source_refs,
        "blocks_enforcement_readiness": gate == "protected_asset_review_hold",
    }
    review_item: JsonObject = {
        "code": checkpoint["checkpoint_id"],
        "category": "legal_workflow_checkpoint",
        "workflow_gate": gate,
        "reason_codes": reason_codes,
        "review_status": "human_review_required",
        "source_refs": source_refs,
    }
    checkpoints: list[JsonValue] = [checkpoint]
    review_items: list[JsonValue] = [review_item]
    legal_checkpoints: JsonObject = {
        "schema_version": "trustgraph-legal-workflow-checkpoints/v1",
        "overall_status": "hold",
        "ready_for_enforcement_advisory": False,
        "checkpoints": checkpoints,
        "review_items": review_items,
    }
    return WorkflowJudgmentRequest(
        claim_domain_payload=adapter_payload(scenario),
        route_decisions=(route_decision("missing_facts", reason_code="required_fact_missing"),),
        evidence_checkpoint=evidence_clear(),
        finance_bridge=finance_ready(),
        legal_checkpoints=legal_checkpoints,
    )


def _finance_review_bridge() -> JsonObject:
    return {
        "schema_version": "trustgraph-finance-workflow-bridge/v1",
        "workflow_review_status": "finance_review_required",
        "advisory_readiness": "finance_reconciliation_required_before_route_readiness",
        "signals": [
            {
                "signal_code": "payment_allocation_review",
                "review_code": "payment_allocation_conflict",
                "category": "finance",
                "reason": "fixture payment allocation conflict",
                "remediation_loop": "finance_reconciliation_loop",
                "review_status": "human_review_required",
                "workflow_hold": True,
                "source_refs": ["fixture:finance_reconciliation_hold#finance"],
            },
        ],
        "workflow_flags": {
            "finance_reconciliation_needed": False,
            "disputed_balance_hold": False,
            "unsupported_interest_review": False,
            "payment_allocation_review": True,
        },
        "source_refs": ["fixture:finance_reconciliation_hold#finance"],
        "collectable_balance_authority": False,
        "non_execution_semantics": "fixture_calculation_only_not_authoritative_balance",
    }
