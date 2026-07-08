from __future__ import annotations

import json
from pathlib import Path

from trustgraph_legal.debtor_context_types import JsonObject, JsonValue
from trustgraph_legal.workflow_judgments import WorkflowJudgmentRequest


def evidence_request(evidence_checkpoint: JsonObject) -> WorkflowJudgmentRequest:
    return WorkflowJudgmentRequest(
        claim_domain_payload=payload(),
        evidence_checkpoint=evidence_checkpoint,
        finance_bridge=finance_ready(),
        legal_checkpoints=legal_clear(),
        playbook_path=Path("resources/workflows/debt_collection_operator_playbook_v1.json"),
    )


def title_request() -> WorkflowJudgmentRequest:
    return WorkflowJudgmentRequest(
        claim_domain_payload=payload(),
        evidence_checkpoint=evidence_clear(),
        finance_bridge=finance_ready(),
        legal_checkpoints=missing_title_checkpoints(),
        playbook_path=Path("resources/workflows/debt_collection_operator_playbook_v1.json"),
    )


def route_request(route_decisions: tuple[JsonObject, ...], claim_payload: JsonObject | None = None) -> WorkflowJudgmentRequest:
    return WorkflowJudgmentRequest(
        claim_domain_payload=claim_payload or payload(),
        route_decisions=route_decisions,
        evidence_checkpoint=evidence_clear(),
        finance_bridge=finance_ready(),
        legal_checkpoints=legal_clear(),
        playbook_path=Path("resources/workflows/debt_collection_operator_playbook_v1.json"),
    )


def unsafe_guardrail_request() -> WorkflowJudgmentRequest:
    return WorkflowJudgmentRequest(
        claim_domain_payload={
            **payload(fact("fact:asset", "bank_account_hint", True)),
            "source_text": "raw debtor statement must not be echoed",
        },
        evidence_checkpoint={
            "schema_version": "trustgraph-evidence-quality-check/v1",
            "decision": "pass",
            "raw_excerpt": "do not include me",
            "source_text": "do not include me either",
            "workflow_signals": [],
        },
        finance_bridge={
            **finance_ready(),
            "collectable_balance_authority": True,
            "remaining_balance": {"currency": "KRW", "amount": 1000},
        },
        legal_checkpoints={
            **legal_clear(),
            "source_text": "legal clearance free text must not clear gates",
        },
        playbook_path=Path("resources/workflows/debt_collection_operator_playbook_v1.json"),
    )


def payload(*facts: JsonObject) -> JsonObject:
    return {
        "schema_version": "trustgraph-claim-domain-adapter/v1",
        "claim_root": {"claim_ref": "claim:workflow-judgment"},
        "fact_handles": list(facts),
        "source_refs": ["fixture:claim#root"],
        "pii_profile": {"raw_text_included": False, "source_text_included": False},
    }


def fact(fact_id: str, fact_handle: str, object_value: JsonValue) -> JsonObject:
    return {
        "fact_id": fact_id,
        "fact_handle": fact_handle,
        "object_value": object_value,
        "source_refs": ["fixture:{}#L1".format(fact_id)],
    }


def evidence_clear() -> JsonObject:
    return {
        "schema_version": "trustgraph-evidence-quality-check/v1",
        "decision": "pass",
        "workflow_signals": [],
        "review_items": [],
        "hold_items": [],
        "pii_profile": {"raw_text_included": False, "source_text_included": False},
    }


def finance_ready() -> JsonObject:
    return {
        "schema_version": "trustgraph-finance-workflow-bridge/v1",
        "workflow_review_status": "finance_fixture_advisory_ready",
        "advisory_readiness": "fixture_finance_can_support_workflow_review",
        "signals": [],
        "workflow_flags": {
            "finance_reconciliation_needed": False,
            "disputed_balance_hold": False,
            "unsupported_interest_review": False,
            "payment_allocation_review": False,
        },
        "source_refs": [],
        "collectable_balance_authority": False,
        "non_execution_semantics": "fixture_calculation_only_not_authoritative_balance",
    }


def legal_clear() -> JsonObject:
    return {
        "schema_version": "trustgraph-legal-workflow-checkpoints/v1",
        "overall_status": "clear",
        "ready_for_enforcement_advisory": True,
        "checkpoints": [],
        "review_items": [],
        "pii_profile": {"raw_text_included": False, "source_text_included": False},
        "non_execution_semantics": "advisory_only_human_review_required",
    }


def missing_title_checkpoints() -> JsonObject:
    checkpoint_id = "enforcement_title"
    reason_codes: list[JsonValue] = ["missing_enforcement_title"]
    source_refs: list[JsonValue] = ["fixture:legal#title"]
    checkpoint: JsonObject = {
        "checkpoint_id": checkpoint_id,
        "status": "missing",
        "workflow_gate": "title_acquisition_loop",
        "reason_codes": reason_codes,
        "source_refs": source_refs,
        "blocks_enforcement_readiness": False,
    }
    review_item: JsonObject = {
        "code": checkpoint_id,
        "category": "legal_workflow_checkpoint",
        "workflow_gate": "title_acquisition_loop",
        "reason_codes": reason_codes,
        "review_status": "human_review_required",
        "source_refs": source_refs,
    }
    checkpoints: list[JsonValue] = [checkpoint]
    review_items: list[JsonValue] = [review_item]
    payload: JsonObject = {
        "schema_version": "trustgraph-legal-workflow-checkpoints/v1",
        "overall_status": "hold",
        "ready_for_enforcement_advisory": False,
        "checkpoints": checkpoints,
        "review_items": review_items,
    }
    return payload


def route_decision(
    status: str,
    *,
    missing_fact_handles: tuple[str, ...] = (),
    reason_code: str,
) -> JsonObject:
    source_refs = ("fixture:route#{}".format(reason_code),)
    return {
        "schema_version": "trustgraph-route-decision-result/v1",
        "route_id": "bank_account_attachment",
        "status": status,
        "priority_score": 80 if status == "possible" else 30,
        "missing_fact_handles": list(missing_fact_handles),
        "blocking_fact_handles": [],
        "reasons": [
            {
                "reason_code": reason_code,
                "message": "fixture route reason",
                "source_refs": list(source_refs),
            },
        ],
        "source_refs": list(source_refs),
        "next_step_action_packet_type": "bank_account_attachment_packet",
        "non_execution_semantics": "advisory_only_human_review_required",
    }


def signal(code: str, category: str, source_refs: tuple[str, ...]) -> JsonObject:
    return {
        "code": code,
        "category": category,
        "review_status": "human_review_required",
        "source_refs": list(source_refs),
    }


def action_types(judgment: JsonObject) -> list[str]:
    actions = judgment["next_best_actions"]
    assert isinstance(actions, list)
    return [str(action["action_type"]) for action in actions if isinstance(action, dict)]


def string_list(entry: JsonObject, field: str) -> list[str]:
    value = entry[field]
    assert isinstance(value, list)
    strings: list[str] = []
    for item in value:
        assert isinstance(item, str)
        strings.append(item)
    return strings


def reason_codes(judgment: JsonObject) -> list[str]:
    reasons = judgment["reasons"]
    assert isinstance(reasons, list)
    codes: list[str] = []
    for reason in reasons:
        assert isinstance(reason, dict)
        code = reason["reason_code"]
        assert isinstance(code, str)
        codes.append(code)
    return codes


def encoded_without_unsafe_fields(judgment: JsonObject) -> bool:
    encoded = json.dumps(judgment, ensure_ascii=False)
    return (
        '"raw_excerpt":' not in encoded
        and '"source_text":' not in encoded
        and '"raw_text":' not in encoded
        and '"debtor_contact_payload":' not in encoded
        and '"filing_destination":' not in encoded
        and '"court_destination":' not in encoded
    )
