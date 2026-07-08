from __future__ import annotations

from dataclasses import dataclass

from trustgraph_legal.debtor_context_types import JsonObject, JsonValue
from trustgraph_legal.evidence_quality import evaluate_evidence_quality
from trustgraph_legal.finance_review_bridge import FINANCE_REVIEW_CODE_TO_WORKFLOW_SIGNAL
from trustgraph_legal.workflow_judgments import WorkflowJudgmentRequest, evaluate_workflow_judgment

NON_EXECUTION_SEMANTICS = "advisory_only_human_review_required"


@dataclass(frozen=True, slots=True)
class DomainWorkflowRequest:
    claim_domain_payload: JsonObject
    route_decisions: tuple[JsonObject, ...]
    finance_review_codes: tuple[str, ...]
    review_items: tuple[JsonObject, ...]


@dataclass(frozen=True, slots=True)
class DomainWorkflowOutput:
    workflow_judgment: JsonObject
    operator_next_steps: tuple[JsonObject, ...]


def build_domain_workflow_output(request: DomainWorkflowRequest) -> DomainWorkflowOutput:
    workflow_judgment = evaluate_workflow_judgment(
        WorkflowJudgmentRequest(
            claim_domain_payload=request.claim_domain_payload,
            route_decisions=request.route_decisions,
            evidence_checkpoint=_evidence_checkpoint(request.claim_domain_payload),
            finance_bridge=_finance_bridge(request),
            legal_checkpoints=_legal_checkpoints(request.claim_domain_payload),
        ),
    )
    return DomainWorkflowOutput(workflow_judgment, _operator_next_steps(workflow_judgment))


def _evidence_checkpoint(payload: JsonObject) -> JsonObject:
    explicit = _support_object(payload, "evidence_checkpoint")
    if explicit:
        return explicit
    return evaluate_evidence_quality(payload).to_json()


def _finance_bridge(request: DomainWorkflowRequest) -> JsonObject:
    explicit = _support_object(request.claim_domain_payload, "finance_bridge")
    if explicit:
        return explicit
    return _finance_workflow_bridge(request.finance_review_codes, request.review_items)


def _legal_checkpoints(payload: JsonObject) -> JsonObject | None:
    explicit = _support_object(payload, "legal_checkpoints")
    if explicit:
        return explicit
    return None


def _finance_workflow_bridge(finance_review_codes: tuple[str, ...], review_items: tuple[JsonObject, ...]) -> JsonObject:
    signals = tuple(_finance_workflow_signal(code, review_items) for code in finance_review_codes)
    source_refs = _unique(tuple(source_ref for signal in signals for source_ref in _strings(signal.get("source_refs"))))
    return {
        "schema_version": "trustgraph-finance-workflow-bridge/v1",
        "workflow_review_status": "finance_review_required" if signals else "finance_fixture_advisory_ready",
        "advisory_readiness": _finance_advisory_readiness(bool(signals)),
        "signals": list(signals),
        "workflow_flags": {
            "finance_reconciliation_needed": _has_signal(signals, "finance_reconciliation_needed"),
            "disputed_balance_hold": _has_signal(signals, "disputed_balance_hold"),
            "unsupported_interest_review": _has_signal(signals, "unsupported_interest_review"),
            "payment_allocation_review": _has_signal(signals, "payment_allocation_review"),
        },
        "source_refs": list(source_refs),
        "collectable_balance_authority": False,
        "non_execution_semantics": "fixture_calculation_only_not_authoritative_balance",
        "pii_profile": {"raw_text_included": False, "source_text_included": False},
    }


def _finance_workflow_signal(code: str, review_items: tuple[JsonObject, ...]) -> JsonObject:
    signal_code = FINANCE_REVIEW_CODE_TO_WORKFLOW_SIGNAL.get(code, "finance_reconciliation_needed")
    return {
        "signal_code": signal_code,
        "review_code": code,
        "category": "finance",
        "reason": "finance review code requires workflow hold",
        "remediation_loop": _finance_remediation_loop(signal_code),
        "review_status": "human_review_required",
        "workflow_hold": True,
        "source_refs": list(_review_item_source_refs(code, review_items)),
    }


def _finance_advisory_readiness(has_signals: bool) -> str:
    if has_signals:
        return "finance_reconciliation_required_before_route_readiness"
    return "fixture_finance_can_support_workflow_review"


def _has_signal(signals: tuple[JsonObject, ...], signal_code: str) -> bool:
    return any(_text(signal.get("signal_code")) == signal_code for signal in signals)


def _finance_remediation_loop(signal_code: str) -> str:
    loops = {
        "payment_allocation_review": "finance_reconciliation_loop",
        "disputed_balance_hold": "disputed_balance_review_loop",
        "unsupported_interest_review": "interest_basis_review_loop",
        "finance_reconciliation_needed": "finance_source_reconciliation_loop",
    }
    return loops.get(signal_code, "finance_source_reconciliation_loop")


def _review_item_source_refs(code: str, review_items: tuple[JsonObject, ...]) -> tuple[str, ...]:
    refs: list[str] = []
    for item in review_items:
        if _text(item.get("code")) == code:
            refs.extend(_strings(item.get("source_refs")))
    return _unique(tuple(refs))


def _operator_next_steps(workflow_judgment: JsonObject) -> tuple[JsonObject, ...]:
    steps: list[JsonObject] = []
    for action in _json_objects(workflow_judgment.get("next_best_actions")):
        steps.append(
            {
                "action_type": _text(action.get("action_type")),
                "current_stage": _text(action.get("stage")) or _text(workflow_judgment.get("current_stage")),
                "remediation_loop": _text(workflow_judgment.get("remediation_loop")),
                "missing_inputs": list(_strings(workflow_judgment.get("missing_inputs"))),
                "review_status": _text(action.get("review_status")) or "human_review_required",
                "source_refs": list(_json_values(action.get("source_refs"))),
                "non_execution_semantics": NON_EXECUTION_SEMANTICS,
            }
        )
    return tuple(steps)


def _json_objects(value: JsonValue) -> tuple[JsonObject, ...]:
    return tuple(item for item in value if isinstance(item, dict)) if isinstance(value, list) else ()


def _json_object(value: JsonValue) -> JsonObject:
    return value if isinstance(value, dict) else {}


def _support_object(payload: JsonObject, key: str) -> JsonObject:
    explicit = _json_object(payload.get(key))
    if explicit:
        return explicit
    workflow_support = _json_object(payload.get("workflow_support"))
    return _json_object(workflow_support.get(key))


def _json_values(value: JsonValue) -> tuple[JsonValue, ...]:
    return tuple(value) if isinstance(value, list) else ()


def _strings(value: JsonValue) -> tuple[str, ...]:
    return tuple(item for item in value if isinstance(item, str) and item) if isinstance(value, list) else ()


def _text(value: JsonValue) -> str:
    return value if isinstance(value, str) else ""


def _unique(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))
