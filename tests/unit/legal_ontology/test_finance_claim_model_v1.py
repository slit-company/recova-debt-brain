from __future__ import annotations

import subprocess
import sys
from dataclasses import replace
from datetime import date
from pathlib import Path

from scripts.legal_ontology.validate_finance_claim_model_v1 import load_finance_model
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


REPO_ROOT = Path(__file__).resolve().parents[3]
FINANCE_MODEL_PATH = REPO_ROOT / "resources" / "finance" / "claim_finance_model_v1.json"
VALIDATOR_PATH = REPO_ROOT / "scripts" / "legal_ontology" / "validate_finance_claim_model_v1.py"


def run_validator(finance_model_path: Path = FINANCE_MODEL_PATH) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), str(finance_model_path)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_validator_accepts_claim_finance_model_resource() -> None:
    # Given: the v1 claim finance model resource.
    # When: the CLI validator checks the finance contract.
    result = run_validator()

    # Then: it proves all required accounting concepts are modeled.
    assert result.returncode == 0
    assert "PASS finance_claim_model" in result.stdout
    assert "components=11" in result.stdout
    assert "allocation_rules=" in result.stdout
    assert "review_triggers=" in result.stdout


def test_validator_rejects_missing_required_component(tmp_path: Path) -> None:
    # Given: a generated resource copy missing the principal component.
    model = load_finance_model(FINANCE_MODEL_PATH)
    invalid_model = model.model_copy(
        update={"component_types": tuple(component for component in model.component_types if component.component_id != "principal")},
    )
    invalid_path = tmp_path / "missing-principal.json"
    _ = invalid_path.write_text(invalid_model.model_dump_json(), encoding="utf-8")

    # When: the CLI validator checks the invalid copy.
    result = run_validator(invalid_path)

    # Then: it fails with the missing component named in diagnostics.
    assert result.returncode != 0
    assert "missing component principal" in result.stderr


def test_fixture_calculator_allocates_payment_and_serializes_schema() -> None:
    # Given: a synthetic, fully explicit claim ledger fixture.
    fixture = _explicit_fixture()

    # When: the deterministic fixture calculator runs.
    result = calculate_claim_finance_fixture(fixture)
    payload = result.to_json()

    # Then: it allocates payment to costs, interest, late damages, then principal.
    assert payload["schema_version"] == "trustgraph-claim-finance-calculation/v1"
    assert payload["claim_id"] == "claim:finance-fixture-001"
    assert payload["balance_review_status"] == "calculated_fixture_only"
    assert object_field(payload, "remaining_balance")["amount"] == 972329
    calculated = object_field(payload, "calculated_components")
    assert object_field(calculated, "interest")["amount"] == 9863
    assert object_field(calculated, "late_damages")["amount"] == 2466
    allocations = object_list_field(payload, "payment_allocations")
    assert object_list_field(allocations[0], "applied") == [
        {"component_type": "enforcement_costs", "amount": 10000},
        {"component_type": "interest", "amount": 9863},
        {"component_type": "late_damages", "amount": 2466},
        {"component_type": "principal", "amount": 27671},
    ]
    assert object_field(payload, "assignment_succession")["status"] == "successor_claimant_reviewed"
    assert object_field(payload, "guarantee_surety")["status"] == "surety_claim_preserved"
    assert object_field(payload, "reimbursement_subrogation_candidate")["status"] == "candidate_preserved_for_review"
    assert payload["pii_profile"] == {"raw_text_included": False, "source_text_included": False}


def test_ambiguous_or_conflicting_balance_returns_finance_review() -> None:
    # Given: a fixture with statutory interest, a disputed amount, and a conflicting allocation rule.
    fixture = _explicit_fixture().with_review_risks()

    # When: the calculator is asked for a balance.
    result = calculate_claim_finance_fixture(fixture)
    payload = result.to_json()

    # Then: it refuses an authoritative balance and emits review items instead.
    assert payload["balance_review_status"] == "needs_finance_review"
    assert "remaining_balance" not in payload
    review_codes = {text_field(item, "code") for item in object_list_field(payload, "review_items")}
    assert {
        "statutory_or_complex_interest",
        "payment_allocation_conflict",
        "disputed_amount",
        "missing_source_ref",
    } <= review_codes


def test_unsupported_allocation_component_returns_finance_review_without_balance() -> None:
    # Given: an explicit fixture allocation rule containing a component the calculator cannot support.
    fixture = _explicit_fixture()
    unsupported_rule = replace(
        fixture.allocation_rule,
        component_order=("unsupported_fee", "principal"),
    )

    # When: the deterministic fixture calculator evaluates the rule.
    result = calculate_claim_finance_fixture(replace(fixture, allocation_rule=unsupported_rule))
    payload = result.to_json()

    # Then: it refuses a balance and preserves the allocation source refs for review.
    assert payload["balance_review_status"] == "needs_finance_review"
    assert "remaining_balance" not in payload
    allocation_reviews = [
        item
        for item in object_list_field(payload, "review_items")
        if text_field(item, "code") == "payment_allocation_conflict"
    ]
    assert allocation_reviews
    assert allocation_reviews[0]["source_refs"] == ["fixture:finance#allocation"]
    assert payload["non_execution_semantics"] == "fixture_calculation_only_not_authoritative_balance"


def test_disputed_amount_placeholder_source_ref_is_preserved_and_reviewed() -> None:
    # Given: a disputed amount whose source ref is still only a placeholder.
    disputed = MoneyComponent(
        "component:disputed",
        "disputed_amount",
        125_000,
        ("placeholder:finance#dispute",),
    )

    # When: the deterministic fixture calculator evaluates the disputed amount.
    result = calculate_claim_finance_fixture(replace(_explicit_fixture(), disputed_amount=disputed))
    payload = result.to_json()

    # Then: the disputed source ref is preserved and the placeholder source is review-blocking.
    review_items = object_list_field(payload, "review_items")
    by_code = {text_field(item, "code"): item for item in review_items}
    assert payload["balance_review_status"] == "needs_finance_review"
    assert "remaining_balance" not in payload
    assert by_code["disputed_amount"]["source_refs"] == ["placeholder:finance#dispute"]
    assert "missing_source_ref" in by_code


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


def _explicit_fixture() -> ClaimFinanceFixture:
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
