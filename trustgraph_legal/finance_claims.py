from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Final, TypeAlias


JsonScalar: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]

CALCULATION_SCHEMA_VERSION: Final = "trustgraph-claim-finance-calculation/v1"
MODEL_VERSION: Final = "recova-claim-finance-model@v1.0.0"
FIXTURE_REVIEW_STATUS: Final = "calculated_fixture_only"
NEEDS_FINANCE_REVIEW: Final = "needs_finance_review"
EXPLICIT_RATE_BASIS: Final = "explicit_contract_rate"
EXPLICIT_ALLOCATION_STATUS: Final = "explicit_fixture_rule"
KRW: Final = "KRW"
PLACEHOLDER_SOURCE_REFS: Final = frozenset({"", "-", "missing", "n/a", "none", "null", "placeholder", "todo", "unknown"})


@dataclass(frozen=True, slots=True)
class MoneyComponent:
    component_id: str
    component_type: str
    amount: int
    source_refs: tuple[str, ...]
    currency: str = KRW

    def to_json(self) -> JsonObject:
        return {
            "component_id": self.component_id,
            "component_type": self.component_type,
            "currency": self.currency,
            "amount": self.amount,
            "source_refs": list(self.source_refs),
        }


@dataclass(frozen=True, slots=True)
class RatePeriod:
    component_type: str
    annual_rate_bps: int
    start_date: date
    end_date: date
    basis: str
    source_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Payment:
    payment_id: str
    amount: int
    paid_on: date
    source_refs: tuple[str, ...]
    currency: str = KRW


@dataclass(frozen=True, slots=True)
class PaymentAllocationRule:
    rule_id: str
    component_order: tuple[str, ...]
    review_status: str
    source_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FinanceRelationship:
    relationship_type: str
    status: str
    source_refs: tuple[str, ...]

    def to_json(self) -> JsonObject:
        return {
            "relationship_type": self.relationship_type,
            "status": self.status,
            "source_refs": list(self.source_refs),
        }


@dataclass(frozen=True, slots=True)
class FinanceReviewItem:
    code: str
    message: str
    source_refs: tuple[str, ...]

    def to_json(self) -> JsonObject:
        return {"code": self.code, "message": self.message, "source_refs": list(self.source_refs)}


@dataclass(frozen=True, slots=True)
class PaymentAllocation:
    payment_id: str
    applied: tuple[MoneyComponent, ...]
    unapplied_amount: int

    def to_json(self) -> JsonObject:
        return {
            "payment_id": self.payment_id,
            "applied": [
                {"component_type": component.component_type, "amount": component.amount}
                for component in self.applied
            ],
            "unapplied_amount": self.unapplied_amount,
        }


@dataclass(frozen=True, slots=True)
class ClaimFinanceFixture:
    claim_id: str
    evaluation_date: date
    principal: MoneyComponent
    interest: RatePeriod
    late_damages: RatePeriod
    enforcement_costs: tuple[MoneyComponent, ...]
    payments: tuple[Payment, ...]
    allocation_rule: PaymentAllocationRule
    assignment_succession: FinanceRelationship
    guarantee_surety: FinanceRelationship
    reimbursement_subrogation_candidate: FinanceRelationship
    disputed_amount: MoneyComponent | None = None

    def with_review_risks(self) -> ClaimFinanceFixture:
        payments = (replace(self.payments[0], source_refs=()),) if self.payments else ()
        return replace(
            self,
            interest=replace(self.interest, basis="statutory_interest_unverified"),
            payments=payments,
            allocation_rule=replace(self.allocation_rule, review_status="conflicting_allocation_claim"),
            disputed_amount=MoneyComponent("component:disputed", "disputed_amount", 125_000, ("fixture:finance#dispute",)),
        )


@dataclass(frozen=True, slots=True)
class ClaimFinanceCalculation:
    claim_id: str
    evaluation_date: date
    balance_review_status: str
    calculated_components: dict[str, int]
    payment_allocations: tuple[PaymentAllocation, ...]
    remaining_balance: int | None
    review_items: tuple[FinanceReviewItem, ...]
    fixture: ClaimFinanceFixture

    def to_json(self) -> JsonObject:
        payload: JsonObject = {
            "schema_version": CALCULATION_SCHEMA_VERSION,
            "model_version": MODEL_VERSION,
            "claim_id": self.claim_id,
            "evaluation_date": self.evaluation_date.isoformat(),
            "balance_review_status": self.balance_review_status,
            "review_items": [item.to_json() for item in self.review_items],
            "assignment_succession": self.fixture.assignment_succession.to_json(),
            "guarantee_surety": self.fixture.guarantee_surety.to_json(),
            "reimbursement_subrogation_candidate": self.fixture.reimbursement_subrogation_candidate.to_json(),
            "non_execution_semantics": "fixture_calculation_only_not_authoritative_balance",
            "pii_profile": {"raw_text_included": False, "source_text_included": False},
        }
        if self.fixture.disputed_amount is not None:
            payload["disputed_amount"] = self.fixture.disputed_amount.to_json()
        if self.remaining_balance is not None:
            payload["calculated_components"] = {
                component_type: {"currency": KRW, "amount": amount}
                for component_type, amount in self.calculated_components.items()
            }
            payload["payment_allocations"] = [allocation.to_json() for allocation in self.payment_allocations]
            payload["remaining_balance"] = {"currency": KRW, "amount": self.remaining_balance}
        return payload


def calculate_claim_finance_fixture(fixture: ClaimFinanceFixture) -> ClaimFinanceCalculation:
    review_items = _review_items(fixture)
    if review_items:
        return ClaimFinanceCalculation(
            fixture.claim_id, fixture.evaluation_date, NEEDS_FINANCE_REVIEW, {}, (), None, tuple(review_items), fixture,
        )

    components = {
        "principal": fixture.principal.amount,
        "interest": _rate_amount(fixture.principal.amount, fixture.interest),
        "late_damages": _rate_amount(fixture.principal.amount, fixture.late_damages),
        "enforcement_costs": sum(cost.amount for cost in fixture.enforcement_costs),
    }
    balances = dict(components)
    allocations = tuple(_allocate_payment(payment, balances, fixture.allocation_rule) for payment in fixture.payments)
    return ClaimFinanceCalculation(
        fixture.claim_id,
        fixture.evaluation_date,
        FIXTURE_REVIEW_STATUS,
        components,
        allocations,
        sum(balances.values()),
        (),
        fixture,
    )


def _rate_amount(principal: int, terms: RatePeriod) -> int:
    days = (terms.end_date - terms.start_date).days
    raw = Decimal(principal) * Decimal(terms.annual_rate_bps) * Decimal(days) / Decimal(3_650_000)
    return int(raw.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _allocate_payment(payment: Payment, balances: dict[str, int], rule: PaymentAllocationRule) -> PaymentAllocation:
    remaining_payment = payment.amount
    applied: list[MoneyComponent] = []
    for component_type in rule.component_order:
        available = balances.get(component_type, 0)
        applied_amount = min(remaining_payment, available)
        if applied_amount <= 0:
            continue
        balances[component_type] = available - applied_amount
        remaining_payment -= applied_amount
        applied.append(MoneyComponent(f"{payment.payment_id}:{component_type}", component_type, applied_amount, payment.source_refs))
        if remaining_payment == 0:
            break
    return PaymentAllocation(payment.payment_id, tuple(applied), remaining_payment)


def _review_items(fixture: ClaimFinanceFixture) -> list[FinanceReviewItem]:
    items: list[FinanceReviewItem] = []
    if _has_missing_source_refs(fixture):
        items.append(FinanceReviewItem("missing_source_ref", "finance facts require non-placeholder source refs", ()))
    if _needs_rate_review(fixture.interest) or _needs_rate_review(fixture.late_damages):
        items.append(FinanceReviewItem("statutory_or_complex_interest", "interest basis is not an explicit fixture rate", _rate_refs(fixture)))
    if fixture.allocation_rule.review_status != EXPLICIT_ALLOCATION_STATUS or not fixture.allocation_rule.component_order:
        items.append(FinanceReviewItem("payment_allocation_conflict", "payment allocation is missing or disputed", fixture.allocation_rule.source_refs))
    if fixture.disputed_amount is not None:
        items.append(FinanceReviewItem("disputed_amount", "disputed amount requires finance review", fixture.disputed_amount.source_refs))
    return items


def _needs_rate_review(terms: RatePeriod) -> bool:
    return terms.basis != EXPLICIT_RATE_BASIS or terms.annual_rate_bps <= 0 or terms.end_date <= terms.start_date


def _rate_refs(fixture: ClaimFinanceFixture) -> tuple[str, ...]:
    return tuple(dict.fromkeys((*fixture.interest.source_refs, *fixture.late_damages.source_refs)))


def _has_missing_source_refs(fixture: ClaimFinanceFixture) -> bool:
    source_groups = (
        fixture.principal.source_refs,
        fixture.interest.source_refs,
        fixture.late_damages.source_refs,
        fixture.allocation_rule.source_refs,
        fixture.assignment_succession.source_refs,
        fixture.guarantee_surety.source_refs,
        fixture.reimbursement_subrogation_candidate.source_refs,
        *(cost.source_refs for cost in fixture.enforcement_costs),
        *(payment.source_refs for payment in fixture.payments),
    )
    return any(not refs or any(_is_placeholder_source_ref(source_ref) for source_ref in refs) for refs in source_groups)


def _is_placeholder_source_ref(source_ref: str) -> bool:
    normalized = source_ref.strip().lower()
    return normalized in PLACEHOLDER_SOURCE_REFS or normalized.startswith("placeholder:") or normalized.startswith("todo:")
