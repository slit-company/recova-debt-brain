from __future__ import annotations

from dataclasses import replace
from datetime import date

from trustgraph_legal.finance_claims import (
    ClaimFinanceFixture,
    FinanceRelationship,
    JsonObject,
    MoneyComponent,
    Payment,
    PaymentAllocationRule,
    RatePeriod,
    calculate_claim_finance_fixture,
)
from trustgraph_legal.finance_review_bridge import bridge_finance_review_to_workflow


def test_clean_fixture_supports_advisory_readiness_without_balance_authority() -> None:
    # Given: a fully explicit fixture finance calculation.
    calculation = calculate_claim_finance_fixture(_explicit_bridge_fixture())

    # When: the finance workflow bridge maps it for workflow judgment.
    bridge = bridge_finance_review_to_workflow(calculation).to_json()

    # Then: it supports advisory readiness without authorizing a collectable balance.
    assert bridge["schema_version"] == "trustgraph-finance-workflow-bridge/v1"
    assert bridge["claim_id"] == "claim:finance-fixture-001"
    assert bridge["workflow_review_status"] == "finance_fixture_advisory_ready"
    assert bridge["advisory_readiness"] == "fixture_finance_can_support_workflow_review"
    assert bridge["collectable_balance_authority"] is False
    assert bridge["non_execution_semantics"] == "fixture_calculation_only_not_authoritative_balance"
    assert bridge["signals"] == []
    assert object_field(bridge, "workflow_flags") == {
        "finance_reconciliation_needed": False,
        "disputed_balance_hold": False,
        "unsupported_interest_review": False,
        "payment_allocation_review": False,
    }


def test_ambiguous_allocation_creates_finance_reconciliation_loop() -> None:
    # Given: a finance calculation with conflicting payment allocation review.
    calculation = calculate_claim_finance_fixture(_explicit_bridge_fixture().with_review_risks())

    # When: the bridge maps finance review items into workflow signals.
    bridge = bridge_finance_review_to_workflow(calculation).to_json()

    # Then: workflow judgment can hold for reconciliation without an authoritative balance.
    assert bridge["workflow_review_status"] == "finance_review_required"
    assert bridge["advisory_readiness"] == "finance_reconciliation_required_before_route_readiness"
    assert bridge["collectable_balance_authority"] is False
    assert object_field(bridge, "workflow_flags")["finance_reconciliation_needed"] is True
    signals = {text_field(signal, "signal_code"): signal for signal in object_list_field(bridge, "signals")}
    assert "payment_allocation_review" in signals
    allocation_signal = signals["payment_allocation_review"]
    assert allocation_signal["review_code"] == "payment_allocation_conflict"
    assert allocation_signal["remediation_loop"] == "finance_reconciliation_loop"
    assert allocation_signal["workflow_hold"] is True
    assert allocation_signal["source_refs"] == ["fixture:finance#allocation"]


def test_disputed_amount_creates_disputed_balance_hold() -> None:
    # Given: a finance calculation with a disputed amount.
    calculation = calculate_claim_finance_fixture(_explicit_bridge_fixture().with_review_risks())

    # When: the bridge maps it for workflow judgment.
    bridge = bridge_finance_review_to_workflow(calculation).to_json()

    # Then: disputed balance review is surfaced as a hold, not a balance authority.
    assert object_field(bridge, "workflow_flags")["disputed_balance_hold"] is True
    signals = {text_field(signal, "signal_code"): signal for signal in object_list_field(bridge, "signals")}
    disputed_signal = signals["disputed_balance_hold"]
    assert disputed_signal["review_code"] == "disputed_amount"
    assert disputed_signal["category"] == "finance"
    assert disputed_signal["workflow_hold"] is True
    assert disputed_signal["source_refs"] == ["fixture:finance#dispute"]
    assert "remaining_balance" not in bridge


def test_unsupported_interest_review_is_source_traceable() -> None:
    # Given: a fixture whose interest basis requires review.
    fixture = _explicit_bridge_fixture()
    calculation = calculate_claim_finance_fixture(
        replace(fixture, interest=replace(fixture.interest, basis="statutory_interest_unverified")),
    )

    # When: the bridge maps finance review items.
    bridge = bridge_finance_review_to_workflow(calculation).to_json()

    # Then: the interest review becomes a source-traceable workflow signal.
    assert object_field(bridge, "workflow_flags")["unsupported_interest_review"] is True
    signals = {text_field(signal, "signal_code"): signal for signal in object_list_field(bridge, "signals")}
    interest_signal = signals["unsupported_interest_review"]
    assert interest_signal["review_code"] == "statutory_or_complex_interest"
    assert interest_signal["remediation_loop"] == "interest_basis_review_loop"
    assert interest_signal["source_refs"] == [
        "fixture:finance#interest",
        "fixture:finance#late-damages",
    ]


def object_field(entry: JsonObject, field: str) -> JsonObject:
    value = entry[field]
    assert isinstance(value, dict)
    return value


def object_list_field(entry: JsonObject, field: str) -> list[JsonObject]:
    value = entry[field]
    assert isinstance(value, list)
    objects: list[JsonObject] = []
    for item in value:
        assert isinstance(item, dict)
        objects.append(item)
    return objects


def text_field(entry: JsonObject, field: str) -> str:
    value = entry[field]
    assert isinstance(value, str)
    return value


def _explicit_bridge_fixture() -> ClaimFinanceFixture:
    return ClaimFinanceFixture(
        claim_id="claim:finance-fixture-001",
        evaluation_date=date(2026, 7, 7),
        principal=MoneyComponent("component:principal", "principal", 1_000_000, ("fixture:finance#principal",)),
        interest=RatePeriod(
            component_type="interest",
            annual_rate_bps=1200,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            basis="explicit_contract_rate",
            source_refs=("fixture:finance#interest",),
        ),
        late_damages=RatePeriod(
            component_type="late_damages",
            annual_rate_bps=300,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            basis="explicit_contract_rate",
            source_refs=("fixture:finance#late-damages",),
        ),
        enforcement_costs=(MoneyComponent("component:cost", "enforcement_costs", 10_000, ("fixture:finance#cost",)),),
        payments=(Payment("payment:001", 50_000, date(2026, 2, 1), ("fixture:finance#payment",)),),
        allocation_rule=PaymentAllocationRule(
            rule_id="allocation:fixture-costs-interest-late-principal",
            component_order=("enforcement_costs", "interest", "late_damages", "principal"),
            review_status="explicit_fixture_rule",
            source_refs=("fixture:finance#allocation",),
        ),
        assignment_succession=FinanceRelationship(
            relationship_type="assignment_succession",
            status="successor_claimant_reviewed",
            source_refs=("fixture:finance#assignment",),
        ),
        guarantee_surety=FinanceRelationship(
            relationship_type="guarantee_surety",
            status="surety_claim_preserved",
            source_refs=("fixture:finance#surety",),
        ),
        reimbursement_subrogation_candidate=FinanceRelationship(
            relationship_type="reimbursement_subrogation_candidate",
            status="candidate_preserved_for_review",
            source_refs=("fixture:finance#subrogation",),
        ),
    )
