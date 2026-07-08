from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from trustgraph_legal.finance_claims import (
    FIXTURE_REVIEW_STATUS,
    ClaimFinanceCalculation,
    FinanceReviewItem,
    JsonObject,
)

BRIDGE_SCHEMA_VERSION: Final = "trustgraph-finance-workflow-bridge/v1"
NON_EXECUTION_SEMANTICS: Final = "fixture_calculation_only_not_authoritative_balance"
FINANCE_FIXTURE_READY: Final = "finance_fixture_advisory_ready"
FINANCE_REVIEW_REQUIRED: Final = "finance_review_required"
FIXTURE_ADVISORY_READINESS: Final = "fixture_finance_can_support_workflow_review"
RECONCILIATION_READINESS: Final = "finance_reconciliation_required_before_route_readiness"
FINANCE_REVIEW_CODE_TO_WORKFLOW_SIGNAL: Final[Mapping[str, str]] = MappingProxyType(
    {
        "missing_source_ref": "finance_reconciliation_needed",
        "statutory_or_complex_interest": "unsupported_interest_review",
        "payment_allocation_conflict": "payment_allocation_review",
        "disputed_amount": "disputed_balance_hold",
    }
)


@dataclass(frozen=True, slots=True)
class FinanceWorkflowSignal:
    signal_code: str
    review_code: str
    reason: str
    remediation_loop: str
    source_refs: tuple[str, ...]
    workflow_hold: bool = True

    def to_json(self) -> JsonObject:
        return {
            "signal_code": self.signal_code,
            "review_code": self.review_code,
            "category": "finance",
            "reason": self.reason,
            "remediation_loop": self.remediation_loop,
            "review_status": "human_review_required",
            "workflow_hold": self.workflow_hold,
            "source_refs": list(self.source_refs),
        }


@dataclass(frozen=True, slots=True)
class FinanceWorkflowBridge:
    claim_id: str
    workflow_review_status: str
    advisory_readiness: str
    signals: tuple[FinanceWorkflowSignal, ...]
    source_refs: tuple[str, ...]

    def to_json(self) -> JsonObject:
        return {
            "schema_version": BRIDGE_SCHEMA_VERSION,
            "claim_id": self.claim_id,
            "workflow_review_status": self.workflow_review_status,
            "advisory_readiness": self.advisory_readiness,
            "signals": [signal.to_json() for signal in self.signals],
            "workflow_flags": {
                "finance_reconciliation_needed": any(signal.signal_code == "finance_reconciliation_needed" for signal in self.signals),
                "disputed_balance_hold": any(signal.signal_code == "disputed_balance_hold" for signal in self.signals),
                "unsupported_interest_review": any(signal.signal_code == "unsupported_interest_review" for signal in self.signals),
                "payment_allocation_review": any(signal.signal_code == "payment_allocation_review" for signal in self.signals),
            },
            "source_refs": list(self.source_refs),
            "collectable_balance_authority": False,
            "non_execution_semantics": NON_EXECUTION_SEMANTICS,
            "pii_profile": {"raw_text_included": False, "source_text_included": False},
        }


def bridge_finance_review_to_workflow(calculation: ClaimFinanceCalculation) -> FinanceWorkflowBridge:
    signals = tuple(_workflow_signal(item) for item in calculation.review_items)
    source_refs = _source_refs(signals)
    fixture_ready = calculation.balance_review_status == FIXTURE_REVIEW_STATUS
    return FinanceWorkflowBridge(
        claim_id=calculation.claim_id,
        workflow_review_status=FINANCE_FIXTURE_READY if fixture_ready else FINANCE_REVIEW_REQUIRED,
        advisory_readiness=FIXTURE_ADVISORY_READINESS if fixture_ready else RECONCILIATION_READINESS,
        signals=() if fixture_ready else signals,
        source_refs=source_refs,
    )


def _workflow_signal(item: FinanceReviewItem) -> FinanceWorkflowSignal:
    signal_code = FINANCE_REVIEW_CODE_TO_WORKFLOW_SIGNAL.get(item.code, "finance_reconciliation_needed")
    return FinanceWorkflowSignal(
        signal_code=signal_code,
        review_code=item.code,
        reason=item.message,
        remediation_loop=_remediation_loop(signal_code),
        source_refs=item.source_refs,
    )


def _remediation_loop(signal_code: str) -> str:
    remediation_loops: Final[Mapping[str, str]] = MappingProxyType(
        {
            "payment_allocation_review": "finance_reconciliation_loop",
            "disputed_balance_hold": "disputed_balance_review_loop",
            "unsupported_interest_review": "interest_basis_review_loop",
            "finance_reconciliation_needed": "finance_source_reconciliation_loop",
        }
    )
    return remediation_loops.get(signal_code, "finance_source_reconciliation_loop")


def _source_refs(signals: tuple[FinanceWorkflowSignal, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(source_ref for signal in signals for source_ref in signal.source_refs))
