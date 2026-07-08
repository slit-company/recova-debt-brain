from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from scripts.legal_ontology.domain_sources_v1_common import load_json
from trustgraph_legal.debtor_context_types import JsonObject, JsonValue

SCHEMA_VERSION: Final = "trustgraph-collection-workflow-judgment/v1"
PLAYBOOK_PATH: Final = Path("resources/workflows/debt_collection_operator_playbook_v1.json")
NON_EXECUTION_SEMANTICS: Final = "advisory_only_human_review_required"
ASSET_FACT_SUFFIXES: Final = ("_asset", "_hint")
LOW_YIELD_HANDLES: Final = frozenset({"low_yield_collection_signal", "low_yield_asset_signal"})
ASSET_REASON_CODES: Final = frozenset({"asset_signal_missing_or_low_yield"})
FINANCE_HOLD_FLAGS: Final = frozenset(
    {
        "finance_reconciliation_needed",
        "disputed_balance_hold",
        "unsupported_interest_review",
        "payment_allocation_review",
    }
)
UNSAFE_REVIEW_ITEM_KEYS: Final = frozenset(
    {
        "body",
        "body_text",
        "collectable_balance_authority",
        "court_destination_payload",
        "debtor_contact_payload",
        "excerpt",
        "filing_destination",
        "raw_excerpt",
        "raw_text",
        "remaining_balance",
        "source_path",
        "source_text",
    }
)


@dataclass(frozen=True, slots=True)
class WorkflowJudgmentRequest:
    claim_domain_payload: JsonObject
    route_decisions: tuple[JsonObject, ...] = ()
    evidence_checkpoint: JsonObject | None = None
    finance_bridge: JsonObject | None = None
    legal_checkpoints: JsonObject | None = None
    playbook_path: Path = PLAYBOOK_PATH


@dataclass(frozen=True, slots=True)
class StageSpec:
    stage_id: str
    posture: str
    next_action_types: tuple[str, ...]
    premature_action_reasons: tuple[str, ...]
    missing_inputs: tuple[str, ...]
    remediation_loops: tuple[str, ...]
    source_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StageDecision:
    stage_id: str
    action_type: str
    premature_action: str
    missing_input: str
    remediation_loop: str
    reason_code: str


def evaluate_workflow_judgment(request: WorkflowJudgmentRequest) -> JsonObject:
    stages = _stage_specs(request.playbook_path)
    facts = _fact_handles(request.claim_domain_payload)
    decision = _stage_decision(request, facts)
    stage = stages[decision.stage_id]
    review_items = _review_items(request)
    source_refs = _source_refs(request, stage, decision)
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": stage.stage_id,
        "current_stage": stage.stage_id,
        "posture": stage.posture,
        "operational_posture": stage.posture,
        "next_best_actions": [_action(decision.action_type, stage, source_refs)],
        "premature_actions": _selected_value(decision.premature_action),
        "missing_inputs": _selected_value(decision.missing_input),
        "review_items": review_items,
        "remediation_loop": decision.remediation_loop,
        "reasons": [_reason(decision.reason_code, source_refs)],
        "source_refs": source_refs,
        "pii_profile": _pii_profile(),
        "non_execution_semantics": NON_EXECUTION_SEMANTICS,
    }


def _stage_specs(path: Path) -> dict[str, StageSpec]:
    root = load_json(path)
    stages: dict[str, StageSpec] = {}
    for item in _objects(root.get("stages")):
        stage_id = _text(item.get("stage_id"))
        if stage_id:
            stages[stage_id] = StageSpec(
                stage_id=stage_id,
                posture=_text(item.get("operational_posture")),
                next_action_types=_strings(item.get("next_action_types")),
                premature_action_reasons=_strings(item.get("premature_action_reasons")),
                missing_inputs=_strings(item.get("required_checkpoint_inputs")),
                remediation_loops=_strings(item.get("remediation_loops")),
                source_refs=_strings(item.get("source_refs")),
            )
    return stages


def _stage_decision(request: WorkflowJudgmentRequest, facts: frozenset[str]) -> StageDecision:
    evidence = request.evidence_checkpoint or {}
    finance = request.finance_bridge or {}
    legal = request.legal_checkpoints or {}
    if _text(evidence.get("decision")) in {"review_required", "hold"}:
        return StageDecision("evidence_completion", "collect_missing_evidence", "evidence_missing_or_conflicted", "evidence_quality", "evidence_completion_loop", "evidence_quality_review")
    if _finance_hold(finance):
        return StageDecision("evidence_completion", "reconcile_finance", "finance_reconciliation_needed", "finance_review", "finance_reconciliation_loop", "finance_workflow_hold")
    legal_decision = _legal_stage_decision(legal)
    if legal_decision is not None:
        return legal_decision
    if _low_yield(facts, request.route_decisions):
        return StageDecision("monitoring", "monitor_retry", "asset_signal_missing_or_low_yield", "asset_signal", "low_yield_monitoring_loop", "asset_signal_missing_or_low_yield")
    if _asset_missing(request.route_decisions):
        return StageDecision("asset_discovery", "enrich_asset_signals", "asset_signal_missing_or_low_yield", "asset_signal", "asset_discovery_loop", "asset_signal_missing")
    if _route_possible(request.route_decisions):
        return StageDecision("enforcement_ready", "prepare_advisory_packet", "", "", "legal_precondition_review_loop", "workflow_preconditions_ready")
    return StageDecision("execution_route_selection", "select_execution_route", "legal_source_review_needed", "route_decision", "legal_precondition_review_loop", "route_review_required")


def _legal_stage_decision(legal: JsonObject) -> StageDecision | None:
    for checkpoint in _objects(legal.get("checkpoints")):
        gate = _text(checkpoint.get("workflow_gate"))
        if gate == "title_acquisition_loop":
            return StageDecision("title_acquisition", "acquire_or_confirm_title", "enforcement_title_missing", "enforcement_title", "title_acquisition_loop", _first_reason(checkpoint))
        if gate in {"legal_precondition_review", "limitation_review_hold", "legal_source_review_hold"}:
            return StageDecision("title_acquisition", "confirm_service_finality_execution_clause", "service_finality_execution_clause_missing", "legal_preconditions", "legal_precondition_review_loop", _first_reason(checkpoint))
        if gate == "protected_asset_review_hold":
            return StageDecision("insolvency_protected_asset_review", "insolvency_protected_asset_review", "protected_asset_or_insolvency_signal", "stopgate", "protected_asset_insolvency_hold", _first_reason(checkpoint))
        if gate not in {"none", ""}:
            return StageDecision("execution_route_selection", "select_execution_route", "legal_source_review_needed", "legal_preconditions", "legal_precondition_review_loop", _first_reason(checkpoint))
    return None


def _finance_hold(finance: JsonObject) -> bool:
    flags = _object(finance.get("workflow_flags"))
    return any(flags.get(flag) is True for flag in FINANCE_HOLD_FLAGS) or bool(_objects(finance.get("signals")))


def _low_yield(facts: frozenset[str], route_decisions: tuple[JsonObject, ...]) -> bool:
    return bool(facts & LOW_YIELD_HANDLES) or any(_reason_codes(route) & ASSET_REASON_CODES for route in route_decisions)


def _asset_missing(route_decisions: tuple[JsonObject, ...]) -> bool:
    for route in route_decisions:
        missing = _strings(route.get("missing_fact_handles"))
        if any(handle.endswith(ASSET_FACT_SUFFIXES) for handle in missing):
            return True
    return False


def _route_possible(route_decisions: tuple[JsonObject, ...]) -> bool:
    return any(_text(route.get("status")) == "possible" for route in route_decisions)


def _review_items(request: WorkflowJudgmentRequest) -> list[JsonValue]:
    items: list[JsonValue] = []
    for surface in (request.evidence_checkpoint, request.finance_bridge, request.legal_checkpoints):
        if surface is not None:
            items.extend(_safe_items(surface.get("workflow_signals")))
            items.extend(_safe_items(surface.get("signals")))
            items.extend(_safe_items(surface.get("review_items")))
            items.extend(_safe_items(surface.get("hold_items")))
    return items


def _safe_items(value: JsonValue) -> list[JsonValue]:
    items: list[JsonValue] = []
    for item in _objects(value):
        items.append(_safe_value(item))
    return items


def _safe_value(value: JsonValue) -> JsonValue:
    if isinstance(value, dict):
        return {key: _safe_value(field) for key, field in value.items() if key not in UNSAFE_REVIEW_ITEM_KEYS}
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    return value


def _source_refs(request: WorkflowJudgmentRequest, stage: StageSpec, decision: StageDecision) -> list[JsonValue]:
    refs = (
        *_refs_from_value(request.claim_domain_payload.get("source_refs")),
        *_refs_from_surface(request.evidence_checkpoint),
        *_refs_from_surface(request.finance_bridge),
        *_refs_from_surface(request.legal_checkpoints),
        *_refs_from_routes(request.route_decisions),
        "playbook:stage:{}".format(decision.stage_id),
    )
    stage_refs = stage.source_refs if not refs else ()
    return list(dict.fromkeys((*refs, *stage_refs)))


def _refs_from_surface(surface: JsonObject | None) -> tuple[str, ...]:
    if surface is None:
        return ()
    refs: list[str] = []
    refs.extend(_refs_from_value(surface.get("source_refs")))
    for field in ("workflow_signals", "signals", "review_items", "hold_items", "checkpoints"):
        for item in _objects(surface.get(field)):
            refs.extend(_refs_from_value(item.get("source_refs")))
    return tuple(refs)


def _refs_from_routes(route_decisions: tuple[JsonObject, ...]) -> tuple[str, ...]:
    refs: list[str] = []
    for route in route_decisions:
        refs.extend(_refs_from_value(route.get("source_refs")))
        for reason in _objects(route.get("reasons")):
            refs.extend(_refs_from_value(reason.get("source_refs")))
    return tuple(refs)


def _refs_from_value(value: JsonValue) -> tuple[str, ...]:
    refs: list[str] = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str) and item:
                refs.append(item)
            elif isinstance(item, dict):
                source_ref = _text(item.get("source_ref"))
                if source_ref:
                    refs.append(source_ref)
    return tuple(refs)


def _reason_codes(route: JsonObject) -> frozenset[str]:
    return frozenset(_text(reason.get("reason_code")) for reason in _objects(route.get("reasons")))


def _first_reason(item: JsonObject) -> str:
    codes = _strings(item.get("reason_codes"))
    return codes[0] if codes else "legal_workflow_review"


def _fact_handles(payload: JsonObject) -> frozenset[str]:
    handles = {_text(item.get("fact_handle")) or _text(item.get("predicate")) for item in _objects(payload.get("fact_handles"))}
    return frozenset(handle for handle in handles if handle)


def _action(action_type: str, stage: StageSpec, source_refs: list[JsonValue]) -> JsonObject:
    return {
        "action_type": action_type,
        "stage": stage.stage_id,
        "review_status": "human_review_required",
        "source_refs": source_refs,
        "non_execution_semantics": NON_EXECUTION_SEMANTICS,
    }


def _reason(reason_code: str, source_refs: list[JsonValue]) -> JsonObject:
    return {
        "reason_code": reason_code,
        "review_status": "human_review_required",
        "source_refs": source_refs,
    }


def _selected_value(selected: str) -> list[JsonValue]:
    if selected:
        return [selected]
    return []


def _pii_profile() -> JsonObject:
    return {
        "raw_text_included": False,
        "source_text_included": False,
        "debtor_contact_payload_included": False,
        "filing_destination_included": False,
        "court_destination_payload_included": False,
    }


def _objects(value: JsonValue) -> tuple[JsonObject, ...]:
    return tuple(item for item in value if isinstance(item, dict)) if isinstance(value, list) else ()


def _object(value: JsonValue) -> JsonObject:
    return value if isinstance(value, dict) else {}


def _strings(value: JsonValue) -> tuple[str, ...]:
    return tuple(item for item in value if isinstance(item, str) and item) if isinstance(value, list) else ()


def _text(value: JsonValue) -> str:
    return value if isinstance(value, str) else ""
